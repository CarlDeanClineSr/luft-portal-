"""
Fit epsilon_coh(t) = epsilon0 + mu*Phi(t) + nu*f(t)^2 + kappa_j*J(t)
Where J(t) is a rolling variance (jitter) of Phi over a window (samples).

Input: sft_states.csv from flare_pipeline.py
Columns required: timestamp, Phi_pfu, f

Outputs JSON with fitted coefficients and basic metrics (R^2, residual RMS).
Usage:
  python3 coherence_shift_fit.py --input sft_states.csv --output epsilon_fit.json --window 60
"""
import argparse, csv, json, math
from typing import List

def rolling_variance(xs: List[float], window: int) -> List[float]:
    if window <= 1:
        return [0.0]*len(xs)
    out = []
    for i in range(len(xs)):
        s = max(0, i-window+1)
        seg = xs[s:i+1]
        m = sum(seg)/len(seg)
        var = sum((v-m)*(v-m) for v in seg)/len(seg)
        out.append(var)
    return out

def ols(X, y):
    try:
        import numpy as np
    except Exception as e:
        raise RuntimeError("Install numpy: pip install numpy")
    XT = np.transpose(X)
    A = XT.dot(X) + 1e-8*np.eye(X.shape[1])
    b = XT.dot(y)
    coeff = np.linalg.solve(A, b)
    yhat = np.array(X).dot(coeff)
    resid = yhat - np.array(y)
    ss_res = float((resid**2).sum())
    ss_tot = float(((np.array(y) - np.mean(y))**2).sum()) if len(y) > 1 else 0.0
    r2 = 1.0 - ss_res/ss_tot if ss_tot > 0 else 0.0
    rms = math.sqrt(ss_res/len(y)) if len(y) else 0.0
    return coeff.tolist(), r2, rms

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--window", type=int, default=60, help="Rolling sample window for jitter")
    # If epsilon-coh is not in input, we construct a proxy from baseline with noise (can be replaced by measured column)
    ap.add_argument("--epsilon0", type=float, default=0.0)
    ap.add_argument("--mu0", type=float, default=0.01)
    ap.add_argument("--nu0", type=float, default=0.0005)
    ap.add_argument("--kappa0", type=float, default=0.0)
    args = ap.parse_args()

    Phi, fvals = [], []
    with open(args.input, "r", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            Phi.append(float(r["Phi_pfu"]))
            fvals.append(float(r["f"]))

    J = rolling_variance(Phi, args.window)

    # Build regression matrices (synthetic epsilon_obs for now)
    try:
        import numpy as np
    except Exception:
        print("Install numpy: pip install numpy")
        raise
    X, y = [], []
    for i in range(len(Phi)):
        phi = Phi[i]
        fv = fvals[i]
        jit = J[i]
        eps_obs = args.epsilon0 + args.mu0*phi + args.nu0*(fv*fv) + args.kappa0*jit
        y.append(eps_obs)
        X.append([1.0, phi, fv*fv, jit])  # [intercept, mu, nu, kappa_j]
    X = np.array(X)
    y = np.array(y)

    coeff, r2, rms = ols(X, y)
    result = {
        "coefficients": {
            "epsilon0": coeff[0],
            "mu": coeff[1],
            "nu": coeff[2],
            "kappa_j": coeff[3]
        },
        "metrics": {
            "R2": r2,
            "residual_RMS": rms
        },
        "window_samples": args.window,
        "note": "Replace synthetic epsilon with measured coherence index when available."
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print("Wrote", args.output)

if __name__ == "__main__":
    main()
