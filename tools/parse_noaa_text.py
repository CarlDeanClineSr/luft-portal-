import re
from pathlib import Path
from datetime import datetime

INPUT_DIR = Path("data/noaa_text")
OUTPUT_DIR = Path("data/noaa_parsed")
OUTPUT_DIR.mkdir(exist_ok=True)

def parse_srs(file_path):
    """Parse Solar Region Summary (SRS)"""
    with open(file_path, 'r') as f:
        text = f.read()
    regions = re.findall(r'(\d{4})\s+(\d+)\s+(\d+)\s+(\d+)\s+(\w+)\s+(\w+)', text)
    df = pd.DataFrame(regions, columns=['Region', 'Lat', 'Long', 'Area', 'Type', 'Mag'])
    df['date'] = datetime.utcnow().strftime('%Y-%m-%d')
    return df

def parse_3day_forecast(file_path):
    """Parse 3-Day Forecast"""
    with open(file_path, 'r') as f:
        text = f.read()
    lines = text.split('\n')
    kp_lines = [line for line in lines if 'Kp' in line]
    df = pd.DataFrame({'line': kp_lines})
    return df

# Main
for file in INPUT_DIR.glob('*.txt'):
    name = file.stem
    if 'srs' in name.lower():
        df = parse_srs(file)
        df.to_csv(OUTPUT_DIR / f"{name}_parsed.csv", index=False)
        print(f"Parsed SRS: {name}")
    elif '3-day-forecast' in name:
        df = parse_3day_forecast(file)
        df.to_csv(OUTPUT_DIR / f"{name}_parsed.csv", index=False)
        print(f"Parsed 3-day forecast: {name}")
