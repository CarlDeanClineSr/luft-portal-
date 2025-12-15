#!/usr/bin/env python3
# space_weather_rapid_report.py
# 10-row rapid summary, unique filename, unique panel title, for LUFT-PORTAL.

import csv
from pathlib import Path
from datetime import datetime

def sparkline(values):
    bars = "▁▂▃▄▅▆▇█"
    if not values:
        return ""
    mn, mx = min(values), max(values)
    def norm(v): return 0 if mx == mn else int((v - mn) / (mx - mn) * (len(bars) - 1))
    return "".join(bars[norm(v)] for v in values)

def to_float(val):
    try:
        return float(val)
    except Exception:
        return None

def amp_flag(val):
    if val is None: return ""
    if val >= 0.15: return "🟢 High"
    elif val < 0.1: return "🔵 Low"
    else: return "🟡 Mod"

def density_flag(val):
    if val is None: return ""
    if val < 1.5: return "🔵 Sparse"
    elif val < 8: return "🟢 Ok"
    elif val < 15: return "🟡 High"
    else: return "🔴 Burst"

def speed_flag(val):
    if val is None: return ""
    if val < 430: return "🔵 Slow"
    elif val < 500: return "🟢 Norm"
    elif val < 700: return "🟡 High"
    else: return "🔴 Fast"

def bz_flag(val):
    if val is None: return ""
    if val > 0: return "🟢 N"
    elif val > -3: return "🟡 ~S"
    elif val <= -3: return "🔴 S"
    return ""

csv_path = Path("cme_heartbeat_log_2025_12.csv")

rows = []
with csv_path.open(newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get("chi_amplitude"):
            rows.append({
                "Timestamp": row.get("timestamp_utc") or "",
                "Amp": to_float(row["chi_amplitude"]),
                "Density": to_float(row.get("density_p_cm3", "")),
                "Speed": to_float(row.get("speed_km_s", "")),
                "Bz": to_float(row.get("bz_nT", "")),
            })

# Last 10 entries (or less if not enough data).
table = rows[-10:]

amp_vals  = [r["Amp"] for r in table if r["Amp"] is not None]
dens_vals = [r["Density"] for r in table if r["Density"] is not None]
spd_vals  = [r["Speed"] for r in table if r["Speed"] is not None]
bz_vals   = [r["Bz"] for r in table if r["Bz"] is not None]

now = datetime.utcnow()
panel_time = now.strftime("%b %d, %Y • %H:%M:%S UTC")
file_time  = now.strftime("DEC%d_%Y_%H%M%S").upper()
filename = f"space_weather_report_{file_time}.md"

PANEL_TITLE = f"# 🚀 SPACE WEATHER RAPID REPORT ({panel_time})"

md = []
md.append(PANEL_TITLE)
md.append(f"**Report generated:** {panel_time}  ")
md.append(f"**Source file:** `{csv_path.name}` (10 most recent rows)\n")
md.append("| Timestamp         | χ Amp   | χ Flag    | Density | Dens Flag | Speed  | Speed Flag |  Bz   | Bz Flag |")
md.append("|-------------------|---------|-----------|---------|-----------|--------|------------|-------|---------|")

for r in table:
    md.append("| {:<17} | {:<7} | {:<9} | {:<7} | {:<9} | {:<6} | {:<10} | {:<5} | {:<7} |".format(
        r["Timestamp"],
        f"{r['Amp']:.4f}" if r["Amp"] is not None else "",
        amp_flag(r["Amp"]),
        f"{r['Density']:.2f}" if r["Density"] is not None else "",
        density_flag(r["Density"]),
        f"{r['Speed']:.1f}" if r["Speed"] is not None else "",
        speed_flag(r["Speed"]),
        f"{r['Bz']:.2f}" if r["Bz"] is not None else "",
        bz_flag(r["Bz"])
    ))

md.append("| **Trend:**        | {} |         | {} |         | {} |          | {} |         |".format(
    sparkline(amp_vals),
    sparkline(dens_vals),
    sparkline(spd_vals),
    sparkline(bz_vals)
))
md.append("\n*Legend: High = █, Low = ▁*")

out_path = Path(filename)
out_path.write_text("\n".join(md))
print(f"\nWrote file: {filename}\n")
print("\n".join(md))
