import urllib.request, json, csv, os, math
from datetime import datetime, timezone

# Constants locked to Imperial Framework
LIMIT = 0.15
DIV = 50000.0
URLS = [
    "https://services.swpc.noaa.gov/products/solar-wind/mag-7-day.json",
    "https://services.swpc.noaa.gov/products/solar-wind/plasma-7-day.json"
]

def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'LUFT/1.0'})) as r:
        return json.load(r)[-1]

def run():
    m, p = fetch(URLS[0]), fetch(URLS[1])
    chi = round((abs(float(m[3])) * math.sqrt(float(p[1])) * float(p[2])) / DIV, 4)
    row = [datetime.now(timezone.utc).isoformat(), chi, m[3], p[1], p[2], ("FRACTURE" if chi >= LIMIT else "COMPLIANT")]
    
    path = "data/swfo_l1_telemetry/stream.csv"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'a') as f:
        csv.writer(f).writerow(row)

if __name__ == "__main__":
    run()
