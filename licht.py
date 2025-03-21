import requests
import time
import os
import threading
from busylight.lights import Light

# 3CX API Credentials
API_URL = "https://pdss.3cx.eu/connect/token"
EXTENSIONS_TO_MONITOR = ["211", "206", "207", "202", "213", "203"]
LOG_FILE = "/home/jarre/logs/cronlog"

CLIENT_ID = "api"
CLIENT_SECRET = "ImJEGB5bgnCiSmv17EXZihEvnXwhsdNl"

# Initialize Busylight
light = Light.first_light()
if not light:
    print("❌ No Busylight detected. Exiting...")
    exit(1)

def log_message(message):
    """Log messages to a file for debugging."""
    with open(LOG_FILE, "a") as log:
        log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    print(message)

def get_access_token():
    """Retrieve an access token from the 3CX API with automatic retries."""
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
    """Check if any monitored extensions are ringing and flicker Busylight."""
    global token
    headers = {"Authorization": f"Bearer {token}"}
    ringing_detected = False

    for extension in EXTENSIONS_TO_MONITOR:
        call_api_url = f"https://pdss.3cx.eu/callcontrol/{extension}"
        try:
            response = requests.get(call_api_url, headers=headers, timeout=5)
            response.raise_for_status()
            active_calls = response.json()

            # Check if the extension is ringing
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
    """Flicker the Busylight while a call is still ringing."""
    for _ in range(5):  # Flicker up to 5 times
        if not is_any_extension_ringing():  # Stop if no extension is ringing
            log_message("✅ Call ended, stopping flicker.")
            return
        light.on((255, 0, 0))  # Light Red
        time.sleep(0.3)
        light.off()              # Light off
        time.sleep(0.3)

def refresh_token_periodically():
    """Refresh API token every 30 seconds in the background."""
    global token
    while True:
        time.sleep(30)
        log_message("🔄 Refreshing API token...")
        token, expires_in = get_access_token()

def is_any_extension_ringing():
    """Check if any monitored extension is currently ringing."""
    headers = {"Authorization": f"Bearer {token}"}
    for extension in EXTENSIONS_TO_MONITOR:
        call_api_url = f"https://pdss.3cx.eu/callcontrol/{extension}"
        try:
            response = requests.get(call_api_url, headers=headers, timeout=3)
            response.raise_for_status()
            active_calls = response.json()
            for participant in active_calls.get("participants", []):
                if participant.get("status") == "Ringing":
                    return True  # At least one extension is still ringing
        except requests.exceptions.RequestException:
            pass  # Ignore errors and keep checking
    return False  # No ringing calls detected

# ✅ **Start Background Thread for Token Refresh**
token, expires_in = get_access_token()
refresh_thread = threading.Thread(target=refresh_token_periodically, daemon=True)
refresh_thread.start()

# ✅ **Main Loop to Check for Ringing Calls**
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
