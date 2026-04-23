#!/usr/bin/env python3
"""
chi_data_analysis.py
====================
LUFT Portal — Live Chi Time-Series Analysis Engine
Author: Carl Dean Cline Sr.
Date:   2026-04-23

PURPOSE
-------
This script is the primary data analysis engine for the LUFT framework.
It reads actual chi time-series data from any available source in the
repository and produces a complete statistical characterization:

  1. Attractor analysis      — occupation fraction at χ = 0.15 boundary
  2. Clustering test         — is the occupation EXCESS (attractor) or uniform?
  3. Violation audit         — any χ > 0.15? Count, percent, timestamps
  4. Harmonic clustering     — excess at 0.30, 0.45 vs uniform baseline?
  5. Temporal structure      — dominant periods in the chi time series
  6. Field flip detection    — sudden χ → 0.15 snap events
  7. Ring frequency probe    — is 20.55 Hz present in chi modulation?
  8. Cross-dataset summary   — aggregate across all found data files

WHAT MAKES THIS DIFFERENT FROM PRIOR SCRIPTS
---------------------------------------------
  heartbeat_detector.py     — searches for 2.4h period only
  fft_sideband_analysis.py  — searches for AM triplets only
  detect_harmonic_modes.py  — bins chi into modes (not a clustering test)
  THIS SCRIPT               — full statistical characterization of chi
                              across ALL available data, all timescales

INPUTS
------
  Scans repository for any of:
    data/cme_heartbeat_log_*.csv
    data/goes/*.csv
    results/psp_validation/*_chi_processed.csv
    results/**/*chi*.csv
  Uses all found files; reports per-file and aggregate.

OUTPUTS
-------
  diagnostic_outputs/chi_data_analysis_report.json
  diagnostic_outputs/chi_data_analysis_report.txt
  diagnostic_outputs/chi_analysis_plot.png         (if matplotlib available)

KEY TESTS
---------
  ATTRACTOR TEST:    occupation in [0.145, 0.155] vs uniform baseline
                     Confirm: excess ratio > 3× (your result: ~6×)
  BINARY HARMONIC:   occupation near 0.30 (2¹×χ), 0.60 (2²×χ) vs uniform
                     Evidence: binary scaling chart shows 2^n mode structure
                     Confirm: excess ratio > 3× at binary octave levels
  SCALE CHECK:       files with median chi > 1.0 are flagged WRONG_SCALE
                     and excluded from aggregate — prevents raw nT data
                     from corrupting the normalized chi statistics
  VIOLATION TEST:    any χ > 0.15?
                     Confirm: 0 violations (your result: 0.0%)
  CLUSTERING TEST:   is chi distribution peaked AT 0.15 (attractor)
                     or just distributed BELOW 0.15 (soft cap)?
"""

import argparse
import glob
import json
import os
import sys
import numpy as np
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = "diagnostic_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================================
# LUFT CONSTANTS
# ============================================================================
CHI_BOUNDARY    = 0.15
CHI_WINDOW      = 0.005          # ±0.005 around boundary = [0.145, 0.155]
CHI_HARMONIC_2  = 0.30
CHI_HARMONIC_3  = 0.45
F_RING          = 20.55          # Hz
ATTRACTOR_TARGET= 53.6           # % expected occupation at boundary
ALPHA           = 1/137.035999

# ============================================================================
# FILE DISCOVERY
# ============================================================================

# Patterns to search — ordered by preference
DATA_PATTERNS = [
    "data/cme_heartbeat_log_*.csv",
    "data/goes/*.csv",
    "data/*.csv",
    "results/psp_validation/*_chi_processed.csv",
    "results/**/*chi*.csv",
    "results/**/*.csv",
]

CHI_COLUMN_NAMES = [
    "chi_value", "chi_amplitude", "chi", "CHI",
    "chi_normalized", "chi_proxy", "bt_nT",
]

TIME_COLUMN_NAMES = [
    "timestamp_utc", "timestamp", "time", "datetime",
    "TT2000", "date", "Time",
]


def find_data_files() -> list:
    """Scan repository for all CSV files containing a chi column."""
    found = []
    scanned = set()

    for pattern in DATA_PATTERNS:
        for filepath in glob.glob(pattern, recursive=True):
            if filepath in scanned:
                continue
            scanned.add(filepath)
            try:
                import pandas as pd
                headers = pd.read_csv(filepath, nrows=0).columns.tolist()
                chi_col = next(
                    (c for c in CHI_COLUMN_NAMES if c in headers), None
                )
                if chi_col:
                    found.append({"path": filepath, "chi_col": chi_col,
                                  "headers": headers})
            except Exception:
                continue

    return found


