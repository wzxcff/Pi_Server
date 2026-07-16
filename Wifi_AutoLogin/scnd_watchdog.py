import time
import requests
import threading
import signal
import sys
import datetime
import re

CHECK_INTERVAL = 5
LOCK = threading.Lock()
RECOVERY_IN_PROGRESS = False

# Заголовки, чтобы сервер принимал нас за настоящий браузер
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest"
}


def signal_handler(sig, frame):
    print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] Stopping watchdog...")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def is_connected():
    try:
        r = requests.get("http://clients3.google.com/generate_204", timeout=3)
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
    print(f"[{start.strftime('%H:%M:%S')}] Starting fast recovery (requests-based)...")

    session = requests.Session()
    session.headers.update(HEADERS)

    try:
        # Шаг 1: Стучимся на neverssl, чтобы поймать редирект на Teledata
        # Нам нужен финальный URL, из которого мы вытащим MAC-адрес и сессию
        response = session.get("http://neverssl.com", timeout=5, allow_redirects=True)
        time.sleep(5)
        final_url = response.url

        if "teledata.wifi.teledata.de" not in final_url:
            print("Already connected or redirected to unknown host.")
            print(final_url)
            return

        print(f"Redirected to: {final_url}")

        # Шаг 2: Извлекаем MAC-адрес из URL
        # URL выглядит так: .../mac/A2:80:55... или .../mac/72:53:D4...
        mac_match = re.search(r'/mac/([0-9A-Fa-f:]+)', final_url)
        if not mac_match:
            print("Could not parse MAC-address from URL!")
            return

        raw_mac = mac_match.group(1)
        # Очищаем MAC-адрес от двоеточий для логина на MikroTik (например, 7253d4320117)
        clean_mac = raw_mac.replace(":", "").lower()
        print(f"Detected MAC: {raw_mac} (clean: {clean_mac})")

        # Шаг 3: Делаем первый AJAX-запрос для генерации пароля
        # Адрес берем из домена, на который нас перенаправило
        ajax_url = "https://teledata.wifi.teledata.de/Ajax/service/"

        payload = {
            "request": '{"model":"customers","method":"loginOverLoginModule","formName":"loginoneclicklogin","formData":{"policy_9":1,"submit_login":"Login"},"requestType":"formValidation","params":{"formID":"formLoginOneClickLogin","data":{"policy_9":1,"submit_login":"Login"}},"countPageImpression":true}'
        }

        ajax_res = session.post(ajax_url, data=payload, timeout=5)

        # Парсим сгенерированный пароль из ответа сервера
        # Обычно он приходит внутри JSON. Давайте найдем его регуляркой, так надежнее
        response_text = ajax_res.text
        password_match = re.search(r'"password"\s*:\s*"(\d+)"', response_text)

        if not password_match:
            # На случай, если структура JSON сложнее, выведем ответ для отладки
            print(f"Failed to get password from JSON. Response: {response_text[:300]}")
            return

        password = password_match.group(1)
        print(f"Successfully generated login credentials. Username: {clean_mac}, Password: {password}")

        # Шаг 4: Отправляем данные авторизации на шлюз MikroTik
        # Ссылка берется из твоего второго запроса
        hotspot_url = "http://hotspot.wifi.teledata.de/login"
        login_data = {
            "username": clean_mac,
            "password": password
        }

        # Отправляем финальный POST на MikroTik
        hotspot_res = session.post(hotspot_url, data=login_data, timeout=5, allow_redirects=True)

        end = datetime.datetime.now()
        if hotspot_res.status_code == 200:
            print(f"[{end.strftime('%H:%M:%S')}] Recovery completed successfully!")
            print(f"It took {(end - start).total_seconds()} seconds (No browser used!)")
        else:
            print(f"Hotspot authentication returned status code: {hotspot_res.status_code}")

    except Exception as e:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Recovery failed: {e}")

    finally:
        RECOVERY_IN_PROGRESS = False


def watchdog():
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Watchdog started...")
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Ready!")

    was_online = True

    while True:
        try:
            online = is_connected()

            if was_online and not online:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Connection LOST detected")
                threading.Thread(target=do_login, daemon=True).start()

            was_online = online

        except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Watchdog error: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    watchdog()