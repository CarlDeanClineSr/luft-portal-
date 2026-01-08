#!/usr/bin/env python3
"""
CDAWeb dataset sweep for 1959–1962:
- List all datasets in range
- Attempt to fetch variables using robust heuristics
- Analyze all numeric series: baseline, normalized perturbations (phi), spectral density
- Write artifacts per dataset (CSV + PNG + JSON summary) and a master index

Usage:
  python scripts/cdasws_sweep_1959_1962.py --start 1959-01-01T00:00:00 --end 1962-12-31T23:59:59 --limit 100 --max-vars 24
"""
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from cdasws import CdasWs
try:
    from analyze_generic_timeseries import rolling_median, compute_phi, summarize, spectral_density
except ImportError as e:
    print(f"ERROR: Failed to import analyze_generic_timeseries module: {e}")
    print("Ensure analyze_generic_timeseries.py is in the same directory or in PYTHONPATH")
    raise


OUT_DIR = Path("results/cdasws_sweep")
FIG_DIR = Path("figures/cdasws_sweep")
INDEX_JSON = OUT_DIR / "index_1959_1962.json"

# Heuristic variable candidate sets for magnetic field vectors/total:
MAG_VAR_CANDIDATES: List[List[str]] = [
    ["BX_GSE", "BY_GSE", "BZ_GSE"],
    ["BX_GSM", "BY_GSM", "BZ_GSM"],
    ["BGSE_X", "BGSE_Y", "BGSE_Z"],
    ["BGSM_X", "BGSM_Y", "BGSM_Z"],
    ["B1", "B2", "B3"],
    ["MAGX", "MAGY", "MAGZ"],
    ["B_X", "B_Y", "B_Z"],
    ["BX", "BY", "BZ"],
]
MAG_TOTAL_CANDIDATES: List[str] = [
    "F", "BT", "|B|", "B_TOTAL", "B", "B_MAG", "BABS", "BTOTAL"
]
# Fallback generic variable list for probing datasets
FALLBACK_VARS: List[str] = ["F", "BX", "BY", "BZ"]


def sanitize_filename(dataset_id: str) -> str:
    """
    Sanitize dataset ID for use as a filename by replacing problematic characters.
    
    Args:
        dataset_id: Raw dataset ID from CDAWeb
    
    Returns:
        Safe filename string
    """
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    safe_id = dataset_id
    for char in invalid_chars:
        safe_id = safe_id.replace(char, '_')
    return safe_id


def discover_datasets(cdas: CdasWs, start_iso: str, end_iso: str, limit: int) -> List[Dict[str, Any]]:
    datasets = cdas.get_datasets(start_iso, end_iso)
    # Minimal schema norm
    items = []
    for ds in datasets[:limit]:
        dsid = ds.get("Id") or ds.get("DatasetID") or ""
        title = ds.get("Label") or ds.get("Name") or ""
        items.append({"id": dsid, "title": title})
    return items


def try_fetch_dataset(cdas: CdasWs, dataset_id: str, start_iso: str, end_iso: str, varlist: List[str]) -> Dict[str, Any]:
    try:
        resp = cdas.get_data(dataset_id, start_iso, end_iso, varlist)
        if not resp or "Epoch" not in resp:
            return {"ok": False, "reason": "No Epoch/empty response", "resp": {}}
        return {"ok": True, "resp": resp}
    except Exception as e:
        return {"ok": False, "reason": str(e), "resp": {}}


def detect_numeric_vars(resp: Dict[str, Any]) -> List[str]:
    numeric = []
    for k, v in resp.items():
        if k == "Epoch":
            continue
        try:
            arr = np.array(v, dtype=float)
            if arr.ndim == 1 and arr.size > 0:
                numeric.append(k)
        except Exception:
            continue
    return numeric


