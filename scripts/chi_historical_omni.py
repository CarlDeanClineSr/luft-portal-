#!/usr/bin/env python3
"""
Historical χ from NASA OMNI hourly (1963–1974 by default) via CDAWeb using Heliopy.

Requires:
  pip install heliopy cdflib astropy pandas numpy matplotlib

Outputs:
  - results/historical_chi/historical_chi_<start>_<end>.csv
  - figures/historical_chi_timeseries_<start>_<end>.png
"""
import argparse
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from imperial_math import rolling_median, compute_chi

def run(start: str, end: str, out_csv: str, out_png: str, baseline_hours: int = 24):
    # Lazy import heliopy to keep base env lean elsewhere
    from heliopy.data import omni

    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)

    # Fetch hourly OMNI (HRO) from CDAWeb
    data = omni.hro(start_dt, end_dt)  # returns pandas-like DataFrame with hourly cadence

    # Ensure we have components; fall back to magnitude if present
    cols = {c.upper(): c for c in data.columns}
    bx = data[cols.get("BX_GSE")] if "BX_GSE" in cols else None
    by = data[cols.get("BY_GSE")] if "BY_GSE" in cols else None
    bz = data[cols.get("BZ_GSE")] if "BZ_GSE" in cols else None

    if bx is not None and by is not None and bz is not None:
        b_mag = np.sqrt(bx.values**2 + by.values**2 + bz.values**2)
        b = pd.Series(b_mag, index=data.index, name="B_total_nT")
    else:
        # Try common total field names in OMNI HRO
        for candidate in ["F", "BT", "|B|", "B"]:
            if candidate in cols:
                b = pd.Series(data[cols[candidate]].values, index=data.index, name="B_total_nT")
                break
        else:
            raise RuntimeError("No magnetic field columns found (BX_GSE/BY_GSE/BZ_GSE or total field).")

    # Compute baseline and chi (χ)
    b_baseline = rolling_median(b, baseline_hours)
    chi = compute_chi(b, b_baseline)

    df = pd.DataFrame({
        "timestamp": b.index.tz_localize(None),
        "B_total_nT": b.values,
        "B_baseline_nT": b_baseline.values,
        "chi": chi.values
    })
    df.dropna(subset=["chi"], inplace=True)

    # Stats
    total = len(df)
    chi_max = float(np.nanmax(df["chi"].values)) if total else float("nan")
    violations = int((df["chi"] > 0.15).sum())
    attractor = float(((df["chi"] >= 0.145) & (df["chi"] <= 0.155)).sum()) / total * 100.0 if total else float("nan")

    print(f"Points: {total}")
    print(f"χ_max:  {chi_max:.6f}")
    print(f"Violations (χ>0.15): {violations}")
    print(f"Attractor occupancy (0.145–0.155): {attractor:.2f}%")

    # Save CSV
    Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)

    # Plot
    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(12, 4))
    plt.plot(df["timestamp"], df["chi"], linewidth=0.8, color="#1565c0")
    plt.axhline(0.15, color="#c62828", linestyle="--", linewidth=1.0, label="χ = 0.15")
    plt.xlabel("Time (UTC)")
    plt.ylabel("χ")
    plt.title(f"Historical χ (OMNI hourly): {start} → {end} (baseline={baseline_hours}h)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--start", default="1963-01-01T00:00:00", help="ISO start (UTC)")
    p.add_argument("--end", default="1974-12-31T23:00:00", help="ISO end (UTC)")
    p.add_argument("--out-csv", default="results/historical_chi/historical_chi_1963_1974.csv")
    p.add_argument("--out-png", default="figures/historical_chi_timeseries_1963_1974.png")
    p.add_argument("--baseline-hours", type=int, default=24)
    args = p.parse_args()
    run(args.start, args.end, args.out_csv, args.out_png, args.baseline_hours)
