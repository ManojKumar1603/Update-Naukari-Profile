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
    page.goto(
        "https://www.naukri.com/nlogin/login?URL=https://www.naukri.com/mnjuser/homepage",
        wait_until="domcontentloaded"
    )
    page.wait_for_timeout(3000)
    page.fill("#usernameField", username)
    page.fill("#passwordField", password)
    page.click("button.blue-btn[type='submit']")
    # Wait for redirect after login by waiting for URL to change away from login page
    page.wait_for_url("**/mnjuser/homepage**", timeout=60000)
    page.wait_for_timeout(4000)
    print("Login successful.")


def update_naukri_resume(username: str, password: str):
    with sync_playwright() as p:

        # ------------------------------------------------
        # STEP 1: LAUNCH BROWSER & LOGIN
        # ------------------------------------------------
        browser = p.chromium.launch(
            headless=False,
            args=["--start-maximized"]
        )
        context = browser.new_context(
            accept_downloads=True,
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        perform_login(page, username, password)


        # ------------------------------------------------
        # STEP 2: OPEN PROFILE
        # ------------------------------------------------
        print("Opening profile...")
        page.wait_for_selector("a[href='/mnjuser/profile']", timeout=60000)
        page.click("a[href='/mnjuser/profile']")
        # Wait for profile page URL
        page.wait_for_url("**/mnjuser/profile**", timeout=60000)
        page.wait_for_timeout(5000)


        # ------------------------------------------------
        # STEP 3: GET PROFILE NAME
        # ------------------------------------------------
        print("Fetching profile name...")
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
        # STEP 5: OPEN UPDATE RESUME SECTION
        # ------------------------------------------------
        print("Opening update resume section...")
        page.wait_for_selector("input.dummyUpload[value='Update resume']", timeout=60000)
        page.wait_for_timeout(3000)


        # ------------------------------------------------
        # STEP 6: UPLOAD RESUME
        # ------------------------------------------------
        print("Uploading resume...")

        try:
            page.set_input_files("#attachCV", str(resume_path))
            page.wait_for_timeout(5000)
            print("Resume uploaded using #attachCV")
        except Exception as e:
            print(f"Primary upload failed ({e}), trying #fileUpload...")
            page.set_input_files("#fileUpload", str(resume_path))
            page.wait_for_timeout(5000)
            print("Resume uploaded using #fileUpload")

        page.wait_for_timeout(5000)
        print("Resume upload successful.")


        # ------------------------------------------------
        # STEP 7: OPEN MENU
        # ------------------------------------------------
        print("Opening menu...")
        page.wait_for_selector(".nI-gNb-drawer__bars", timeout=30000)
        page.locator(".nI-gNb-drawer__bars").click()
        page.wait_for_timeout(3000)


        # ------------------------------------------------
        # STEP 8: LOGOUT
        # ------------------------------------------------
        print("Logging out...")
        page.wait_for_selector("[data-type='logoutLink']", timeout=30000)
        page.locator("[data-type='logoutLink']").click()
        page.wait_for_timeout(5000)


        # ------------------------------------------------
        # STEP 9: CLOSE BROWSER
        # ------------------------------------------------
        print("Closing browser...")
        browser.close()
        print("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate Naukri Resume Update")
    parser.add_argument("--username", required=True, help="Naukri login email")
    parser.add_argument("--password", required=True, help="Naukri login password")

    args = parser.parse_args()

    update_naukri_resume(username=args.username, password=args.password)