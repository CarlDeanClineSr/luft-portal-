import requests
from pathlib import Path
from datetime import datetime, timezone

URL = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=text&starttime=now-1day&minmagnitude=2.5"
OUTPUT_DIR = Path("data/usgs_quakes")
OUTPUT_DIR.mkdir(exist_ok=True)

response = requests.get(URL, timeout=30)
timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
file = OUTPUT_DIR / f"usgs_quakes_{timestamp}.csv"
with open(file, 'w') as f:
    f.write(response.text)
print(f"Fetched USGS quakes: {file}")
