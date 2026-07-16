import time
import requests
import threading
import signal
import sys
import datetime

from playwright.sync_api import sync_playwright

CHECK_INTERVAL = 5
LOCK = threading.Lock()
RECOVERY_IN_PROGRESS = False


def signal_handler(sig, frame):
    print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] Stopping watchdog...")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def is_connected():
    try:
        r = requests.get("http://clients3.google.com/generate_204", timeout=5)
        return r.status_code == 204
    except:
        return False


def do_login():
    global RECOVERY_IN_PROGRESS

    with LOCK:
        if RECOVERY_IN_PROGRESS:
            return
        RECOVERY_IN_PROGRESS = True

    start = datetime.datetime.now()

    print(f"[{start.strftime('%H:%M:%S')}] Starting recovery...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ]
            )

            page = browser.new_page()

            page.goto("http://neverssl.com", timeout=10000, wait_until="load")

            print(f"Current URL: {page.url}")
            time.sleep(2)

            page.click("#btn2", timeout=15000)
            print("Clicked login button")


            page.check("#policy_9", timeout=15000)
            print("Checkbox set")


            page.click("#submit_login", timeout=5000)
            print("Submitted login button")

            try:
                page.wait_for_selector("#submit_login", state="detached", timeout=5000)
                print("Login processed (button detached)")
            except Exception:
                time.sleep(1.5)

            browser.close()

            end = datetime.datetime.now()
            print(f"[{end.strftime('%H:%M:%S')}] Recovery completed")
            print(f"It took {(end - start).total_seconds()} seconds")

    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Recovery failed: {e}")

    finally:
        RECOVERY_IN_PROGRESS = False



def watchdog():
    print(f"{[datetime.datetime.now().strftime('%H:%M:%S')]} Watchdog started...")

    print(f"{[datetime.datetime.now().strftime('%H:%M:%S')]} Ready!")

    was_online = True

    while True:
        try:
            online = is_connected()

            if was_online and not online:
                print(f"[{time.strftime('%H:%M:%S')}] Connection LOST detected") # TODO: Change to datetime
                threading.Thread(target=do_login, daemon=True).start()

            was_online = online

        except Exception as e:
            print("Watchdog error:", e)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    watchdog()