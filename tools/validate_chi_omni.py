#!/usr/bin/env python3
"""
validate_chi_omni.py

Full χ-physics validator.

Validates and characterizes:
  - χ cap (≈ 0.15) as a hard ceiling
  - χ floor (≈ 0.004) as an elastic recoil floor
  - χ rebounds (derivative sign flip after floor contact)
  - χ locks (sustained cap contact)
  - χ modulation period (slow–fast oscillator)
  - χ vs. OMNI parameter space (pressure, beta, Mach)

Usage:
  python validate_chi_omni.py \
    --input data/extended_heartbeat_log_2025.csv \
    --output reports/chi_validation_omni_2025.md

Dependencies:
  pip install pandas numpy matplotlib
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


# ------------------------
# Configuration / thresholds
# ------------------------

CHI_COLUMN = "chi_amplitude_extended"
TIME_COLUMN = "datetime"

# Cap / floor thresholds
CHI_CAP_TARGET = 0.15
CHI_CAP_TOL = 0.001      # cap window: [0.149, 0.151]
CHI_FLOOR_TARGET = 0.004
CHI_FLOOR_TOL = 0.001    # floor window: [0.003, 0.005]

# Lock definition
MIN_CAP_LOCK_POINTS = 3  # minimum consecutive cap points to count as a cap lock

# Rebound detection
MIN_REBOUND_DELTA = 0.01   # χ must climb at least this amount after a floor touch

# Modulation period estimation
MAX_LAG_HOURS = 10         # search window for primary period


# ------------------------
# Utility functions
# ------------------------

def load_data(input_file: Path) -> pd.DataFrame:
    df = pd.read_csv(input_file, parse_dates=[TIME_COLUMN])
    if TIME_COLUMN in df.columns:
        df = df.set_index(TIME_COLUMN)
    if CHI_COLUMN not in df.columns:
        raise ValueError(f"Expected χ column '{CHI_COLUMN}' not found in input data.")

    # Restrict to valid χ
    df = df[df[CHI_COLUMN].notna()].copy()
    df.sort_index(inplace=True)
    return df


def classify_cap_floor(df: pd.DataFrame) -> pd.DataFrame:
    chi = df[CHI_COLUMN]

    df["chi_is_cap"] = (
        (chi >= CHI_CAP_TARGET - CHI_CAP_TOL) &
        (chi <= CHI_CAP_TARGET + CHI_CAP_TOL)
    )

    df["chi_is_floor"] = (
        (chi >= CHI_FLOOR_TARGET - CHI_FLOOR_TOL) &
        (chi <= CHI_FLOOR_TARGET + CHI_FLOOR_TOL)
    )

    return df


def find_runs(bool_series: pd.Series, min_length: int = 1):
    """
    Find consecutive True runs in a boolean series.
    Returns a list of (start_timestamp, end_timestamp, length) tuples.
    """
    runs = []
    in_run = False
    start_idx = None
    length = 0

    for t, val in bool_series.items():
        if val and not in_run:
            in_run = True
            start_idx = t
            length = 1
        elif val and in_run:
            length += 1
        elif not val and in_run:
            end_idx = t
            if length >= min_length:
                runs.append((start_idx, end_idx, length))
            in_run = False
            start_idx = None
            length = 0

    # Handle run at end
    if in_run and start_idx is not None:
        end_idx = bool_series.index[-1]
        if length >= min_length:
            runs.append((start_idx, end_idx, length))

    return runs


def detect_cap_locks(df: pd.DataFrame):
    cap_runs = find_runs(df["chi_is_cap"], min_length=MIN_CAP_LOCK_POINTS)
    return cap_runs


def detect_floor_touches(df: pd.DataFrame):
    floor_runs = find_runs(df["chi_is_floor"], min_length=1)
    return floor_runs


def detect_rebounds(df: pd.DataFrame, floor_runs):
    """
    For each floor run, check χ after the floor touch to see if it rebounds.
    A rebound is counted if χ increases by at least MIN_REBOUND_DELTA
    within a reasonable time window after the last floor point.
    """
    rebounds = []

    chi = df[CHI_COLUMN]

    for start_t, end_t, length in floor_runs:
        # use the last timestamp in the floor run
        floor_ts = end_t if end_t in chi.index else chi.index[chi.index.get_loc(end_t, method="pad")]
        floor_val = chi.loc[floor_ts]

        # look forward N points (e.g., up to 50 steps or full series)
        idx = chi.index.get_loc(floor_ts)
        lookahead_end = min(idx + 50, len(chi) - 1)
        future_segment = chi.iloc[idx:lookahead_end + 1]

        if len(future_segment) < 2:
            continue

        max_after = future_segment.max()
        if max_after - floor_val >= MIN_REBOUND_DELTA:
            rebound_ts = future_segment.idxmax()
            rebounds.append(
                {
                    "floor_time": floor_ts,
                    "floor_value": float(floor_val),
                    "rebound_time": rebound_ts,
                    "rebound_value": float(max_after),
                    "delta_chi": float(max_after - floor_val),
                }
            )

    return rebounds


def estimate_modulation_period(df: pd.DataFrame) -> float:
    """
    Estimate modulation period using autocorrelation of χ.
    Assumes roughly regular sampling.
    Returns period in hours (float) or np.nan if not estimable.
    """
    chi = df[CHI_COLUMN].astype(float)
    if len(chi) < 50:
        return np.nan

    # subtract mean
    chi = chi - chi.mean()

    # compute autocorrelation up to max lag index
    dt = (df.index[1] - df.index[0]).total_seconds() / 3600.0  # hours
    max_lag_idx = int(MAX_LAG_HOURS / dt)
    max_lag_idx = min(max_lag_idx, len(chi) - 2)

    if max_lag_idx <= 1:
        return np.nan

    acf = []
    for lag in range(1, max_lag_idx + 1):
        a = chi[:-lag]
        b = chi[lag:]
        num = np.sum(a * b)
        den = np.sqrt(np.sum(a * a) * np.sum(b * b))
        val = num / den if den != 0 else 0.0
        acf.append(val)

    acf = np.array(acf)
    best_lag = np.argmax(acf) + 1  # +1 because lag indices start at 1
    period_hours = best_lag * dt
    return period_hours


def compute_basic_stats(df: pd.DataFrame):
    chi = df[CHI_COLUMN]
    stats = {
        "chi_max": float(chi.max()),
        "chi_min": float(chi.min()),
        "chi_mean": float(chi.mean()),
        "n_records": int(len(chi)),
    }
    return stats


def omni_binned_stats(df: pd.DataFrame):
    # pressure
    if "Flow_pressure" in df.columns:
        df["pressure_bin"] = pd.cut(
            df["Flow_pressure"],
            bins=[0, 1, 2, 5, 100],
            labels=["<1", "1-2", "2-5", ">5"],
            include_lowest=True,
        )
        pressure_stats = df.groupby("pressure_bin")[CHI_COLUMN].agg(["max", "mean", "count"])
    else:
        pressure_stats = None

    # beta
    if "Plasma_beta" in df.columns:
        df["beta_bin"] = pd.cut(
            df["Plasma_beta"],
            bins=[0, 1, 10, 1000],
            labels=["<1", "1-10", ">10"],
            include_lowest=True,
        )
        beta_stats = df.groupby("beta_bin")[CHI_COLUMN].agg(["max", "mean", "count"])
    else:
        beta_stats = None

    # Mach
    if "Alfven_Mach" in df.columns:
        df["mach_bin"] = pd.cut(
            df["Alfven_Mach"],
            bins=[0, 5, 10, 100],
            labels=["<5", "5-10", ">10"],
            include_lowest=True,
        )
        mach_stats = df.groupby("mach_bin")[CHI_COLUMN].agg(["max", "mean", "count"])
    else:
        mach_stats = None

    return pressure_stats, beta_stats, mach_stats


def format_runs_markdown(runs, label: str):
    if not runs:
        return f"No {label} events detected.\n"

    lines = ["| Start | End | Length (points) |",
             "|-------|-----|-----------------|"]
    for start, end, length in runs:
        lines.append(f"| {start} | {end} | {length} |")
    return "\n".join(lines) + "\n"


def format_rebounds_markdown(rebounds):
    if not rebounds:
        return "No rebound events detected (no significant χ recovery after floor touches).\n"

    lines = [
        "| Floor time | Floor χ | Rebound time | Rebound χ | Δχ |",
        "|------------|---------|--------------|-----------|----|",
    ]
    for r in rebounds:
        lines.append(
            f"| {r['floor_time']} | {r['floor_value']:.4f} | "
            f"{r['rebound_time']} | {r['rebound_value']:.4f} | {r['delta_chi']:.4f} |"
        )
    return "\n".join(lines) + "\n"


def imperial_math_summary(stats, period_hours, cap_runs, floor_runs, rebounds):
    chi_max = stats["chi_max"]
    chi_min = stats["chi_min"]

    cap_ok = chi_max <= CHI_CAP_TARGET + CHI_CAP_TOL
    floor_ok = chi_min >= CHI_FLOOR_TARGET - CHI_FLOOR_TOL

    # Cap law
    cap_line = (
        f"chi <= {CHI_CAP_TARGET:.3f} [coherence {'OK' if cap_ok else 'VIOLATED'}]"
    )

    # Floor law
    floor_line = (
        f"chi >= {CHI_FLOOR_TARGET:.3f} [floor {'OK' if floor_ok else 'VIOLATED'}]"
    )

    # Oscillator / period law
    if np.isfinite(period_hours):
        osc_line = f"chi after T:{period_hours:.2f}h -> chi [oscillator OK]"
    else:
        osc_line = "chi after T:?h -> chi [oscillator UNRESOLVED]"

    # Rebound law
    if rebounds:
        rebound_line = "rebound = dchi per dt [elastic OK]"
    else:
        rebound_line = "rebound = dchi per dt [elastic UNRESOLVED]"

    # Locks
    lock_count = len(cap_runs)
    if lock_count > 0:
        lock_line = f"locks(count={lock_count}) [cap contact OK]"
    else:
        lock_line = "locks(count=0) [cap contact RARE]"

    return "\n".join([cap_line, floor_line, osc_line, rebound_line, lock_line])


def generate_report(
    df: pd.DataFrame,
    stats,
    pressure_stats,
    beta_stats,
    mach_stats,
    cap_runs,
    floor_runs,
    rebounds,
    period_hours: float,
) -> str:
    chi_max = stats["chi_max"]
    chi_min = stats["chi_min"]
    chi_mean = stats["chi_mean"]
    n_records = stats["n_records"]

    cap_ok = chi_max <= CHI_CAP_TARGET + CHI_CAP_TOL
    floor_ok = chi_min >= CHI_FLOOR_TARGET - CHI_FLOOR_TOL

    n_cap_points = int(df["chi_is_cap"].sum())
    n_floor_points = int(df["chi_is_floor"].sum())

    cap_fraction = 100.0 * n_cap_points / n_records if n_records > 0 else 0.0
    floor_fraction = 100.0 * n_floor_points / n_records if n_records > 0 else 0.0

    imperial_block = imperial_math_summary(stats, period_hours, cap_runs, floor_runs, rebounds)

    report_lines = []

    report_lines.append("# χ Physics Validation Report")
    report_lines.append("")
    report_lines.append(f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M UTC')}")
    report_lines.append("**Data Source:** Extended heartbeat log (DSCOVR + OMNIWeb merged)")
    report_lines.append(f"**Time Span:** {df.index.min()} to {df.index.max()}")
    report_lines.append(f"**Total Records:** {n_records}")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## Imperial Math Summary")
    report_lines.append("")
    report_lines.append("```")
    report_lines.append(imperial_block)
    report_lines.append("```")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## Overall χ Statistics")
    report_lines.append("")
    report_lines.append("| Metric                | Value        |")
    report_lines.append("|-----------------------|--------------|")
    report_lines.append(f"| Maximum χ             | {chi_max:.6f} |")
    report_lines.append(f"| Mean χ                | {chi_mean:.6f} |")
    report_lines.append(f"| Minimum χ             | {chi_min:.6f} |")
    report_lines.append(f"| Cap points (≈{CHI_CAP_TARGET:.3f})   | {n_cap_points} ({cap_fraction:.1f}%) |")
    report_lines.append(f"| Floor points (≈{CHI_FLOOR_TARGET:.3f}) | {n_floor_points} ({floor_fraction:.1f}%) |")
    report_lines.append("")
    report_lines.append(f"**Cap verdict:** {'✅ HOLDS' if cap_ok else '⚠️ VIOLATED'} "
                        f"(max χ = {chi_max:.6f}, cap target = {CHI_CAP_TARGET:.3f})")
    report_lines.append(f"**Floor verdict:** {'✅ HOLDS' if floor_ok else '⚠️ VIOLATED'} "
                        f"(min χ = {chi_min:.6f}, floor target = {CHI_FLOOR_TARGET:.3f})")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## Cap Locks (Sustained Cap Contact)")
    report_lines.append("")
    report_lines.append(format_runs_markdown(cap_runs, label="cap lock"))
    report_lines.append("")
    report_lines.append("## Floor Touches (Elastic Recoil Contact)")
    report_lines.append("")
    report_lines.append(format_runs_markdown(floor_runs, label="floor touch"))
    report_lines.append("")
    report_lines.append("## Rebound Events (χ Recovery After Floor)")
    report_lines.append("")
    report_lines.append(format_rebounds_markdown(rebounds))
    report_lines.append("")
    report_lines.append("## Modulation Period (Relaxation Oscillator)")
    report_lines.append("")
    if np.isfinite(period_hours):
        report_lines.append(
            f"- Estimated primary modulation period: **{period_hours:.2f} hours**"
        )
    else:
        report_lines.append("- Period could not be reliably estimated from current data.")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## χ vs. OMNI Parameters")
    report_lines.append("")
    if pressure_stats is not None:
        report_lines.append("### χ vs. Flow Pressure (nPa)")
        report_lines.append("")
        report_lines.append(pressure_stats.to_markdown())
        report_lines.append("")
    else:
        report_lines.append("- Flow pressure data not available in this dataset.")
        report_lines.append("")

    if beta_stats is not None:
        report_lines.append("### χ vs. Plasma Beta")
        report_lines.append("")
        report_lines.append(beta_stats.to_markdown())
        report_lines.append("")
    else:
        report_lines.append("- Plasma beta data not available in this dataset.")
        report_lines.append("")

    if mach_stats is not None:
        report_lines.append("### χ vs. Alfvén Mach Number")
        report_lines.append("")
        report_lines.append(mach_stats.to_markdown())
        report_lines.append("")
    else:
        report_lines.append("- Alfvén Mach data not available in this dataset.")
        report_lines.append("")

    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## Verdict")
    report_lines.append("")
    report_lines.append(f"- **χ cap law (χ ≤ {CHI_CAP_TARGET:.3f}):** "
                        f"{'✅ HOLDS' if cap_ok else '⚠️ VIOLATED (investigate outliers)'}")
    report_lines.append(f"- **χ floor law (χ ≥ {CHI_FLOOR_TARGET:.3f}):** "
                        f"{'✅ HOLDS' if floor_ok else '⚠️ VIOLATED (investigate dips)'}")
    if np.isfinite(period_hours):
        report_lines.append(f"- **χ modulation period:** ~{period_hours:.2f} hours (relaxation oscillator)")
    else:
        report_lines.append("- **χ modulation period:** unresolved from this run.")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("**Generated by:** `validate_chi_omni.py`")
    report_lines.append("**Contact:** CARLDCLINE@GMAIL.COM")
    report_lines.append("")

    return "\n".join(report_lines)


def validate_chi(input_file: Path, output_file: Path):
    df = load_data(input_file)
    print(f"[INFO] Loaded {len(df)} records with valid χ from {input_file}")

    df = classify_cap_floor(df)

    stats = compute_basic_stats(df)
    print(f"[INFO] χ stats: max={stats['chi_max']:.6f}, min={stats['chi_min']:.6f}, mean={stats['chi_mean']:.6f}")

    pressure_stats, beta_stats, mach_stats = omni_binned_stats(df)

    cap_runs = detect_cap_locks(df)
    floor_runs = detect_floor_touches(df)
    rebounds = detect_rebounds(df, floor_runs)
    period_hours = estimate_modulation_period(df)

    print(f"[INFO] Cap locks detected: {len(cap_runs)}")
    print(f"[INFO] Floor touches detected: {len(floor_runs)}")
    print(f"[INFO] Rebounds detected: {len(rebounds)}")
    if np.isfinite(period_hours):
        print(f"[INFO] Estimated modulation period: {period_hours:.2f} hours")
    else:
        print("[INFO] Modulation period unresolved.")

    report = generate_report(
        df,
        stats,
        pressure_stats,
        beta_stats,
        mach_stats,
        cap_runs,
        floor_runs,
        rebounds,
        period_hours,
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[OK] Validation report saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Validate χ physics (cap, floor, rebound, period) with OMNIWeb data")
    parser.add_argument("--input", type=Path, required=True, help="Input merged CSV")
    parser.add_argument("--output", type=Path, required=True, help="Output markdown report")
    args = parser.parse_args()

    validate_chi(args.input, args.output)


if __name__ == "__main__":
    main()
