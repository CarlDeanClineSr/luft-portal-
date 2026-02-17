#!/usr/bin/env python3
"""
merge_omni_heartbeat.py

Unified χ-physics merge engine for LUFT core.

Merges:
  - CME heartbeat log (DSCOVR-derived χ, density, speed, Bz)
  - OMNI2 parsed data (pressure, beta, Mach, etc.)
  - Optional NOAA solar wind CSVs (for redundancy / gap fill)

Outputs a single extended heartbeat CSV with:
  - normalized datetime index
  - merged density, speed, Bz
  - OMNI drivers (pressure, beta, Mach, etc.)
  - derived E-field, dynamic pressure (if possible)
  - χ_amplitude_extended (recomputed from merged density/speed)
  - chi_amplitude_original (if present in heartbeat)

Usage:
  python merge_omni_heartbeat.py \
    --heartbeat data/cme_heartbeat_log_2025_12.csv \
    --omni data/omni2_parsed_2025.csv \
    --output data/extended_heartbeat_log_2025.csv \
    [--noaa-dir data/noaa_solarwind]

Dependencies:
  pip install pandas numpy
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


# ------------------------
# χ computation
# ------------------------

def compute_chi_from_density_speed(density: float, speed: float) -> float:
    """
    χ amplitude using Carl's Dec 2025 formula:

      χ = min(0.15, 0.0012 * (speed - 350) * (10 / density)^0.3)

    Inputs:
      density [p/cm³]
      speed   [km/s]

    Returns:
      χ amplitude (dimensionless, capped at 0.15), or NaN if inputs invalid.
    """
    if pd.isna(density) or pd.isna(speed) or density <= 0:
        return np.nan

    modulation = (speed - 350.0) * (10.0 / density) ** 0.3
    chi_val = 0.0012 * modulation
    chi_val = max(0.0, chi_val)
    chi_val = min(0.15, chi_val)
    return chi_val


def compute_chi_row(row: pd.Series) -> float:
    return compute_chi_from_density_speed(row.get("density"), row.get("speed"))


# ------------------------
# Loaders
# ------------------------

def load_heartbeat(path: Path) -> pd.DataFrame:
    if not path.exists():
        print(f"[WARN] Heartbeat file not found: {path}")
        return pd.DataFrame()

    df = pd.read_csv(path)
    # Normalize time column to 'datetime'
    if "timestamp_utc" in df.columns:
        df["datetime"] = pd.to_datetime(df["timestamp_utc"], utc=True, errors="coerce")
    elif "time_utc" in df.columns:
        df["datetime"] = pd.to_datetime(df["time_utc"], utc=True, errors="coerce")
    else:
        raise ValueError("Heartbeat file must contain 'timestamp_utc' or 'time_utc' column.")

    df = df.dropna(subset=["datetime"]).copy()
    df.set_index("datetime", inplace=True)
    df.sort_index(inplace=True)
    return df


def load_omni(path: Path) -> pd.DataFrame:
    if not path.exists():
        print(f"[WARN] OMNI file not found: {path}")
        return pd.DataFrame()

    df = pd.read_csv(path)
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], utc=True, errors="coerce")
    elif "time_utc" in df.columns:
        df["datetime"] = pd.to_datetime(df["time_utc"], utc=True, errors="coerce")
    else:
        raise ValueError("OMNI file must contain 'datetime' or 'time_utc' column.")

    df = df.dropna(subset=["datetime"]).copy()
    df.set_index("datetime", inplace=True)
    df.sort_index(inplace=True)

    # Subset / rename to consistent names
    omni_cols = {}
    for col in df.columns:
        omni_cols[col] = col

    rename_map = {
        "Np": "density_omni",
        "V": "speed_omni",
        "Bz_GSM": "Bz_omni",
    }
    for src, dst in rename_map.items():
        if src in df.columns:
            omni_cols[src] = dst

    df = df.rename(columns=omni_cols)

    return df


def load_noaa_dir(noaa_dir: Path) -> pd.DataFrame:
    if not noaa_dir or not noaa_dir.exists():
        print(f"[INFO] NOAA dir not found or not provided: {noaa_dir}")
        return pd.DataFrame()

    files = sorted(noaa_dir.glob("*.csv"))
    if not files:
        print(f"[WARN] No NOAA CSV files found in {noaa_dir}")
        return pd.DataFrame()

    parts = []
    for f in files:
        try:
            df = pd.read_csv(f)
            parts.append(df)
        except Exception as e:
            print(f"[WARN] Failed to read NOAA file {f}: {e}")

    if not parts:
        return pd.DataFrame()

    df = pd.concat(parts, ignore_index=True)

    # Normalize time column
    if "time_tag" in df.columns:
        df["datetime"] = pd.to_datetime(df["time_tag"], utc=True, errors="coerce")
    elif "time_utc" in df.columns:
        df["datetime"] = pd.to_datetime(df["time_utc"], utc=True, errors="coerce")
    else:
        print("[WARN] NOAA data has no 'time_tag' or 'time_utc'; skipping.")
        return pd.DataFrame()

    df = df.dropna(subset=["datetime"]).copy()
    df.set_index("datetime", inplace=True)
    df.sort_index(inplace=True)

    # Clean placeholder values
    df = df.replace([999.9, 9999., 99999, 9.9999, 99.99, 999], np.nan)

    # Normalize some expected columns
    # Typically: density, speed, bz_gsm or similar
    col_map = {}
    for col in df.columns:
        lc = col.lower()
        if "density" == lc:
            col_map[col] = "density_noaa"
        elif lc in ("speed", "v_sw", "velocity"):
            col_map[col] = "speed_noaa"
        elif lc in ("bz_gsm", "bz", "bz_sm"):
            col_map[col] = "Bz_noaa"

    df = df.rename(columns=col_map)

    return df


# ------------------------
# Lightweight helpers for tests
# ------------------------

def compute_derived(df: pd.DataFrame) -> pd.DataFrame:
    """
    Minimal derived field calculator used in tests.
    Accepts raw NOAA-style columns (time_tag, density, speed, bz_gsm)
    and returns pressure (nPa) and electric field (mV/m).
    """
    working = df.copy()
    if "bz_gsm" in working.columns:
        working = working.rename(columns={"bz_gsm": "Bz"})
    if "time_tag" in working.columns and "datetime" not in working.columns:
        working["datetime"] = pd.to_datetime(working["time_tag"], utc=True, errors="coerce")

    working["pressure_npa"] = 2e-6 * pd.to_numeric(working["density"], errors="coerce") * (
        pd.to_numeric(working["speed"], errors="coerce") ** 2
    )
    working["E_mVpm"] = -pd.to_numeric(working["speed"], errors="coerce") * pd.to_numeric(
        working["Bz"], errors="coerce"
    ) * 1e-3
    return working


def read_latest_noaa(noaa_dir: Path | None = None) -> pd.DataFrame:
    """Stub loader used by tests; delegates to load_noaa_dir when a path is given."""
    if noaa_dir is None:
        return pd.DataFrame()
    return load_noaa_dir(noaa_dir)


# ------------------------
# Derived fields
# ------------------------

def add_derived_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add derived quantities where possible:
      - Flow_pressure (if missing and density/speed available)
      - E_field (if speed, Bz available)
    Uses OMNI naming if present; otherwise computes from merged density/speed/Bz.
    """

    # Dynamic pressure (if not already present as Flow_pressure)
    if "Flow_pressure" not in df.columns:
        if {"density", "speed"}.issubset(df.columns):
            Np = pd.to_numeric(df["density"], errors="coerce")
            V = pd.to_numeric(df["speed"], errors="coerce")
            # Approx: P [nPa] = 2e-6 * Np[p/cm^3] * V[km/s]^2
            df["Flow_pressure"] = 2e-6 * Np * (V ** 2)

    # E-field (mV/m) = - V[km/s] * Bz[nT] * 1e-3
    if "E_field" not in df.columns:
        if "speed" in df.columns and "Bz" in df.columns:
            V = pd.to_numeric(df["speed"], errors="coerce")
            Bz = pd.to_numeric(df["Bz"], errors="coerce")
            df["E_field"] = -V * Bz * 1e-3

    return df


