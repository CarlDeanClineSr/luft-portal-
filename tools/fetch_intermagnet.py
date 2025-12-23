import requests
from pathlib import Path
from datetime import datetime
import pandas as pd

URL = "https://intermagnet.org/data-donnee/imos/imos-eng.php"  # Example endpoint; adjust to real data URL
OUTPUT_DIR = Path("data/intermagnet")
OUTPUT_DIR.mkdir(exist_ok=True)

response = requests.get(URL)
text = response.text

# Parse simple table (adjust regex to match actual format)
lines = text.split('\n')
data = []
for line in lines:
    if line.strip() and not line.startswith('#'):
        parts = line.split()
        if len(parts) >= 4:
            timestamp = parts[0] + ' ' + parts[1]
            h = float(parts[2])
            d = float(parts[3])
            z = float(parts[4])
            data.append({'timestamp_utc': timestamp, 'H_nT': h, 'D_nT': d, 'Z_nT': z})

df = pd.DataFrame(data)
timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
file = OUTPUT_DIR / f"intermagnet_{timestamp}.csv"
df.to_csv(file, index=False)
print(f"Fetched INTERMAGNET data: {file}")
