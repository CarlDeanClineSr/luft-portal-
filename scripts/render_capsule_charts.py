#!/usr/bin/env python3
"""
render_capsule_charts.py

Unified χ‑physics chart engine for LUFT.

Reads:
    data/extended_heartbeat_log_2025.csv

Produces:
    capsules/2025_dec_batch/charts/
        chi_waveform.png
        solarwind_drivers.png
        multi_panel_capsule.png

Features:
    - χ extended waveform
    - cap contacts (≈0.15)
    - floor contacts (≈0.004)
    - rebounds (dχ/dt > threshold)
    - modulation period shading
    - density / speed / Bz / pressure / E-field
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ------------------------
# Paths
# ------------------------

DATA_PATH = Path("data") / "extended_heartbeat_log_2025.csv"
OUTPUT_DIR = Path("capsules") / "2025_dec_batch" / "charts"

CHI_COL = "chi_amplitude_extended"

CHI_CAP = 0.15
CHI_CAP_TOL = 0.001

CHI_FLOOR = 0.004
CHI_FLOOR_TOL = 0.001

MIN_REBOUND_DELTA = 0.01


# ------------------------
# Helpers
# ------------------------

def detect_cap_floor(df):
    df["is_cap"] = (
        (df[CHI_COL] >= CHI_CAP - CHI_CAP_TOL) &
        (df[CHI_COL] <= CHI_CAP + CHI_CAP_TOL)
    )
    df["is_floor"] = (
        (df[CHI_COL] >= CHI_FLOOR - CHI_FLOOR_TOL) &
        (df[CHI_COL] <= CHI_FLOOR + CHI_FLOOR_TOL)
    )
    return df


def detect_rebounds(df):
    rebounds = []
    chi = df[CHI_COL].values
    t = df.index

    for i in range(1, len(df) - 5):
        if df["is_floor"].iloc[i]:
            floor_val = chi[i]
            future_max = chi[i:i+20].max()
            if future_max - floor_val >= MIN_REBOUND_DELTA:
                j = i + np.argmax(chi[i:i+20])
                rebounds.append((t[i], t[j], floor_val, chi[j]))
    return rebounds


def estimate_modulation_period(df):
    chi = df[CHI_COL].astype(float)
    if len(chi) < 50:
        return np.nan

    dt = (df.index[1] - df.index[0]).total_seconds() / 3600.0
    max_lag = int(10 / dt)
    max_lag = min(max_lag, len(chi) - 2)

    chi = chi - chi.mean()

    acf = []
    for lag in range(1, max_lag):
        a = chi[:-lag]
        b = chi[lag:]
        num = np.sum(a * b)
        den = np.sqrt(np.sum(a*a) * np.sum(b*b))
        acf.append(num / den if den != 0 else 0)

    best_lag = np.argmax(acf) + 1
    return best_lag * dt


# ------------------------
# Chart 1 — χ waveform with physics overlays
# ------------------------

def render_chi_waveform(df, outpath):
    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(df.index, df[CHI_COL], color="black", linewidth=1.2, label="χ")

    # Cap contacts
    cap_df = df[df["is_cap"]]
    ax.scatter(cap_df.index, cap_df[CHI_COL], color="red", s=20, label="Cap contact")

    # Floor contacts
    floor_df = df[df["is_floor"]]
    ax.scatter(floor_df.index, floor_df[CHI_COL], color="blue", s=20, label="Floor contact")

    # Rebounds
    rebounds = detect_rebounds(df)
    for t_floor, t_reb, v_floor, v_reb in rebounds:
        ax.scatter(t_reb, v_reb, color="green", s=40, marker="^")
        ax.plot([t_floor, t_reb], [v_floor, v_reb], color="green", alpha=0.5)

    # Modulation period shading
    period = estimate_modulation_period(df)
    if np.isfinite(period):
        ax.text(0.01, 0.95, f"Modulation ≈ {period:.2f} h",
                transform=ax.transAxes, fontsize=12, color="purple")

    ax.set_title("χ Waveform — Extended χ Physics", fontsize=16)
    ax.set_ylabel("χ amplitude")
    ax.grid(True, alpha=0.3)
    ax.legend()

    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    print(f"✓ Saved {outpath}")


# ------------------------
# Chart 2 — Solar wind drivers
# ------------------------

def render_solarwind_drivers(df, outpath):
    fig, axs = plt.subplots(4, 1, figsize=(14, 10), sharex=True)

    axs[0].plot(df.index, df["density"], color="darkorange")
    axs[0].set_ylabel("Density (p/cm³)")

    axs[1].plot(df.index, df["speed"], color="steelblue")
    axs[1].set_ylabel("Speed (km/s)")

    axs[2].plot(df.index, df["Bz"], color="purple")
    axs[2].set_ylabel("Bz (nT)")

    if "Flow_pressure" in df.columns:
        axs[3].plot(df.index, df["Flow_pressure"], color="black")
        axs[3].set_ylabel("Pressure (nPa)")
    else:
        axs[3].text(0.1, 0.5, "No pressure data", transform=axs[3].transAxes)

    axs[0].set_title("Solar Wind Drivers")

    for ax in axs:
        ax.grid(True, alpha=0.3)

    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    print(f"✓ Saved {outpath}")


# ------------------------
# Chart 3 — Multi‑panel capsule chart
# ------------------------

def render_multi_panel(df, outpath):
    fig, axs = plt.subplots(6, 1, figsize=(14, 14), sharex=True)

    axs[0].plot(df.index, df[CHI_COL], color="black")
    axs[0].set_ylabel("χ")

    axs[1].plot(df.index, df["density"], color="darkorange")
    axs[1].set_ylabel("Density")

    axs[2].plot(df.index, df["speed"], color="steelblue")
    axs[2].set_ylabel("Speed")

    axs[3].plot(df.index, df["Bz"], color="purple")
    axs[3].set_ylabel("Bz")

    if "Flow_pressure" in df.columns:
        axs[4].plot(df.index, df["Flow_pressure"], color="black")
        axs[4].set_ylabel("Pressure")

    if "E_field" in df.columns:
        axs[5].plot(df.index, df["E_field"], color="green")
        axs[5].set_ylabel("E-field")

    axs[0].set_title("Capsule Multi‑Panel — χ Physics")

    for ax in axs:
        ax.grid(True, alpha=0.3)

    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    print(f"✓ Saved {outpath}")


# ------------------------
# Main
# ------------------------

def main():
    if not DATA_PATH.exists():
        print(f"ERROR: Missing {DATA_PATH}")
        return

    df = pd.read_csv(DATA_PATH, parse_dates=["datetime"])
    df = df.set_index("datetime").sort_index()

    df = detect_cap_floor(df)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    render_chi_waveform(df, OUTPUT_DIR / "chi_waveform.png")
    render_solarwind_drivers(df, OUTPUT_DIR / "solarwind_drivers.png")
    render_multi_panel(df, OUTPUT_DIR / "multi_panel_capsule.png")

    print("✓ All charts generated.")


if __name__ == "__main__":
    main()
