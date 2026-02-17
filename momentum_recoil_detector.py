#!/usr/bin/env python3
"""Momentum recoil detector for LUFT plasma datasets."""

import json
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from scipy.signal import find_peaks


# Configuration constants
CHI_MAX = 0.15
DELTA_V_THRESHOLD = 1.0  # km/s
DENSITY_DROP_THRESHOLD = 0.30  # fractional drop (30%)
BASELINE_WINDOW_SECONDS = 3600  # 1-hour rolling baseline
RECOIL_DURATION_SECONDS = 60  # minimum duration for an event


def _read_table_from_json(path: str) -> pd.DataFrame:
    """Handle NOAA-style array-of-arrays JSON payloads."""
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if isinstance(payload, list) and payload and isinstance(payload[0], list):
        header, rows = payload[0], payload[1:]
        return pd.DataFrame(rows, columns=header)

    raise ValueError(f"Unrecognized JSON format for plasma data: {path}")


def _standardize_plasma_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename and coerce columns to expected schema."""
    rename_map = {
        "time_tag": "time",
        "timestamp": "time",
        "density": "n",
        "n_cm3": "n",
        "speed": "v_sw",
        "velocity": "v_sw",
        "bt": "B",
        "B_total": "B",
    }
    df = df.rename(columns=rename_map)

    if "time" not in df.columns:
        return pd.DataFrame(columns=["time", "n", "v_sw", "B"])

    df["time"] = pd.to_datetime(df["time"], errors="coerce", utc=True)
    df = df.dropna(subset=["time"]).sort_values("time").drop_duplicates(subset=["time"])

    for col in ("n", "v_sw", "B"):
        if col not in df.columns:
            df[col] = np.nan
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df[["time", "n", "v_sw", "B"]]


def load_plasma_data(
    source: str = "dscovr",
    start_date: str | None = None,
    end_date: str | None = None,
    path: str | None = None,
) -> pd.DataFrame:
    """
    Load plasma data from CSV/JSON sources and return a standardized DataFrame.

    Returns columns: time, n, v_sw, B
    """
    candidates: list[str] = []
    if path:
        candidates.append(path)

    if source == "dscovr":
        if start_date and end_date:
            candidates.append(f"data/dscovr_plasma_{start_date}_{end_date}.csv")
        candidates.append("data/dscovr/dscovr_realtime.json")
    elif source == "psp":
        if start_date and end_date:
            candidates.append(f"data/psp_sweap_{start_date}_{end_date}.csv")
    else:
        raise ValueError(f"Unknown source: {source}")

    dataset_path = next((c for c in candidates if os.path.exists(c)), None)
    if not dataset_path:
        print(
            "[momentum_recoil_detector] No plasma dataset found for source="
            f"{source}. Checked: {', '.join(candidates)}"
        )
        return pd.DataFrame(columns=["time", "n", "v_sw", "B"])

    if dataset_path.lower().endswith(".json"):
        df = _read_table_from_json(dataset_path)
    else:
        df = pd.read_csv(dataset_path)

    return _standardize_plasma_columns(df)


def _add_baselines(df: pd.DataFrame) -> pd.DataFrame:
    """Compute rolling baselines and chi metric."""
    if df.empty:
        return df

    df = df.copy().sort_values("time")
    df = df.set_index("time")

    rolling = (
        df[["B", "n", "v_sw"]]
        .rolling(f"{BASELINE_WINDOW_SECONDS}s", center=True, min_periods=1)
        .mean()
    )
    df["B_baseline"] = rolling["B"]
    df["n_baseline"] = rolling["n"]
    df["v_baseline"] = rolling["v_sw"]

    df = df.reset_index()

    def _safe_delta(series: pd.Series, baseline: pd.Series) -> pd.Series:
        denom = baseline.replace(0, np.nan)
        return (series - denom).abs() / denom

    df["delta_B"] = _safe_delta(df["B"], df["B_baseline"])
    df["delta_n"] = _safe_delta(df["n"], df["n_baseline"])
    df["delta_v"] = _safe_delta(df["v_sw"], df["v_baseline"])
    df["chi"] = df[["delta_B", "delta_n", "delta_v"]].max(axis=1, skipna=True).fillna(0)

    return df


def detect_recoil(df: pd.DataFrame) -> list[dict]:
    """Identify candidate recoil events."""
    if df.empty:
        return []

    delta_v_abs = (df["v_sw"] - df["v_baseline"]).abs().fillna(0)
    cadence = (
        df["time"]
        .diff()
        .dt.total_seconds()
        .dropna()
        .median()
    )
    if not cadence or np.isnan(cadence):
        print("[momentum_recoil_detector] Unable to infer cadence; defaulting to 60s")
        cadence = 60.0

    min_distance = max(1, int(RECOIL_DURATION_SECONDS / cadence))
    window_points = max(1, int(300 / cadence))

    peaks, properties = find_peaks(
        delta_v_abs,
        height=DELTA_V_THRESHOLD,
        distance=min_distance,
    )

    events: list[dict] = []
    for peak_idx in peaks:
        start_idx = max(0, peak_idx - window_points)
        end_idx = min(len(df), peak_idx + window_points)
        event_window = df.iloc[start_idx:end_idx]
        if event_window.empty:
            continue

        baseline_mean = event_window["n_baseline"].mean()
        if baseline_mean and not np.isnan(baseline_mean):
            density_drop = (baseline_mean - event_window["n"].min()) / baseline_mean
        else:
            density_drop = 0.0

        chi_max = float(event_window["chi"].max())
        delta_v_peak = float(delta_v_abs.iloc[peak_idx])

        if chi_max <= CHI_MAX and density_drop > DENSITY_DROP_THRESHOLD:
            classification = "Cline-candidate"
        elif chi_max > CHI_MAX:
            classification = "chi-violation"
        else:
            classification = "ambiguous"

        events.append(
            {
                "start_time": event_window["time"].iloc[0],
                "end_time": event_window["time"].iloc[-1],
                "delta_v_peak": delta_v_peak,
                "density_drop": density_drop,
                "chi_max": chi_max,
                "classification": classification,
            }
        )

    return events


def main() -> None:
    print("=== Momentum Recoil Detector ===")
    start_date = os.getenv("PLASMA_START_DATE", "2023-01-01")
    end_date = os.getenv("PLASMA_END_DATE", datetime.now(timezone.utc).date().isoformat())
    df = load_plasma_data(source="dscovr", start_date=start_date, end_date=end_date)

    if df.empty:
        print("No plasma data available. Skipping event detection.")
        return

    df = _add_baselines(df)
    events = detect_recoil(df)
    os.makedirs("results", exist_ok=True)
    output_path = "results/momentum_recoil_events.csv"
    pd.DataFrame(events).to_csv(output_path, index=False)

    print(f"Found {len(events)} candidate events")
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()
