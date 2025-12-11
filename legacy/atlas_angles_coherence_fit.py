"""
ATLAS Angles Coherence Fitter — single ε_coh parameter.

Model:
  A_i_obs = A_i_MC + ε_coh * C_i
Fit ε_coh by minimizing χ² over coefficients i ∈ {0..4} and all rows.

Input CSV expected columns (case-sensitive):
  A0_obs,A1_obs,A2_obs,A3_obs,A4_obs
  A0_MC,A1_MC,A2_MC,A3_MC,A4_MC
Optional:
  C0,C1,C2,C3,C4          (sensitivity kernels; default 1.0 if missing)
  dA0,dA1,dA2,dA3,dA4     (per-measurement uncertainties; if absent -> estimated)
  run, lb, timestamp      (for reporting/permutation stratification)

Outputs JSON with ε_best, uncertainty, χ², ndof, p_global (permutation),
and per-run summaries.

Usage:
  python3 scripts/atlas_angles_coherence_fit.py --input angles.csv --output angles_epsilon.json
Options:
  --permutations N (default 500)
  --seed SEED
  --use-errors (require dA* columns; else fail)
  --require-kernels (require C* columns; else fail)
  --runs-column run --lb-column lb
"""
import argparse, csv, json, math, random
from typing import List, Dict, Any, Tuple

COEFF_NAMES = ["A0","A1","A2","A3","A4"]

def read_rows(path: str) -> List[Dict[str, str]]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            rows.append(r)
    if not rows:
        raise RuntimeError("No rows parsed from input CSV.")
    return rows

def extract_values(rows: List[Dict[str,str]],
                   use_errors: bool,
                   require_kernels: bool) -> Tuple[List[Dict[str, Any]], List[str]]:
    processed = []
    missing_cols = set()
    for r in rows:
        entry = {}
        for cn in COEFF_NAMES:
            obs_key = f"{cn}_obs"
            mc_key  = f"{cn}_MC"
            if obs_key not in r or mc_key not in r:
                missing_cols.update({obs_key, mc_key})
                continue
            try:
                entry[obs_key] = float(r[obs_key])
                entry[mc_key]  = float(r[mc_key])
            except Exception:
                raise ValueError(f"Non-numeric value for {obs_key} or {mc_key}")
            # Kernel
            k_key = f"C{cn[1:]}" if cn.startswith("A") else f"C{cn}"
            # We'll define kernel keys as C0..C4 for simplicity
        # Kernels
        kernels = []
        for i in range(len(COEFF_NAMES)):
            k_name = f"C{i}"
            if k_name in r and r[k_name] != "":
                try:
                    kernels.append(float(r[k_name]))
                except Exception:
                    raise ValueError(f"Non-numeric kernel {k_name}")
            else:
                if require_kernels:
                    missing_cols.add(k_name)
                kernels.append(1.0)
        entry["kernels"] = kernels
        # Errors
        errors = []
        for i in range(len(COEFF_NAMES)):
            d_name = f"dA{i}"
            if d_name in r and r[d_name] != "":
                try:
                    errors.append(float(r[d_name]))
                except Exception:
                    raise ValueError(f"Non-numeric error {d_name}")
            else:
                if use_errors:
                    missing_cols.add(d_name)
                errors.append(None)  # to be filled later if not provided
        entry["errors"] = errors
        # run/lb info
        entry["run"] = r.get("run","")
        entry["lb"]  = r.get("lb","")
        processed.append(entry)
    return processed, sorted(list(missing_cols))

def estimate_missing_errors(data: List[Dict[str,Any]]) -> None:
    # Estimate per-coefficient global variance of residuals to assign uniform σ_i
    # residual_i = (A_i_obs - A_i_MC)
    accum_sq = [0.0]*len(COEFF_NAMES)
    count = [0]*len(COEFF_NAMES)
    for d in data:
        for i, cn in enumerate(COEFF_NAMES):
            obs = d[f"{cn}_obs"]
            mc  = d[f"{cn}_MC"]
            resid = obs - mc
            accum_sq[i] += resid*resid
            count[i] += 1
    for d in data:
        for i in range(len(COEFF_NAMES)):
            if d["errors"][i] is None:
                # RMS residual as crude σ
                rms = math.sqrt(accum_sq[i]/count[i]) if count[i] else 1.0
                d["errors"][i] = rms if rms > 0 else 1.0

def fit_epsilon(data: List[Dict[str,Any]]) -> Tuple[float,float,float,int]:
    # Compute ε_best and χ²
    num = 0.0
    denom = 0.0
    chi2 = 0.0
    ndof = 0
    for d in data:
        for i, cn in enumerate(COEFF_NAMES):
            obs = d[f"{cn}_obs"]
            mc  = d[f"{cn}_MC"]
            resid = obs - mc
            C_i = d["kernels"][i]
            sigma = d["errors"][i]
            if sigma <= 0:
                sigma = 1.0
            num += (resid * C_i) / (sigma*sigma)
            denom += (C_i * C_i) / (sigma*sigma)
    epsilon = num / denom if denom != 0 else 0.0
    # Compute χ²
    for d in data:
        for i, cn in enumerate(COEFF_NAMES):
            obs = d[f"{cn}_obs"]
            mc  = d[f"{cn}_MC"]
            C_i = d["kernels"][i]
            sigma = d["errors"][i]
            if sigma <= 0:
                sigma = 1.0
            model = mc + epsilon * C_i
            chi2 += ((obs - model)**2) / (sigma*sigma)
            ndof += 1
    # ndof minus one parameter (epsilon)
    ndof_eff = ndof - 1 if ndof > 1 else ndof
    epsilon_unc = 1.0 / math.sqrt(denom) if denom > 0 else float("inf")
    return epsilon, epsilon_unc, chi2, ndof_eff

