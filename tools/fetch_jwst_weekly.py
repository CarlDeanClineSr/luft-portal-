import requests
from pathlib import Path
from datetime import datetime

URL = "https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:JWST/product/"
OUTPUT_DIR = Path("data/jwst")
OUTPUT_DIR.mkdir(exist_ok=True)

# Example: Fetch latest JADES flux
response = requests.get(URL + "jades-latest.fits")  # replace with real URI
timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
file = OUTPUT_DIR / f"jades_flux_{timestamp}.fits"
with open(file, 'wb') as f:
    f.write(response.content)
print(f"Fetched JWST data: {file}")
