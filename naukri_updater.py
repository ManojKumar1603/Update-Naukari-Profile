from playwright.sync_api import sync_playwright
from datetime import datetime
from pathlib import Path
import argparse
import re
import os


def sanitize_filename(name):
    cleaned = re.sub(r"\s+", "_", name.strip())
    cleaned = re.sub(r"[^A-Za-z0-9_]", "", cleaned)
    return cleaned


def get_chrome_path():
    paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\\" + os.environ.get("USERNAME", "") + r"\AppData\Local\Google\Chrome\Application\chrome.exe",
    ]
    for path in paths:
        if os.path.exists(path):
            print("Found Chrome at: " + path)
            return path
    print("Chrome not found, using bundled Chromium")
    return None


def perform_login(page, username, password):
    print("Opening login page...")
    page.goto(
        "https://www.naukri.com/nlogin/login?URL=https://www.naukri.com/mnjuser/homepage",
        wait_until="domcontentloaded"
    )
    page.wait_for_timeout(5000)
    print("URL after goto: " + page.url)
    print("Title after goto: " + page.title())

    if "Access Denied" in page.title():
        raise Exception("Naukri returned Access Denied.")

    page.wait_for_selector("#usernameField", timeout=30000)

    page.locator("#usernameField").click()
    page.locator("#usernameField").fill("")
    page.wait_for_timeout(500)
    page.type("#usernameField", username, delay=80)

    page.locator("#passwordField").click()
    page.locator("#passwordField").fill("")
    page.wait_for_timeout(500)
    page.type("#passwordField", password, delay=80)

    page.wait_for_timeout(1000)
    page.click("button.blue-btn[type='submit']")
    page.wait_for_url("**/mnjuser/homepage**", timeout=60000)
    page.wait_for_timeout(4000)
    print("Login successful.")


def update_naukri_resume(username, password):
    with sync_playwright() as p:

        chrome_path = get_chrome_path()

        launch_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--window-size=1366,768",
        ]

        if chrome_path:
            print("Launching with real Chrome...")
            browser = p.chromium.launch(
                executable_path=chrome_path,
                headless=True,
                args=launch_args
            )
        else:
            print("Launching with bundled Chromium...")
            browser = p.chromium.launch(
                headless=True,
                args=launch_args
            )

        context = browser.new_context(
            accept_downloads=True,
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )

        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: function() {return undefined}})"
        )

        page = context.new_page()

        screenshot_login = str(Path.cwd() / "after_login_debug.png")
        screenshot_profile = str(Path.cwd() / "profile_error_debug.png")

        try:
            perform_login(page, username, password)
        except Exception as e:
            page.screenshot(path=screenshot_login, full_page=True)
            print("Login failed screenshot saved.")
            browser.close()
            raise

        page.screenshot(path=screenshot_login, full_page=True)
        print("Screenshot saved: after_login_debug.png")
        print("Current URL: " + page.url)
        print("Page title: " + page.title())

        print("Opening profile...")
        try:
            page.wait_for_selector("a[href='/mnjuser/profile']", timeout=60000)
            page.click("a[href='/mnjuser/profile']")
            page.wait_for_url("**/mnjuser/profile**", timeout=60000)
            page.wait_for_timeout(5000)
        except Exception as e:
            page.screenshot(path=screenshot_profile, full_page=True)
            print("Profile selector failed: " + str(e))
            print("URL at failure: " + page.url)
            browser.close()
            raise

        print("Fetching profile name...")
        page.wait_for_selector(".fullname", timeout=60000)
        profile_name = page.locator(".fullname").inner_text()
        safe_name = sanitize_filename(profile_name)
        print("Detected profile name: " + profile_name)

        print("Downloading resume...")
        page.wait_for_selector("[data-title='download-resume']", timeout=60000)
        with page.expect_download() as download_info:
            page.locator("[data-title='download-resume']").first.click(force=True)
            page.wait_for_timeout(5000)
        download = download_info.value
        today = datetime.now().strftime("%d_%B_%Y")
        filename = safe_name + "_Resume_" + today + ".pdf"
        resume_path = Path.cwd() / filename
        download.save_as(str(resume_path))
        print("Resume downloaded: " + str(resume_path))

        print("Opening update resume section...")
        page.wait_for_selector("input.dummyUpload[value='Update resume']", timeout=60000)
        page.wait_for_timeout(3000)

        print("Uploading resume...")
        try:
            page.set_input_files("#attachCV", str(resume_path))
            page.wait_for_timeout(5000)
            print("Resume uploaded using #attachCV")
        except Exception as ex:
            print("Primary upload failed, trying #fileUpload...")
            page.set_input_files("#fileUpload", str(resume_path))
            page.wait_for_timeout(5000)
            print("Resume uploaded using #fileUpload")

        page.wait_for_timeout(5000)
        print("Resume upload successful.")

        print("Opening menu...")
        page.wait_for_selector(".nI-gNb-drawer__bars", timeout=30000)
        page.locator(".nI-gNb-drawer__bars").click()
        page.wait_for_timeout(3000)

        print("Logging out...")
        page.wait_for_selector("[data-type='logoutLink']", timeout=30000)
        page.locator("[data-type='logoutLink']").click()
        page.wait_for_timeout(5000)

        print("Closing browser...")
        browser.close()
        print("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()
    update_naukri_resume(username=args.username, password=args.password)