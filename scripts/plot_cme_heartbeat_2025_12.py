#!/usr/bin/env python3
"""
Plot LUFT CME Heartbeat Log for 2025-12 with dynamic pressure and χ amplitude.

- Reads:  data/cme_heartbeat_log_2025_12.csv
- Computes dynamic pressure P_dyn (nPa) from density and speed.
- Plots:
  - P_dyn vs time (black line, left axis)
  - χ amplitude vs time (colored by storm_phase, right axis)
  - Optional: χ_pred from boundary recoil law (orange dashed line)

Color scheme (Christmas-style):
- Red   = peak (storm_phase == "peak")
- Green = post-storm (storm_phase == "post-storm")
- Grey  = pre (storm_phase == "pre")
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Path to CSV relative to repo root
DATA_PATH = Path("data") / "cme_heartbeat_log_2025_12.csv"
OUT_PATH = Path("results")
OUT_PATH.mkdir(exist_ok=True, parents=True)


def compute_dynamic_pressure(df: pd.DataFrame) -> pd.Series:
    """
    Compute dynamic pressure P_dyn in nPa from density (p/cm^3) and speed (km/s).

    Formula (standard solar wind approximation):
        P_dyn [nPa] = 1.6726e-6 * n * v^2

    where:
        n = density_p_cm3 (protons per cubic cm)
        v = speed_km_s (km/s)
    """
    n = df["density_p_cm3"]
    v = df["speed_km_s"]
    return 1.6726e-6 * n * v * v


def map_colors(storm_phase: pd.Series) -> pd.Series:
    """
    Map storm_phase to colors:
    - 'peak'        -> 'red'
    - 'post-storm'  -> 'green'
    - 'pre' or others -> 'grey'
    """
    mapping = {
        "peak": "red",
        "post-storm": "green",
        "pre": "grey",
    }
    return storm_phase.map(mapping).fillna("grey")


def main():
    # Load CSV
    df = pd.read_csv(DATA_PATH, sep="\t")
    # Parse timestamps
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"])

    # Sort by time
    df = df.sort_values("timestamp_utc")

    # Compute dynamic pressure
    df["P_dyn_nPa"] = compute_dynamic_pressure(df)

    # Boundary recoil law: optional predicted chi from P_dyn
    # Δχ = 0.0032 * P_dyn + 0.054  (from your capsule)
    # Here we interpret that as χ_pred = 0.0032 * P_dyn + 0.054
    df["chi_pred"] = 0.0032 * df["P_dyn_nPa"] + 0.054

    # Color mapping
    df["color"] = map_colors(df["storm_phase"])

    # Create figure
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Left axis: P_dyn
    ax1.plot(
        df["timestamp_utc"],
        df["P_dyn_nPa"],
        color="black",
        linewidth=1.5,
        label="P_dyn (nPa)",
    )
    ax1.set_ylabel("Dynamic Pressure P_dyn (nPa)", color="black")
    ax1.tick_params(axis="y", labelcolor="black")

    # Second axis: χ amplitude
    ax2 = ax1.twinx()
    ax2.set_ylabel("χ amplitude", color="black")
    ax2.tick_params(axis="y", labelcolor="black")

    # Scatter χ with colors by storm_phase
    ax2.scatter(
        df["timestamp_utc"],
        df["chi_amplitude"],
        c=df["color"],
        s=25,
        edgecolor="none",
        label="χ (colored by storm_phase)",
        alpha=0.9,
    )

    # Optional: plot predicted χ from boundary recoil law
    ax2.plot(
        df["timestamp_utc"],
        df["chi_pred"],
        color="orange",
        linestyle="--",
        linewidth=1.2,
        label="χ_pred (boundary recoil law)",
    )

    # Title and formatting
    fig.suptitle("LUFT CME Heartbeat — χ and Dynamic Pressure (2025-12)", fontsize=14)
    fig.autofmt_xdate()

    # Build a combined legend from both axes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    plt.tight_layout()

    # Save figure
    out_file = OUT_PATH / "cme_heartbeat_2025_12_chi_pdyn.png"
    fig.savefig(out_file, dpi=200)
    print(f"Saved plot to {out_file.resolve()}")

    # Optionally show interactively
    # plt.show()


if __name__ == "__main__":
    main()
