from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict

import numpy as np
import pandas as pd

from analyses.desi_drift.desi_loader import load_residuals
from analyses.desi_drift.desi_bound import fit_chi_bound, ChiBound
from analyses.desi_drift.desi_null_tests import shuffled_time_pvalue
from analyses.desi_drift.bootstrap import bootstrap_amp_ci
from analyses.desi_drift.desi_window import sampling_window_power

def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def linear_detrend(t: np.ndarray, y: np.ndarray) -> np.ndarray:
    X = np.column_stack([np.ones_like(t), t])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return y - (X @ beta)

def fit_wrap(t: np.ndarray, y: np.ndarray, omega_hz: float, do_detrend: bool) -> Dict[str, float]:
    y_use = linear_detrend(t, y) if do_detrend else y
    cb: ChiBound = fit_chi_bound(t, y_use, omega_hz=omega_hz)
    return {
        "chi_hat": cb.chi_hat,
        "chi_95": cb.chi_95,
        "delta_rms": cb.delta_rms,
    }

def main():
    ap = argparse.ArgumentParser(description="Capsule 009 DESI Λ(t) drift χ bound runner")
    ap.add_argument("--csv", required=True, help="Path to residuals CSV (t_s,residual)")
    ap.add_argument("--omega", type=float, default=1e-4, help="Test frequency Ω in Hz (default 1e-4)")
    ap.add_argument("--K", type=int, default=500, help="Null shuffled-time iterations (default 500)")
    ap.add_argument("--bootstrap", type=int, default=0, help="Bootstrap resamples for CI (0 to skip)")
    ap.add_argument("--block-key", type=str, default=None, help="Optional column name for block bootstrap (e.g., group_id)")
    ap.add_argument("--detrend", action="store_true", help="Apply linear detrend before χ fit (report both)")
    ap.add_argument("--omega-scan", action="store_true", help="Scan Ω in ±10%% window (11 points)")
    ap.add_argument("--outdir", type=str, default="results/desi", help="Output directory")
    args = ap.parse_args()

    csv_path = Path(args.csv)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # Load
    t, y, meta = load_residuals(csv_path)
    input_sha = sha256_of_file(csv_path)

    # Optional block ids
    group_ids = None
    if args.block_key:
        try:
            df = pd.read_csv(csv_path, usecols=[args.block_key])
            group_ids = df[args.block_key].to_numpy()
        except Exception:
            group_ids = None

    # Raw fit
    raw = fit_wrap(t, y, args.omega, do_detrend=False)
    # Detrended fit (optional)
    det = fit_wrap(t, y, args.omega, do_detrend=True) if args.detrend else None

    # Null shuffled-time p-values
    p_null_raw, chi_null_mean_raw = shuffled_time_pvalue(t, y, args.omega, K=args.K, seed=0)
    p_null_det, chi_null_mean_det = (np.nan, np.nan)
    if args.detrend:
        y_det = linear_detrend(t, y)
        p_null_det, chi_null_mean_det = shuffled_time_pvalue(t, y_det, args.omega, K=args.K, seed=0)

    # Bootstrap CI (optional)
    bt = {"chi_05": np.nan, "chi_50": np.nan, "chi_95": np.nan}
    bt_det = {"chi_05": np.nan, "chi_50": np.nan, "chi_95": np.nan}
    if args.bootstrap > 0:
        chi05, chi50, chi95 = bootstrap_amp_ci(t, y, args.omega, K=args.bootstrap, seed=1, group_ids=group_ids)
        bt = {"chi_05": chi05, "chi_50": chi50, "chi_95": chi95}
        if args.detrend:
            y_det = linear_detrend(t, y)
            chi05d, chi50d, chi95d = bootstrap_amp_ci(t, y_det, args.omega, K=args.bootstrap, seed=1, group_ids=group_ids)
            bt_det = {"chi_05": chi05d, "chi_50": chi50d, "chi_95": chi95d}

    # Spectral window metrics (if astropy available)
    win = sampling_window_power(t, args.omega, sideband_frac=0.1)

    # Ω scan (±10%)
    omega_scan = []
    if args.omega_scan:
        omegas = np.linspace(0.9*args.omega, 1.1*args.omega, 11)
        for om in omegas:
            sub = fit_wrap(t, y, om, do_detrend=False)
            omega_scan.append({"omega_hz": float(om), "chi_hat": sub["chi_hat"], "chi_95": sub["chi_95"]})

    # Decision (raw; v1 rule)
    accept = (raw["chi_95"] < 0.01) and (p_null_raw < 0.05)

    # JSON summary
    summary = {
        "input_path": str(csv_path),
        "input_sha256": input_sha,
        "n": int(meta.get("n", len(t))),
        "omega_hz": float(args.omega),
        "chi_hat_raw": float(raw["chi_hat"]),
        "chi_95_raw": float(raw["chi_95"]),
        "delta_rms_raw": float(raw["delta_rms"]),
        "p_null_raw": float(p_null_raw),
        "chi_null_mean_raw": float(chi_null_mean_raw),
        "bootstrap_raw": bt,
        "chi_hat_detrended": (float(det["chi_hat"]) if det else np.nan),
        "chi_95_detrended": (float(det["chi_95"]) if det else np.nan),
        "delta_rms_detrended": (float(det["delta_rms"]) if det else np.nan),
        "p_null_detrended": float(p_null_det) if args.detrend else np.nan,
        "chi_null_mean_detrended": float(chi_null_mean_det) if args.detrend else np.nan,
        "bootstrap_detrended": bt_det if args.detrend else None,
        "window_power": win,
        "omega_scan": omega_scan,
        "accept_bound_v1": bool(accept),
    }
    with open(outdir / "capsule_009_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)

    # diagnostics.md
    diag = []
    diag.append("# Capsule 009 — DESI Λ(t) Drift Diagnostics\n")
    diag.append("## R0 (claim)\n- Λ(t) = Λ₀ [1 + χ cos(Ω t)], Ω = {:.6e} Hz\n".format(args.omega))
    diag.append("## R1 (alternate)\n- Two‑phase basis (cos+sin); optional window correction; optional linear detrend.\n")
    diag.append("## R2 (audit)\n")
    diag.append(f"- N = {summary['n']}\n")
    diag.append("- Raw: χ_hat = {:.6g}, χ_95 = {:.6g}, ΔRMS = {:.6g}, p_null = {:.3g}\n".format(
        summary["chi_hat_raw"], summary["chi_95_raw"], summary["delta_rms_raw"], summary["p_null_raw"]))
    if args.detrend:
        diag.append("- Detrended: χ_hat = {:.6g}, χ_95 = {:.6g}, ΔRMS = {:.6g}, p_null = {:.3g}\n".format(
            summary["chi_hat_detrended"], summary["chi_95_detrended"], summary["delta_rms_detrended"], summary["p_null_detrended"]))
    if args.bootstrap > 0:
        diag.append("- Bootstrap (raw): χ_05 = {:.6g}, χ_50 = {:.6g}, χ_95 = {:.6g}\n".format(
            summary["bootstrap_raw"]["chi_05"], summary["bootstrap_raw"]["chi_50"], summary["bootstrap_raw"]["chi_95"]))
        if args.detrend:
            diag.append("- Bootstrap (detrended): χ_05 = {:.6g}, χ_50 = {:.6g}, χ_95 = {:.6g}\n".format(
                summary["bootstrap_detrended"]["chi_05"], summary["bootstrap_detrended"]["chi_50"], summary["bootstrap_detrended"]["chi_95"]))
    diag.append("### Spectral window\n")
    diag.append("- Window power at Ω: {:.6g}\n".format(summary["window_power"]["power"]))
    sb = summary["window_power"]["sidebands"]
    if sb:
        diag.append("- Sidebands: Ω(1±0.1) power = [{:.6g}, {:.6g}]\n".format(sb[0]["power"], sb[1]["power"]))
    diag.append("- N_eff = {}, gaps: median = {}, max = {}\n".format(
        summary["window_power"]["n_eff"],
        summary["window_power"]["gap_stats"]["median_gap_s"],
        summary["window_power"]["gap_stats"]["max_gap_s"]))
    if omega_scan:
        diag.append("### Ω scan (±10%)\n")
        for row in omega_scan:
            diag.append("- Ω = {:.6e}: χ_hat = {:.6g}, χ_95 = {:.6g}\n".format(
                row["omega_hz"], row["chi_hat"], row["chi_95"]))
    diag.append("## R3 (decision)\n")
    if accept:
        diag.append("- Adopt bound (v1): χ_95 < 0.01 and p_null < 0.05 satisfied.\n")
    else:
        diag.append("- Track: bound not adopted at v1 thresholds; consider aliasing/covariates/window.\n")
    diag.append("\n### Provenance\n")
    diag.append(f"- Input: {summary['input_path']}\n- SHA256: {summary['input_sha256']}\n")

    (outdir / "diagnostics.md").write_text("".join(diag), encoding="utf-8")

    # Console summary
    print("\n== DESI Capsule 009 summary ==")
    print(f"Ω = {args.omega:.6e} Hz | N = {summary['n']}")
    print(f"χ_hat(raw) = {summary['chi_hat_raw']:.6g} | χ_95(raw) = {summary['chi_95_raw']:.6g} | p_null(raw) = {summary['p_null_raw']:.3g}")
    if args.detrend:
        print(f"χ_hat(det) = {summary['chi_hat_detrended']:.6g} | χ_95(det) = {summary['chi_95_detrended']:.6g} | p_null(det) = {summary['p_null_detrended']:.3g}")
    print(f"Window power @ Ω = {summary['window_power']['power']}")
    print(f"Accept v1 bound: {summary['accept_bound_v1']} | Results → {outdir/'capsule_009_summary.json'}")

if __name__ == "__main__":
    main()
