import requests
from pathlib import Path
from datetime import datetime

# Direct public INTERMAGNET mirror (Kyoto WDC) - latest daily text file
URL = "http://wdc.kugi.kyoto-u.ac.jp/geomag/data/aso/aso_current.txt"
OUTPUT_DIR = Path("data/intermagnet")
OUTPUT_DIR.mkdir(exist_ok=True)

try:
    response = requests.get(URL, timeout=30)
    response.raise_for_status()
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    file = OUTPUT_DIR / f"intermagnet_{timestamp}.txt"
    with open(file, 'w') as f:
        f.write(response.text)
    print(f"Fetched INTERMAGNET data: {file}")
except Exception as e:
    print(f"INTERMAGNET fetch failed: {e}")
