#!/usr/bin/env python3
"""
chi_learning_loop_v2.py

Forecast-aware χ learning loop for LUFT.

- Reads recent CME heartbeat data.
- Identifies χ = 0.15 locks vs non-locks.
- Reads NOAA 3-day solar/geomagnetic predictions (daypre.txt).
- Reads current space weather indices (curind.txt).
- Attaches forecast and nowcast context to χ rows.
- Computes correlations between χ and key drivers.
- Writes:
    - results/chi_learning_loop_v2_YYYYMMDD.csv
    - reports/chi_learning_loop_v2_YYYYMMDD.md

This is *not* ingestion. It is the engine *learning from what it already ingested*.
"""

from __future__ import annotations
from pathlib import Path
from datetime import timedelta
import math
import re
from typing import Dict, Any, Tuple, Optional, List

import pandas as pd


# --- CONFIG -----------------------------------------------------------------

HEARTBEAT_CSV = Path("data/cme_heartbeat_log_2025_12.csv")

FORECAST_PATH = Path(
    "data/noaa_text/3_day_solar_geomag_predictions/20251220.txt"
)
CURIND_PATH = Path(
    "data/noaa_text/current_space_weather_indices/20251220.txt"
)

RESULTS_DIR = Path("results")
REPORTS_DIR = Path("reports")

HOURS_BACK = 72

CHI_LOCK_VALUE = 0.1500
CHI_LOCK_TOL = 0.0005  # |χ - 0.1500| <= 0.0005


# --- UTILITIES --------------------------------------------------------------

