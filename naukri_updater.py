from playwright.sync_api import sync_playwright
from datetime import datetime
from pathlib import Path
import argparse
import re


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r"\s+", "_", name.strip())
    cleaned = re.sub(r"[^A-Za-z0-9_]", "", cleaned)
    return cleaned


def perform_login(page, username, password):
    print("Opening login page...")
    page.goto("https://www.naukri.com/nlogin/login?URL=https://www.naukri.com/mnjuser/homepage")
    page.fill("#usernameField", username)
    page.fill("#passwordField", password)
    page.click("button.blue-btn[type='submit']")
    page.wait_for_timeout(5000)
    print("Login successful.")


def update_naukri_resume(username: str, password: str):
    with sync_playwright() as p:

        # ------------------------------------------------
        # STEP 1: LOGIN (FIRST PASS)
        # ------------------------------------------------
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        perform_login(page, username, password)

        print("Closing browser after first login to avoid UI conflicts...")
        page.wait_for_timeout(3000)
        browser.close()


        # ------------------------------------------------
        # STEP 1 REPEAT: LOGIN AGAIN (SECOND PASS)
        # ------------------------------------------------
        print("Reopening browser and repeating login...")

        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        perform_login(page, username, password)


        # ------------------------------------------------
        # STEP 2: OPEN PROFILE
        # ------------------------------------------------
        print("Opening profile...")
        page.wait_for_selector("a[href='/mnjuser/profile']", timeout=60000)
        page.click("a[href='/mnjuser/profile']")
        page.wait_for_timeout(5000)


        # ------------------------------------------------
        # STEP 3: GET PROFILE NAME
        # ------------------------------------------------
        page.wait_for_selector(".fullname", timeout=60000)
        profile_name = page.locator(".fullname").inner_text()
        safe_name = sanitize_filename(profile_name)
        print(f"Detected profile name: {profile_name}")


        # ------------------------------------------------
        # STEP 4: DOWNLOAD RESUME
        # ------------------------------------------------
        print("Downloading resume...")
        page.wait_for_selector("[data-title='download-resume']", timeout=60000)

        with page.expect_download() as download_info:
            page.locator("[data-title='download-resume']").first.click(force=True)
            page.wait_for_timeout(5000)

        download = download_info.value

        today = datetime.now().strftime("%d_%B_%Y")
        filename = f"{safe_name}_Resume_{today}.pdf"
        resume_path = Path.cwd() / filename

        download.save_as(str(resume_path))
        print(f"Resume downloaded: {resume_path}")


        # ------------------------------------------------
        # STEP 5: UPDATE RESUME
        # ------------------------------------------------
        print("Opening update resume section...")
        page.wait_for_selector("input.dummyUpload[value='Update resume']", timeout=60000)
        page.wait_for_timeout(5000)


        # ------------------------------------------------
        # STEP 6: UPLOAD RESUME
        # ------------------------------------------------
        print("Uploading resume...")

        try:
            page.set_input_files("#attachCV", str(resume_path))
            page.wait_for_timeout(5000)
            print("Resume uploaded using #attachCV")
        except Exception:
            print("Primary upload failed, trying #fileUpload...")
            page.set_input_files("#fileUpload", str(resume_path))
            page.wait_for_timeout(5000)
            print("Resume uploaded using #fileUpload")

        page.wait_for_timeout(3000)
        print("Resume upload successful.")


        # ------------------------------------------------
        # STEP 7: OPEN MENU
        # ------------------------------------------------
        print("Opening menu...")
        page.wait_for_selector(".nI-gNb-drawer__bars", timeout=30000)
        page.locator(".nI-gNb-drawer__bars").click()
        page.wait_for_timeout(5000)


        # ------------------------------------------------
        # STEP 8: LOGOUT
        # ------------------------------------------------
        print("Logging out...")
        page.wait_for_selector("[data-type='logoutLink']", timeout=30000)
        page.locator("[data-type='logoutLink']").click()
        page.wait_for_timeout(5000)

        page.wait_for_timeout(3000)


        # ------------------------------------------------
        # STEP 9: CLOSE BROWSER
        # ------------------------------------------------
        print("Closing browser...")
        browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate Naukri Resume Update")
    parser.add_argument("--username", required=True, help="Naukri login email")
    parser.add_argument("--password", required=True, help="Naukri login password")

    args = parser.parse_args()

    update_naukri_resume(username=args.username, password=args.password)

