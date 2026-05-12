from playwright.sync_api import sync_playwright
from datetime import datetime
from pathlib import Path
import re
import os
import shutil


def sanitize_filename(name):
    cleaned = re.sub(r"\s+", "_", name.strip())
    cleaned = re.sub(r"[^A-Za-z0-9_]", "", cleaned)
    return cleaned


# All 10 proxies — will try each one until one works
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

# Track files created during the run for cleanup
created_files = []


def cleanup():
    """Delete all downloaded/created files and clear sensitive env variables."""
    print("\n--- Cleanup started ---")

    # Delete all tracked files
    for f in created_files:
        try:
            path = Path(f)
            if path.exists():
                path.unlink()
                print(f"Deleted file: {path.name}")
        except Exception as e:
            print(f"Could not delete {f}: {e}")

    # Delete all .png screenshots
    for png in Path.cwd().glob("*.png"):
        try:
            png.unlink()
            print(f"Deleted screenshot: {png.name}")
        except Exception as e:
            print(f"Could not delete {png}: {e}")

    # Delete all .pdf files
    for pdf in Path.cwd().glob("*.pdf"):
        try:
            pdf.unlink()
            print(f"Deleted resume: {pdf.name}")
        except Exception as e:
            print(f"Could not delete {pdf}: {e}")

    # Clear sensitive environment variables from current process
    for var in ["NAUKRI_EMAIL", "NAUKRI_PASSWORD"]:
        if var in os.environ:
            os.environ.pop(var)
            print(f"Cleared env var: {var}")

    # Delete Playwright browser cache to free space
    playwright_cache = Path.home() / "AppData" / "Local" / "ms-playwright"
    if playwright_cache.exists():
        try:
            shutil.rmtree(playwright_cache)
            print(f"Deleted Playwright cache: {playwright_cache}")
        except Exception as e:
            print(f"Could not delete Playwright cache: {e}")

    print("--- Cleanup done ---\n")


