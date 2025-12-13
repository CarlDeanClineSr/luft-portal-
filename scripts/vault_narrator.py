#!/usr/bin/env python3
"""
Vault Narrator - Auto-generate latest status markdown
Reads the latest CSV data and creates LATEST_VAULT_STATUS.md
"""

import pandas as pd
from datetime import datetime
import os

csv_path = "data/cme_heartbeat_log_2025_12.csv"

# Check if file exists
if not os.path.exists(csv_path):
    print(f"Warning: {csv_path} not found")
    exit(0)

# Read CSV with proper column names
df = pd.read_csv(csv_path, header=None, names=[
    'timestamp_utc', 'chi_amplitude', 'density_p_cm3', 'phase', 
    'temperature_kK', 'speed_km_s', 'bz_nT', 'bt_nT', 'source'
])

# Convert timestamp
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
df = df.sort_values('timestamp_utc')

# Last 20 rows
latest = df.tail(20)

# Current streak (consecutive 0.15 from end)
streak = 0
for chi in df['chi_amplitude'].iloc[::-1]:
    if abs(chi - 0.15) < 0.0001:
        streak += 1
    else:
        break

# Find last lock
lock_rows = df[abs(df['chi_amplitude'] - 0.15) < 0.0001]
last_lock = lock_rows.iloc[-1]['timestamp_utc'] if len(lock_rows) > 0 else "None"

status = "ACTIVE SUPERSTREAK" if streak >= 3 else "Quiet or building"

# Generate summary
summary = f"""# LUFT Vault – Live Status Report
**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

## Current Streak
- Confirmed χ = 0.15 locks: **{streak}**  
- Last lock: {last_lock}  
- Status: **{status}**

## Latest 20 Rows

| Timestamp              | χ Amplitude | Density | Speed  | Bz    | Bt     | Phase |
|------------------------|-------------|---------|--------|-------|--------|-------|
"""

for _, row in latest.iterrows():
    chi = "**0.15**" if abs(row['chi_amplitude'] - 0.15) < 0.0001 else f"{row['chi_amplitude']:.4f}"
    summary += f"| {row['timestamp_utc']} | {chi} | {row['density_p_cm3']:.2f} | {row['speed_km_s']:.1f} | {row['bz_nT']:.2f} | {row['bt_nT']:.2f} | {row['phase']} |\n"

summary += f"\n**Source:** Auto-generated from `{csv_path}`\n"
summary += f"**Total rows in log:** {len(df)}\n"

# Write to file
with open("LATEST_VAULT_STATUS.md", "w") as f:
    f.write(summary)

print(f"✓ Vault narrator complete – Current streak: {streak} locks")
print(f"✓ Status: {status}")
print(f"✓ Last lock: {last_lock}")
