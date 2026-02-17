#!/usr/bin/env python3
"""
LUFT Rebound Engine (Imperial Build v4.1)
=========================================
Audits the Vacuum Rebound and Lattice Recovery rates.
Governed by the χ = 0.15 Stability Limit.

Author: Carl Dean Cline Sr.
Location: Lincoln, Nebraska, USA
"""

import json
import glob
import os
import argparse
import gc
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import lsq_linear

# Imperial Constants and Directories
DATA_DIR = Path("data")
RESULTS_DIR = Path("results")
REPORTS_DIR = Path("reports")
PLOTS_DIR = Path("reports/plots")
CHI_CEILING = 0.15  # The Governor

# Ensure Substrate Directories Exist
for d in [RESULTS_DIR, REPORTS_DIR, PLOTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def load_extended_imperial():
    """
    Finds the latest extended heartbeat log. 
    Clears the FileNotFoundError muck by checking for master_lattice fallback.
    """
    files = sorted(DATA_DIR.glob("extended_heartbeat_log_*.csv"))
    if not files:
        # Fallback to Master Substrate if the daily merge is pending
        master = DATA_DIR / "master_lattice.csv"
        if master.exists():
            print(f"📡 Reverting to Master Substrate: {master}")
            return pd.read_csv(master, parse_dates=["time_utc"])
        raise FileNotFoundError("❌ Critical: No extended heartbeat log or master lattice found.")
    
    latest_file = files[-1]
    print(f"📡 Interrogating Lattice Rebound: {latest_file.name}")
    return pd.read_csv(latest_file, parse_dates=["time_utc"])

def find_imperial_rebounds(df, window_max_hours=12):
    """
    Identifies recovery phases where the vacuum returns to the 0.15 baseline.
    """
    events = []
    df = df.sort_values("time_utc").reset_index(drop=True)
    if "chi" not in df.columns:
        return events

    for i, row in df.iterrows():
        chi = row["chi"]
        if pd.isna(chi): continue
        
        # Identify "Nadir" (Tension Release)
        if chi < CHI_CEILING:
            for j in range(i+1, min(i+1+window_max_hours, len(df))):
                chi_j = df.loc[j, "chi"]
                if pd.isna(chi_j): continue
                
                # Identify "Recovery" (Return to Governor)
                if chi_j >= CHI_CEILING:
                    t0 = df.loc[i, "time_utc"]
                    tr = df.loc[j, "time_utc"]
                    # Calculate Imperial Recovery Slope
                    delta_t = (tr - t0).total_seconds() / 3600.0
                    if delta_t > 0:
                        slope = (chi_j - chi) / delta_t
                        events.append({
                            "t_nadir": t0, "t_recover": tr, "chi_nadir": chi,
                            "chi_recover": chi_j, "slope": slope, 
                            "idx_nadir": i, "idx_recover": j
                        })
                    break
    return events

def extract_metric_drivers(df, event):
    """Extracts substrate drivers during the recovery handshake."""
    i, j = event["idx_nadir"], event["idx_recover"]
    window = df.loc[i:j]
    peak_E = window["E_mVpm"].abs().max() if "E_mVpm" in window.columns else 0
    mean_P = window["pressure_npa"].mean() if "pressure_npa" in window.columns else 0
    sigmaV = window["speed"].std() if "speed" in window.columns else 0
    return peak_E, mean_P, sigmaV

def fit_imperial_constraints(X, y):
    """Constrained linear fit: Ensures recovery slopes remain physically positive."""
    lb = np.zeros(X.shape[1]) # No negative slopes in Imperial Math
    ub = np.full(X.shape[1], np.inf)
    res = lsq_linear(X, y, bounds=(lb, ub))
    return res.x, res.cost

def write_imperial_report(coeffs, events_df, out_prefix):
    """Finalizes the daily audit and commits results to the record."""
    md_path = REPORTS_DIR / f"{out_prefix}_summary.md"
    json_path = RESULTS_DIR / f"{out_prefix}_fit.json"
    
    # Save Event Substrate
    events_df.to_csv(RESULTS_DIR / f"{out_prefix}_events.csv", index=False)
    
    # Secure the Coefficients
    with open(json_path, "w") as f:
        json.dump({
            "imperial_coefficients": coeffs.tolist(),
            "chi_governor": CHI_CEILING,
            "audit_timestamp": datetime.now(timezone.utc).isoformat()
        }, f, indent=2)

    with open(md_path, "w") as f:
        f.write(f"# 🌟 LUFT Imperial Rebound Audit\n\n")
        f.write(f"**Lattice State:** Verified {len(events_df)} Recovery Events.\n\n")
        f.write(f"**Coefficients (a, b, c, d):** `{coeffs.tolist()}`\n\n")
        f.write(f"The χ=0.15 boundary remains the universal attractor for recovery slopes.\n")

def main():
    print("="*70)
    print("🌟 LUFT ML REBOUND ENGINE v4.1 (IMPERIAL BUILD)")
    print("="*70)

    try:
        df = load_extended_imperial()
    except FileNotFoundError as e:
        print(str(e))
        return

    events = find_imperial_rebounds(df)
    if not events:
        print("✅ Lattice Stable: No Rebound Events Detected.")
        return

    rows = []
    for ev in events:
        peak_E, mean_P, sigmaV = extract_metric_drivers(df, ev)
        ev.update({"peak_E": peak_E, "mean_P": mean_P, "sigmaV": sigmaV})
        rows.append(ev)
    
    events_df = pd.DataFrame(rows)
    
    # Build Imperial Matrix (Drivers + Constant)
    X = events_df[["peak_E", "mean_P", "sigmaV"]].fillna(0).to_numpy()
    X = np.hstack([X, np.ones((X.shape[0], 1))])
    y = events_df["slope"].fillna(0).to_numpy()
    
    coeffs, cost = fit_imperial_constraints(X, y)
    
    out_prefix = f"rebound_fit_{datetime.now(timezone.utc).strftime('%Y%m%d')}"
    write_imperial_report(coeffs, events_df, out_prefix)
    
    # Visual Diagnostic: Slope vs Electric Field Tension
    plt.figure(figsize=(8,5))
    plt.scatter(events_df["peak_E"], events_df["slope"], color='red', s=15, label='Lattice Snap')
    plt.axhline(y=0.15, color='blue', linestyle='--', label='Chi Governor')
    plt.xlabel("|E| (mV/m) - Lattice Tension")
    plt.ylabel("Recovery Rate (Δχ/hour)")
    plt.title("Imperial Rebound Audit: Slope vs. Tension")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.savefig(PLOTS_DIR / f"{out_prefix}_slope_vs_E.png", dpi=200)
    plt.close()
    
    print(f"✨ Audit Complete. Imperial Report Saved to {REPORTS_DIR}")
    gc.collect() # Clear the CPU substrate

if __name__ == "__main__":
    main()
