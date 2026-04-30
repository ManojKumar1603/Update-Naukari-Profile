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
            ]
        )

        # ✅ Load saved session (no OTP)
        context = browser.new_context(
            storage_state="auth.json",
            viewport={"width": 1366, "height": 768},
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )

        page = context.new_page()

        print("Opening profile page...")
        page.goto("https://www.naukri.com/mnjuser/profile", wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        # ❗ Session validation
        if "login" in page.url:
            page.screenshot(path="session_expired.png", full_page=True)
            raise Exception("Session expired. Regenerate auth.json")

        print("Fetching profile name...")
        page.wait_for_selector(".fullname", timeout=60000)
        profile_name = page.locator(".fullname").inner_text()
        safe_name = sanitize_filename(profile_name)

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
        except:
            page.set_input_files("#fileUpload", str(resume_path))
            print("Uploaded via #fileUpload")

        # wait for upload to complete
        page.wait_for_timeout(5000)

        # 📸 Screenshot AFTER upload
        screenshot_path = str(Path.cwd() / "after_upload.png")
        page.screenshot(path=screenshot_path, full_page=True)

        print(f"✅ Resume upload successful. Screenshot saved: {screenshot_path}")

        browser.close()
        print("Done!")


if __name__ == "__main__":
    update_naukri_resume()