# ------------------------
# Merge logic
# ------------------------

def merge_sources(
    hb: pd.DataFrame,
    omni: pd.DataFrame,
    noaa: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge heartbeat, OMNI, and NOAA on datetime index (outer join).
    Then perform priority gap filling for density/speed/Bz:
      1. Heartbeat
      2. OMNI
      3. NOAA
    """

    frames = []
    if not hb.empty:
        frames.append(hb)
    if not omni.empty:
        frames.append(omni)
    if not noaa.empty:
        frames.append(noaa)

    if not frames:
        raise RuntimeError("No input data sources available to merge.")

    print(f"[INFO] Merging {len(frames)} source(s) on datetime index (outer join).")

    merged = frames[0]
    for f in frames[1:]:
        merged = merged.join(f, how="outer", rsuffix="_r")

    merged.sort_index(inplace=True)

    # Build unified density/speed/Bz with priority: hb -> omni -> noaa
    # density
    density_cols = []
    for c in ["density", "density_omni", "density_noaa"]:
        if c in merged.columns:
            density_cols.append(c)
    if density_cols:
        merged["density"] = merged[density_cols[0]]
        for c in density_cols[1:]:
            merged["density"] = merged["density"].fillna(merged[c])

    # speed
    speed_cols = []
    for c in ["speed", "speed_omni", "speed_noaa"]:
        if c in merged.columns:
            speed_cols.append(c)
    if speed_cols:
        merged["speed"] = merged[speed_cols[0]]
        for c in speed_cols[1:]:
            merged["speed"] = merged["speed"].fillna(merged[c])

    # Bz
    bz_cols = []
    for c in ["Bz", "Bz_omni", "Bz_noaa"]:
        if c in merged.columns:
            bz_cols.append(c)
    if bz_cols:
        merged["Bz"] = merged[bz_cols[0]]
        for c in bz_cols[1:]:
            merged["Bz"] = merged["Bz"].fillna(merged[c])

    # Preserve original χ (if available) from heartbeat
    if "chi_amplitude" in merged.columns:
        merged["chi_amplitude_original"] = merged["chi_amplitude"]

    # Recompute extended χ from merged density/speed
    merged["chi_amplitude_extended"] = merged.apply(compute_chi_row, axis=1)

    # Add derived fields (pressure, E_field, etc.)
    merged = add_derived_fields(merged)

    print(f"[INFO] Merge complete: {merged.index.min()} to {merged.index.max()}, N={len(merged)}")
    print(f"[INFO] Records with density: {merged['density'].notna().sum()}")
    print(f"[INFO] Records with χ (extended): {merged['chi_amplitude_extended'].notna().sum()}")

    return merged


# ------------------------
# CLI
# ------------------------

def main(argv: list[str] | None = None):
    if argv is None:
        argv = []
    if not argv:
        print("[INFO] No CLI arguments provided; skipping merge execution.")
        return

    parser = argparse.ArgumentParser(
        description="Merge CME heartbeat log, OMNI2, and optional NOAA solar wind into extended χ dataset."
    )
    parser.add_argument("--heartbeat", type=Path, required=True, help="Input heartbeat CSV")
    parser.add_argument("--omni", type=Path, required=True, help="Input parsed OMNIWeb CSV")
    parser.add_argument("--output", type=Path, required=True, help="Output merged CSV")
    parser.add_argument(
        "--noaa-dir",
        type=Path,
        default=None,
        help="Optional NOAA solar wind CSV directory (e.g., data/noaa_solarwind)",
    )
    args = parser.parse_args(argv)

    hb = load_heartbeat(args.heartbeat)
    omni = load_omni(args.omni)
    noaa = load_noaa_dir(args.noaa_dir) if args.noaa_dir else pd.DataFrame()

    merged = merge_sources(hb, omni, noaa)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(args.output)
    print(f"[OK] Saved merged extended dataset to {args.output}")


if __name__ == "__main__":
    main(sys.argv[1:])
