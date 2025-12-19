#!/usr/bin/env python3
"""
Merge NOAA solarwind CSVs, OMNI2 parsed CSV, and DSCOVR heartbeat log
into data/extended_heartbeat_log_YYYYMMDD.csv with derived fields.
"""
import glob
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone

DATA_DIR = Path("data")
NOAA_DIR = DATA_DIR / "noaa_solarwind"
OMNI_FILE = DATA_DIR / "omni2_parsed_2025.csv"
HEARTBEAT_FILE = DATA_DIR / "cme_heartbeat_log_2025_12.csv"
OUT_DIR = DATA_DIR
OUT_DIR.mkdir(parents=True, exist_ok=True)

def read_latest_noaa():
    files = sorted(NOAA_DIR.glob("*.csv"))
    if not files:
        return pd.DataFrame()
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    return df

def load_omni():
    if OMNI_FILE.exists():
        return pd.read_csv(OMNI_FILE)
    return pd.DataFrame()

def load_heartbeat():
    if HEARTBEAT_FILE.exists():
        return pd.read_csv(HEARTBEAT_FILE)
    return pd.DataFrame()

def compute_derived(df):
    df = df.replace([999.9, 9999., 99999, 9.9999, 99.99, 999], pd.NA)
    if "time_tag" in df.columns:
        df["time_utc"] = pd.to_datetime(df["time_tag"], utc=True, errors="coerce")
    elif "datetime" in df.columns:
        df["time_utc"] = pd.to_datetime(df["datetime"], utc=True, errors="coerce")
    if {"density","speed"}.issubset(df.columns):
        Np = pd.to_numeric(df["density"], errors="coerce")
        V = pd.to_numeric(df["speed"], errors="coerce")
        df["pressure_npa"] = 2e-6 * Np * V**2
    if {"speed","bz_gsm"}.issubset(df.columns):
        df["E_mVpm"] = -pd.to_numeric(df["speed"], errors="coerce") * pd.to_numeric(df["bz_gsm"], errors="coerce") * 1e-3
    return df

def main():
    noaa = read_latest_noaa()
    omni = load_omni()
    hb = load_heartbeat()
    sources = []
    if not hb.empty:
        hb["time_utc"] = pd.to_datetime(hb["time_utc"], utc=True, errors="coerce")
        sources.append(hb)
    if not omni.empty:
        omni["time_utc"] = pd.to_datetime(omni["time_utc"], utc=True, errors="coerce")
        sources.append(omni)
    if not noaa.empty:
        if "time_tag" in noaa.columns:
            noaa["time_utc"] = pd.to_datetime(noaa["time_tag"], utc=True, errors="coerce")
        sources.append(noaa)
    if not sources:
        print("[WARN] No input data found. Exiting.")
        return
    merged = pd.DataFrame()
    for s in sources:
        if merged.empty:
            merged = s
        else:
            merged = pd.merge(merged, s, on="time_utc", how="outer", suffixes=("", "_r"))
    merged = compute_derived(merged)
    out_name = OUT_DIR / f"extended_heartbeat_log_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"
    merged.sort_values("time_utc", inplace=True)
    merged.to_csv(out_name, index=False)
    print(f"[OK] Wrote merged extended heartbeat log: {out_name}")

if __name__ == "__main__":
    main()
