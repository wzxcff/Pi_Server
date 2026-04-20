import time
import requests
import signal
import sys
from playwright.sync_api import sync_playwright


def signal_handler(sig, frame):
    print("\nStopping the script...")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def is_connected():
    try:
        return requests.get("http://clients3.google.com/generate_204", timeout=5).status_code == 204
    except:
        return False


def run_logic():
    if is_connected():
        return

    print(f"[{time.strftime('%H:%M:%S')}] Connection LOST. Starting auth...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto("http://neverssl.com", timeout=60000)
            page.wait_for_load_state("networkidle")
            print(f"Current URL: {page.url}")

            page.wait_for_selector("#btn2", timeout=15000)
            page.click("#btn2")
            print("Clicked #btn2 (Free Wifi)")

            print("Waiting for checkbox #policy_9...")
            try:
                page.wait_for_selector("#policy_9", timeout=20000, state="visible")
                page.check("#policy_9")
                print("Checkbox set!")
            except Exception as e:
                page.screenshot(path="error_debug.png")
                print("Element not found, saving screenshot as error_debug.png")
                raise e

            page.wait_for_selector("#submit_login", timeout=10000)
            page.click("#submit_login")

            time.sleep(5)
            browser.close()
            print(f"[{time.strftime('%H:%M:%S')}] Auth completed!")

    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Error occurred: {e}")


if __name__ == "__main__":
    print("Captive Portal Automator started...")
    run_logic()

    while True:
        time.sleep(300)
        run_logic()