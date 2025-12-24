import requests
from pathlib import Path
from datetime import datetime

# Public CERN luminosity CSV (example from 2025 run — adjust to latest)
URL = "https://opendata.cern.ch/record/15001/files/lumi.csv"  # Real public file
OUTPUT_DIR = Path("data/cern_lhc")
OUTPUT_DIR.mkdir(exist_ok=True)

response = requests.get(URL, timeout=30)
timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
file = OUTPUT_DIR / f"cern_lumi_{timestamp}.csv"
with open(file, 'w') as f:
    f.write(response.text)
print(f"Fetched CERN LHC luminosity: {file}")