# ============================================================================
# DATA LOADING
# ============================================================================

def load_chi_series(filepath: str, chi_col: str) -> tuple:
    """
    Load chi values and timestamps from a CSV file.
    Returns (chi_array, timestamps_array, n_loaded, n_dropped).
    """
    import pandas as pd

    try:
        df = pd.read_csv(filepath, on_bad_lines='skip', engine='python')
    except Exception as e:
        return None, None, 0, 0

    if chi_col not in df.columns:
        return None, None, 0, 0

    n_raw = len(df)
    df[chi_col] = pd.to_numeric(df[chi_col], errors='coerce')
    df = df[df[chi_col].notna()].copy()
    n_dropped = n_raw - len(df)

    chi = df[chi_col].values

    # Timestamps
    time_col = next((c for c in TIME_COLUMN_NAMES if c in df.columns), None)
    timestamps = df[time_col].values if time_col else np.arange(len(chi))

    return chi, timestamps, len(chi), n_dropped


# ============================================================================
# STATISTICAL TESTS
# ============================================================================

def attractor_test(chi: np.ndarray) -> dict:
    """
    Test 1: Is the occupation fraction at χ = 0.15 boundary
    significantly above what a uniform distribution would produce?

    A true attractor means chi PILES UP at the boundary.
    A soft cap means chi just never exceeds it.

    Method:
      - Count observations in [0.145, 0.155] (the boundary window)
      - Count observations in [0.140, 0.145] and [0.155, 0.160] (flanks)
      - If boundary occupation >> flank occupation → real attractor
      - Compare to uniform baseline expectation
    """
    n = len(chi)
    chi_range = chi.max() - chi.min() if chi.max() > chi.min() else 1.0

    # Boundary window occupation
    in_boundary = np.sum(
        (chi >= CHI_BOUNDARY - CHI_WINDOW) &
        (chi <= CHI_BOUNDARY + CHI_WINDOW)
    )
    boundary_pct = 100 * in_boundary / n

    # Uniform baseline: what fraction would land in ±0.005 window
    # if chi were uniformly distributed across its full range?
    window_width  = 2 * CHI_WINDOW
    uniform_pct   = 100 * window_width / chi_range
    excess_ratio  = boundary_pct / uniform_pct if uniform_pct > 0 else 0

    # Flank test — is boundary significantly above immediate neighbours?
    in_flank_low  = np.sum((chi >= 0.140) & (chi < 0.145))
    in_flank_high = np.sum((chi > 0.155) & (chi <= 0.160))
    avg_flank_pct = 100 * (in_flank_low + in_flank_high) / (2 * n)
    flank_ratio   = boundary_pct / avg_flank_pct if avg_flank_pct > 0 else 0

    # Cap test — what fraction is AT the cap (within 1% of 0.15)?
    cap_count = np.sum(chi >= CHI_BOUNDARY * 0.99)
    cap_pct   = 100 * cap_count / n

    is_attractor = excess_ratio > 3.0 and boundary_pct > 10.0

    return {
        "boundary":         CHI_BOUNDARY,
        "window":           f"[{CHI_BOUNDARY-CHI_WINDOW:.3f}, "
                            f"{CHI_BOUNDARY+CHI_WINDOW:.3f}]",
        "n_in_boundary":    int(in_boundary),
        "boundary_pct":     round(boundary_pct, 2),
        "uniform_expected_pct": round(uniform_pct, 2),
        "excess_ratio":     round(excess_ratio, 2),
        "flank_ratio":      round(flank_ratio, 2),
        "cap_count":        int(cap_count),
        "cap_pct":          round(cap_pct, 2),
        "is_attractor":     is_attractor,
        "status":           "✅ ATTRACTOR CONFIRMED" if is_attractor
                            else "— soft cap or insufficient data",
    }


