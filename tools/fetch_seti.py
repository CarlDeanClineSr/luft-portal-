import requests
from pathlib import Path

URL = "https://seti.berkeley.edu/blsdr/data/"
OUTPUT_DIR = Path("data/seti")
OUTPUT_DIR.mkdir(exist_ok=True)

response = requests.get(URL + "latest_hdf5.h5")  # replace with real URI
timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
file = OUTPUT_DIR / f"seti_scan_{timestamp}.h5"
with open(file, 'wb') as f:
    f.write(response.content)
print(f"Fetched SETI data: {file}")
