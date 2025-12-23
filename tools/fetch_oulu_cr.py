import requests
from pathlib import Path
from datetime import datetime

URL = "https://cosmicrays.oulu.fi/webform/QuickData.php?station=Oulu"
OUTPUT_DIR = Path("data/oulu_cr")
OUTPUT_DIR.mkdir(exist_ok=True)

# Fetch with SSL verification disabled (public data, safe)
response = requests.get(URL, verify=False)
text = response.text

# Parse latest hourly neutron counts (simple regex for last valid row)
import re
match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s+(\d+\.\d+)', text)
if match:
    timestamp = match.group(1)
    counts = float(match.group(2))
    data = {"timestamp_utc": timestamp, "neutron_counts": counts}
    file = OUTPUT_DIR / f"oulu_cr_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(file, 'w') as f:
        f.write(f"timestamp_utc,neutron_counts\n{timestamp},{counts}\n")
    print(f"Fetched Oulu CR data: {file}")
else:
    print("No new data found.")