def try_login_and_update(proxy_url, email, password, playwright):
    """Try the full flow with a given proxy. Returns True on success, False on Access Denied."""

    host_port = proxy_url.split("@")[-1]
    print(f"\n--- Trying proxy: {host_port} ---")

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
        # STEP 1 — Check if proxy can access Naukri
        # -------------------------------------------------------
        print("Navigating to Naukri login page...")
        page.goto("https://www.naukri.com/nlogin/login", wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)

        print("Login page URL:", page.url)
        print("Login page title:", page.title())

        if "Access Denied" in page.title() or "access denied" in page.title().lower():
            print(f"Proxy {host_port} blocked by Naukri — trying next proxy...")
            return False

        # -------------------------------------------------------
        # STEP 2 — Fill login form
        # -------------------------------------------------------
        inputs = page.locator("input").all()
        print(f"Found {len(inputs)} input fields:")
        for i, inp in enumerate(inputs):
            try:
                print(f"  input[{i}] id='{inp.get_attribute('id')}' type='{inp.get_attribute('type')}' placeholder='{inp.get_attribute('placeholder')}'")
            except Exception:
                pass

        email_selectors = [
            "#usernameField",
            "input[placeholder*='Email']",
            "input[placeholder*='email']",
            "input[type='email']",
            "input[name='username']",
            "input[id*='username']",
            "input[id*='email']",
        ]

        email_filled = False
        for selector in email_selectors:
            try:
                if page.locator(selector).count() > 0:
                    page.locator(selector).first.fill(email)
                    print(f"Email entered using: {selector}")
                    email_filled = True
                    break
            except Exception:
                continue

        if not email_filled:
            page.screenshot(path="login_page.png", full_page=True)
            created_files.append("login_page.png")
            raise Exception("Could not find email input field. Check login_page.png.")

        page.wait_for_timeout(500)

        password_selectors = [
            "#passwordField",
            "input[placeholder*='Password']",
            "input[placeholder*='password']",
            "input[type='password']",
            "input[name='password']",
            "input[id*='password']",
        ]

        password_filled = False
        for selector in password_selectors:
            try:
                if page.locator(selector).count() > 0:
                    page.locator(selector).first.fill(password)
                    print(f"Password entered using: {selector}")
                    password_filled = True
                    break
            except Exception:
                continue

        if not password_filled:
            page.screenshot(path="login_page.png", full_page=True)
            created_files.append("login_page.png")
            raise Exception("Could not find password input field. Check login_page.png.")

        page.wait_for_timeout(500)

        login_button_selectors = [
            "button[type='submit']",
            "button:has-text('Login')",
            "button:has-text('Sign in')",
            "input[type='submit']",
            ".loginButton",
            "#login-submit",
        ]

        login_clicked = False
        for selector in login_button_selectors:
            try:
                if page.locator(selector).count() > 0:
                    page.locator(selector).first.click()
                    print(f"Login button clicked using: {selector}")
                    login_clicked = True
                    break
            except Exception:
                continue

        if not login_clicked:
            raise Exception("Could not find login button.")

        page.wait_for_timeout(8000)
        page.screenshot(path="after_login.png", full_page=True)
        created_files.append("after_login.png")
        print("URL after login:", page.url)
        print("Title after login:", page.title())

        if "nlogin" in page.url or "login" in page.url:
            raise Exception("Login failed — wrong credentials or captcha. Check after_login.png.")

        print("Login successful!")

        # -------------------------------------------------------
        # STEP 3 — Go to profile page
        # -------------------------------------------------------
        print("Opening profile page...")
        page.goto("https://www.naukri.com/mnjuser/profile", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)

        page.screenshot(path="profile_page.png", full_page=True)
        created_files.append("profile_page.png")
        print("Profile URL:", page.url)
        print("Profile title:", page.title())

        if "Access Denied" in page.title() or "access denied" in page.title().lower():
            raise Exception("Access Denied on profile page. Check profile_page.png.")

        if not page.locator(".fullname").count():
            raise Exception("Profile not loaded. Check profile_page.png.")

        page.wait_for_selector(".fullname", timeout=60000)
        profile_name = page.locator(".fullname").inner_text()
        safe_name = sanitize_filename(profile_name)
        print(f"Profile name: {profile_name}")

        # -------------------------------------------------------
        # STEP 4 — Download resume
        # -------------------------------------------------------
        print("Downloading resume...")
        page.wait_for_selector("[data-title='download-resume']", timeout=60000)
        with page.expect_download() as download_info:
            page.locator("[data-title='download-resume']").first.click(force=True)
        download = download_info.value

        today = datetime.now().strftime("%d_%B_%Y")
        filename = f"{safe_name}_Resume_{today}.pdf"
        resume_path = Path.cwd() / filename
        download.save_as(str(resume_path))
        created_files.append(str(resume_path))
        print(f"Resume downloaded: {resume_path}")

        # -------------------------------------------------------
        # STEP 5 — Upload resume
        # -------------------------------------------------------
        print("Uploading resume...")
        try:
            page.set_input_files("#attachCV", str(resume_path))
            print("Uploaded via #attachCV")
        except Exception:
            try:
                page.set_input_files("#fileUpload", str(resume_path))
                print("Uploaded via #fileUpload")
            except Exception as e:
                raise Exception(f"Resume upload failed: {e}")

        page.wait_for_timeout(5000)
        page.screenshot(path="after_upload.png", full_page=True)
        created_files.append("after_upload.png")
        print("Resume upload successful!")

        return True

    finally:
        browser.close()


def update_naukri_resume():
    email = os.environ.get("NAUKRI_EMAIL", "")
    password = os.environ.get("NAUKRI_PASSWORD", "")

    if not email or not password:
        raise Exception("NAUKRI_EMAIL and NAUKRI_PASSWORD environment variables must be set.")

    success = False
    try:
        with sync_playwright() as p:
            for i, proxy in enumerate(PROXIES):
                try:
                    result = try_login_and_update(proxy, email, password, p)
                    if result:
                        print(f"\nDone! Succeeded with proxy {i + 1}/{len(PROXIES)}")
                        success = True
                        break
                except Exception as e:
                    print(f"Proxy {i + 1} error: {e}")
                    continue

        if not success:
            raise Exception("All 10 proxies failed. Check screenshots for details.")

    finally:
        # Always cleanup regardless of success or failure
        cleanup()


if __name__ == "__main__":
    update_naukri_resume()