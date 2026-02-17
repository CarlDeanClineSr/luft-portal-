#!/usr/bin/env python3
"""
make_example_chart.py
Reads normalized plasma JSON (with chi_from_pdyn), and creates an example
chart saved to charts/chart_example_chi.png.

Usage:
    python3 scripts/make_example_chart.py
"""
import json
from pathlib import Path
import matplotlib.pyplot as plt
from datetime import datetime

DATA = Path('data')
OUT = Path('charts')
OUT.mkdir(exist_ok=True)

IN_FILE = DATA / 'ace_plasma_audit_normalized.json'

if not IN_FILE.exists():
    print(f"Missing input file: {IN_FILE}")
    raise SystemExit(1)

plasma = json.loads(IN_FILE.read_text(encoding='utf-8'))

times = []
chis = []
for rec in plasma:
    t = rec.get('timestamp_utc')
    if not t:
        continue
    try:
        dt = datetime.strptime(t, '%Y-%m-%d %H:%M:%S.%f')
    except Exception:
        try:
            dt = datetime.strptime(t, '%Y-%m-%d %H:%M:%S')
        except Exception:
            continue
    times.append(dt)
    chis.append(rec.get('chi_from_pdyn'))

if len(times) == 0:
    print('No valid timestamps found in normalized plasma file.')
    raise SystemExit(1)

plt.figure(figsize=(10,5))
plt.plot(times, chis, marker='o', color='royalblue', label='χ (from P_dyn)')
plt.axhline(0.055, color='gray', linestyle='--', label='baseline χ=0.055')
plt.xlabel('Timestamp UTC')
plt.ylabel('χ amplitude')
plt.title('Example χ amplitude (computed from normalized plasma)')
plt.legend()
plt.tight_layout()
outfile = OUT / 'chart_example_chi.png'
plt.savefig(outfile, dpi=200)
plt.close()
print(f"Saved example chart to {outfile}")
