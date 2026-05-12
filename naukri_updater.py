from playwright.sync_api import sync_playwright
from datetime import datetime
from pathlib import Path
import re
import os


def sanitize_filename(name):
    cleaned = re.sub(r"\s+", "_", name.strip())
    cleaned = re.sub(r"[^A-Za-z0-9_]", "", cleaned)
    return cleaned


def update_naukri_resume():
    email = os.environ.get("NAUKRI_EMAIL", "")
    password = os.environ.get("NAUKRI_PASSWORD", "")

    if not email or not password:
        raise Exception("NAUKRI_EMAIL and NAUKRI_PASSWORD environment variables must be set.")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--window-size=1366,768",
                "--disable-infobars",
                "--disable-extensions",
            ]
        )

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

        # Hide automation signals
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-IN', 'en'] });
            window.chrome = { runtime: {} };
        """)

        # -------------------------------------------------------
        # STEP 1 — Login fresh
        # -------------------------------------------------------
        print("Navigating to Naukri login page...")
        page.goto("https://www.naukri.com/nlogin/login", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        page.screenshot(path="login_page.png", full_page=True)
        print("Current URL:", page.url)

        print("Entering email...")
        page.locator("#usernameField").fill(email)
        page.wait_for_timeout(500)

        print("Entering password...")
        page.locator("#passwordField").fill(password)
        page.wait_for_timeout(500)

        print("Clicking login button...")
        page.locator("button[type='submit']").click()

        # Wait for redirect after login
        page.wait_for_timeout(6000)
        page.screenshot(path="after_login.png", full_page=True)
        print("URL after login:", page.url)

        # Detect login failure
        if "nlogin" in page.url or "login" in page.url:
            raise Exception("Login failed — wrong email/password or Naukri is showing a captcha. Check after_login.png.")

        print("Login successful!")

        # -------------------------------------------------------
        # STEP 2 — Go to profile page
        # -------------------------------------------------------
        print("Opening profile page...")
        page.goto("https://www.naukri.com/mnjuser/profile", wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        page.screenshot(path="profile_page.png", full_page=True)
        print("Current URL:", page.url)
        print("Page title:", page.title())

        if "Access Denied" in page.title() or "access denied" in page.title().lower():
            raise Exception("Access Denied on profile page. Check profile_page.png.")

        if not page.locator(".fullname").count():
            raise Exception("Profile not loaded — .fullname element not found. Check profile_page.png.")

        print("Fetching profile name...")
        page.wait_for_selector(".fullname", timeout=60000)
        profile_name = page.locator(".fullname").inner_text()
        safe_name = sanitize_filename(profile_name)
        print(f"Profile name: {profile_name}")

        # -------------------------------------------------------
        # STEP 3 — Download resume
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
        print(f"Resume downloaded: {resume_path}")

        # -------------------------------------------------------
        # STEP 4 — Upload resume (triggers "profile updated" on Naukri)
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
                raise Exception(f"Resume upload failed — could not find upload input: {e}")

        page.wait_for_timeout(5000)

        page.screenshot(path="after_upload.png", full_page=True)
        print("Resume upload successful. Screenshot saved: after_upload.png")

        browser.close()
        print("Done!")


if __name__ == "__main__":
    update_naukri_resume()