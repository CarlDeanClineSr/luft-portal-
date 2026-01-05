#!/usr/bin/env python3
"""Correlate plasma and magnetic wake events with chi boundary checks."""

import os
from datetime import timedelta

import pandas as pd
from pandas.errors import EmptyDataError


CHI_CEILING = 0.15


def _load_csv_optional(path: str, parse_dates: list[str] | None = None) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        return pd.read_csv(path, parse_dates=parse_dates)
    except EmptyDataError:
        return pd.DataFrame()


def find_coincidences(
    plasma_events: pd.DataFrame,
    mag_events: pd.DataFrame,
    chi_data: pd.DataFrame,
    time_window_seconds: int = 600,
) -> pd.DataFrame:
    plasma_events = plasma_events.copy()
    mag_events = mag_events.copy()
    chi_data = chi_data.copy()

    for col in ("start_time", "end_time"):
        if col in plasma_events:
            plasma_events[col] = pd.to_datetime(plasma_events[col], utc=True, errors="coerce")

    if "time" in mag_events:
        mag_events["time"] = pd.to_datetime(mag_events["time"], utc=True, errors="coerce")
    else:
        mag_events = mag_events.assign(time=pd.to_datetime([], utc=True))

    if "time" in chi_data:
        chi_data["time"] = pd.to_datetime(chi_data["time"], utc=True, errors="coerce")
    else:
        chi_data = chi_data.assign(time=pd.to_datetime([], utc=True))

    results = []
    for _, row in plasma_events.iterrows():
        start = row["start_time"]
        end = row["end_time"]
        mag_match = mag_events[
            (mag_events["time"] >= start - timedelta(seconds=time_window_seconds))
            & (mag_events["time"] <= end + timedelta(seconds=time_window_seconds))
        ]
        chi_window = chi_data[
            (chi_data["time"] >= start) & (chi_data["time"] <= end)
        ]
        chi_max = chi_window["chi"].max() if not chi_window.empty else 0.0
        chi_violated = chi_max > CHI_CEILING

        score = 0
        if not mag_match.empty:
            score += 1
        if not chi_violated:
            score += 2
        if row.get("density_drop", 0) > 0.5:
            score += 1

        if score >= 3 and row.get("classification") == "Cline-candidate":
            classification = "High-Confidence Cline"
        elif score == 2:
            classification = "Moderate-Confidence Cline"
        elif chi_violated:
            classification = "Standard Shock/CME"
        else:
            classification = "Ambiguous"

        results.append(
            {
                "plasma_start": start,
                "plasma_end": end,
                "delta_v": row.get("delta_v_peak", 0),
                "density_drop": row.get("density_drop", 0),
                "chi_max": chi_max,
                "mag_events": len(mag_match),
                "score": score,
                "classification": classification,
            }
        )
    return pd.DataFrame(results)


def main() -> None:
    plasma = _load_csv_optional(
        "results/momentum_recoil_events.csv",
        parse_dates=["start_time", "end_time"],
    )
    mag = _load_csv_optional("results/magnetic_wake_rotations.csv", parse_dates=["time"])
    chi = _load_csv_optional("data/chi_at_boundary_timeseries.csv", parse_dates=["time"])

    if plasma.empty:
        print("No plasma events available. Skipping correlation.")
        return

    correlated = find_coincidences(plasma, mag, chi, time_window_seconds=600)
    os.makedirs("results", exist_ok=True)
    output_path = "results/cline_pack_correlated_events.csv"
    correlated.to_csv(output_path, index=False)

    print(f"Correlated {len(correlated)} plasma events")
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()
