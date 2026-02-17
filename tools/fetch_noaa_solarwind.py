#!/usr/bin/env python3
"""
Fetch NOAA SWPC solar wind plasma and magnetic field 7-day JSON feeds,
convert to CSV with headers, save with UTC timestamped filenames.
"""

import requests
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

PLASMA_URL = "https://services.swpc.noaa.gov/products/solar-wind/plasma-7-day.json"
MAG_URL    = "https://services.swpc.noaa.gov/products/solar-wind/mag-7-day.json"

OUTPUT_DIR = Path("data/noaa_solarwind")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def fetch_json_to_csv(url: str, name: str) -> Path:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()

    # First row contains column names; subsequent rows are data
    header = data[0]
    rows = data[1:]

    df = pd.DataFrame(rows, columns=header)

    # Normalize timestamp column to ISO8601 if present
    if "time_tag" in df.columns:
        df["time_tag"] = pd.to_datetime(df["time_tag"], utc=True, errors="coerce")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = OUTPUT_DIR / f"{name}_{timestamp}.csv"
    df.to_csv(out_path, index=False)
    print(f"[OK] Saved {name}: {out_path}")
    return out_path

if __name__ == "__main__":
    fetch_json_to_csv(PLASMA_URL, "noaa_plasma")
    fetch_json_to_csv(MAG_URL,    "noaa_mag")
