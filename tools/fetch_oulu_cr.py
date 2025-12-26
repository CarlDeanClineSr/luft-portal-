import requests
from pathlib import Path
from datetime import datetime

# Direct public Oulu neutron monitor data (hourly averages, text format)
URL = "https://cosmicrays.oulu.fi/phi/Phi_mon.txt"  # Real endpoint
OUTPUT_DIR = Path("data/oulu_cr")
OUTPUT_DIR.mkdir(exist_ok=True)

try:
    response = requests.get(URL, timeout=30)
    response.raise_for_status()
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    file = OUTPUT_DIR / f"oulu_cr_{timestamp}.txt"
    with open(file, 'w') as f:
        f.write(response.text)
    print(f"Fetched Oulu CR data: {file}")
except Exception as e:
    print(f"Oulu fetch failed: {e}")
