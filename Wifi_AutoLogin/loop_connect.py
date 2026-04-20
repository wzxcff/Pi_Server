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
        print(f"[{time.strftime('%H:%M:%S')}] Connection ALIVE.")
        return

    print(f"[{time.strftime('%H:%M:%S')}] No connection. Reconnecting...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            page.goto("http://neverssl.com", timeout=60000)

            page.click("#btn2")
            page.wait_for_timeout(2000)
            page.check("#policy_9")
            page.click("#submit_login")

            time.sleep(5)
            browser.close()
            print(f"[{time.strftime('%H:%M:%S')}] Auth attempt completed!")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Error occurred: {e}")


if __name__ == "__main__":
    print("Captive Portal Automator started...")
    run_logic()

    while True:
        time.sleep(300)
        run_logic()