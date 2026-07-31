import requests
import pandas as pd
import os
from datetime import datetime

# NOAA's real-time JSON endpoints for L1 Spacecraft (DSCOVR/SWFO)
PLASMA_URL = "https://services.swpc.noaa.gov/products/solar-wind/plasma-1-day.json"
MAG_URL = "https://services.swpc.noaa.gov/products/solar-wind/mag-1-day.json"
CSV_FILE = "data/swfo_l1_telemetry/stream.csv"

def fetch_and_validate():
    print(f"[{datetime.utcnow()}] Initiating SWFO-L1 Telemetry Pull...")
    
    try:
        plasma_res = requests.get(PLASMA_URL, timeout=10)
        mag_res = requests.get(MAG_URL, timeout=10)
        
        if plasma_res.status_code != 200 or mag_res.status_code != 200:
            print("API Error: Spacecraft feed unresponsive.")
            return
            
        plasma_data = plasma_res.json()
        mag_data = mag_res.json()
        
        # Grab the absolute newest row of data (index -1)
        # JSON structure: [time, density, speed, temp]
        latest_plasma = plasma_data[-1] 
        # JSON structure: [time, bx, by, bz, lon, lat, bt]
        latest_mag = mag_data[-1]
        
        # 1. FILTER TRAP: Ensure data is not blank/uncalibrated
        density = latest_plasma[1]
        speed = latest_plasma[2]
        bz = latest_mag[3]
        bt = latest_mag[6]
        
        if None in [density, speed, bz, bt]:
            print("CRITICAL: NOAA transmitted calibration blanks. Rejecting data.")
            return

        # 2. Package the valid data
        new_record = pd.DataFrame([{
            'timestamp': latest_plasma[0],
            'density_cm3': float(density),
            'speed_km_s': float(speed),
            'bz_nt': float(bz),
            'bt_nt': float(bt)
        }])
        
        # 3. APPEND MODE ('a'): Never overwrite the historical ledger
        # If the file doesn't exist, write the header. If it does, just append the row.
        file_exists = os.path.isfile(CSV_FILE)
        new_record.to_csv(CSV_FILE, mode='a', index=False, header=not file_exists)
        
        print(f"SUCCESS: Valid SWFO record appended at {latest_plasma[0]}")
        print(f"Bt: {bt} nT | Bz: {bz} nT | Speed: {speed} km/s | Density: {density}")

    except Exception as e:
        print(f"Ingest Engine Failed: {e}")

if __name__ == "__main__":
    # Ensure directory exists
    os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
    fetch_and_validate()
