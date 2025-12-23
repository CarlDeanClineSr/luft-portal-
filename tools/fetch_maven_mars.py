import requests
from pathlib import Path
from datetime import datetime

# Example: Fetch latest MAVEN plasma summary (adjust to real PDS endpoint)
URL = "https://pds-ppi.igpp.ucla.edu/archive/mvn/data/sci/plasma/mav_pls_2025.csv"  # Placeholder
OUTPUT_DIR = Path("data/maven_mars")
OUTPUT_DIR.mkdir(exist_ok=True)

response = requests.get(URL)
timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
file = OUTPUT_DIR / f"maven_plasma_{timestamp}.csv"
with open(file, 'wb') as f:
    f.write(response.content)
print(f"Fetched MAVEN Mars data: {file}")
