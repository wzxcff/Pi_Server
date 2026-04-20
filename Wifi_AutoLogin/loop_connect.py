import time
import subprocess
import sys
import requests
from playwright.sync_api import sync_playwright


def is_connected():
    try:
        return requests.get("http://clients3.google.com/generate_204", timeout=5).status_code == 204
    except:
        return False


def install_playwright_browsers():
    print("Checking browser components...")
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])


def run_logic():
    if is_connected():
        print(f"[{time.strftime('%H:%M:%S')}] Connection ALIVE.")
        return

    print(f"[{time.strftime('%H:%M:%S')}] No connection.. Trying to reconnect...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("http://neverssl.com", timeout=60000)

            page.click("#btn2")
            page.wait_for_timeout(2000)
            page.check("#policy_9")
            page.click("#submit_login")

            time.sleep(5)
            browser.close()
            print("Auth attempt completed!")
    except Exception as e:
        print(f"Error occurred: {e}")


if __name__ == "__main__":
    install_playwright_browsers()

    minutes = int(input("Check connectivity every ... minutes (ex. 3): "))
    print(f"Number set:\nChecking connectivity every {minutes} minutes")
    while True:
        run_logic()
        time.sleep(minutes * 60)