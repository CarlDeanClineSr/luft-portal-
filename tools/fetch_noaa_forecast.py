#!/usr/bin/env python3
"""
Fetch NOAA SWPC 3-day forecast text and save with UTC timestamped filename.
Clean, reproducible, no fluff.
"""

import requests
from datetime import datetime, timezone
from pathlib import Path

URL = "https://services.swpc.noaa.gov/text/3-day-forecast.txt"
OUTPUT_DIR = Path("data/noaa_forecasts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
filename = OUTPUT_DIR / f"noaa_3day_forecast_{timestamp}.txt"

resp = requests.get(URL, timeout=30)
resp.raise_for_status()

with open(filename, "w", encoding="utf-8") as f:
    f.write(resp.text)

print(f"[OK] Fetched NOAA 3-day forecast: {filename}")
