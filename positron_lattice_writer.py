"""
Positron Lattice Writer (PLW) — Impulse-to-f simulator (radiation-free emulation)

Goal:
  Explore how localized energy impulses (E_dep) in an effective cell volume V_cell
  map into a lattice fraction kick f_imp and evolve under LUFT memory dynamics.

Model:
  f_imp        = sigma_f * sgn * E_dep / (u0 * V_cell)
  f_{t+dt}     = f_t + lambda*(v_gain - 1) - eta*f_t + noise
  v_gain       = (1 + 0.1 * f_t)         # simple drift gain factor
  noise        ~ N(0, sigma^2)

Where:
  - u0       : baseline lattice energy density (J/m^3)
  - sigma_f  : (0..1), effective coupling efficiency
  - sgn      : {-1, +1} choose hypothesis (void vs compressive)
  - V_cell   : effective interaction volume (m^3)

Usage (example):
  python3 positron_lattice_writer.py --E_dep 1e-15 --V_cell 1e-6 --sigma_f 0.02 --sgn -1 \
    --u0 4.79e-10 --lambda 0.05 --eta 0.003 --sigma 1e-4 --steps 5000 --dt 0.1 --out plw_run.json

To print results to console instead of writing a file:
  python3 positron_lattice_writer.py --print
"""
import argparse
import json
import math
import random
from typing import Tuple, List, Dict, Any


def simulate(
    E_dep: float = 1e-15,
    V_cell: float = 1e-6,
    sigma_f: float = 0.02,
    sgn: int = -1,
    u0: float = 4.79e-10,
    lam: float = 0.05,
    eta: float = 0.003,
    sigma: float = 1e-4,
    steps: int = 5000,
    dt: float = 0.1,
    f0: float = 0.0,
    target_band: float = 0.05,
    rng_seed: int | None = None,
) -> Tuple[Dict[str, Any], List[float]]:
    # Basic validation to avoid silent math errors
    if V_cell <= 0:
        raise ValueError("V_cell must be > 0")
    if u0 <= 0:
        raise ValueError("u0 must be > 0")
    if not (0 <= sigma_f <= 1):
        raise ValueError("sigma_f must be in [0, 1]")
    if steps <= 0:
        raise ValueError("steps must be > 0")
    if dt <= 0:
        raise ValueError("dt must be > 0")
    if sgn not in (-1, +1):
        raise ValueError("sgn must be -1 (void) or +1 (compressive)")

    if rng_seed is not None:
        random.seed(rng_seed)

    # Initial impulse
    f_imp = sigma_f * (1 if sgn >= 0 else -1) * (E_dep / (u0 * V_cell))
    f = f0 + f_imp
    t_ret = None
    series = [f]

    for i in range(1, steps):
        v_gain = (1.0 + 0.1 * f)  # simple proxy
        noise = random.gauss(0.0, sigma)
        f = f + lam * (v_gain - 1.0) - eta * f + noise
        series.append(f)
        # retention time: when |f| falls back within the target band around 0
        if t_ret is None and abs(f) < target_band:
            t_ret = i * dt

    if t_ret is None:
        t_ret = steps * dt

    stats = {
        "f_imp": f_imp,
        "f_init": series[0],
        "f_final": f,
        "f_min": min(series),
        "f_max": max(series),
        "f_mean": sum(series) / len(series),
        "retention_time_s": t_ret,
    }
    return stats, series


def main():
    ap = argparse.ArgumentParser(description="PLW impulse-to-f simulator")
    ap.add_argument("--E_dep", type=float, default=1e-15, help="Deposited energy (J)")
    ap.add_argument("--V_cell", type=float, default=1e-6, help="Effective cell volume (m^3)")
    ap.add_argument("--sigma_f", type=float, default=0.02, help="Coupling efficiency [0..1]")
    ap.add_argument("--sgn", type=int, default=-1, help="-1 for void hypothesis, +1 for compressive")
    ap.add_argument("--u0", type=float, default=4.79e-10, help="Baseline lattice energy density (J/m^3)")
    ap.add_argument("--lambda", dest="lam", type=float, default=0.05, help="Memory coupling gain")
    ap.add_argument("--eta", type=float, default=0.003, help="Damping coefficient")
    ap.add_argument("--sigma", type=float, default=1e-4, help="Noise std dev for N(0, sigma^2)")
    ap.add_argument("--steps", type=int, default=5000, help="Simulation steps")
    ap.add_argument("--dt", type=float, default=0.1, help="Time step (s)")
    ap.add_argument("--f0", type=float, default=0.0, help="Initial f before impulse")
    ap.add_argument("--target_band", type=float, default=0.05, help="Retention band threshold |f|")
    ap.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    ap.add_argument("--out", default="plw_run.json", help="Output JSON file (stats + sampled series)")
    ap.add_argument("--print", dest="to_print", action="store_true", help="Print JSON to stdout instead of writing file")
    ap.add_argument("--sample_points", type=int, default=1000, help="Max points to include from time series")
    args = ap.parse_args()

    stats, series = simulate(
        E_dep=args.E_dep,
        V_cell=args.V_cell,
        sigma_f=args.sigma_f,
        sgn=args.sgn,
        u0=args.u0,
        lam=args.lam,
        eta=args.eta,
        sigma=args.sigma,
        steps=args.steps,
        dt=args.dt,
        f0=args.f0,
        target_band=args.target_band,
        rng_seed=args.seed,
    )

    # Sample down the series for compact output (keep first and last)
    stride = max(1, len(series) // max(1, args.sample_points))
    sampled = series[::stride]
    if sampled[-1] != series[-1]:
        sampled.append(series[-1])

    result = {
        "params": {
            "E_dep": args.E_dep,
            "V_cell": args.V_cell,
            "sigma_f": args.sigma_f,
            "sgn": args.sgn,
            "u0": args.u0,
            "lambda": args.lam,
            "eta": args.eta,
            "sigma": args.sigma,
            "steps": args.steps,
            "dt": args.dt,
            "f0": args.f0,
            "target_band": args.target_band,
            "seed": args.seed,
        },
        "stats": stats,
        "series_sampled": sampled,
    }

    if args.to_print:
        print(json.dumps(result, indent=2))
    else:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"Wrote {args.out}")
        print("f_imp=", stats["f_imp"], "retention_time_s=", stats["retention_time_s"])


if __name__ == "__main__":
    main()
