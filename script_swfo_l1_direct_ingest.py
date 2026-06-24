#!/usr/bin/env python3
import requests
from datetime import datetime, timezone
import os

# NASA NAIF SPICE kernels (The "Master Key" for satellite positioning)
SPICE_URL = "https://naif.jpl.nasa.gov/pub/naif/DSCOVR/kernels/spk/dscovr_orbit.bsp"

def get_craft_attitude():
    """Extracts orientation (Pitch, Yaw, Roll) from the craft telemetry packet."""
    # Note: Actual attitude data is often embedded in the binary 'CCSDS' packets.
    # We poll the SWPC 'spacecraft-state' product.
    url = "https://services.swpc.noaa.gov/products/spacecraft-state.json"
    response = requests.get(url, headers={'User-Agent': 'LUFT-Attitude-Tracker/1.0'})
    return response.json()

def run_log():
    state = get_craft_attitude()
    # Log the Quaternion/Attitude and precise timestamp
    now = datetime.now(timezone.utc).isoformat()
    path = "data/swfo_l1_telemetry/attitude_log.csv"
    
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'a') as f:
        # Format: Time, Pitch, Yaw, Roll, X, Y, Z
        f.write(f"{now}, {state['pitch']}, {state['yaw']}, {state['roll']}, {state['x']}, {state['y']}, {state['z']}\n")

if __name__ == "__main__":
    run_log()
