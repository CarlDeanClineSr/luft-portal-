"""
ATLAS Ω-scan scaffold — LB-level time modulation fit
Model: R(t) = R0 * [1 + chi * cos(omega * t + phi)]
Linearized fit per omega: y = a + b cos(ω t) + c sin(ω t),
  with a=R0, chi = sqrt(b^2 + c^2) / a, phi = atan2(-c, b)

Input CSV schema (example below):
- timestamp: ISO8601 or epoch seconds
- run: run number (optional)
- lb: lumiblock (optional)
- rate: observed per-LB rate or count
- lumi: per-LB luminosity (optional; default 1.0 if missing)
- prescale: trigger prescale (optional; default 1.0 if missing)

Outputs:
- JSON: best omega, chi, phi, global p-value (permutation), and chi(omega) spectrum
- Optional CSV with chi spectrum

Usage:
  python3 scripts/atlas_omega_scan.py --input examples/atlas_lb_example.csv --output atlas_omega_scan.json
  python3 scripts/atlas_omega_scan.py --input lb.csv --omega-min 1e-5 --omega-max 1e-3 --n-omega 200 \
      --permutations 200 --seed 42 --spectrum-csv atlas_chi_spectrum.csv
"""
import argparse, csv, json, math, sys, datetime, random
from typing import List, Tuple, Dict

def parse_time(ts: str) -> float | None:
    # Return seconds since first timestamp; absolute value handled outside
    try:
        # ISO8601
        dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.timestamp()
    except Exception:
        try:
            return float(ts)
        except Exception:
            return None

def load_lb_series(path: str,
                   time_col="timestamp",
                   rate_col="rate",
                   lumi_col="lumi",
                   prescale_col="prescale") -> Tuple[List[float], List[float], List[Dict]]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            t = parse_time(r.get(time_col, ""))
            if t is None:
                continue
            try:
                rate = float(r.get(rate_col, "nan"))
            except:
                continue
            lumi = float(r.get(lumi_col, 1.0)) if r.get(lumi_col) not in (None, "") else 1.0
            prescale = float(r.get(prescale_col, 1.0)) if r.get(prescale_col) not in (None, "") else 1.0
            rows.append({"t": t, "rate": rate, "lumi": lumi, "prescale": prescale, **r})
    if not rows:
        raise RuntimeError("No valid rows parsed from input.")
    rows.sort(key=lambda x: x["t"])
    t0 = rows[0]["t"]
    ts = [r["t"] - t0 for r in rows]  # seconds relative to first LB
    # Corrected rate (if lumi/prescale provided)
    ys = []
    for r in rows:
        denom = (r["lumi"] if r["lumi"] != 0 else 1.0) * (r["prescale"] if r["prescale"] != 0 else 1.0)
        ys.append(r["rate"] / denom)
    return ts, ys, rows

def fit_linear(ts: List[float], ys: List[float], omega: float) -> Tuple[float, float, float]:
    """
    Solve y = a + b cos(ω t) + c sin(ω t) by least squares
    Returns (a, b, c)
    """
    try:
        import numpy as np
    except Exception:
        raise RuntimeError("Install numpy: pip install numpy")
    t = np.array(ts, dtype=float)
    y = np.array(ys, dtype=float)
    X = np.column_stack([np.ones_like(t), np.cos(omega*t), np.sin(omega*t)])
    # normal equations with tiny ridge
    XT = X.T
    A = XT @ X + 1e-12 * np.eye(3)
    bvec = XT @ y
    coeff = np.linalg.solve(A, bvec)
    a, b, c = coeff.tolist()
    return a, b, c

def chi_phi_from_coeff(a: float, b: float, c: float) -> Tuple[float, float]:
    # chi = sqrt(b^2 + c^2) / a ; phi satisfies tan(phi) = -c / b
    if a == 0:
        return float("nan"), float("nan")
    chi = math.sqrt(b*b + c*c) / abs(a)
    phi = math.atan2(-c, b)
    return chi, phi

