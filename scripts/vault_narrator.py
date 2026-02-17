#!/usr/bin/env python3
"""
vault_narrator.py — χ‑Physics Aligned

Generates:
  - LATEST_VAULT_STATUS.md
  - Mini‑charts (χ sparkline + solar wind)
  - NOAA summary links
  - χ streak flags
  - Uses unified dataset: data/extended_heartbeat_log_*.csv
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from pathlib import Path
from datetime import datetime, timezone
import os

# ------------------------
# Paths
# ------------------------

DATA_DIR = Path("data")
REPORTS_DIR = Path("reports")
CHARTS_DIR = REPORTS_DIR / "charts"
OUTPUT_MD = Path("LATEST_VAULT_STATUS.md")

CHARTS_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------
# Constants
# ------------------------

CHI_COL = "chi_amplitude_extended"
TIME_COL = "datetime"

CHI_CAP = 0.15
CHI_CAP_TOL = 0.001
CHI_FLOOR = 0.004
CHI_FLOOR_TOL = 0.001

# χ = 0.15 Universal Boundary Constants (discovered Dec 2025)
CHI_BOUNDARY_MIN = CHI_CAP - 0.01  # 0.145
CHI_BOUNDARY_MAX = CHI_CAP + 0.01  # 0.155

LONG_STREAK_HOURS = float(os.environ.get("VAULT_LONG_STREAK_HOURS", "48"))
SUPERSTREAK_HOURS = float(os.environ.get("VAULT_SUPERSTREAK_HOURS", "72"))

NOAA_SRS_PATH = Path("reports/latest_srs.md")
NOAA_F107_PATH = Path("reports/latest_f107.md")

# ------------------------
# Helpers
# ------------------------

def load_latest_extended():
    files = sorted(DATA_DIR.glob("extended_heartbeat_log_*.csv"))
    if not files:
        raise FileNotFoundError("No extended heartbeat logs found.")
    df = pd.read_csv(files[-1], parse_dates=[TIME_COL])
    df = df.sort_values(TIME_COL)
    return df


def analyze_chi_boundary(df):
    """
    Analyze χ values relative to the universal χ = 0.15 boundary.
    
    Returns:
        Dictionary with boundary analysis results
    """
    if CHI_COL not in df.columns:
        return None
    
    chi_values = df[CHI_COL].dropna()
    
    if len(chi_values) == 0:
        return None
    
    # Count observations in each category
    chi_at_boundary = len(chi_values[(chi_values >= CHI_BOUNDARY_MIN) & 
                                     (chi_values <= CHI_BOUNDARY_MAX)])
    chi_violations = len(chi_values[chi_values > CHI_BOUNDARY_MAX])
    
    # Compute fractions
    chi_boundary_fraction = chi_at_boundary / len(chi_values)
    chi_violation_fraction = chi_violations / len(chi_values)
    
    return {
        'total': len(chi_values),
        'at_boundary': chi_at_boundary,
        'at_boundary_pct': chi_boundary_fraction * 100,
        'violations': chi_violations,
        'violations_pct': chi_violation_fraction * 100,
        'attractor_state': chi_boundary_fraction > 0.5
    }


def detect_cap_streak(df):
    df["is_cap"] = (df[CHI_COL] >= CHI_CAP - CHI_CAP_TOL)
    if not df["is_cap"].any():
        return 0, None, None, None

    streak = 0
    last_lock_time = None
    first_lock_time = None

    for i in range(len(df) - 1, -1, -1):
        if df["is_cap"].iloc[i]:
            streak += 1
            if last_lock_time is None:
                last_lock_time = df[TIME_COL].iloc[i]
            first_lock_time = df[TIME_COL].iloc[i]
        else:
            break

    duration = last_lock_time - first_lock_time
    return streak, last_lock_time, first_lock_time, duration

def streak_flag(hours):
    if hours >= SUPERSTREAK_HOURS:
        return f"Superstreak {hours:.0f}h"
    if hours >= LONG_STREAK_HOURS:
        return f"Long streak {hours:.0f}h"
    return None

def check_noaa():
    out = {}
    for name, path in [("SRS", NOAA_SRS_PATH), ("F10.7", NOAA_F107_PATH)]:
        if path.exists():
            ts = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            out[name] = {"available": True, "path": path, "timestamp": ts}
        else:
            out[name] = {"available": False, "path": path, "timestamp": None}
    return out

# ------------------------
# Mini‑charts
# ------------------------

def make_chi_sparkline(df, streak):
    out = CHARTS_DIR / "chi_amplitude_sparkline.png"

    fig, ax = plt.subplots(figsize=(8, 2), dpi=100)
    ax.plot(df[TIME_COL], df[CHI_COL], color="#2E86AB", linewidth=1.5)
    ax.axhline(CHI_CAP, color="#A23B72", linestyle="--", linewidth=1)
    locks = df[df["is_cap"]]
    ax.scatter(locks[TIME_COL], locks[CHI_COL], color="#F18F01", s=20)

    ax.set_title(f"χ Amplitude (72h) — Streak: {streak}", fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    plt.xticks(rotation=45, ha="right")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out

def make_solarwind_miniplot(df):
    out = CHARTS_DIR / "solar_wind_miniplot.png"

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 3), dpi=100, sharex=True)

    if "speed" in df.columns:
        ax1.plot(df[TIME_COL], df["speed"], color="#06A77D")
        ax1.set_ylabel("Speed (km/s)", fontsize=8)
        ax1.grid(True, alpha=0.3)

    if "density" in df.columns:
        ax2.plot(df[TIME_COL], df["density"], color="#D62246")
        ax2.set_ylabel("Density (p/cm³)", fontsize=8)
        ax2.grid(True, alpha=0.3)

    ax2.set_xlabel("UTC", fontsize=8)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    plt.xticks(rotation=45, ha="right")

    fig.suptitle("Solar Wind (72h)", fontsize=9)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out

# ------------------------
# Markdown
# ------------------------

def write_markdown(df, streak, last_lock, first_lock, duration, noaa, chi_chart, sw_chart, chi_boundary_analysis):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    md = []
    md.append("# 🔐 VAULT STATUS REPORT\n")
    md.append(f"**Generated:** {now}  \n")
    md.append(f"**Data Source:** `extended_heartbeat_log`  \n")
    md.append("---\n")

    # Status
    status = "ACTIVE" if streak > 0 else "QUIET"
    line = f"## ⚡ CURRENT STATUS: {status}"

    if streak > 0:
        hours = duration.total_seconds() / 3600
        flag = streak_flag(hours)
        if flag:
            line += f" — {flag} @ χ=0.15"

    md.append(line + "\n\n")
    if streak > 0:
        md.append(f"**Streak Count:** {streak} readings  \n")
        md.append(f"**First Lock:** {first_lock}  \n")
        md.append(f"**Last Lock:** {last_lock}  \n")
        md.append(f"**Duration:** {duration}  \n")

    # χ = 0.15 Universal Boundary Analysis
    if chi_boundary_analysis:
        md.append("\n---\n")
        md.append("## 🔬 χ = 0.15 UNIVERSAL BOUNDARY\n\n")
        md.append(f"**Total observations (72h):** {chi_boundary_analysis['total']}  \n")
        md.append(f"**At boundary (0.145-0.155):** {chi_boundary_analysis['at_boundary']} "
                 f"({chi_boundary_analysis['at_boundary_pct']:.1f}%)  \n")
        
        if chi_boundary_analysis['violations'] > 0:
            md.append(f"**⚠️ Violations (χ > 0.155):** {chi_boundary_analysis['violations']} "
                     f"({chi_boundary_analysis['violations_pct']:.2f}%)  \n")
            md.append("**Status:** Coherence loss - investigating filamentary breakdown  \n")
        elif chi_boundary_analysis['attractor_state']:
            md.append("**✅ ATTRACTOR STATE CONFIRMED** - System spending >50% time at optimal coupling  \n")
            md.append("**Status:** Plasma locked to glow-mode maximum amplitude  \n")
        else:
            md.append("**Status:** Normal operations, system below boundary  \n")

    md.append("\n---\n")
    md.append("## 🌞 NOAA SPACE WEATHER SUMMARIES\n\n")

    for name, info in noaa.items():
        if info["available"]:
            ts = info["timestamp"].strftime("%Y-%m-%d %H:%M UTC") if info["timestamp"] else ""
            md.append(f"- [{name} Report]({info['path']}) (fetched: {ts})  \n")
        else:
            md.append(f"- {name} Report: *not available*  \n")

    md.append("\n---\n")
    md.append("## 📈 MINI CHARTS\n\n")
    md.append("### χ Amplitude (72h)\n")
    md.append(f"![χ Sparkline]({chi_chart})\n\n")
    md.append("### Solar Wind (72h)\n")
    md.append(f"![Solar Wind]({sw_chart})\n\n")
    md.append("---\n")
    md.append("## 📊 LATEST 20 READINGS\n\n")
    md.append("| Time (UTC) | χ | Density | Speed |\n")
    md.append("|------------|----|---------|--------|\n")
    latest = df.tail(20)
    # Use apply() for vectorized string formatting - faster than iterrows() or iloc
    rows = latest.apply(
        lambda row: f"| {row[TIME_COL]} | {row[CHI_COL]:.4f} | {row.get('density', np.nan)} | {row.get('speed', np.nan)} |\n",
        axis=1
    ).tolist()
    md.extend(rows)

    OUTPUT_MD.write_text("".join(md), encoding="utf-8")

# ------------------------
# Main
# ------------------------

def main():
    df = load_latest_extended()
    # 72h window
    cutoff = df[TIME_COL].max() - pd.Timedelta(hours=72)
    df72 = df[df[TIME_COL] >= cutoff].copy()

    streak, last_lock, first_lock, duration = detect_cap_streak(df72)
    chi_boundary_analysis = analyze_chi_boundary(df72)
    noaa = check_noaa()

    chi_chart = make_chi_sparkline(df72, streak)
    sw_chart = make_solarwind_miniplot(df72)

    write_markdown(df72, streak, last_lock, first_lock, duration, noaa, chi_chart, sw_chart, chi_boundary_analysis)

    print("[OK] Vault narrator complete.")

if __name__ == "__main__":
    main()
