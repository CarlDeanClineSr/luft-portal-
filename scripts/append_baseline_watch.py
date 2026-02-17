#!/usr/bin/env python3
"""
Auto-append daily baseline watch entry to DAILY_BASELINE_WATCH.md
Law #46: The vacuum baseline must be monitored continuously.
"""

import os
from datetime import datetime, timezone
import json

def append_baseline_entry():
    """Append today's baseline watch entry"""
    
    # File paths
    capsule_file = "capsules/DAILY_BASELINE_WATCH.md"
    ace_mag_file = "data/ace_mag_latest.json"
    ace_plasma_file = "data/ace_plasma_latest.json"
    
    # Get current UTC timestamp
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Load latest data
    # Note: This assumes NOAA SWPC JSON format with header row at index 0
    # and data rows following. If the API format changes, this will need updating.
    try:
        with open(ace_mag_file, 'r') as f:
            mag_data = json.load(f)
        # Data is in array format: [["header", ...], ["data", ...], ...]
        # Expected header: ["time_tag","bx_gsm","by_gsm","bz_gsm","lon_gsm","lat_gsm","bt"]
        # Get the last data row and extract bt (index 6)
        if len(mag_data) > 1:
            last_row = mag_data[-1]
            mag_bt = last_row[6] if len(last_row) > 6 else 'N/A'
        else:
            mag_bt = 'N/A'
    except (FileNotFoundError, json.JSONDecodeError, IndexError, KeyError) as e:
        print(f"Warning: Could not read magnetic field data: {e}")
        mag_bt = 'N/A'
    
    try:
        with open(ace_plasma_file, 'r') as f:
            plasma_data = json.load(f)
        # Data is in array format: [["header", ...], ["data", ...], ...]
        # Expected header: ["time_tag","density","speed","temperature"]
        # Get the last data row and extract density (index 1) and speed (index 2)
        if len(plasma_data) > 1:
            last_row = plasma_data[-1]
            density = last_row[1] if len(last_row) > 1 else 'N/A'
            speed = last_row[2] if len(last_row) > 2 else 'N/A'
        else:
            density = 'N/A'
            speed = 'N/A'
    except (FileNotFoundError, json.JSONDecodeError, IndexError, KeyError) as e:
        print(f"Warning: Could not read plasma data: {e}")
        density = 'N/A'
        speed = 'N/A'
    
    # Create entry
    entry = f"""
## {date_str}

**Timestamp**: {timestamp}

**Baseline Watch Status**:
- Magnetic Field (Bt): {mag_bt} nT
- Plasma Density: {density} p/cm³
- Solar Wind Speed: {speed} km/s

**Law #46 Compliance**: ✅ MONITORED

---
"""
    
    # Append to file
    os.makedirs("capsules", exist_ok=True)
    
    # Initialize file if it doesn't exist
    if not os.path.exists(capsule_file):
        with open(capsule_file, 'w') as f:
            f.write("# Daily Baseline Watch\n\n")
            f.write("Law #46: The vacuum baseline must be monitored continuously.\n\n")
            f.write("---\n\n")
    
    # Append entry
    with open(capsule_file, 'a') as f:
        f.write(entry)
    
    print(f"✅ Appended baseline watch entry for {date_str}")

if __name__ == "__main__":
    append_baseline_entry()