def analyze_dataset(dataset: Dict[str, Any], resp: Dict[str, Any], out_prefix: Path, max_vars: int):
    times = pd.to_datetime(resp["Epoch"])
    df = pd.DataFrame(index=times)

    # Assemble DataFrame with numeric columns
    numeric_vars = detect_numeric_vars(resp)
    for var in numeric_vars[:max_vars]:
        df[var] = pd.Series(resp[var], index=times)

    # Compute derived magnetic magnitude if vector available
    mag_made = False
    for triple in MAG_VAR_CANDIDATES:
        if all(v in df.columns for v in triple):
            # Use nan-safe operations for magnetic field magnitude calculation
            b1 = pd.to_numeric(df[triple[0]], errors="coerce")
            b2 = pd.to_numeric(df[triple[1]], errors="coerce")
            b3 = pd.to_numeric(df[triple[2]], errors="coerce")
            bmag = np.sqrt(b1**2 + b2**2 + b3**2)
            df["B_total_nT"] = bmag
            mag_made = True
            break

    # Add known total field if present
    if not mag_made:
        for t in MAG_TOTAL_CANDIDATES:
            if t in df.columns:
                df["B_total_nT"] = pd.to_numeric(df[t], errors="coerce")
                mag_made = True
                break

    # Analysis per column
    summaries: Dict[str, Any] = {}
    baseline_hours = 24
    for col in df.columns:
        series = pd.to_numeric(df[col], errors="coerce")
        base = rolling_median(series, baseline_hours)
        phi = compute_phi(series, base)
        summaries[col] = summarize(series, phi)

        # Save CSV per variable
        var_csv = out_prefix.with_suffix(".csv").parent / f"{out_prefix.stem}_{col}.csv"
        var_csv.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"timestamp": df.index, "value": series, "baseline": base, "phi": phi}).to_csv(var_csv, index=False)

        # Plot time series + phi
        var_png = out_prefix.with_suffix(".png").parent / f"{out_prefix.stem}_{col}.png"
        plt.figure(figsize=(12, 4))
        plt.plot(df.index, phi, linewidth=0.8, color="#1565c0")
        # Annotate known boundary band for magnetics or generic visibility
        plt.axhline(0.15, color="#c62828", linestyle="--", linewidth=1.0, label="0.15 band")
        plt.xlabel("Time (UTC)")
        plt.ylabel("Normalized perturbation (phi)")
        plt.title(f"{dataset['id']} • {col} • normalized |value - baseline| / baseline")
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        var_png.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(var_png, dpi=150)
        plt.close()

        # PSD (optional)
        freqs, psd = spectral_density(series)
        if len(freqs) > 0:
            psd_png = out_prefix.with_suffix(".png").parent / f"{out_prefix.stem}_{col}_psd.png"
            plt.figure(figsize=(12, 4))
            plt.semilogy(freqs, psd, color="#2e7d32")
            plt.xlabel("Frequency (Hz)")
            plt.ylabel("PSD")
            plt.title(f"{dataset['id']} • {col} • Welch PSD")
            plt.grid(alpha=0.3)
            plt.tight_layout()
            plt.savefig(psd_png, dpi=150)
            plt.close()

    # Write dataset summary JSON
    summary_json = out_prefix.parent / f"{out_prefix.stem}_summary.json"
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_json, "w") as f:
        json.dump({"dataset": dataset, "summaries": summaries}, f, indent=2, default=str)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True, help="ISO start (UTC)")
    ap.add_argument("--end", required=True, help="ISO end (UTC)")
    ap.add_argument("--limit", type=int, default=100, help="max datasets to process")
    ap.add_argument("--max-vars", type=int, default=24, help="max variables per dataset to analyze")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    cdas = CdasWs()
    datasets = discover_datasets(cdas, args.start, args.end, args.limit)

    index = {"range": {"start": args.start, "end": args.end}, "count": len(datasets), "items": []}

    for ds in datasets:
        dsid = ds["id"]
        title = ds["title"]
        print(f"== Dataset: {dsid} • {title}")

        # Try vectors first
        fetched = None
        for triple in MAG_VAR_CANDIDATES:
            fetched = try_fetch_dataset(cdas, dsid, args.start, args.end, triple)
            if fetched["ok"]:
                break

        # If no vector, try totals
        if not fetched or not fetched["ok"]:
            for tot in MAG_TOTAL_CANDIDATES:
                fetched = try_fetch_dataset(cdas, dsid, args.start, args.end, [tot])
                if fetched["ok"]:
                    break

        # If still no luck, try without heuristics: pick any variables CDAWeb returns for dataset info
        if not fetched or not fetched["ok"]:
            # Attempt a small grab with a common generic list to probe response
            fetched = try_fetch_dataset(cdas, dsid, args.start, args.end, FALLBACK_VARS)
            if not fetched["ok"]:
                # Final fallback: mark skipped
                print(f"[SKIP] Could not fetch usable data for {dsid}: {fetched.get('reason')}")
                index["items"].append({"id": dsid, "title": title, "status": "skipped", "reason": fetched.get("reason")})
                continue

        resp = fetched["resp"]
        # Sanitize dataset ID for filesystem: replace problematic characters
        safe_dsid = sanitize_filename(dsid)
        out_prefix = OUT_DIR / f"{safe_dsid}_1959_1962"
        try:
            analyze_dataset(ds, resp, out_prefix, args.max_vars)
            index["items"].append({"id": dsid, "title": title, "status": "analyzed"})
        except Exception as e:
            print(f"[ERROR] Analysis failed for {dsid}: {e}")
            index["items"].append({"id": dsid, "title": title, "status": "error", "error": str(e)})

    # Write master index
    with open(INDEX_JSON, "w") as f:
        json.dump(index, f, indent=2)


if __name__ == "__main__":
    main()