def scan_omegas(ts: List[float], ys: List[float], omega_vals: List[float]) -> List[Dict]:
    out = []
    for om in omega_vals:
        a, b, c = fit_linear(ts, ys, om)
        chi, phi = chi_phi_from_coeff(a, b, c)
        out.append({"omega": om, "a": a, "b": b, "c": c, "chi": chi, "phi": phi})
    return out

def permutation_global_p(ts: List[float], ys: List[float], omega_vals: List[float],
                         chi_obs_max: float, permutations: int, seed: int | None) -> float:
    if permutations <= 0:
        return float("nan")
    try:
        import numpy as np
    except Exception:
        raise RuntimeError("Install numpy: pip install numpy")
    rng = np.random.default_rng(seed) if seed is not None else np.random.default_rng()
    count = 0
    y = np.array(ys, dtype=float)
    for _ in range(permutations):
        y_perm = rng.permutation(y)
        spec = []
        for om in omega_vals:
            a, b, c = fit_linear(ts, y_perm.tolist(), om)
            chi, _ = chi_phi_from_coeff(a, b, c)
            spec.append(chi)
        if max(spec) >= chi_obs_max:
            count += 1
    return (count + 1) / (permutations + 1)

def main():
    ap = argparse.ArgumentParser(description="ATLAS Ω-scan scaffold (LB-level time modulation)")
    ap.add_argument("--input", required=True, help="LB CSV with columns: timestamp, rate, [lumi], [prescale]")
    ap.add_argument("--output", required=True, help="Output JSON for best-fit + spectrum")
    ap.add_argument("--time-col", default="timestamp")
    ap.add_argument("--rate-col", default="rate")
    ap.add_argument("--lumi-col", default="lumi")
    ap.add_argument("--prescale-col", default="prescale")
    ap.add_argument("--omega-min", type=float, default=1e-5)
    ap.add_argument("--omega-max", type=float, default=1e-3)
    ap.add_argument("--n-omega", type=int, default=120)
    ap.add_argument("--logspace", action="store_true", help="Use log-spaced ω grid")
    ap.add_argument("--permutations", type=int, default=200, help="LB shuffle for global p")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--spectrum-csv", default=None, help="Optional CSV dump of chi(ω)")
    args = ap.parse_args()

    # Load data
    ts, ys, rows = load_lb_series(args.input, args.time_col, args.rate_col, args.lumi_col, args.prescale_col)

    # Build omega grid
    try:
        import numpy as np
    except Exception:
        print("Install numpy: pip install numpy")
        raise
    if args.logspace:
        omega_vals = np.logspace(math.log10(args.omega_min), math.log10(args.omega_max), args.n_omega).tolist()
    else:
        omega_vals = np.linspace(args.omega_min, args.omega_max, args.n_omega).tolist()

    # Spectrum
    spectrum = scan_omegas(ts, ys, omega_vals)
    best = max(spectrum, key=lambda r: (r["chi"] if not math.isnan(r["chi"]) else -1.0))
    chi_obs_max = best["chi"]

    # Global p via permutations
    p_global = permutation_global_p(ts, ys, omega_vals, chi_obs_max, args.permutations, args.seed)

    result = {
        "input": args.input,
        "n_points": len(ts),
        "omega_grid": {"min": args.omega_min, "max": args.omega_max, "n": args.n_omega, "logspace": args.logspace},
        "best": {
            "omega": best["omega"],
            "chi": best["chi"],
            "phi": best["phi"],
            "a": best["a"],
            "b": best["b"],
            "c": best["c"]
        },
        "p_global": p_global,
        "notes": "chi is fractional modulation amplitude relative to baseline a (R0). p_global via LB-shuffle."
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    if args.spectrum_csv:
        with open(args.spectrum_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["omega", "chi", "phi", "a", "b", "c"])
            for r in spectrum:
                w.writerow([r["omega"], r["chi"], r["phi"], r["a"], r["b"], r["c"]])

    print("Best ω =", best["omega"], "chi =", best["chi"], "phi =", best["phi"], "p_global =", p_global)
    print("Wrote", args.output, ("and " + args.spectrum_csv) if args.spectrum_csv else "")

if __name__ == "__main__":
    main()
