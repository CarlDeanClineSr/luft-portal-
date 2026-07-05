import urllib.request
import urllib.error
import json
import sys
import os
from datetime import datetime

# Primary SWFO-L1 endpoints (The ones currently throwing 404s)
URLS = [
    "https://services.swpc.noaa.gov/json/swfo/mag-1-day.json",
    "https://services.swpc.noaa.gov/json/swfo/plasma-1-day.json"
]

# DSCOVR/ACE Fallbacks - Keeps the engine fed if SWFO is moved/restricted
FALLBACK_URLS = [
    "https://services.swpc.noaa.gov/products/solar-wind/mag-1-day.json",
    "https://services.swpc.noaa.gov/products/solar-wind/plasma-1-day.json"
]

def fetch(url):
    """
    Hardened fetch protocol. Catches 404s and connection errors 
    without crashing the main LUFT workflow.
    """
    # Custom User-Agent identifies your crawler professionally
    req = urllib.request.Request(url, headers={'User-Agent': 'LUFT-Engine/4.0 (Imperial Physics)'})
    
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode('utf-8'))
            
    except urllib.error.HTTPError as e:
        print(f"[!] HTTP Error {e.code} for URL: {url}")
        return None
    except Exception as e:
        print(f"[!] Connection Error: {e} for URL: {url}")
        return None

def process_and_append(mag_data, plasma_data):
    """
    Placeholder for your existing data extraction and stream.csv append logic.
    Aligns magnetic and plasma data by timestamp, calculates Chi (X), 
    and determines COMPLIANT/FRACTURE status.
    """
    # This is where your existing logic to parse the JSON and write to stream.csv goes.
    # The crucial part is that the script only reaches here if data is successfully fetched.
    print(f"[*] Processing {len(mag_data)} mag records and {len(plasma_data)} plasma records...")
    
    # ... [Insert your existing CSV write logic here] ...
    
    print("[*] LUFT Stream append successful.")

def run():
    print(f"[{datetime.utcnow().isoformat()}] Initiating L1 Telemetry Ingest...")
    
    # 1. Attempt Primary SWFO-L1 Fetch
    print("[*] Targeting Primary SWFO Endpoints...")
    m = fetch(URLS[0])
    p = fetch(URLS[1])
    
    # 2. Check for 404 / Missing Data
    if m is None or p is None:
        print("[!] Primary endpoints offline or relocated (404).")
        print("[*] Engaging proxy fallback telemetry (DSCOVR/ACE)...")
        m = fetch(FALLBACK_URLS[0])
        p = fetch(FALLBACK_URLS[1])
        
    # 3. Final Integrity Check
    if m is None or p is None:
        print("[X] CRITICAL: Both primary and fallback endpoints failed.")
        print("[X] Aborting ingest to preserve data integrity. No false rows written.")
        sys.exit(1) # Fails cleanly so GitHub Actions logs it without breaking downstream processes
        
    # 4. Route to Processing
    process_and_append(m, p)

if __name__ == "__main__":
    run()
