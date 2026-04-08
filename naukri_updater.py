from playwright.sync_api import sync_playwright
import argparse

def update_naukri_resume(username: str, password: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://www.naukri.com/nlogin/login?URL=https://www.naukri.com/mnjuser/homepage")
        page.wait_for_selector("#usernameField")
        page.fill("#usernameField", username)
        page.wait_for_selector("#passwordField")
        page.fill("#passwordField", password)
        page.click("button.blue-btn[type='submit']")
        page.wait_for_selector("a[href='/mnjuser/profile']")
        page.click("a[href='/mnjuser/profile']")
        # page.wait_for_selector("input.dummyUpload[value='Update resume']")
        # page.click("input.dummyUpload[value='Update resume']")
        page.wait_for_timeout(20000)
        browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update Naukri resume")
    parser.add_argument("--username", required=True, help="Naukri login email")
    parser.add_argument("--password", required=True, help="Naukri login password")
    args = parser.parse_args()

    update_naukri_resume(username=args.username, password=args.password)