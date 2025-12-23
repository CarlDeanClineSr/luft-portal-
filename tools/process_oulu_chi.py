import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/oulu_cr")
OUTPUT_DIR = Path("results/oulu_chi")
OUTPUT_DIR.mkdir(exist_ok=True)

latest = max(DATA_DIR.glob("*.csv"), key=lambda x: x.stat().st_mtime)
df = pd.read_csv(latest, parse_dates=['timestamp_utc'])

# Normalize counts (0–1 scale)
df['norm_counts'] = (df['neutron_counts'] - df['neutron_counts'].min()) / (df['neutron_counts'].max() - df['neutron_counts'].min())

cap = df['norm_counts'].max()
floor = df['norm_counts'].min()

print(f"Oulu CR normalized cap: {cap:.4f}, floor: {floor:.4f}")

df.to_csv(OUTPUT_DIR / f"oulu_chi_{latest.stem}.csv", index=False)
