#!/usr/bin/env python3
# vault_forecast_autogen.py
# 10-row forecast with traffic-light flags, sparklines, and exact table structure as your vault wants.

import csv
import sys
from pathlib import Path

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

# --- Traffic light logic ---
def chi_flag(chi):
    if chi is None: return ''
    if chi >= 0.15:
        return "🟢"
    elif chi >= 0.13:
        return "🟡"
    else:
        return "🔵"

def dens_flag(dens):
    if dens is None: return ''
    if dens >= 8:
        return "🔴"
    elif dens >= 4:
        return "🟡"
    elif dens > 0:
        return "🟢"
    else:
        return "🔵"

def speed_flag(spd):
    if spd is None: return ''
    if spd >= 600:
        return "🔴"
    elif spd >= 500:
        return "🟡"
    elif spd > 0:
        return "🟢"
    else:
        return "🔵"

def bz_flag(bz):
    if bz is None: return ''
    if bz <= -8:
        return "🔴"
    elif bz < 0:
        return "🟡"
    elif bz >= 0:
        return "🟢"
    else:
        return "🔵"

csv_path = Path("data/cme_heartbeat_log_2025_12.csv")

# Check if file exists
if not csv_path.exists():
    print(f"ERROR: CSV file not found at {csv_path}", file=sys.stderr)
    print(f"ERROR: The vault forecast requires the heartbeat log to generate the panel.", file=sys.stderr)
    print(f"ERROR: Expected file location: {csv_path.absolute()}", file=sys.stderr)
    sys.exit(1)

rows = []
with csv_path.open(newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get("chi_amplitude"):
            rows.append({
                "Time": row.get("timestamp_utc") or "",
                "χ": to_float(row["chi_amplitude"]),
                "Density": to_float(row.get("density_p_cm3", "")),
                "Speed": to_float(row.get("speed_km_s", "")),
                "Bz": to_float(row.get("bz_nT", "")),
                "Source": row.get("source", "")
            })

# Use the last 10
table_rows = rows[-10:]

chi_vals  = [r["χ"] for r in table_rows if r["χ"] is not None]
dens_vals = [r["Density"] for r in table_rows if r["Density"] is not None]
spd_vals  = [r["Speed"] for r in table_rows if r["Speed"] is not None]
bz_vals   = [r["Bz"] for r in table_rows if r["Bz"] is not None]

latest_time = table_rows[-1]["Time"] if table_rows else "N/A"

md = []
md.append(f"# 🔮 VAULT 10-ROW FORECAST INDICATOR (Dec 15, 2025 – Latest {latest_time} UTC)\n")
md.append(f"**Generated:** {latest_time} UTC  ")
md.append(f"**Source:** `{csv_path.name}` (rows {table_rows[0]['Time']}–{latest_time} UTC)\n")
md.append("| Time (UTC)       | χ Amp   | χ  | Density (p/cm³) | Dens | Speed (km/s) | Spd | Bz (nT) | Bz  | Source     |")
md.append("|------------------|---------|----|-----------------|------|--------------|-----|---------|-----|------------|")

for r in table_rows:
    md.append("| {:<16} | {:<7} | {:<2} | {:<15} | {:<4} | {:<12} | {:<3} | {:<7} | {:<3} | {:<10} |".format(
        r["Time"],
        f"{r['χ']:.4f}" if r["χ"] is not None else "",
        chi_flag(r["χ"]),
        f"{r['Density']:.2f}" if r["Density"] is not None else "",
        dens_flag(r["Density"]),
        f"{r['Speed']:.1f}" if r["Speed"] is not None else "",
        speed_flag(r["Speed"]),
        f"{r['Bz']:.2f}" if r["Bz"] is not None else "",
        bz_flag(r["Bz"]),
        r["Source"] or ""
    ))

md.append("\n---\n")
md.append("### 📈 Trend Sparklines")
md.append(f"- χ Amplitude: {sparkline(chi_vals)}  ")
md.append(f"- Density: {sparkline(dens_vals)}  ")
md.append(f"- Speed: {sparkline(spd_vals)}  ")
md.append(f"- Bz: {sparkline(bz_vals)}  ")
md.append("\n*Legend: High = █, Low = ▁*\n")
md.append("---\n")
md.append("### 🧭 Vault Status")
md.append("- **χ Status:** Quiet (<0.15 = 🟡/🔵, >=0.15 = 🟢)  ")
md.append("- **Density:** 🟢 = Normal, 🟡 = Mild Elevation, 🔴 = High/Compression  ")
md.append("- **Speed:** 🟢 = Nominal, 🟡 = Fast, 🔴 = Very Fast  ")
md.append("- **Bz:** 🟢 = Northward/Quiet, 🟡 = Southward, 🔴 = Possible storm  ")
if any(bz is not None for bz in bz_vals):
    bz_status = ""
    if len(table_rows) > 4:
        # Show Bz value from middle of forecast window (row 5) and current value (last row)
        if table_rows[4]["Bz"] is not None:
            bz_status += f"- **Bz Event:** {table_rows[4]['Bz']:.2f} nT ({table_rows[4]['Time']} UTC), "
        if table_rows[-1]["Bz"] is not None:
            bz_status += f"now {table_rows[-1]['Bz']:.2f} nT ({table_rows[-1]['Time']} UTC)  "
    elif table_rows:
        # If we have fewer than 5 rows, just show the latest Bz value
        if table_rows[-1]["Bz"] is not None:
            bz_status += f"- **Latest Bz:** {table_rows[-1]['Bz']:.2f} nT ({table_rows[-1]['Time']} UTC)  "
    md.append(bz_status)
else:
    md.append("- **Bz:** (no Bz data for this segment)")
md.append("- **Overall:** Vault remains **Watchful / Quiet**\n")
md.append("---\n**Commit Title Suggestion:**  \n`vault_10row_forecast_indicator_dec15.md`\n")

Path("vault_10row_forecast_indicator_dec15.md").write_text("\n".join(md))
print("\n".join(md))
