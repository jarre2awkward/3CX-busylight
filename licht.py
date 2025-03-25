import requests
import time
import os
import threading
from busylight.lights import Light

# 🧠 Prompt voor PBX URL en extensies
# DO NOT MODIFY – setup.sh will update these
API_URL = "https://your-3cx-url/connect/token"
EXTENSIONS_TO_MONITOR = ["201", "202"]
CLIENT_ID = "api"
CLIENT_SECRET = "your_api_key_here"
LOG_FILE = "/home/PDSS/logs/cronlog"

# Initialize Busylight
light = Light.first_light()
if not light:
    print("❌ No Busylight detected. Exiting...")
    exit(1)

def log_message(message):
    with open(LOG_FILE, "a") as log:
        log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    print(message)

def get_access_token():
    retries = 5
    while retries > 0:
        try:
            data = {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "client_credentials"
            }
            response = requests.post(API_URL, data=data, timeout=5)
            response.raise_for_status()
            token_info = response.json()
            log_message("✅ Access token obtained.")
            return token_info["access_token"], token_info["expires_in"]
        except requests.exceptions.RequestException as e:
            log_message(f"⚠️ Connection failed: {e}. Retrying in 5 seconds...")
            time.sleep(5)
            retries -= 1

    log_message("❌ Failed to get access token after multiple retries.")
    os.system("sudo systemctl restart networking.service")
    time.sleep(5)
    return None, None

def check_ringing_status():
    global token
    headers = {"Authorization": f"Bearer {token}"}
    ringing_detected = False

    for extension in EXTENSIONS_TO_MONITOR:
        call_api_url = f"{PBX_BASE}/callcontrol/{extension}"
        try:
            response = requests.get(call_api_url, headers=headers, timeout=5)
            response.raise_for_status()
            active_calls = response.json()

            for participant in active_calls.get("participants", []):
                if participant.get("status") == "Ringing":
                    log_message(f"📞 Phone is RINGING on extension {extension}! Flickering Busylight.")
                    flicker_busylight()
                    ringing_detected = True

        except requests.exceptions.RequestException as e:
            log_message(f"⚠️ Error fetching status for extension {extension}: {e}")

    if not ringing_detected:
        log_message("❌ No ringing calls detected. Turning OFF Busylight.")
        light.off()

def flicker_busylight():
    for _ in range(5):
        if not is_any_extension_ringing():
            log_message("✅ Call ended, stopping flicker.")
            return
        light.on((255, 0, 0))
        time.sleep(0.3)
        light.off()
        time.sleep(0.3)

def is_any_extension_ringing():
    headers = {"Authorization": f"Bearer {token}"}
    for extension in EXTENSIONS_TO_MONITOR:
        call_api_url = f"{PBX_BASE}/callcontrol/{extension}"
        try:
            response = requests.get(call_api_url, headers=headers, timeout=3)
            response.raise_for_status()
            active_calls = response.json()
            for participant in active_calls.get("participants", []):
                if participant.get("status") == "Ringing":
                    return True
        except requests.exceptions.RequestException:
            pass
    return False

def refresh_token_periodically():
    global token
    while True:
        time.sleep(30)
        log_message("🔄 Refreshing API token...")
        token, _ = get_access_token()

token, expires_in = get_access_token()
refresh_thread = threading.Thread(target=refresh_token_periodically, daemon=True)
refresh_thread.start()

try:
    while True:
        check_ringing_status()
        time.sleep(2)
except KeyboardInterrupt:
    log_message("🛑 Script stopped manually. Turning off Busylight.")
    light.off()
except Exception as e:
    log_message(f"⚠️ Unexpected error: {e}")
    light.off()
    time.sleep(5)
