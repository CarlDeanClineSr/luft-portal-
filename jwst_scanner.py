import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import os

# --- TARGETS ---
SCID = "170"
DSN_URL = "https://eyes.nasa.gov/dsn/data/dsn.xml"
LOG_FILE = "mission_log.txt"

def check_dsn():
    try:
        resp = requests.get(DSN_URL, timeout=10)
        root = ET.fromstring(resp.content)
        
        for dish in root.findall(".//dish"):
            dish_name = dish.get("name")
            for target in dish.findall("target"):
                if target.get("id") == SCID:
                    down = target.find("downSignal")
                    if down is not None:
                        rate = float(down.get("dataRate", 0))
                        # TRIGGER: Data Rate > 5 Mbps (Science Dump)
                        if rate > 5000000:
                            return True, f"Ka-BAND LOCK | {dish_name} | {rate/1000000:.2f} Mbps"
        return False, "Silent"
    except:
        return False, "Error"

# --- EXECUTION ---
timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
found, message = check_dsn()

if found:
    entry = f"\n[🚨 DETECTED] {timestamp} : {message}"
    print(entry)
    # Write to file for the GitHub Action to save
    with open(LOG_FILE, "a") as f:
        f.write(entry)
else:
    print(f"[SCAN] {timestamp} : No Signal.")
