#!/usr/bin/env python3
"""Magnetic wake analyzer for USGS/GOES magnetometer data."""

import json
import os
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from scipy.fft import fft, fftfreq


CHI_MAX = 0.15
B_ROTATION_THRESHOLD_DEG = 15.0
B_COMPRESSION_THRESHOLD = 0.2
ALFVEN_FREQ_RANGE: Tuple[float, float] = (0.001, 0.1)  # Hz
ROLLING_BASELINE = "3600s"


def _load_latest_usgs(station: str = "BOU") -> pd.DataFrame:
    """Load the most recent USGS magnetometer JSON for a station."""
    base = Path("data/usgs_magnetometer") / station
    if not base.exists():
        return pd.DataFrame(columns=["time", "Bx", "By", "Bz"])

    files = sorted(base.glob("*.json"))
    if not files:
        return pd.DataFrame(columns=["time", "Bx", "By", "Bz"])

    with open(files[-1], "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    times = pd.to_datetime(payload.get("times", []), utc=True, errors="coerce")
    values = payload.get("values", [])
    component_map = {}
    for entry in values:
        component_map[entry.get("id")] = entry.get("values", [])

    Bx = pd.to_numeric(component_map.get("X", []), errors="coerce")
    By = pd.to_numeric(component_map.get("Y", []), errors="coerce")
    Bz = pd.to_numeric(component_map.get("Z", []), errors="coerce")

    df = pd.DataFrame({"time": times, "Bx": Bx, "By": By, "Bz": Bz})
    df = df.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)
    return df


def _add_baselines(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy().set_index("time")
    rolling = (
        df[["Bx", "By", "Bz"]]
        .rolling(ROLLING_BASELINE, center=True, min_periods=1)
        .mean()
    )
    df["B_total"] = np.sqrt(df["Bx"] ** 2 + df["By"] ** 2 + df["Bz"] ** 2)
    df["B_total_baseline"] = np.sqrt(
        rolling["Bx"] ** 2 + rolling["By"] ** 2 + rolling["Bz"] ** 2
    )
    df = df.reset_index()
    return df


def detect_rotations(df: pd.DataFrame, threshold_deg: float) -> list[dict]:
    if df.empty:
        return []

    df = df.copy()
    df["norm"] = np.sqrt(df["Bx"] ** 2 + df["By"] ** 2 + df["Bz"] ** 2).replace(0, np.nan)
    for axis in ("Bx", "By", "Bz"):
        df[f"{axis}_hat"] = df[axis] / df["norm"]

    events = []
    for i in range(1, len(df)):
        prev = df.iloc[i - 1]
        curr = df.iloc[i]
        dot = (
            (curr["Bx_hat"] * prev["Bx_hat"])
            + (curr["By_hat"] * prev["By_hat"])
            + (curr["Bz_hat"] * prev["Bz_hat"])
        )
        angle_deg = np.degrees(np.arccos(np.clip(dot, -1, 1)))
        delta_b = (curr["B_total"] - prev["B_total"]) / max(prev["B_total"], 1e-6)

        if angle_deg > threshold_deg and abs(delta_b) > B_COMPRESSION_THRESHOLD:
            events.append(
                {
                    "time": curr["time"],
                    "angle_deg": angle_deg,
                    "delta_b_fraction": delta_b,
                }
            )
    return events


def detect_alfven_waves(df: pd.DataFrame, freq_range: Tuple[float, float]) -> bool:
    if df.empty:
        return False
    cadence = (
        df["time"].diff().dt.total_seconds().dropna().median()
    )
    if not cadence or np.isnan(cadence) or cadence <= 0:
        print("[magnetic_wake_analyzer] Unable to infer cadence; skipping Alfvén check")
        return False

    df_idx = df.set_index("time")
    bx = df_idx["Bx"] - df_idx["Bx"].rolling(ROLLING_BASELINE, min_periods=1, center=True).mean()
    bx = bx.reset_index(drop=True).fillna(0)
    N = len(bx)
    if N < 4:
        return False

    freqs = fftfreq(N, cadence)
    fft_vals = np.abs(fft(bx))
    mask = (freqs >= freq_range[0]) & (freqs <= freq_range[1])
    if not mask.any():
        return False

    power = np.sum(fft_vals[mask] ** 2)
    median_power = np.median(fft_vals ** 2)
    return power > 2 * median_power


def main() -> None:
    print("=== Magnetic Wake Analyzer ===")
    df = _load_latest_usgs("BOU")
    df = _add_baselines(df)

    rotations = detect_rotations(df, threshold_deg=B_ROTATION_THRESHOLD_DEG)
    wave_present = detect_alfven_waves(df, freq_range=ALFVEN_FREQ_RANGE)

    os.makedirs("results", exist_ok=True)
    output_path = "results/magnetic_wake_rotations.csv"
    pd.DataFrame(rotations).to_csv(output_path, index=False)

    print(f"Found {len(rotations)} rotations > {B_ROTATION_THRESHOLD_DEG}° with compression")
    print(f"Alfvén wave activity: {'YES' if wave_present else 'NO'}")
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()
