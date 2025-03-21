#!/usr/bin/env python3
import requests
import time
import os
import threading
from busylight.lights import Light

API_URL = "https://pdss.3cx.eu/connect/token"
EXTENSIONS_TO_MONITOR = ["211", "206", "207", "202", "213", "203"]
LOG_FILE = "/home/pi/logs/cronlog"

CLIENT_ID = "api"
CLIENT_SECRET = "ImJEGB5bgnCiSmv17EXZihEvnXwhsdNl"

# Safe global variable
light = None
token = None

def log_message(message):
    with open(LOG_FILE, "a") as log:
        log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    print(message)

def get_light():
    try:
        l = Light.first_light()
        if not l:
            raise Exception("❌ No Busylight detected.")
        return l
    except Exception as e:
        log_message(f"🚫 Error initializing Busylight: {e}")
        return None

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
            log_message(f"⚠️ Token error: {e}. Retrying...")
            time.sleep(5)
            retries -= 1
    log_message("❌ Could not get token.")
    return None, None

def is_any_extension_ringing():
    headers = {"Authorization": f"Bearer {token}"}
    for ext in EXTENSIONS_TO_MONITOR:
        try:
            r = requests.get(f"https://pdss.3cx.eu/callcontrol/{ext}", headers=headers, timeout=3)
            r.raise_for_status()
            if any(p.get("status") == "Ringing" for p in r.json().get("participants", [])):
                return True
        except:
            continue
    return False

def flicker_busylight():
    if not light:
        return
    for _ in range(5):
        if not is_any_extension_ringing():
            log_message("✅ Call ended, stopping flicker.")
            return
        light.on((255, 0, 0))
        time.sleep(0.3)
        light.off()
        time.sleep(0.3)

def check_ringing_status():
    global light
    if not light:
        light = get_light()
        if not light:
            return
    headers = {"Authorization": f"Bearer {token}"}
    ringing = False

    for ext in EXTENSIONS_TO_MONITOR:
        try:
            r = requests.get(f"https://pdss.3cx.eu/callcontrol/{ext}", headers=headers, timeout=5)
            r.raise_for_status()
            if any(p.get("status") == "Ringing" for p in r.json().get("participants", [])):
                log_message(f"📞 RINGING on {ext}")
                flicker_busylight()
                ringing = True
        except Exception as e:
            log_message(f"❗ Error on {ext}: {e}")
    
    if not ringing and light:
        light.off()
        log_message("❌ No ringing calls. Busylight OFF.")

def refresh_token_periodically():
    global token
    while True:
        time.sleep(30)
        log_message("🔄 Refreshing token...")
        token, _ = get_access_token()

# Start
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
light = get_light()
token, _ = get_access_token()

if not token:
    log_message("❌ Exiting: No valid token.")
    exit(1)

threading.Thread(target=refresh_token_periodically, daemon=True).start()

try:
    while True:
        check_ringing_status()
        time.sleep(2)
except KeyboardInterrupt:
    if light:
        light.off()
except Exception as e:
    log_message(f"🔥 Unexpected error: {e}")
    if light:
        light.off()
    time.sleep(5)