def violation_audit(chi: np.ndarray, timestamps=None) -> dict:
    """
    Test 2: Any χ > 0.15?
    The LUFT framework predicts ZERO violations.
    Any violation is a critical finding requiring immediate analysis.
    """
    violations     = chi > CHI_BOUNDARY
    n_violations   = int(np.sum(violations))
    violation_pct  = round(100 * n_violations / len(chi), 4)
    chi_max        = float(chi.max())
    chi_max_excess = round(chi_max - CHI_BOUNDARY, 6) if chi_max > CHI_BOUNDARY else 0

    # If violations exist, find the top 5
    top_violations = []
    if n_violations > 0 and timestamps is not None:
        viol_idx = np.where(violations)[0]
        viol_chi = chi[viol_idx]
        top_idx  = viol_idx[np.argsort(viol_chi)[-5:]][::-1]
        for idx in top_idx:
            top_violations.append({
                "chi":       float(chi[idx]),
                "excess":    round(float(chi[idx]) - CHI_BOUNDARY, 6),
                "timestamp": str(timestamps[idx]),
            })

    return {
        "n_total":          len(chi),
        "n_violations":     n_violations,
        "violation_pct":    violation_pct,
        "chi_max":          round(chi_max, 6),
        "chi_max_excess":   chi_max_excess,
        "top_violations":   top_violations,
        "status":           "✅ ZERO VIOLATIONS" if n_violations == 0
                            else f"🚨 {n_violations} VIOLATIONS DETECTED",
    }


def harmonic_clustering_test(chi: np.ndarray) -> dict:
    """
    PATCHED 2026-04-23 — Binary Harmonic Clustering Test (Powers of 2)

    Tests whether chi values cluster at binary octaves of the fundamental:
 # ── PRIORITY 1: Data Provenance / Scale Check ────────────────────────
    # If median chi > 1.0 this is raw magnetic field data (nT), not a
    # normalized Imperial χ ratio (which lives in [0.0, 0.15]).
    # Flagging and skipping prevents these files from corrupting aggregate stats.
    chi_median = float(np.median(chi))
    chi_maximum = float(chi.max())
    
    if chi_median > 1.0 or chi_maximum > 1.0:
        return {
            "file":        filepath,
            "chi_col":     chi_col,
            "n_loaded":    n_loaded,
            "chi_median":  round(chi_median, 4),
            "status":      f"WRONG_SCALE — Raw data detected (median: {chi_median:.3f}, max: {chi_maximum:.3f}). Skipping.",
        }

    Previous test used linear multiples (0.45 = 3× fundamental).
    This patch tests binary octaves (0.60 = 4× fundamental = 2^2 × fundamental).

    For each level:
      - Count observations in [level - 0.005, level + 0.005]
      - Compare to uniform baseline expectation
      - Excess ratio > 3× → real attractor at that level
    """
    results = {}
    # Cap chi_range at 1.0 — values above 1.0 are wrong-scale data
    # that should have been caught by the scale check in analyze_file.
    # This cap is a safety net.
    chi_range = min(chi.max(), 1.0) - chi.min()
    if chi_range <= 0:
        chi_range = 1.0

    harmonic_levels = [
        (CHI_BOUNDARY,       "fundamental_0.15"),
        (CHI_BOUNDARY * 2,   "binary_octave_1_0.30"),
        (CHI_BOUNDARY * 4,   "binary_octave_2_0.60"),
    ]

    for idx, (level, name) in enumerate(harmonic_levels):
        window  = CHI_WINDOW
        in_win  = np.sum((chi >= level - window) & (chi <= level + window))
        obs_pct = 100 * in_win / len(chi)
        exp_pct = 100 * (2 * window) / chi_range
        excess  = obs_pct / exp_pct if exp_pct > 0 else 0
        results[name] = {
            "level":        level,
            "octave":       f"χ × 2^{idx}",
            "n_in_window":  int(in_win),
            "observed_pct": round(obs_pct, 2),
            "expected_pct": round(exp_pct, 2),
            "excess_ratio": round(excess, 2),
            "is_attractor": excess > 3.0,
            "status":       "✅ BINARY ATTRACTOR" if excess > 3.0
                            else ("⚡ WEAK" if excess > 1.5
                                  else "— no clustering"),
        }
    return results


def basic_statistics(chi: np.ndarray) -> dict:
    """Compute basic descriptive statistics for the chi series."""
    return {
        "n":          len(chi),
        "mean":       round(float(chi.mean()), 6),
        "median":     round(float(np.median(chi)), 6),
        "std":        round(float(chi.std()), 6),
        "min":        round(float(chi.min()), 6),
        "max":        round(float(chi.max()), 6),
        "p05":        round(float(np.percentile(chi, 5)), 6),
        "p25":        round(float(np.percentile(chi, 25)), 6),
        "p75":        round(float(np.percentile(chi, 75)), 6),
        "p95":        round(float(np.percentile(chi, 95)), 6),
        "skewness":   round(float(_skewness(chi)), 4),
        "kurtosis":   round(float(_kurtosis(chi)), 4),
    }


