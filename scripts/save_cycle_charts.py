#!/usr/bin/env python3
"""
save_cycle_charts.py (updated)
Generates cycle charts using the normalized plasma audit JSON. This script
computes p_dyn and χ if they are missing (by calling compute_pdyn_chi logic
inline), and saves a numbered chart for a given cycle.

Usage:
    python3 scripts/save_cycle_charts.py --cycle 1
or
    python3 scripts/save_cycle_charts.py 1

If no cycle is provided, saves chart_cycle_latest.png using all available data.
"""
import argparse
import json
from pathlib import Path
import matplotlib.pyplot as plt
from datetime import datetime

K_PDYN = 1.6726e-6
CHI_A = 0.0032
CHI_B = 0.054

DATA = Path('data')
OUT = Path('charts')
OUT.mkdir(exist_ok=True)
IN_FILE = DATA / 'ace_plasma_audit_normalized.json'

parser = argparse.ArgumentParser()
parser.add_argument('--cycle', '-c', type=int, default=None, help='Cycle number to save')
args = parser.parse_args()

if not IN_FILE.exists():
    print(f"Missing input file: {IN_FILE}")
    raise SystemExit(1)

plasma = json.loads(IN_FILE.read_text(encoding='utf-8'))
# ensure p_dyn and chi are present
for rec in plasma:
    if rec.get('p_dyn_nPa') is None or rec.get('chi_from_pdyn') is None:
        try:
            n = float(rec.get('density_p_cm3') or 0.0)
            v = float(rec.get('speed_km_s') or 0.0)
            p_dyn = K_PDYN * n * (v**2)
            rec['p_dyn_nPa'] = round(p_dyn, 4)
            rec['chi_from_pdyn'] = round(CHI_A * p_dyn + CHI_B, 6)
        except Exception:
            rec['p_dyn_nPa'] = None
            rec['chi_from_pdyn'] = None

# build time series
times = []
chis = []
for rec in plasma:
    t = rec.get('timestamp_utc')
    try:
        dt = datetime.strptime(t, '%Y-%m-%d %H:%M:%S.%f')
    except Exception:
        try:
            dt = datetime.strptime(t, '%Y-%m-%d %H:%M:%S')
        except Exception:
            continue
    times.append(dt)
    chis.append(rec.get('chi_from_pdyn'))

if args.cycle is None:
    filename = OUT / 'chart_cycle_latest.png'
else:
    filename = OUT / f'chart_cycle_{args.cycle}.png'

plt.figure(figsize=(14,6))
plt.plot(times, chis, marker='o', color='royalblue', label='χ Amplitude (from P_dyn)')
plt.axhline(CHI_B, color='gray', linestyle='--', label=f'baseline χ={CHI_B}')
plt.xlabel('Timestamp UTC')
plt.ylabel('χ Amplitude')
plt.title(f'χ Amplitude Over Time (Cycle {args.cycle or "latest"})')
plt.legend()
plt.tight_layout()
plt.savefig(filename, dpi=300)
plt.close()
print(f"Saved {filename}")