def _find_column(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    """Return the first column name in df that matches any candidate."""
    lower_map = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand in df.columns:
            return cand
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None


def _safe_corr(a: pd.Series, b: pd.Series) -> Optional[float]:
    """Return Pearson r or None if not enough valid data."""
    s = pd.concat([a, b], axis=1).dropna()
    if len(s) < 5:
        return None
    return float(s.corr().iloc[0, 1])


def _parse_forecast_daypre(path: Path) -> Dict[str, Any]:
    """
    Parse key values from the 3-day Space Weather Predictions (daypre.txt).

    We keep it simple:
    - A_Planetary for day 1, 2, 3
    - Pred_Mid_k: we store average predicted K for day 1
    - Pred_High_k: same for high latitude, day 1
    - Prob_Mid: Active/Minor/Major for day 1
    - Prob_High: Active/Minor/Major for day 1
    - 10cm_flux for day 1
    - Whole_Disk_Flare_Prob: M, X, Proton for day 1
    """
    result: Dict[str, Any] = {}

    if not path.exists():
        return result

    text = path.read_text(encoding="utf-8", errors="ignore").splitlines()

    # Helpers to find sections
    def find_section_start(tag: str) -> int:
        for i, line in enumerate(text):
            if line.strip().startswith(tag):
                return i
        return -1

    # Geomagnetic A indices
    i_a = find_section_start(":Geomagnetic_A_indices:")
    if i_a != -1:
        for line in text[i_a + 1:i_a + 5]:
            if line.strip().startswith("A_Planetary"):
                parts = line.split()
                try:
                    # last three values should be day1, day2, day3
                    vals = list(map(int, parts[-3:]))
                    result["A_planetary_day1"] = vals[0]
                    result["A_planetary_day2"] = vals[1]
                    result["A_planetary_day3"] = vals[2]
                except Exception:
                    pass
                break

    # Predicted K indices - Middle latitude
    i_mid = find_section_start(":Pred_Mid_k:")
    mid_vals_day1: List[float] = []
    if i_mid != -1:
        for line in text[i_mid + 1:i_mid + 1 + 8]:
            if line.strip().startswith("Mid/"):
                parts = line.split()
                # last three entries are day1, day2, day3
                try:
                    k1 = float(parts[-3])
                    mid_vals_day1.append(k1)
                except Exception:
                    continue
    if mid_vals_day1:
        result["Kp_mid_day1_mean"] = sum(mid_vals_day1) / len(mid_vals_day1)

    # Predicted K indices - High latitude
    i_high = find_section_start(":Pred_High_k:")
    high_vals_day1: List[float] = []
    if i_high != -1:
        for line in text[i_high + 1:i_high + 1 + 8]:
            if line.strip().startswith("High/"):
                parts = line.split()
                try:
                    k1 = float(parts[-3])
                    high_vals_day1.append(k1)
                except Exception:
                    continue
    if high_vals_day1:
        result["Kp_high_day1_mean"] = sum(high_vals_day1) / len(high_vals_day1)

    # Probability of Geomagnetic conditions at Middle Latitude
    i_prob_mid = find_section_start(":Prob_Mid:")
    if i_prob_mid != -1:
        for line in text[i_prob_mid + 1:i_prob_mid + 4]:
            line = line.strip()
            if line.startswith("Mid/Active"):
                parts = line.split()
                try:
                    result["Prob_mid_active_day1"] = int(parts[-3])
                except Exception:
                    pass
            if line.startswith("Mid/Minor_Storm"):
                parts = line.split()
                try:
                    result["Prob_mid_minor_day1"] = int(parts[-3])
                except Exception:
                    pass
            if line.startswith("Mid/Major-Severe_Storm"):
                parts = line.split()
                try:
                    result["Prob_mid_major_day1"] = int(parts[-3])
                except Exception:
                    pass

    # Probability of Geomagnetic conditions at High Latitudes
    i_prob_high = find_section_start(":Prob_High:")
    if i_prob_high != -1:
        for line in text[i_prob_high + 1:i_prob_high + 4]:
            line = line.strip()
            if line.startswith("High/Active"):
                parts = line.split()
                try:
                    result["Prob_high_active_day1"] = int(parts[-3])
                except Exception:
                    pass
            if line.startswith("High/Minor_Storm"):
                parts = line.split()
                try:
                    result["Prob_high_minor_day1"] = int(parts[-3])
                except Exception:
                    pass
            if line.startswith("High/Major-Severe_Storm"):
                parts = line.split()
                try:
                    result["Prob_high_major_day1"] = int(parts[-3])
                except Exception:
                    pass

    # 10cm flux
    i_flux = find_section_start(":10cm_flux:")
    if i_flux != -1:
        for line in text[i_flux + 1:i_flux + 4]:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 3:
                try:
                    f1 = float(parts[-3])
                    result["F10_7_day1"] = f1
                except Exception:
                    pass
                break

    # Whole disk flare probabilities
    i_flare = find_section_start(":Whole_Disk_Flare_Prob:")
    if i_flare != -1:
        for line in text[i_flare + 1:i_flare + 5]:
            stripped = line.strip()
            if stripped.startswith("Class_M"):
                vals = stripped.split()
                try:
                    result["Prob_flare_M_day1"] = int(vals[-3])
                except Exception:
                    pass
            elif stripped.startswith("Class_X"):
                vals = stripped.split()
                try:
                    result["Prob_flare_X_day1"] = int(vals[-3])
                except Exception:
                    pass
            elif stripped.startswith("Proton"):
                vals = stripped.split()
                try:
                    result["Prob_flare_proton_day1"] = int(vals[-3])
                except Exception:
                    pass

    return result


def _parse_curind(path: Path) -> Dict[str, Any]:
    """
    Parse key values from Current Space Weather Indices (curind.txt).

    We keep it light:
    - F10.7 now (from Solar_Radio_Flux Penticton 1700/2000)
    - GOES proton/electron flux (>1 MeV, >2 MeV)
    - latest planetary K estimate and running A if visible.
    """
    result: Dict[str, Any] = {}

    if not path.exists():
        return result

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()

    # F10.7 from the 2800 MHz row with Penticton columns
    in_flux = False
    for line in lines:
        if line.strip().startswith(":Solar_Radio_Flux:"):
            in_flux = True
            continue
        if in_flux:
            if line.strip().startswith("#"):
                continue
            if not line.strip():
                in_flux = False
                continue
            parts = line.split()
            if len(parts) >= 8:
                try:
                    freq = int(parts[0])
                except Exception:
                    continue
                if freq == 2800:
                    # use Penticton 1700 as primary, 2000 as secondary
                    try:
                        pent_1700 = float(parts[4])
                        pent_2000 = float(parts[5])
                        f_now = pent_2000 if pent_2000 > 0 else pent_1700
                        if f_now > 0:
                            result["F10_7_now"] = f_now
                    except Exception:
                        pass
                    break

    # GOES proton/electron flux block
    in_particles = False
    for line in lines:
        if line.strip().startswith(":Energetic_Particle_Flux:"):
            in_particles = True
            continue
        if in_particles:
            if line.strip().startswith("#"):
                continue
            if not line.strip():
                continue
            if line.strip().startswith(":Geomagnetic_Values:"):
                break
            parts = line.split()
            if len(parts) >= 7:
                try:
                    p_gt1 = float(parts[0])
                    p_gt10 = float(parts[1])
                    p_gt100 = float(parts[2])
                    e_gt2 = float(parts[3])
                except Exception:
                    continue
                result["GOES_p_gt1MeV"] = p_gt1
                result["GOES_p_gt10MeV"] = p_gt10
                result["GOES_p_gt100MeV"] = p_gt100
                result["GOES_e_gt2MeV"] = e_gt2
                break

    # Geomagnetic values - we attempt to grab last planetary K in the line
    for line in lines:
        if line.strip().startswith("#Running A"):
            # Next line should have the values
            # Example:
            # 6  1 1 1 2 2 2 2 -1   2.00 0.67 1.33 1.33 1.67 1.67 1.67 -1.00
            continue
        if re.search(r"\d+\s+\d\s+\d\s+\d\s+\d\s+\d\s+\d", line):
            parts = line.split()
            if len(parts) >= 16:
                try:
                    running_A = int(parts[0])
                    planetary_vals = [float(x) for x in parts[-8:]]
                    # last valid (not -1.00)
                    planetary_last = None
                    for v in reversed(planetary_vals):
                        if v > -0.5:
                            planetary_last = v
                            break
                    result["Running_A_now"] = running_A
                    if planetary_last is not None:
                        result["Kp_planetary_last"] = planetary_last
                except Exception:
                    pass
            break

    return result


# --- CORE LEARNING LOOP -----------------------------------------------------

def run_chi_learning_loop_v2() -> None:
    if not HEARTBEAT_CSV.exists():
        print(f"[chi-learning-v2] No heartbeat CSV at {HEARTBEAT_CSV}, nothing to learn from.")
        return

    df = pd.read_csv(HEARTBEAT_CSV)

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
        print(f"[chi-learning-v2] Missing required columns in heartbeat CSV: {missing}")
        return

    df[ts_col] = pd.to_datetime(df[ts_col], utc=True, errors="coerce")
    df = df.dropna(subset=[ts_col])
    df = df.sort_values(ts_col)

    if df.empty:
        print("[chi-learning-v2] No valid rows after timestamp parsing.")
        return

    now_utc = df[ts_col].max()
    window_start = now_utc - timedelta(hours=HOURS_BACK)
    df_win = df[df[ts_col] >= window_start].copy()

    if df_win.empty:
        print(f"[chi-learning-v2] No rows in the last {HOURS_BACK} hours.")
        return

    df_win["is_lock"] = df_win[chi_col].apply(
        lambda x: bool(
            isinstance(x, (int, float))
            and not math.isnan(x)
            and abs(x - CHI_LOCK_VALUE) <= CHI_LOCK_TOL
        )
    )

    n_total = len(df_win)
    n_lock = int(df_win["is_lock"].sum())
    n_nolock = n_total - n_lock

    # Forecast + nowcast context
    forecast_ctx = _parse_forecast_daypre(FORECAST_PATH)
    curind_ctx = _parse_curind(CURIND_PATH)

    # Attach same context to every row in the window (it's global context)
    for key, val in {**forecast_ctx, **curind_ctx}.items():
        df_win[key] = val

    # Correlations
    chi_series = df_win[chi_col].astype(float)

    corr_density = _safe_corr(chi_series, df_win[dens_col].astype(float)) if dens_col else None
    corr_speed = _safe_corr(chi_series, df_win[spd_col].astype(float)) if spd_col else None
    corr_bz = _safe_corr(chi_series, df_win[bz_col].astype(float)) if bz_col else None

    def ctx_corr(name: str) -> Optional[float]:
        if name not in df_win.columns:
            return None
        return _safe_corr(chi_series, df_win[name].astype(float))

    corr_A_planetary = ctx_corr("A_planetary_day1")
    corr_Kp_mid = ctx_corr("Kp_mid_day1_mean")
    corr_Kp_high = ctx_corr("Kp_high_day1_mean")
    corr_F10_day1 = ctx_corr("F10_7_day1")
    corr_F10_now = ctx_corr("F10_7_now")
    corr_goes_p1 = ctx_corr("GOES_p_gt1MeV")
    corr_goes_e2 = ctx_corr("GOES_e_gt2MeV")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    date_tag = now_utc.strftime("%Y%m%d")
    out_csv = RESULTS_DIR / f"chi_learning_loop_v2_{date_tag}.csv"
    out_md = REPORTS_DIR / f"chi_learning_loop_v2_{date_tag}.md"

    export_cols = [ts_col, chi_col, "is_lock"]
    for col in [dens_col, spd_col, bz_col]:
        if col:
            export_cols.append(col)

    # context columns
    export_ctx_cols = [
        "A_planetary_day1",
        "Kp_mid_day1_mean",
        "Kp_high_day1_mean",
        "Prob_mid_active_day1",
        "Prob_mid_minor_day1",
        "Prob_mid_major_day1",
        "Prob_high_active_day1",
        "Prob_high_minor_day1",
        "Prob_high_major_day1",
        "F10_7_day1",
        "Prob_flare_M_day1",
        "Prob_flare_X_day1",
        "Prob_flare_proton_day1",
        "F10_7_now",
        "GOES_p_gt1MeV",
        "GOES_p_gt10MeV",
        "GOES_p_gt100MeV",
        "GOES_e_gt2MeV",
        "Running_A_now",
        "Kp_planetary_last",
    ]
    for col in export_ctx_cols:
        if col in df_win.columns:
            export_cols.append(col)

    df_win[export_cols].to_csv(out_csv, index=False)

    # Markdown capsule
    lines: list[str] = []
    lines.append("# 🔍 χ Learning Loop Report v2 (Forecast-aware)")
    lines.append("")
    lines.append(f"**Generated:** {now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append(f"**Source heartbeat:** `{HEARTBEAT_CSV}` (last {HOURS_BACK} hours)")
    lines.append(f"**Forecast file:** `{FORECAST_PATH}`")
    lines.append(f"**Current indices file:** `{CURIND_PATH}`")
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
    lines.append("## 🔗 Correlations (χ vs solar wind drivers)")
    lines.append("")
    def fmt_corr(label: str, val: Optional[float]) -> str:
        if val is None:
            return f"- **{label}:** _not enough data_"
        return f"- **{label}:** `r = {val:+.3f}`"

    lines.append(fmt_corr("Density", corr_density))
    lines.append(fmt_corr("Speed", corr_speed))
    lines.append(fmt_corr("Bz", corr_bz))
    lines.append("")
    lines.append("## 🔗 Correlations (χ vs forecast & indices)")
    lines.append("")
    lines.append(fmt_corr("A_planetary (day 1 forecast)", corr_A_planetary))
    lines.append(fmt_corr("Kp_mid (day 1 mean forecast)", corr_Kp_mid))
    lines.append(fmt_corr("Kp_high (day 1 mean forecast)", corr_Kp_high))
    lines.append(fmt_corr("F10.7 (day 1 forecast)", corr_F10_day1))
    lines.append(fmt_corr("F10.7 (current, curind)", corr_F10_now))
    lines.append(fmt_corr("GOES p >1 MeV (current)", corr_goes_p1))
    lines.append(fmt_corr("GOES e >2 MeV (current)", corr_goes_e2))
    lines.append("")
    lines.append("*(Pearson r over last hours; |r| close to 1 means strong linear relation.)*")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 🧠 Notes for LUFT Students")
    lines.append("")
    lines.append("- This v2 report includes **forecast (daypre)** and **nowcast (curind)** context.")
    lines.append("- Each row still tracks whether the system was in a χ lock or not.")
    lines.append("- Correlations now hint at which forecasted or current indices matter for χ.")
    lines.append("")
    lines.append(f"Raw features: `{out_csv}`")
    lines.append("")
    lines.append("*— χ Learning Loop v2*")

    out_md.write_text("\n".join(lines), encoding="utf-8")

    print(f"[chi-learning-v2] Wrote {out_csv}")
    print(f"[chi-learning-v2] Wrote {out_md}")


if __name__ == "__main__":
    run_chi_learning_loop_v2()