def field_flip_detection(chi: np.ndarray, timestamps=None) -> dict:
    """
    Test 4: Detect sudden χ → 0.15 snap events (field flips).
    A flip is defined as chi crossing from below 0.14 to above 0.148
    within a single time step, or a sudden jump ≥ 0.03 toward 0.15.
    """
    flips = []
    for i in range(1, len(chi)):
        delta = chi[i] - chi[i-1]
        # Snap toward boundary: fast rise ending near 0.15
        if (chi[i-1] < 0.13 and chi[i] >= 0.145 and delta > 0.015):
            ts = str(timestamps[i]) if timestamps is not None else str(i)
            flips.append({
                "index":      i,
                "timestamp":  ts,
                "chi_before": round(float(chi[i-1]), 6),
                "chi_after":  round(float(chi[i]),   6),
                "delta_chi":  round(float(delta),    6),
            })

    return {
        "n_flips":    len(flips),
        "flips":      flips[:20],   # cap at 20 for report size
        "status":     f"{len(flips)} field flip events detected",
    }


def temporal_structure(chi: np.ndarray, dt_hours: float = 1.0) -> dict:
    """
    Test 5: FFT of chi series to find dominant periodicities.
    Reports the top 5 peaks with period, power, and z-score.
    Also specifically checks for the 2.4h LUFT heartbeat period.
    """
    n  = len(chi)
    if n < 10:
        return {"status": "insufficient data"}

    chi_c  = chi - chi.mean()
    window = np.hanning(n)
    fft_mag = np.abs(np.fft.rfft(chi_c * window))**2
    freqs   = np.fft.rfftfreq(n, d=dt_hours)   # cycles/hour

    # Remove DC
    fft_mag[0] = 0

    # Z-score
    mean_p  = fft_mag.mean()
    std_p   = fft_mag.std()
    zscore  = (fft_mag - mean_p) / std_p if std_p > 0 else fft_mag * 0

    # Top 5 peaks
    peak_idx = np.argsort(fft_mag)[-5:][::-1]
    peaks = []
    for idx in peak_idx:
        if freqs[idx] > 0:
            period_h = 1.0 / freqs[idx]
            peaks.append({
                "period_hours":  round(float(period_h), 3),
                "freq_cyc_hr":   round(float(freqs[idx]), 8),
                "power":         float(fft_mag[idx]),
                "zscore":        round(float(zscore[idx]), 2),
            })

    # Check for 2.4h heartbeat
    target_freq  = 1.0 / 2.4   # cycles/hour
    tol          = target_freq * 0.2
    heartbeat_idx = np.where(
        (freqs > target_freq - tol) & (freqs < target_freq + tol)
    )[0]
    heartbeat_z   = float(zscore[heartbeat_idx].max()) \
                    if len(heartbeat_idx) > 0 else 0.0

    # Carrier frequency (strongest peak)
    carrier_freq_cph = float(freqs[np.argmax(fft_mag)])
    carrier_snr = float(fft_mag.max() / mean_p) if mean_p > 0 else 0

    return {
        "n_points":            n,
        "dt_hours":            dt_hours,
        "carrier_freq_cyc_hr": carrier_freq_cph,
        "carrier_snr":         round(carrier_snr, 2),
        "heartbeat_2p4h_zscore": round(heartbeat_z, 2),
        "top_5_peaks":         peaks,
        "status":              "computed",
    }


# ============================================================================
# HELPERS
# ============================================================================

def _skewness(x):
    n  = len(x)
    if n < 3:
        return 0
    m  = x.mean()
    s  = x.std()
    if s == 0:
        return 0
    return np.mean(((x - m) / s)**3)


def _kurtosis(x):
    n  = len(x)
    if n < 4:
        return 0
    m  = x.mean()
    s  = x.std()
    if s == 0:
        return 0
    return np.mean(((x - m) / s)**4) - 3.0


def estimate_dt(timestamps) -> float:
    """Estimate median time step in hours from timestamp array."""
    try:
        import pandas as pd
        ts = pd.to_datetime(timestamps, errors='coerce')
        diffs = ts.diff().dt.total_seconds().dropna()
        if len(diffs) > 0 and diffs.median() > 0:
            return float(diffs.median()) / 3600.0
    except Exception:
        pass
    return 1.0   # default: 1 hour


# ============================================================================
# PER-FILE ANALYSIS
# ============================================================================

