#!/usr/bin/env python3
"""
chi_learning_loop.py

First χ learning loop for LUFT.

- Reads recent CME heartbeat data.
- Identifies χ = 0.15 locks vs non-locks.
- Computes basic correlations between χ and key solar wind drivers.
- Writes:
    - results/chi_learning_loop_YYYYMMDD.csv    (per-row features)
    - reports/chi_learning_loop_YYYYMMDD.md     (human-readable capsule)

This is *not* ingestion. It is *learning from what the engine already ingested*.
"""

from __future__ import annotations
import os
from pathlib import Path
from datetime import datetime, timedelta
import math
import pandas as pd


# --- CONFIG -----------------------------------------------------------------

HEARTBEAT_CSV = Path("data/cme_heartbeat_log_2025_12.csv")
RESULTS_DIR = Path("results")
REPORTS_DIR = Path("reports")

# how much history to use for the learning window (hours)
HOURS_BACK = 72

# χ lock threshold
CHI_LOCK_VALUE = 0.1500
CHI_LOCK_TOL = 0.0005  # treat ~0.1495–0.1505 as lock


# --- UTILITIES --------------------------------------------------------------

def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Return the first column name in df that matches any candidate."""
    lower_map = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand in df.columns:
            return cand
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None


def _safe_corr(a: pd.Series, b: pd.Series) -> float | None:
    """Return Pearson r or None if not enough valid data."""
    s = pd.concat([a, b], axis=1).dropna()
    if len(s) < 5:
        return None
    return float(s.corr().iloc[0, 1])


# --- CORE LEARNING LOOP -----------------------------------------------------

def run_chi_learning_loop() -> None:
    if not HEARTBEAT_CSV.exists():
        print(f"[chi-learning] No heartbeat CSV at {HEARTBEAT_CSV}, nothing to learn from.")
        return

    df = pd.read_csv(HEARTBEAT_CSV)

    # Try to locate columns in a tolerant way
    ts_col = _find_column(df, ["timestamp_utc", "time", "Time (UTC)", "timestamp"])
    chi_col = _find_column(df, ["chi_amplitude", "chi_amp", "χ Amp", "chi"])
    dens_col = _find_column(df, ["density_p_cm3", "density", "Density (p/cm³)"])
    spd_col = _find_column(df, ["speed_km_s", "speed", "Speed (km/s)"])
    bz_col = _find_column(df, ["bz_nT", "Bz (nT)", "bz"])

    missing = [name for name, col in [
        ("timestamp", ts_col),
        ("χ", chi_col),
        ("density", dens_col),
        ("speed", spd_col),
        ("Bz", bz_col),
    ] if col is None]

    if missing:
        print(f"[chi-learning] Missing required columns in heartbeat CSV: {missing}")
        return

    # Parse timestamps and restrict to recent window
    df[ts_col] = pd.to_datetime(df[ts_col], utc=True, errors="coerce")
    df = df.dropna(subset=[ts_col])
    df = df.sort_values(ts_col)

    if df.empty:
        print("[chi-learning] No valid rows after timestamp parsing.")
        return

    now_utc = df[ts_col].max()
    window_start = now_utc - timedelta(hours=HOURS_BACK)
    df_win = df[df[ts_col] >= window_start].copy()

    if df_win.empty:
        print(f"[chi-learning] No rows in the last {HOURS_BACK} hours.")
        return

    # Add derived flags
    df_win["is_lock"] = df_win[chi_col].apply(
        lambda x: bool(
            isinstance(x, (int, float))
            and not math.isnan(x)
            and abs(x - CHI_LOCK_VALUE) <= CHI_LOCK_TOL
        )
    )

    # Basic stats
    n_total = len(df_win)
    n_lock = int(df_win["is_lock"].sum())
    n_nolock = n_total - n_lock

    # Correlations
    chi_series = df_win[chi_col].astype(float)

    corr_density = _safe_corr(chi_series, df_win[dens_col].astype(float)) if dens_col else None
    corr_speed = _safe_corr(chi_series, df_win[spd_col].astype(float)) if spd_col else None
    corr_bz = _safe_corr(chi_series, df_win[bz_col].astype(float)) if bz_col else None

    # Per-row learning features CSV
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    date_tag = now_utc.strftime("%Y%m%d")
    out_csv = RESULTS_DIR / f"chi_learning_loop_{date_tag}.csv"
    out_md = REPORTS_DIR / f"chi_learning_loop_{date_tag}.md"

    export_cols = [ts_col, chi_col, "is_lock"]
    if dens_col:
        export_cols.append(dens_col)
    if spd_col:
        export_cols.append(spd_col)
    if bz_col:
        export_cols.append(bz_col)

    df_win[export_cols].to_csv(out_csv, index=False)

    # Markdown capsule
    lines: list[str] = []

    lines.append("# 🔍 χ Learning Loop Report")
    lines.append("")
    lines.append(f"**Generated:** {now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append(f"**Source:** `{HEARTBEAT_CSV}` (last {HOURS_BACK} hours)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 📊 Dataset Overview")
    lines.append("")
    lines.append(f"- Rows in window: `{n_total}`")
    lines.append(f"- χ lock rows (≈ {CHI_LOCK_VALUE:.3f}): `{n_lock}`")
    lines.append(f"- Non-lock rows: `{n_nolock}`")
    lines.append("")
    lines.append("Lock criterion:")
    lines.append("")
    lines.append(f"- `|χ - {CHI_LOCK_VALUE:.3f}| ≤ {CHI_LOCK_TOL:.4f}`")
    lines.append("")

    lines.append("## 🔗 Correlations (χ vs drivers)")
    lines.append("")
    def fmt_corr(name: str, val: float | None) -> str:
        if val is None:
            return f"- **{name}:** _not enough data_"
        return f"- **{name}:** `r = {val:+.3f}`"

    lines.append(fmt_corr("Density", corr_density))
    lines.append(fmt_corr("Speed", corr_speed))
    lines.append(fmt_corr("Bz", corr_bz))
    lines.append("")

    lines.append("*(Pearson r over last hours; |r| close to 1 means strong linear relation.)*")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 🧠 Notes for LUFT Students")
    lines.append("")
    lines.append("- This report is the engine **learning from its own data**, not from new feeds.")
    lines.append("- Each row in the CSV marks whether the system was in a χ lock or not.")
    lines.append("- Correlations hint at which drivers matter most for χ in this window.")
    lines.append("")
    lines.append(f"Raw features: `{out_csv}`")
    lines.append("")
    lines.append("*— χ Learning Loop v1*")

    out_md.write_text("\n".join(lines), encoding="utf-8")

    print(f"[chi-learning] Wrote {out_csv}")
    print(f"[chi-learning] Wrote {out_md}")


if __name__ == "__main__":
    run_chi_learning_loop()
