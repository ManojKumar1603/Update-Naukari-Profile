from playwright.sync_api import sync_playwright
from datetime import datetime
from pathlib import Path
import re
import os


def sanitize_filename(name):
    cleaned = re.sub(r"\s+", "_", name.strip())
    cleaned = re.sub(r"[^A-Za-z0-9_]", "", cleaned)
    return cleaned


PROXIES = [
    "http://ciadmdtj:1f2beqnn2it7@31.59.20.176:6754",
    "http://ciadmdtj:1f2beqnn2it7@31.56.127.193:7684",
    "http://ciadmdtj:1f2beqnn2it7@45.38.107.97:6014",
    "http://ciadmdtj:1f2beqnn2it7@107.172.163.27:6543",
    "http://ciadmdtj:1f2beqnn2it7@198.23.243.226:6361",
    "http://ciadmdtj:1f2beqnn2it7@216.10.27.159:6837",
    "http://ciadmdtj:1f2beqnn2it7@142.111.67.146:5611",
    "http://ciadmdtj:1f2beqnn2it7@191.96.254.138:6185",
    "http://ciadmdtj:1f2beqnn2it7@31.58.9.4:6077",
    "http://ciadmdtj:1f2beqnn2it7@23.229.19.94:8689",
]


def cleanup(resume_path=None):
    """Delete downloaded resume and screenshots."""
    print("\n--- Cleanup ---")
    # Delete resume pdf
    if resume_path:
        try:
            Path(resume_path).unlink(missing_ok=True)
            print(f"Deleted: {Path(resume_path).name}")
        except Exception:
            pass
    # Delete any leftover pngs or pdfs in cwd
    for pattern in ["*.png", "*.pdf"]:
        for f in Path.cwd().glob(pattern):
            try:
                f.unlink()
                print(f"Deleted: {f.name}")
            except Exception:
                pass
    # Clear sensitive env vars
    for var in ["NAUKRI_EMAIL", "NAUKRI_PASSWORD"]:
        os.environ.pop(var, None)
    print("Cleared env vars.")
    print("--- Cleanup done ---")


def try_login_and_update(proxy_url, email, password, playwright):
    host_port = proxy_url.split("@")[-1]
    print(f"Trying proxy: {host_port}")

    browser = playwright.chromium.launch(
        headless=True,
        proxy={"server": proxy_url},
        args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
            "--window-size=1366,768",
            "--disable-infobars",
            "--disable-extensions",
        ]
    )

    resume_path = None
    try:
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            extra_http_headers={
                "Accept-Language": "en-IN,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            }
        )

        page = context.new_page()

        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-IN', 'en'] });
            window.chrome = { runtime: {} };
        """)

        # -------------------------------------------------------
        # STEP 1 — Check proxy works (fast: domcontentloaded not networkidle)
        # -------------------------------------------------------
        page.goto("https://www.naukri.com/nlogin/login", wait_until="domcontentloaded", timeout=30000)

        if "Access Denied" in page.title() or "access denied" in page.title().lower():
            print(f"  Blocked — skipping.")
            return False, None

        print(f"  Login page loaded: {page.title()}")

        # -------------------------------------------------------
        # STEP 2 — Login
        # -------------------------------------------------------
        email_selectors = [
            "#usernameField",
            "input[type='email']",
            "input[name='username']",
            "input[placeholder*='email' i]",
            "input[id*='username' i]",
            "input[id*='email' i]",
        ]
        for selector in email_selectors:
            try:
                el = page.locator(selector)
                if el.count() > 0:
                    el.first.fill(email)
                    print(f"  Email filled: {selector}")
                    break
            except Exception:
                continue
        else:
            raise Exception("Email field not found.")

        password_selectors = [
            "#passwordField",
            "input[type='password']",
            "input[name='password']",
            "input[placeholder*='password' i]",
            "input[id*='password' i]",
        ]
        for selector in password_selectors:
            try:
                el = page.locator(selector)
                if el.count() > 0:
                    el.first.fill(password)
                    print(f"  Password filled: {selector}")
                    break
            except Exception:
                continue
        else:
            raise Exception("Password field not found.")

        # Click login and wait for navigation
        with page.expect_navigation(wait_until="domcontentloaded", timeout=30000):
            for selector in ["button[type='submit']", "button:has-text('Login')", "input[type='submit']"]:
                try:
                    el = page.locator(selector)
                    if el.count() > 0:
                        el.first.click()
                        print(f"  Login clicked: {selector}")
                        break
                except Exception:
                    continue

        print(f"  Post-login URL: {page.url}")

        if "nlogin" in page.url or "login" in page.url:
            raise Exception("Login failed — bad credentials or captcha.")

        print("  Login successful!")

        # -------------------------------------------------------
        # STEP 3 — Profile page
        # -------------------------------------------------------
        page.goto("https://www.naukri.com/mnjuser/profile", wait_until="domcontentloaded", timeout=30000)

        # Wait only for the specific element we need
        page.wait_for_selector(".fullname", timeout=30000)

        profile_name = page.locator(".fullname").inner_text()
        safe_name = sanitize_filename(profile_name)
        print(f"  Profile: {profile_name}")

        # -------------------------------------------------------
        # STEP 4 — Download resume
        # -------------------------------------------------------
        page.wait_for_selector("[data-title='download-resume']", timeout=30000)
        with page.expect_download(timeout=30000) as download_info:
            page.locator("[data-title='download-resume']").first.click(force=True)
        download = download_info.value

        today = datetime.now().strftime("%d_%B_%Y")
        filename = f"{safe_name}_Resume_{today}.pdf"
        resume_path = str(Path.cwd() / filename)
        download.save_as(resume_path)
        print(f"  Resume downloaded: {filename}")

        # -------------------------------------------------------
        # STEP 5 — Upload resume
        # -------------------------------------------------------
        for selector in ["#attachCV", "#fileUpload"]:
            try:
                page.set_input_files(selector, resume_path)
                print(f"  Uploaded via {selector}")
                break
            except Exception:
                continue

        # Wait for upload confirmation instead of blind sleep
        page.wait_for_timeout(3000)
        print("  Upload done!")

        return True, resume_path

    finally:
        browser.close()

    return False, resume_path


def update_naukri_resume():
    email = os.environ.get("NAUKRI_EMAIL", "")
    password = os.environ.get("NAUKRI_PASSWORD", "")

    if not email or not password:
        raise Exception("NAUKRI_EMAIL and NAUKRI_PASSWORD must be set.")

    resume_path = None
    success = False

    try:
        with sync_playwright() as p:
            for i, proxy in enumerate(PROXIES):
                try:
                    success, resume_path = try_login_and_update(proxy, email, password, p)
                    if success:
                        print(f"\nSuccess with proxy {i + 1}/{len(PROXIES)}")
                        break
                except Exception as e:
                    print(f"  Proxy {i + 1} failed: {e}")
                    continue

        if not success:
            raise Exception("All proxies failed.")

    finally:
        cleanup(resume_path)


if __name__ == "__main__":
    update_naukri_resume()