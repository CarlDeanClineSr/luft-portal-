import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pathlib import Path
from datetime import datetime
import pandas as pd
import sys

URL = "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt"
OUTPUT_DIR = Path("data/gistemp")
OUTPUT_DIR.mkdir(exist_ok=True)

# Create session with retry strategy
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

try:
    print(f"Fetching GISTEMP data from {URL}...")
    response = session.get(URL, timeout=(30, 60), stream=True)
    response.raise_for_status()
    
    # Read text content from stream
    lines = response.text.split('\n')
    
except requests.exceptions.RequestException as e:
    print(f"❌ Failed to fetch GISTEMP data after retries: {e}")
    sys.exit(1)

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
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
file = OUTPUT_DIR / f"gistemp_anomalies_{timestamp}.csv"
df.to_csv(file, index=False)
print(f"Fetched GISTEMP data: {file}")
