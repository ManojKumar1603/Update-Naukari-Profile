from playwright.sync_api import sync_playwright
from datetime import datetime
from pathlib import Path
import re


def sanitize_filename(name):
    cleaned = re.sub(r"\s+", "_", name.strip())
    cleaned = re.sub(r"[^A-Za-z0-9_]", "", cleaned)
    return cleaned


def update_naukri_resume():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--window-size=1366,768",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-infobars",
                "--disable-extensions",
            ]
        )

        # Load saved session (no OTP)
        context = browser.new_context(
            storage_state="auth.json",
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

        # Small human-like pause before navigating
        page.wait_for_timeout(2000)

        print("Opening profile page...")
        page.goto("https://www.naukri.com/mnjuser/profile", wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        # Debug screenshot always saved
        page.screenshot(path="debug_page.png", full_page=True)
        print("Current URL:", page.url)
        print("Page title:", page.title())

        # Detect login failure — redirected to login page
        if "login" in page.url or "nlogin" in page.url:
            raise Exception("Session invalid — redirected to login. Regenerate auth.json.")

        # Detect access denied
        if "Access Denied" in page.title() or "access denied" in page.title().lower():
            raise Exception("Access Denied — Naukri blocked the request. Regenerate auth.json or check bot detection fixes.")

        # Check if profile element exists
        if not page.locator(".fullname").count():
            raise Exception("Not logged in — profile not loaded. Regenerate auth.json.")

        print("Fetching profile name...")
        page.wait_for_selector(".fullname", timeout=60000)
        profile_name = page.locator(".fullname").inner_text()
        safe_name = sanitize_filename(profile_name)
        print(f"Profile name: {profile_name}")

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

        # Wait for upload to complete
        page.wait_for_timeout(5000)

        # Screenshot after upload
        screenshot_path = str(Path.cwd() / "after_upload.png")
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Resume upload successful. Screenshot saved: {screenshot_path}")

        browser.close()
        print("Done!")


if __name__ == "__main__":
    update_naukri_resume()