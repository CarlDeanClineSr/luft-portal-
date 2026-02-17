#!/usr/bin/env python3
"""
Rolling fit and spectral analysis of LUFT CME Heartbeat Log.

- Reads: data/cme_heartbeat_log_2025_12.csv (tab-separated)
- Computes dynamic pressure P_dyn.
- Performs rolling linear fits of chi_amplitude vs P_dyn_nPa.
- Computes Lomb-Scargle spectrum of chi(t).
- Outputs plots:
  - results/rolling_slope_2025_12.png
  - results/chi_spectrum_2025_12.png
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

try:
    from astropy.timeseries import LombScargle
except ImportError:
    LombScargle = None
    print("Warning: astropy not installed, spectrum plot will be skipped.")

DATA_PATH = Path("data") / "cme_heartbeat_log_2025_12.csv"
OUT_PATH = Path("results")
OUT_PATH.mkdir(exist_ok=True, parents=True)


def compute_dynamic_pressure(df: pd.DataFrame) -> pd.Series:
    """
    Compute dynamic pressure P_dyn in nPa from density (p/cm^3) and speed (km/s).

    P_dyn [nPa] = 1.6726e-6 * n * v^2
    """
    return 1.6726e-6 * df["density_p_cm3"] * (df["speed_km_s"] ** 2)


def rolling_fit_chi_vs_pdyn(df: pd.DataFrame, window: int = 12):
    """
    Perform a rolling linear fit of chi_amplitude vs P_dyn_nPa.

    window: number of points per window (≈ hour if cadence ~1h)
    Returns:
      times: list of window-end timestamps
      slopes: list of fitted slopes (Δχ / P_dyn)
    """
    slopes = []
    times = []
    for i in range(len(df) - window + 1):
        sub = df.iloc[i : i + window]
        x = sub["P_dyn_nPa"].values
        y = sub["chi_amplitude"].values
        # Require some variation in x to avoid singular fit
        if np.allclose(x, x[0]):
            continue
        m, b = np.polyfit(x, y, 1)
        slopes.append(m)
        times.append(sub["timestamp_utc"].iloc[-1])
    return times, slopes


def plot_rolling_slope(times, slopes, out_path: Path):
    plt.figure(figsize=(10, 4))
    plt.plot(times, slopes, marker="o", linestyle="-", label="rolling slope")
    # Canonical boundary recoil law slope
    plt.axhline(0.0032, color="orange", linestyle="--", label="canonical slope 0.0032")
    plt.ylabel("Slope (Δχ / P_dyn)")
    plt.title("Rolling fit of χ vs P_dyn (2025-12)")
    plt.legend()
    plt.tight_layout()
    plt.gcf().autofmt_xdate()
    plt.savefig(out_path, dpi=200)
    print(f"Saved rolling slope plot to {out_path.resolve()}")


def plot_chi_spectrum(df: pd.DataFrame, out_path: Path):
    if LombScargle is None:
        print("astropy not available, skipping spectrum plot.")
        return

    # Time in hours from first sample
    t_hours = (df["timestamp_utc"] - df["timestamp_utc"].min()).dt.total_seconds() / 3600.0
    y = df["chi_amplitude"].values

    ls = LombScargle(t_hours, y)
    freq, power = ls.autopower()  # freq in 1/hour

    plt.figure(figsize=(10, 4))
    plt.plot(freq, power, label="Lomb-Scargle power")
    # Mark the 2.4 h heartbeat
    heartbeat_freq = 1.0 / 2.4
    plt.axvline(heartbeat_freq, color="red", linestyle="--", label="2.4 h heartbeat")
    plt.xlabel("Frequency (1/h)")
    plt.ylabel("Power")
    plt.title("Spectrum of χ(t) (2025-12)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    print(f"Saved χ spectrum plot to {out_path.resolve()}")


def main():
    df = pd.read_csv(DATA_PATH, sep="\t")
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"])
    df = df.sort_values("timestamp_utc")

    df["P_dyn_nPa"] = compute_dynamic_pressure(df)

    # Rolling fit
    times, slopes = rolling_fit_chi_vs_pdyn(df, window=12)
    plot_rolling_slope(times, slopes, OUT_PATH / "rolling_slope_2025_12.png")

    # Spectrum
    plot_chi_spectrum(df, OUT_PATH / "chi_spectrum_2025_12.png")


if __name__ == "__main__":
    main()
