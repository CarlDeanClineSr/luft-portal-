import requests
from pathlib import Path
from datetime import datetime

URL = "https://services.swpc.noaa.gov/text/goes-xray-flux.txt"  # Real GOES X-ray flux
OUTPUT_DIR = Path("data/goes")
OUTPUT_DIR.mkdir(exist_ok=True)

try:
    response = requests.get(URL, timeout=30)
    response.raise_for_status()
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    file = OUTPUT_DIR / f"goes_xray_{timestamp}.txt"
    with open(file, 'w') as f:
        f.write(response.text)
    print(f"Fetched GOES X-ray data: {file}")
except Exception as e:
    print(f"GOES fetch failed: {e}")