def permutation_test(data: List[Dict[str,Any]], epsilon_obs: float,
                     permutations: int, seed: int | None) -> float:
    if permutations <= 0:
        return float("nan")
    rng = random.Random(seed)
    count = 0
    # Flatten residuals & kernels & errors
    resid_list = []
    kernel_list = []
    error_list = []
    for d in data:
        for i, cn in enumerate(COEFF_NAMES):
            obs = d[f"{cn}_obs"]
            mc  = d[f"{cn}_MC"]
            resid_list.append(obs - mc)
            kernel_list.append(d["kernels"][i])
            error_list.append(d["errors"][i])
    n = len(resid_list)
    for _ in range(permutations):
        # Shuffle residuals
        perm_resid = resid_list[:]
        rng.shuffle(perm_resid)
        num = 0.0
        denom = 0.0
        for r, k, e in zip(perm_resid, kernel_list, error_list):
            sigma = e if e > 0 else 1.0
            num += (r * k) / (sigma*sigma)
            denom += (k * k) / (sigma*sigma)
        eps_perm = num / denom if denom > 0 else 0.0
        if abs(eps_perm) >= abs(epsilon_obs):
            count += 1
    return (count + 1) / (permutations + 1)

def per_run_summary(data: List[Dict[str,Any]], epsilon: float) -> Dict[str, Dict[str, float]]:
    runs = {}
    for d in data:
        rkey = d["run"] or "NO_RUN"
        if rkey not in runs:
            runs[rkey] = {"n":0, "resid_sum":0.0}
        for i, cn in enumerate(COEFF_NAMES):
            obs = d[f"{cn}_obs"]
            mc  = d[f"{cn}_MC"]
            C_i = d["kernels"][i]
            resid_model = obs - (mc + epsilon*C_i)
            runs[rkey]["resid_sum"] += resid_model
            runs[rkey]["n"] += 1
    out = {}
    for rk, val in runs.items():
        n = val["n"]
        out[rk] = {
            "n_points": n,
            "residual_mean": val["resid_sum"]/n if n else 0.0
        }
    return out

def classify_result(epsilon: float, epsilon_unc: float, p_global: float, per_run: Dict[str,Dict[str,float]]) -> str:
    stable = True
    # Rough stability: residual_mean near 0 (|mean| < 2*unc scaled)
    for rk, stats in per_run.items():
        if abs(stats["residual_mean"]) > 2 * epsilon_unc:
            stable = False
            break
    sig = abs(epsilon) / epsilon_unc if epsilon_unc > 0 else 0.0
    if p_global < 0.01 and stable and sig >= 2:
        return "signal-quality"
    if p_global < 0.05 and not stable:
        return "candidate"
    return "bound"

def main():
    ap = argparse.ArgumentParser(description="ATLAS Angles Coherence Fitter (ε_coh)")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--permutations", type=int, default=500)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--use-errors", action="store_true", help="Require dA* columns; fail if missing")
    ap.add_argument("--require-kernels", action="store_true", help="Require C* columns; fail if missing")
    args = ap.parse_args()

    rows = read_rows(args.input)
    data, missing = extract_values(rows, use_errors=args.use_errors, require_kernels=args.require_kernels)
    if missing:
        if args.use_errors or args.require_kernels:
            raise RuntimeError(f"Missing required columns: {missing}")
    # Estimate errors if not provided
    estimate_missing_errors(data)
    epsilon, epsilon_unc, chi2, ndof = fit_epsilon(data)
    chi2_red = chi2 / ndof if ndof > 0 else float("nan")
    p_global = permutation_test(data, epsilon, args.permutations, args.seed)
    per_run = per_run_summary(data, epsilon)
    classification = classify_result(epsilon, epsilon_unc, p_global, per_run)

    result = {
        "epsilon_best": epsilon,
        "epsilon_uncert": epsilon_unc,
        "chi2": chi2,
        "ndof": ndof,
        "chi2_red": chi2_red,
        "p_global": p_global,
        "classification": classification,
        "per_run": per_run,
        "config": {
            "permutations": args.permutations,
            "seed": args.seed,
            "use_errors": args.use_errors,
            "require_kernels": args.require_kernels
        },
        "notes": "Replace MC with tuned reference; add kernels C0..C4 for theory sensitivity."
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print("Wrote", args.output)
    print("epsilon_best=", epsilon, "±", epsilon_unc, "p_global=", p_global, "classification=", classification)

if __name__ == "__main__":
    main()
