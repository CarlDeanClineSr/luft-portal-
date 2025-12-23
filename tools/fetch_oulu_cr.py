import requests
from pathlib import Path
from datetime import datetime
import re

URL = "https://cosmicrays.oulu.fi/webform/QuickData.php?station=Oulu"
OUTPUT_DIR = Path("data/oulu_cr")
OUTPUT_DIR.mkdir(exist_ok=True)

response = requests.get(URL)
text = response.text

# Parse latest hourly neutron counts (simple regex for last row)
match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s+(\d+\.\d+)', text)
if match:
    timestamp = match.group(1)
    counts = float(match.group(2))
    data = {"timestamp_utc": timestamp, "neutron_counts": counts}
    file = OUTPUT_DIR / f"oulu_cr_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    pd.DataFrame([data]).to_csv(file, index=False)
    print(f"Fetched Oulu CR data: {file}")
else:
    print("No new data found.")