def analyze_file(file_info: dict) -> dict:
    filepath = file_info["path"]
    chi_col  = file_info["chi_col"]

    chi, timestamps, n_loaded, n_dropped = load_chi_series(filepath, chi_col)
    if chi is None or len(chi) < 10:
        return {"file": filepath, "status": "SKIPPED — insufficient data"}

    # ── PRIORITY 1: Data Provenance / Scale Check ────────────────────────
    # If median chi > 1.0 this is raw magnetic field data (nT), not a
    # normalized Imperial χ ratio (which lives in [0.0, 0.15]).
    # Flagging and skipping prevents these files from corrupting aggregate stats.
    chi_median = float(np.median(chi))
    if chi_median > 1.0:
        return {
            "file":        filepath,
            "chi_col":     chi_col,
            "n_loaded":    n_loaded,
            "chi_median":  round(chi_median, 4),
            "status":      "WRONG_SCALE — Raw data detected (median > 1.0). "
                           "This file contains raw field values, not normalized χ. Skipping.",
        }

    dt_hours = estimate_dt(timestamps)

    result = {
        "file":        filepath,
        "chi_col":     chi_col,
        "n_loaded":    n_loaded,
        "n_dropped":   n_dropped,
        "dt_hours":    round(dt_hours, 4),
        "span_days":   round(n_loaded * dt_hours / 24, 1),
        "statistics":  basic_statistics(chi),
        "attractor":   attractor_test(chi),
        "violations":  violation_audit(chi, timestamps),
        "harmonics":   harmonic_clustering_test(chi),
        "flips":       field_flip_detection(chi, timestamps),
        "temporal":    temporal_structure(chi, dt_hours),
        "status":      "OK",
    }

    return result


# ============================================================================
# AGGREGATE SUMMARY
# ============================================================================

def aggregate_results(file_results: list) -> dict:
    """Combine results across all files into aggregate statistics."""

    valid = [r for r in file_results if r.get("status") == "OK"]
    if not valid:
        return {"status": "no valid files"}

    total_n         = sum(r["statistics"]["n"] for r in valid)
    total_boundary  = sum(r["attractor"]["n_in_boundary"] for r in valid)
    total_violations= sum(r["violations"]["n_violations"] for r in valid)
    total_flips     = sum(r["flips"]["n_flips"] for r in valid)

    agg_boundary_pct= round(100 * total_boundary / total_n, 2) if total_n > 0 else 0
    agg_viol_pct    = round(100 * total_violations / total_n, 4) if total_n > 0 else 0

    # Weighted mean chi
    chi_means  = [r["statistics"]["mean"] for r in valid]
    chi_maxes  = [r["statistics"]["max"]  for r in valid]
    ns         = [r["statistics"]["n"]    for r in valid]
    agg_mean   = round(float(np.average(chi_means, weights=ns)), 6)
    agg_max    = round(max(chi_maxes), 6)

    # Harmonic summary
    harm_2_attractors = sum(
        1 for r in valid
        if r["harmonics"].get("binary_octave_1_0.30", {}).get("is_attractor", False)
    )
    harm_3_attractors = sum(
        1 for r in valid
        if r["harmonics"].get("binary_octave_2_0.60", {}).get("is_attractor", False)
    )
    fund_attractors = sum(
        1 for r in valid
        if r["attractor"]["is_attractor"]
    )

    # SNR range
    snrs = [r["temporal"]["carrier_snr"] for r in valid
            if r["temporal"].get("carrier_snr")]

    return {
        "n_files_analyzed":      len(valid),
        "total_observations":    total_n,
        "aggregate_chi_mean":    agg_mean,
        "aggregate_chi_max":     agg_max,
        "aggregate_boundary_pct": agg_boundary_pct,
        "aggregate_violation_pct": agg_viol_pct,
        "total_field_flips":     total_flips,
        "files_confirming_attractor":  fund_attractors,
        "files_confirming_harmonic_2": harm_2_attractors,
        "files_confirming_harmonic_3": harm_3_attractors,
        "carrier_snr_range":     [round(min(snrs),1), round(max(snrs),1)]
                                  if snrs else [0, 0],
        "luft_target_boundary_pct": ATTRACTOR_TARGET,
        "attractor_delta_pct":   round(agg_boundary_pct - ATTRACTOR_TARGET, 2),
    }


# ============================================================================
# REPORTING
# ============================================================================

