#!/usr/bin/env python3
"""
Rebound runner:
- Load data/extended_heartbeat_log_YYYYMMDD.csv
- Identify rebound events where chi < 0.15 and recovers
- Compute event metrics and run constrained linear fit:
    slope = a*|E| + b*P + c*sigmaV + d  (slope >= 0)
- Save results CSV, JSON (coeffs), and a Markdown summary with plots.
"""
import json
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import lsq_linear

DATA_DIR = Path("data")
RESULTS_DIR = Path("results")
REPORTS_DIR = Path("reports")
PLOTS_DIR = Path("reports/plots")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

CHI_CEILING = 0.15

def load_extended():
    files = sorted(DATA_DIR.glob("extended_heartbeat_log_*.csv"))
    if not files:
        raise FileNotFoundError("No extended heartbeat log found.")
    return pd.read_csv(files[-1], parse_dates=["time_utc"], infer_datetime_format=True)

def find_rebounds(df, window_max_hours=12):
    events = []
    df = df.sort_values("time_utc").reset_index(drop=True)
    if "chi" not in df.columns:
        return events
    for i, row in df.iterrows():
        chi = row["chi"]
        if pd.isna(chi):
            continue
        if chi < CHI_CEILING:
            for j in range(i+1, min(i+1+window_max_hours, len(df))):
                chi_j = df.loc[j, "chi"]
                if pd.isna(chi_j):
                    continue
                if chi_j >= CHI_CEILING:
                    t0 = df.loc[i, "time_utc"]
                    tr = df.loc[j, "time_utc"]
                    slope = (chi_j - chi) / ((tr - t0).total_seconds() / 3600.0)
                    events.append({
                        "t_nadir": t0, "t_recover": tr, "chi_nadir": chi,
                        "chi_recover": chi_j, "slope": slope, "idx_nadir": i, "idx_recover": j
                    })
                    break
    return events

def extract_drivers(df, event):
    i = event["idx_nadir"]
    j = event["idx_recover"]
    window = df.loc[i:j]
    peak_E = window["E_mVpm"].abs().max() if "E_mVpm" in window.columns else np.nan
    mean_P = window["pressure_npa"].mean() if "pressure_npa" in window.columns else np.nan
    sigmaV = window["speed"].std() if "speed" in window.columns else np.nan
    return peak_E, mean_P, sigmaV

def fit_constrained_linear(X, y):
    lb = np.zeros(X.shape[1])
    ub = np.full(X.shape[1], np.inf)
    res = lsq_linear(X, y, bounds=(lb, ub))
    return res.x, res.cost, res

def write_report(coeffs, events_df, out_prefix):
    csv_path = RESULTS_DIR / f"{out_prefix}_events.csv"
    json_path = RESULTS_DIR / f"{out_prefix}_fit.json"
    md_path = REPORTS_DIR / f"{out_prefix}_summary.md"
    events_df.to_csv(csv_path, index=False)
    fit_obj = {"coefficients": coeffs.tolist(), "generated": datetime.now(timezone.utc).isoformat()}
    with open(json_path, "w") as f:
        json.dump(fit_obj, f, indent=2)
    with open(md_path, "w") as f:
        f.write(f"# Rebound Fit Summary\n\n")
        f.write(f"Generated: {datetime.now(timezone.utc).isoformat()}\n\n")
        f.write(f"Coefficients (a, b, c, d): {coeffs.tolist()}\n\n")
        f.write(f"Events processed: {len(events_df)}\n\n")
        f.write(f"Plots: see `reports/plots/` for visual diagnostics.\n")
    print(f"[OK] Wrote report: {md_path}")

def main():
    df = load_extended()
    events = find_rebounds(df)
    if not events:
        print("[INFO] No rebound events found.")
        return
    rows = []
    for ev in events:
        peak_E, mean_P, sigmaV = extract_drivers(df, ev)
        ev.update({"peak_E": peak_E, "mean_P": mean_P, "sigmaV": sigmaV})
        rows.append(ev)
    events_df = pd.DataFrame(rows)
    X = events_df[["peak_E", "mean_P", "sigmaV"]].fillna(0).to_numpy()
    X = np.hstack([X, np.ones((X.shape[0], 1))])
    y = events_df["slope"].fillna(0).to_numpy()
    coeffs, cost, res = fit_constrained_linear(X, y)
    out_prefix = f"rebound_fit_{datetime.now(timezone.utc).strftime('%Y%m%d')}"
    write_report(coeffs, events_df, out_prefix)
    plt.figure(figsize=(6,4))
    plt.scatter(events_df["peak_E"], events_df["slope"], s=8)
    plt.xlabel("|E| (mV/m)")
    plt.ylabel("Recovery slope (Δχ/hour)")
    plt.title("Recovery slope vs |E|")
    plt.grid(True)
    plot_path = PLOTS_DIR / f"{out_prefix}_slope_vs_E.png"
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"[OK] Wrote plot: {plot_path}")

if __name__ == "__main__":
    main()
