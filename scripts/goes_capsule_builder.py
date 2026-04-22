import requests
import json
import os
from pathlib import Path

# 1. Update to NOAA's active JSON endpoint for GOES X-ray flux
GOES_URL = "https://services.swpc.noaa.gov/json/goes/primary/xrays-1-day.json"

def fetch_goes_data():
    try:
        # 2. Pull the active JSON data
        response = requests.get(GOES_URL, timeout=30)
        response.raise_for_status()  # Catches 404s and server errors immediately
        
        xray_data = response.json()
        
        # 3. Ensure the output directory exists
        OUTPUT_DIR = Path("data/goes")
        OUTPUT_DIR.mkdir(exist_ok=True)
        
        # 4. Save the full 1-day batch for the archive
        latest_file = OUTPUT_DIR / "xray_flux_latest.json"
        with open(latest_file, 'w') as f:
            json.dump(xray_data, f, indent=4)
            
        # 5. Extract the absolute latest reading (the scalpel) for the continuous audit
        audit_file = OUTPUT_DIR / "xray_flux_audit.json"
        latest_reading = xray_data[-1]
        with open(audit_file, 'w') as f:
            json.dump(latest_reading, f, indent=4)
            
        print("✅ GOES X-Ray JSON fetched and parsed successfully.")
        
    except Exception as e:
        print(f"GOES fetch failed: {e}")

if __name__ == "__main__":
    fetch_goes_data()