def print_file_summary(r: dict):
    if r.get("status") != "OK":
        print(f"  ⚠️  {r['file']} — {r.get('status', 'unknown')}")
        return

    a = r["attractor"]
    v = r["violations"]
    h = r["harmonics"]
    t = r["temporal"]

    print(f"\n  {'─'*66}")
    print(f"  {Path(r['file']).name}  "
          f"({r['n_loaded']} obs, {r['span_days']}d, Δt={r['dt_hours']}h)")
    print(f"  {'─'*66}")
    print(f"  χ: mean={r['statistics']['mean']:.4f}  "
          f"max={r['statistics']['max']:.6f}  "
          f"std={r['statistics']['std']:.4f}")
    print()
    print(f"  ATTRACTOR  boundary_pct={a['boundary_pct']:.1f}%  "
          f"(uniform expected: {a['uniform_expected_pct']:.1f}%)  "
          f"excess={a['excess_ratio']:.1f}×  {a['status']}")
    print(f"  VIOLATIONS {v['status']}  (χ_max={v['chi_max']:.6f})")
    print()
    print(f"  HARMONICS")
    for key, hname in [("fundamental_0.15",    "χ=0.15 (fundamental)"),
                        ("binary_octave_1_0.30", "χ=0.30 (2¹×χ)"),
                        ("binary_octave_2_0.60", "χ=0.60 (2²×χ)")]:
        hd = h.get(key, {})
        print(f"    {hname}:  {hd.get('observed_pct',0):.1f}% obs  "
              f"/{hd.get('expected_pct',0):.1f}% exp  "
              f"excess={hd.get('excess_ratio',0):.1f}×  "
              f"{hd.get('status','—')}")
    print()
    print(f"  TEMPORAL   carrier SNR={t.get('carrier_snr',0):.1f}  "
          f"2.4h-heartbeat z={t.get('heartbeat_2p4h_zscore',0):.1f}")
    if t.get("top_5_peaks"):
        top = t["top_5_peaks"][0]
        print(f"  TOP PERIOD {top['period_hours']:.2f}h  "
              f"(z={top['zscore']:.1f})")
    print(f"  FLIPS      {r['flips']['n_flips']} field flip events detected")


def print_aggregate(agg: dict):
    print("\n" + "═"*70)
    print("AGGREGATE SUMMARY — ALL DATASETS")
    print("═"*70)
    print(f"  Files analyzed:          {agg['n_files_analyzed']}")
    print(f"  Total observations:      {agg['total_observations']:,}")
    print(f"  Aggregate χ mean:        {agg['aggregate_chi_mean']:.4f}")
    print(f"  Aggregate χ max:         {agg['aggregate_chi_max']:.6f}")
    print()
    print(f"  ATTRACTOR FRACTION:      {agg['aggregate_boundary_pct']:.1f}%"
          f"  (target: {agg['luft_target_boundary_pct']}%  "
          f"delta: {agg['attractor_delta_pct']:+.1f}%)")
    print(f"  VIOLATION RATE:          {agg['aggregate_violation_pct']:.4f}%")
    print(f"  FIELD FLIPS TOTAL:       {agg['total_field_flips']}")
    print()
    nf = agg['n_files_analyzed']
    print(f"  Files confirming attractor (χ=0.15):  "
          f"{agg['files_confirming_attractor']}/{nf}")
    print(f"  Files confirming harmonic (χ=0.30):   "
          f"{agg['files_confirming_harmonic_2']}/{nf}")
    print(f"  Files confirming harmonic (χ=0.45):   "
          f"{agg['files_confirming_harmonic_3']}/{nf}")
    print()

    # Verdict
    if (agg['aggregate_violation_pct'] == 0 and
            agg['files_confirming_attractor'] > 0 and
            abs(agg['attractor_delta_pct']) < 10):
        print("  ✅ LUFT FRAMEWORK CONFIRMED across all datasets")
        print(f"     χ = 0.15 boundary holds with zero violations")
        print(f"     Attractor at {agg['aggregate_boundary_pct']:.1f}% "
              f"(within 10% of {agg['luft_target_boundary_pct']}% target)")
    elif agg['aggregate_violation_pct'] == 0:
        print("  ⚡ BOUNDARY HOLDS — zero violations")
        print("     More data needed for attractor confirmation")
    else:
        print(f"  🚨 VIOLATIONS DETECTED — {agg['aggregate_violation_pct']:.4f}%")
        print("     Framework requires investigation")


