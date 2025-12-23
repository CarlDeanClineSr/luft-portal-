import requests
from pathlib import Path
from datetime import datetime
import pandas as pd

URL = "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt"
OUTPUT_DIR = Path("data/gistemp")
OUTPUT_DIR.mkdir(exist_ok=True)

response = requests.get(URL)
lines = response.text.split('\n')

# Skip header, parse data rows
data = []
for line in lines[7:]:  # data starts after header
    if not line.strip() or line.startswith('Year'):
        continue
    parts = line.split()
    if len(parts) >= 19:  # year + 12 months + J-D + D-N + DJF + MAM + JJA + SON
        year = int(parts[0])
        for i, month in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
            if parts[i+1] != '****':
                data.append({'year': year, 'month': month, 'anomaly': float(parts[i+1])})

df = pd.DataFrame(data)
timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
file = OUTPUT_DIR / f"gistemp_anomalies_{timestamp}.csv"
df.to_csv(file, index=False)
print(f"Fetched GISTEMP data: {file}")
