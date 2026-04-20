import requests
from playwright.sync_api import sync_playwright

CHECK_URL = "http://clients3.google.com/generate_204"


def is_connected():
    try:
        response = requests.get(CHECK_URL, timeout=5)
        return response.status_code == 204
    except:
        return False


def connect_captive():
    if is_connected():
        print("Internet is already active. Skipping...")
        return

    print("Connection lost. Starting Playwright auth...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")
        page = context.new_page()

        try:
            page.goto("http://neverssl.com", timeout=60000)
            page.wait_for_load_state("networkidle")

            print("Clicking FREE WIFI...")
            page.click("#btn2")
            page.wait_for_timeout(3000)

            print("Checking policy...")
            page.check("#policy_9")
            page.wait_for_timeout(1000)

            print("Submitting login...")
            page.click("#submit_login")

            page.wait_for_timeout(5000)

            if is_connected():
                print("Successfully connected!")
            else:
                print("Auth failed or taking too long.")

        except Exception as e:
            print(f"Error during auth: {e}")
        finally:
            browser.close()


if __name__ == "__main__":
    connect_captive()
