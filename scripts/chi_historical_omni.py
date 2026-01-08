#!/usr/bin/env python3
"""
Historical χ from NASA OMNI hourly (1963–1974 by default) via SPDF CDAWeb (cdasws).

Replaces HelioPy with cdasws (HelioPy is deprecated).

Requires:
  pip install cdasws pandas numpy matplotlib xarray cdflib

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

# Local helper for rolling median + chi
from imperial_math import rolling_median, compute_chi


def fetch_omni_hourly_cdasws(start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
    """Fetch OMNI hourly data using CDAWeb web services (cdasws)."""
    from cdasws import CdasWs

    cdas = CdasWs()
    # Dataset name for hourly OMNI in CDAWeb
    dataset = "OMNI2_H0_MRG1HR"

    # Request all variables to get both Epoch and Epoch_1800 data
    status, data = cdas.get_data(dataset, ["ALL-VARIABLES"], start_dt, end_dt)

    if status['http']['status_code'] != 200:
        raise RuntimeError(f"CDAWeb request failed with status {status['http']['status_code']}")

    if data is None:
        raise RuntimeError("No OMNI hourly data returned for the requested range.")

    # Convert xarray Dataset to pandas DataFrame
    # Use only variables on the Epoch coordinate (hourly data)
    hourly_vars = [v for v in data.data_vars if 'Epoch' in data[v].dims and 'Epoch_1800' not in data[v].dims]
    df = data[hourly_vars].to_dataframe().reset_index()
    
    # Basic sanity check
    if df.empty:
        raise RuntimeError("No OMNI hourly data returned for the requested range.")
    
    return df.sort_values('Epoch').set_index('Epoch')


def run(start: str, end: str, out_csv: str, out_png: str, baseline_hours: int = 24):
    # Parse dates (ISO)
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)

    # Fetch data
    df_omni = fetch_omni_hourly_cdasws(start_dt, end_dt)

    # Prefer vector if available, else total field (ABS_B)
    if {"BX_GSE", "BY_GSE", "BZ_GSE"}.issubset(df_omni.columns):
        b_mag = np.sqrt(
            df_omni["BX_GSE"].values**2
            + df_omni["BY_GSE"].values**2
            + df_omni["BZ_GSE"].values**2
        )
        b = pd.Series(b_mag, index=df_omni.index, name="B_total_nT")
    elif "ABS_B" in df_omni.columns:
        b = pd.Series(df_omni["ABS_B"].values, index=df_omni.index, name="B_total_nT")
    else:
        raise RuntimeError("No magnetic field columns found (BX_GSE/BY_GSE/BZ_GSE or ABS_B).")

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
    attractor = (
        float(((df["chi"] >= 0.145) & (df["chi"] <= 0.155)).sum()) / total * 100.0
        if total else float("nan")
    )

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
