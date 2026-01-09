#!/usr/bin/env python3
"""
CDAWeb dataset sweep for 1959–1962:
- List datasets (no time-range args for get_datasets; filter by data availability via get_data)
- Iterate monthly chunks to avoid large responses/timeouts
- For each dataset, attempt magnetic vectors/total fields; else analyze any numeric series
- Write per-chunk artifacts (CSV/PNG/JSON) and a master index

Usage:
  python scripts/cdasws_sweep_1959_1962.py --start 1959-01-01T00:00:00 --end 1962-12-31T23:59:59 --limit 100 --max-vars 24
"""
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from cdasws import CdasWs


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


def rolling_median(series: pd.Series, window_hours: int) -> pd.Series:
    """Rolling median baseline for time series."""
    return series.rolling(window=window_hours, min_periods=max(1, window_hours // 2)).median()


def compute_phi(series: pd.Series, baseline: pd.Series) -> pd.Series:
    """Compute normalized perturbation phi = |x - baseline| / baseline."""
    eps = 1e-12
    # For baseline values near zero, use epsilon to avoid division issues
    # Don't replace legitimate zeros with NaN; instead use safe division
    base_safe = baseline.where(baseline.abs() > eps, eps)
    return (series - baseline).abs() / base_safe.abs()


def spectral_density(series: pd.Series, fs_hz: float = 1.0/3600.0) -> Tuple[np.ndarray, np.ndarray]:
    """Welch PSD for evenly sampled series; default fs assumes hourly data."""
    from scipy.signal import welch
    x = series.dropna().values
    if len(x) < 256:
        return np.array([]), np.array([])
    freqs, psd = welch(x, fs=fs_hz, nperseg=min(1024, len(x)))
    return freqs, psd


def discover_datasets(cdas: CdasWs, limit: int) -> List[Dict[str, Any]]:
    """
    Get datasets from CDAWeb catalog.
    
    Note: get_datasets() takes no time-range positional args; we return
    basic catalog info and limit results.
    """
    datasets = cdas.get_datasets() or []
    items = []
    for ds in datasets[:limit]:
        dsid = ds.get("Id") or ds.get("DatasetID") or ""
        title = ds.get("Label") or ds.get("Name") or ""
        if dsid:
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
    """Detect numeric variables in the response."""
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


def month_chunks(start_iso: str, end_iso: str) -> List[Tuple[str, str]]:
    """Build inclusive monthly chunks from start to end."""
    start = pd.Timestamp(start_iso)
    end = pd.Timestamp(end_iso)
    # Include the month containing the end date by extending to the next month start
    end_month_start = end.normalize().replace(day=1)
    next_month = end_month_start + pd.offsets.MonthBegin(1)
    months = pd.date_range(start=start.normalize().replace(day=1), end=next_month, freq="MS")
    chunks = []
    for i in range(len(months) - 1):
        chunk_start = months[i]
        chunk_end = months[i+1] - pd.Timedelta(seconds=1)
        # Ensure we don't go beyond the original end date
        if chunk_end > end:
            chunk_end = end
        # Skip chunks that are entirely before the start
        if chunk_end < start:
            continue
        # Adjust chunk_start if it's before the original start
        if chunk_start < start:
            chunk_start = start
        chunks.append((chunk_start.strftime("%Y-%m-%dT%H:%M:%S"), chunk_end.strftime("%Y-%m-%dT%H:%M:%S")))
    return chunks


def analyze_chunk(dataset: Dict[str, Any], resp: Dict[str, Any], out_prefix: Path, max_vars: int, chunk_tag: str):
    """Analyze a single monthly chunk of data."""
    times = pd.to_datetime(resp["Epoch"])
    df = pd.DataFrame(index=times)

    # Assemble DataFrame with numeric columns
    numeric_vars = detect_numeric_vars(resp)
    for var in numeric_vars[:max_vars]:
        df[var] = pd.Series(resp[var], index=times)

    # Derived magnetic magnitude if vector available
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

    # Known total field
    if not mag_made:
        for t in MAG_TOTAL_CANDIDATES:
            if t in df.columns:
                df["B_total_nT"] = pd.to_numeric(df[t], errors="coerce")
                mag_made = True
                break

    # Analysis per variable
    summaries: Dict[str, Any] = {}
    baseline_hours = 24
    for col in df.columns:
        series = pd.to_numeric(df[col], errors="coerce")
        base = rolling_median(series, baseline_hours)
        phi = compute_phi(series, base)

        # Save CSV per variable
        var_csv = out_prefix.with_suffix(".csv").parent / f"{out_prefix.stem}_{chunk_tag}_{col}.csv"
        var_csv.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"timestamp": df.index, "value": series, "baseline": base, "phi": phi}).to_csv(var_csv, index=False)

        # Plot phi
        var_png = out_prefix.with_suffix(".png").parent / f"{out_prefix.stem}_{chunk_tag}_{col}.png"
        plt.figure(figsize=(12, 4))
        plt.plot(df.index, phi, linewidth=0.8, color="#1565c0")
        plt.axhline(0.15, color="#c62828", linestyle="--", linewidth=1.0, label="0.15 band")
        plt.xlabel("Time (UTC)")
        plt.ylabel("Normalized perturbation (phi)")
        plt.title(f"{dataset['id']} • {col} • {chunk_tag}")
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        var_png.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(var_png, dpi=150)
        plt.close()

        # PSD
        freqs, psd = spectral_density(series)
        if len(freqs) > 0:
            psd_png = out_prefix.with_suffix(".png").parent / f"{out_prefix.stem}_{chunk_tag}_{col}_psd.png"
            plt.figure(figsize=(12, 4))
            plt.semilogy(freqs, psd, color="#2e7d32")
            plt.xlabel("Frequency (Hz)")
            plt.ylabel("PSD")
            plt.title(f"{dataset['id']} • {col} • Welch PSD • {chunk_tag}")
            plt.grid(alpha=0.3)
            plt.tight_layout()
            plt.savefig(psd_png, dpi=150)
            plt.close()

        # Compute summary statistics safely (handle all-NaN cases)
        phi_valid = phi.dropna()
        has_valid = len(phi_valid) > 0
        summaries[col] = {
            "points": int(phi.count()),
            "phi_max": float(np.nanmax(phi_valid)) if has_valid else np.nan,
            "phi_p95": float(np.nanpercentile(phi_valid, 95)) if has_valid else np.nan,
            "phi_p99": float(np.nanpercentile(phi_valid, 99)) if has_valid else np.nan,
            "over_0p15": int((phi > 0.15).sum())
        }

    # Write chunk summary JSON
    summary_json = out_prefix.parent / f"{out_prefix.stem}_{chunk_tag}_summary.json"
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_json, "w") as f:
        json.dump({"dataset": dataset, "chunk": chunk_tag, "summaries": summaries}, f, indent=2, default=str)


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
    datasets = discover_datasets(cdas, args.limit)

    index = {"range": {"start": args.start, "end": args.end}, "count": len(datasets), "items": []}
    chunks = month_chunks(args.start, args.end)

    for ds in datasets:
        dsid = ds["id"]
        title = ds["title"]
        print(f"== Dataset: {dsid} • {title}")
        analyzed_any = False

        for chunk_start, chunk_end in chunks:
            chunk_tag = f"{chunk_start[:7]}"  # YYYY-MM
            # Try vector first
            fetched = None
            for triple in MAG_VAR_CANDIDATES:
                fetched = try_fetch_dataset(cdas, dsid, chunk_start, chunk_end, triple)
                if fetched["ok"]:
                    break
            # Try totals
            if not fetched or not fetched["ok"]:
                for tot in MAG_TOTAL_CANDIDATES:
                    fetched = try_fetch_dataset(cdas, dsid, chunk_start, chunk_end, [tot])
                    if fetched["ok"]:
                        break
            # Generic probe
            if not fetched or not fetched["ok"]:
                fetched = try_fetch_dataset(cdas, dsid, chunk_start, chunk_end, FALLBACK_VARS)
                if not fetched["ok"]:
                    continue  # no data in this chunk; move on

            resp = fetched["resp"]
            out_prefix = OUT_DIR / f"{dsid.replace('/', '_')}_1959_1962"
            try:
                analyze_chunk(ds, resp, out_prefix, args.max_vars, chunk_tag)
                analyzed_any = True
            except Exception as e:
                print(f"[ERROR] Analysis failed for {dsid} chunk {chunk_tag}: {e}")

        index["items"].append({"id": dsid, "title": title, "status": "analyzed" if analyzed_any else "skipped"})

    with open(INDEX_JSON, "w") as f:
        json.dump(index, f, indent=2)

    print(f"[DONE] Sweep index written to {INDEX_JSON}")


if __name__ == "__main__":
    main()
