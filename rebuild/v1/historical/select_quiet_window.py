#!/usr/bin/env python3
"""Select a 30-day quiet DSCOVR interval without looking at magnetic χ.

Selection is lexicographic, not a hidden weighted score:

1. lowest kinetic transient fraction;
2. lowest 95th-percentile speed;
3. lowest 95th-percentile density;
4. lowest median dynamic pressure.

Only windows meeting the configured data-coverage gate are eligible.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def one_hour_speed_jump(frame: pd.DataFrame, tolerance_seconds: int = 120) -> pd.Series:
    source = frame[["time_tag", "speed"]].dropna().sort_values("time_tag").copy()
    prior = source.rename(
        columns={"time_tag": "prior_time", "speed": "speed_1h_prior"}
    )
    prior["target_time"] = prior["prior_time"] + pd.Timedelta(hours=1)
    joined = pd.merge_asof(
        source,
        prior.sort_values("target_time"),
        left_on="time_tag",
        right_on="target_time",
        direction="nearest",
        tolerance=pd.Timedelta(seconds=tolerance_seconds),
    )
    jump = (joined["speed"] - joined["speed_1h_prior"]).abs()
    return pd.Series(jump.values, index=source.index).reindex(frame.index)


def score_windows(
    plasma: pd.DataFrame,
    *,
    window_days: int = 30,
    stride_days: int = 1,
    minimum_coverage_fraction: float = 0.95,
    speed_high_km_s: float = 600.0,
    density_high_cm3: float = 15.0,
    speed_jump_1h_km_s: float = 50.0,
) -> pd.DataFrame:
    frame = plasma.copy()
    frame["time_tag"] = pd.to_datetime(frame["time_tag"], utc=True, errors="coerce")
    for column in ("density", "speed"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["time_tag", "density", "speed"])
    frame = frame.sort_values("time_tag").drop_duplicates("time_tag", keep="last")
    if frame.empty:
        return pd.DataFrame()

    frame["speed_jump_1h_km_s"] = one_hour_speed_jump(frame)
    frame["kinetic_transient"] = (
        (frame["speed"] > speed_high_km_s)
        | (frame["density"] > density_high_cm3)
        | (frame["speed_jump_1h_km_s"] > speed_jump_1h_km_s)
    )
    frame["dynamic_pressure_nPa"] = (
        frame["density"] * frame["speed"] ** 2 * 1.6726e-6
    )

    first = frame["time_tag"].min().floor("D")
    last_start = frame["time_tag"].max().ceil("D") - pd.Timedelta(days=window_days)
    expected = window_days * 24 * 60
    rows: list[dict[str, Any]] = []
    cursor = first
    while cursor <= last_start:
        stop = cursor + pd.Timedelta(days=window_days)
        subset = frame[(frame["time_tag"] >= cursor) & (frame["time_tag"] < stop)]
        coverage = len(subset) / expected
        if coverage >= minimum_coverage_fraction:
            rows.append(
                {
                    "start_utc": cursor.isoformat(),
                    "end_utc": stop.isoformat(),
                    "rows": int(len(subset)),
                    "coverage_fraction": float(coverage),
                    "transient_fraction": float(subset["kinetic_transient"].mean()),
                    "p95_speed_km_s": float(subset["speed"].quantile(0.95)),
                    "p95_density_cm3": float(subset["density"].quantile(0.95)),
                    "median_dynamic_pressure_nPa": float(
                        subset["dynamic_pressure_nPa"].median()
                    ),
                }
            )
        cursor += pd.Timedelta(days=stride_days)

    result = pd.DataFrame(rows)
    if result.empty:
        return result
    return result.sort_values(
        [
            "transient_fraction",
            "p95_speed_km_s",
            "p95_density_cm3",
            "median_dynamic_pressure_nPa",
            "start_utc",
        ],
        kind="stable",
    ).reset_index(drop=True)


def select_quiet_window(
    plasma_path: str | Path,
    output_dir: str | Path,
    **kwargs: Any,
) -> dict[str, Any]:
    frame = pd.read_csv(plasma_path)
    candidates = score_windows(frame, **kwargs)
    if candidates.empty:
        raise ValueError("no candidate window passed the coverage gate")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(out / "quiet_window_candidates.csv", index=False)
    selected = candidates.iloc[0].to_dict()
    payload = {
        "method": "kinetic-only lexicographic quiet-window selection",
        "chi_used_in_selection": False,
        "selected": selected,
        "candidate_count": int(len(candidates)),
        "parameters": kwargs,
    }
    (out / "quiet_window_selected.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plasma", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--window-days", type=int, default=30)
    parser.add_argument("--minimum-coverage", type=float, default=0.95)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = select_quiet_window(
        args.plasma,
        args.outdir,
        window_days=args.window_days,
        minimum_coverage_fraction=args.minimum_coverage,
    )
    print(json.dumps(payload["selected"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