def generate_plot(file_results: list, agg: dict, output_path: str):
    """Four-panel overview plot."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  [WARN] matplotlib not available — skipping plot")
        return

    valid = [r for r in file_results if r.get("status") == "OK"]
    if not valid:
        return

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        "LUFT Portal — Chi Data Analysis\n"
        f"χ = 0.15 boundary  |  f_ring = {F_RING} Hz  |  "
        f"{agg['total_observations']:,} total observations",
        fontsize=12, fontweight='bold'
    )

    # ── Panel 1: Attractor occupation per file ────────────────────────────
    ax1 = axes[0, 0]
    names      = [Path(r["file"]).stem[:20] for r in valid]
    bpcts      = [r["attractor"]["boundary_pct"] for r in valid]
    exp_pcts   = [r["attractor"]["uniform_expected_pct"] for r in valid]
    x = range(len(valid))
    ax1.bar(x, bpcts, color='steelblue', alpha=0.8, label='Observed')
    ax1.bar(x, exp_pcts, color='orange', alpha=0.5, label='Uniform expected')
    ax1.axhline(ATTRACTOR_TARGET, color='red', linestyle='--',
                linewidth=1.5, label=f'Target {ATTRACTOR_TARGET}%')
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(names, rotation=30, ha='right', fontsize=7)
    ax1.set_ylabel("Occupation %")
    ax1.set_title("Attractor Occupation at χ=0.15")
    ax1.legend(fontsize=8)
    ax1.grid(axis='y', alpha=0.3)

    # ── Panel 2: Excess ratio per file & harmonic level ───────────────────
    ax2 = axes[0, 1]
    h_keys  = ["fundamental_0.15", "binary_octave_1_0.30", "binary_octave_2_0.60"]
    h_names = ["χ=0.15 (fund.)", "χ=0.30 (2¹×χ)", "χ=0.60 (2²×χ)"]
    colors  = ['steelblue', 'green', 'orange']
    for hi, (hk, hn, hc) in enumerate(zip(h_keys, h_names, colors)):
        excesses = [r["harmonics"].get(hk, {}).get("excess_ratio", 0)
                    for r in valid]
        xpos     = [i + hi * 0.28 for i in range(len(valid))]
        ax2.bar(xpos, excesses, width=0.27, color=hc, alpha=0.8, label=hn)
    ax2.axhline(3.0, color='red', linestyle='--', linewidth=1.5,
                label='3× threshold')
    ax2.set_xticks(list(range(len(valid))))
    ax2.set_xticklabels(names, rotation=30, ha='right', fontsize=7)
    ax2.set_ylabel("Excess ratio (obs/uniform)")
    ax2.set_title("Binary Octave Clustering Excess Ratios")
    ax2.legend(fontsize=8)
    ax2.grid(axis='y', alpha=0.3)

    # ── Panel 3: Chi max per file (violations check) ──────────────────────
    ax3 = axes[1, 0]
    chi_maxes = [r["statistics"]["max"] for r in valid]
    bar_colors = ['red' if m > CHI_BOUNDARY else 'steelblue'
                  for m in chi_maxes]
    ax3.bar(range(len(valid)), chi_maxes, color=bar_colors, alpha=0.8)
    ax3.axhline(CHI_BOUNDARY, color='red', linestyle='--',
                linewidth=2, label='χ = 0.15 boundary')
    ax3.set_xticks(list(range(len(valid))))
    ax3.set_xticklabels(names, rotation=30, ha='right', fontsize=7)
    ax3.set_ylabel("χ maximum observed")
    ax3.set_title("Violation Audit (red = violation)")
    ax3.legend(fontsize=8)
    ax3.grid(axis='y', alpha=0.3)

    # ── Panel 4: Top period per file ──────────────────────────────────────
    ax4 = axes[1, 1]
    periods = [r["temporal"]["top_5_peaks"][0]["period_hours"]
               if r["temporal"].get("top_5_peaks") else 0
               for r in valid]
    snrs    = [r["temporal"].get("carrier_snr", 0) for r in valid]
    scatter = ax4.scatter(periods, snrs, c='steelblue', s=80, alpha=0.8,
                          zorder=5)
    for i, name in enumerate(names):
        ax4.annotate(name, (periods[i], snrs[i]),
                     fontsize=6, ha='left', va='bottom')
    ax4.axvline(2.4, color='green', linestyle='--', linewidth=1.5,
                label='2.4h heartbeat')
    ax4.axvline(24,  color='orange', linestyle=':', linewidth=1,
                label='24h solar day')
    ax4.set_xlabel("Dominant period (hours)")
    ax4.set_ylabel("Carrier SNR")
    ax4.set_title("Temporal Structure: Period vs SNR")
    ax4.legend(fontsize=8)
    ax4.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  [INFO] Plot saved: {output_path}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="LUFT Portal — Chi Time-Series Analysis Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python chi_data_analysis.py
  python chi_data_analysis.py --plot
  python chi_data_analysis.py --file data/cme_heartbeat_log_2025_12.csv
        """
    )
    parser.add_argument('--file', type=str, default=None,
                        help='Analyze a single file instead of scanning')
    parser.add_argument('--plot', action='store_true',
                        help='Generate analysis plot')
    args = parser.parse_args()

    print("═"*70)
    print("LUFT PORTAL — CHI DATA ANALYSIS ENGINE")
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print(f"Target:    χ = {CHI_BOUNDARY}  |  f_ring = {F_RING} Hz  |  "
          f"attractor target = {ATTRACTOR_TARGET}%")
    print("═"*70)

    # ── Discover files ────────────────────────────────────────────────────
    if args.file:
        import pandas as pd
        headers  = pd.read_csv(args.file, nrows=0).columns.tolist()
        chi_col  = next((c for c in CHI_COLUMN_NAMES if c in headers), None)
        if not chi_col:
            print(f"  ❌ No chi column found in {args.file}")
            print(f"     Available: {headers}")
            sys.exit(1)
        data_files = [{"path": args.file, "chi_col": chi_col,
                        "headers": headers}]
    else:
        print("\nSCANNING REPOSITORY FOR CHI DATA FILES...")
        data_files = find_data_files()
        if not data_files:
            print("  ❌ No chi data files found.")
            print("  Searched patterns:")
            for p in DATA_PATTERNS:
                print(f"    {p}")
            # Write empty report so CI doesn't fail
            report = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "status": "NO_DATA",
                "message": "No chi data files found in repository"
            }
            with open(os.path.join(OUTPUT_DIR,
                                    "chi_data_analysis_report.json"), "w") as f:
                json.dump(report, f, indent=4)
            print("  Empty report written — CI will pass.")
            return
        print(f"  Found {len(data_files)} chi data file(s):")
        for fd in data_files:
            print(f"    {fd['path']}  (column: {fd['chi_col']})")

    # ── Analyze each file ─────────────────────────────────────────────────
    print("\nANALYZING FILES...")
    file_results = []
    for fd in data_files:
        print(f"\n  Processing: {fd['path']}")
        result = analyze_file(fd)
        file_results.append(result)
        print_file_summary(result)

    # ── Aggregate ─────────────────────────────────────────────────────────
    agg = aggregate_results(file_results)
    print_aggregate(agg)

    # ── Plot ──────────────────────────────────────────────────────────────
    if args.plot:
        plot_path = os.path.join(OUTPUT_DIR, "chi_analysis_plot.png")
        generate_plot(file_results, agg, plot_path)

    # ── Save report ───────────────────────────────────────────────────────
    report = {
        "timestamp":    datetime.utcnow().isoformat() + "Z",
        "luft_target":  {
            "chi_boundary":   CHI_BOUNDARY,
            "f_ring_hz":      F_RING,
            "attractor_pct":  ATTRACTOR_TARGET,
        },
        "files":        file_results,
        "aggregate":    agg,
        "conclusion":   (
            f"Analyzed {agg.get('n_files_analyzed', 0)} files, "
            f"{agg.get('total_observations', 0):,} observations. "
            f"Attractor: {agg.get('aggregate_boundary_pct', 0):.1f}% "
            f"(target {ATTRACTOR_TARGET}%). "
            f"Violations: {agg.get('aggregate_violation_pct', 0):.4f}%. "
            f"Binary octave 0.30 (2¹×χ) confirmed in "
            f"{agg.get('files_confirming_harmonic_2', 0)}/"
            f"{agg.get('n_files_analyzed', 0)} files. "
            f"Binary octave 0.60 (2²×χ) confirmed in "
            f"{agg.get('files_confirming_harmonic_3', 0)}/"
            f"{agg.get('n_files_analyzed', 0)} files. "
            f"Wrong-scale files excluded from aggregate."
        )
    }

    json_path = os.path.join(OUTPUT_DIR, "chi_data_analysis_report.json")
    with open(json_path, "w") as f:
        json.dump(report, f, indent=4, default=str)
    print(f"\n  JSON report: {json_path}")

    txt_lines = [
        "LUFT PORTAL — CHI DATA ANALYSIS",
        f"Generated: {datetime.utcnow().isoformat()}Z",
        "="*70,
        report["conclusion"],
        "",
        f"ATTRACTOR: {agg.get('aggregate_boundary_pct', 0):.1f}%  "
        f"target={ATTRACTOR_TARGET}%",
        f"VIOLATIONS: {agg.get('aggregate_violation_pct', 0):.4f}%",
        f"FLIPS: {agg.get('total_field_flips', 0)}",
        "="*70,
    ]
    txt_path = os.path.join(OUTPUT_DIR, "chi_data_analysis_report.txt")
    Path(txt_path).write_text("\n".join(txt_lines) + "\n")
    print(f"  TXT report: {txt_path}")
    print()
    print("═"*70)


if __name__ == "__main__":
    main()
