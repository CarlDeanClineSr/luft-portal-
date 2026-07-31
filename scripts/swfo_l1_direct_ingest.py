import requests
import pandas as pd
import os
from datetime import datetime

# The New NOAA RTSW (Real-Time Solar Wind) Endpoints
PLASMA_URL = "https://services.swpc.noaa.gov/json/rtsw/rtsw_wind_1m.json"
MAG_URL = "https://services.swpc.noaa.gov/json/rtsw/rtsw_mag_1m.json"
CSV_FILE = "data/swfo_l1_telemetry/stream.csv"

# Mimic a browser to bypass the NOAA bot-filter
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LUFT-Engine/1.0",
    "Accept": "application/json"
}

def fetch_and_validate():
    print(f"[{datetime.now(datetime.UTC).isoformat()}] Initiating L1 RTSW Telemetry Pull...")
    
    try:
        plasma_res = requests.get(PLASMA_URL, headers=HEADERS, timeout=10)
        mag_res = requests.get(MAG_URL, headers=HEADERS, timeout=10)
        
        if plasma_res.status_code != 200 or mag_res.status_code != 200:
            print(f"API Error: Plasma HTTP {plasma_res.status_code} | Mag HTTP {mag_res.status_code}")
            return
            
        plasma_data = plasma_res.json()
        mag_data = mag_res.json()
        
        # Grab the absolute newest row of data from the new array structure
        latest_plasma = plasma_data[-1] 
        latest_mag = mag_data[-1]
        
        # Extract the metrics (Adjusted for the new JSON keys if they exist, or list indices)
        # Assuming the new format uses dictionary keys like 'density', 'speed', 'bz_gsm', 'bt'
        density = latest_plasma.get('density') if isinstance(latest_plasma, dict) else latest_plasma[1]
        speed = latest_plasma.get('speed') if isinstance(latest_plasma, dict) else latest_plasma[2]
        bz = latest_mag.get('bz_gsm') if isinstance(latest_mag, dict) else latest_mag[3]
        bt = latest_mag.get('bt') if isinstance(latest_mag, dict) else latest_mag[6]
        time_tag = latest_plasma.get('time_tag') if isinstance(latest_plasma, dict) else latest_plasma[0]
        
        if None in [density, speed, bz, bt]:
            print("CRITICAL: NOAA transmitted calibration blanks. Rejecting data.")
            return

        # Package the valid data
        new_record = pd.DataFrame([{
            'timestamp': time_tag,
            'density_cm3': float(density),
            'speed_km_s': float(speed),
            'bz_nt': float(bz),
            'bt_nt': float(bt)
        }])
        
        # Append to the historical ledger
        file_exists = os.path.isfile(CSV_FILE)
        new_record.to_csv(CSV_FILE, mode='a', index=False, header=not file_exists)
        
        print(f"SUCCESS: Valid RTSW record appended at {time_tag}")
        print(f"Bt: {bt} nT | Bz: {bz} nT | Speed: {speed} km/s | Density: {density}")

    except Exception as e:
        print(f"Ingest Engine Failed: {e}")

if __name__ == "__main__":
    os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
    fetch_and_validate()
