import requests
from pathlib import Path
from datetime import datetime

# Direct public Oulu neutron monitor data (hourly text file)
URL = "https://cosmicrays.oulu.fi/phi/Phi_mon.txt"
OUTPUT_DIR = Path("data/oulu_cr")
OUTPUT_DIR.mkdir(exist_ok=True)

try:
    response = requests.get(URL, timeout=30)
    response.raise_for_status()
    if response.text.strip():  # Ensure content
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        file = OUTPUT_DIR / f"oulu_cr_{timestamp}.txt"
        with open(file, 'w') as f:
            f.write(response.text)
        print(f"Fetched Oulu CR data: {file}")
    else:
        print("Empty response — no new data")
except Exception as e:
    print(f"Oulu fetch failed: {e}")
