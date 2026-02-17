import pandas as pd
from pathlib import Path
from datetime import datetime

LOG_PATH = Path("data/cme_heartbeat_log_2025_12.csv")
PARSED_DIR = Path("data/noaa_parsed")
OUTPUT_PATH = Path("data/merged_noaa_luft.csv")

log = pd.read_csv(LOG_PATH, parse_dates=['timestamp_utc']).set_index('timestamp_utc')

# Load latest parsed files
latest_files = list(PARSED_DIR.glob("*.csv"))
if not latest_files:
    print("No parsed files found.")
    exit()

# Example: Merge 3-day forecast (expand as needed)
forecast = pd.read_csv(PARSED_DIR / "3day_forecast_parsed.csv")
# Add merge logic (e.g., align on date or nearest timestamp)

# Placeholder: add dummy column for demo
log['forecast_kp_max'] = forecast['line'].str.extract(r'Kp.*max.*(\d+\.\d+)').astype(float).iloc[0]

log.to_csv(OUTPUT_PATH)
print(f"Merged: {OUTPUT_PATH}")
