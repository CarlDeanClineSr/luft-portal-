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
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import logging

# Local helper for rolling median + chi
from imperial_math import rolling_median, compute_chi

# Constants for chi analysis
CHI_VIOLATION_THRESHOLD = 0.15  # Upper limit for chi violations
CHI_ATTRACTOR_LOWER = 0.145     # Lower bound of attractor region
CHI_ATTRACTOR_UPPER = 0.155     # Upper bound of attractor region
OMNI_DATASET_START = datetime(1963, 1, 1, tzinfo=timezone.utc)  # OMNI hourly coverage start (CDAWeb)
# Minimal window (1 hour) to avoid zero-length CDAWeb queries while matching the hourly cadence.
MINIMAL_QUERY_WINDOW_HOURS = 1
logger = logging.getLogger(__name__)


def _extract_request_url(status_dict) -> str | None:
    """
    Best-effort extraction of the request URL from cdasws status metadata.
    Prefers status_dict['http']['url'], but falls back to legacy keys
    ('requestUrl', 'request_url') seen in some cdasws responses.
    """
    return (
        status_dict.get("http", {}).get("url")
        or status_dict.get("requestUrl")
        or status_dict.get("request_url")
    )


def _log_cdasws_status(status, request_url: str | None) -> None:
    if request_url:
        logger.warning("Failed request URL: %s", request_url)
    logger.debug("CDAWeb status payload: %s", status)


def fetch_omni_hourly_cdasws(start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
    """Fetch OMNI hourly data using CDAWeb web services (cdasws)."""
    from cdasws import CdasWs

    start_req = start_dt
    end_req = end_dt

    if end_req < OMNI_DATASET_START:
        logger.warning(
            "Requested range %s -> %s ends before OMNI hourly coverage starts (%s); "
            "shifting both bounds to the dataset start.",
            start_req.isoformat(),
            end_req.isoformat(),
            OMNI_DATASET_START.isoformat(),
        )
        # Use a minimal one-hour window to avoid zero-length queries while surfacing coverage limits.
        start_req = OMNI_DATASET_START
        end_req = OMNI_DATASET_START + timedelta(hours=MINIMAL_QUERY_WINDOW_HOURS)
        logger.warning(
            "Proceeding with adjusted range %s -> %s (dataset start clamp; returning first coverage hour).",
            start_req.isoformat(),
            end_req.isoformat(),
        )
    elif start_req < OMNI_DATASET_START:
        logger.warning(
            "Adjusting start from %s to OMNI dataset start %s to avoid 404.",
            start_req.isoformat(),
            OMNI_DATASET_START.isoformat(),
        )
        start_req = OMNI_DATASET_START
        logger.warning(
            "Proceeding with adjusted range %s -> %s.",
            start_req.isoformat(),
            end_req.isoformat(),
        )

    cdas = CdasWs()
    # Dataset name for hourly OMNI in CDAWeb
    dataset = "OMNI2_H0_MRG1HR"

    # Request all variables to get both Epoch and Epoch_1800 data
    status, data = cdas.get_data(dataset, ["ALL-VARIABLES"], start_req, end_req)
    status_code = status.get("http", {}).get("status_code")
    request_url = _extract_request_url(status)

    if status_code != 200:
        logger.warning("CDAWeb request failed; logging payload for debugging.")
        _log_cdasws_status(status, request_url)
        raise RuntimeError(
            f"CDAWeb request failed with status {status_code} "
            f"for range {start_req.isoformat()} → {end_req.isoformat()} "
            f"(url={request_url or 'unknown'})"
        )

    if data is None:
        logger.warning("CDAWeb returned no data; logging payload for debugging.")
        _log_cdasws_status(status, request_url)
        raise RuntimeError(
            "No OMNI hourly data returned for the requested range "
            f"{start_req.isoformat()} → {end_req.isoformat()} "
            f"(url={request_url or 'unknown'})"
        )

    # Convert xarray Dataset to pandas DataFrame
    # Use only variables on the Epoch coordinate (hourly data)
    # The OMNI2_H0_MRG1HR dataset has two time coordinates:
    # - Epoch: hourly data
    # - Epoch_1800: 30-minute averaged data (1800 seconds)
    hourly_vars = []
    for v in data.data_vars:
        dims = data[v].dims
        # Check if the variable is on the Epoch coordinate but NOT on Epoch_1800
        if 'Epoch' in dims and 'Epoch_1800' not in dims:
            hourly_vars.append(v)
    
    if not hourly_vars:
        raise RuntimeError("No hourly variables found on Epoch coordinate in OMNI data.")
    
    df = data[hourly_vars].to_dataframe().reset_index()
    
    return df.sort_values('Epoch').set_index('Epoch')


def run(start: str, end: str, out_csv: str, out_png: str, baseline_hours: int = 24):
    # Parse dates (ISO)
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=timezone.utc)

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
        "timestamp": b.index.tz_localize(None) if (hasattr(b.index, 'tz') and b.index.tz is not None) else b.index,
        "B_total_nT": b.values,
        "B_baseline_nT": b_baseline.values,
        "chi": chi.values
    })
    df.dropna(subset=["chi"], inplace=True)

    # Stats
    total = len(df)
    chi_max = float(np.nanmax(df["chi"].values)) if total else float("nan")
    violations = int((df["chi"] > CHI_VIOLATION_THRESHOLD).sum())
    attractor = (
        float(((df["chi"] >= CHI_ATTRACTOR_LOWER) & (df["chi"] <= CHI_ATTRACTOR_UPPER)).sum()) / total * 100.0
        if total else float("nan")
    )

    print(f"Points: {total}")
    print(f"χ_max:  {chi_max:.6f}")
    print(f"Violations (χ>{CHI_VIOLATION_THRESHOLD}): {violations}")
    print(f"Attractor occupancy ({CHI_ATTRACTOR_LOWER}–{CHI_ATTRACTOR_UPPER}): {attractor:.2f}%")

    # Save CSV
    Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)

    # Plot
    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(12, 4))
    plt.plot(df["timestamp"], df["chi"], linewidth=0.8, color="#1565c0")
    plt.axhline(CHI_VIOLATION_THRESHOLD, color="#c62828", linestyle="--", 
                linewidth=1.0, label=f"χ = {CHI_VIOLATION_THRESHOLD}")
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
