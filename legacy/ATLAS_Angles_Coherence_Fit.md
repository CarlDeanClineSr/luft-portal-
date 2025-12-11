# Capsule: ATLAS Angles Coherence Fitter — ε_coh from Drell–Yan Angular Coefficients

Purpose
Estimate a single LUFT-style coherence parameter ε_coh that shifts Drell–Yan angular coefficients A0–A4 away from their MC expectation across multiple runs (lumiblocks). Model:
A_i^obs = A_i^MC + ε_coh C_i  for i ∈ {0,1,2,3,4}

Where:
- C_i are sensitivity kernels (dimensionless). If not provided, default C_i = 1 for all i (uniform sensitivity).
- ε_coh is determined by minimizing χ² over all (run, LB) measurements.

Input CSV schema (example columns):
timestamp,run,lb,A0_obs,A1_obs,A2_obs,A3_obs,A4_obs,A0_MC,A1_MC,A2_MC,A3_MC,A4_MC[,C0,C1,C2,C3,C4]

Required:
- Observed angular coefficients (A*_obs) and MC reference (A*_MC).
Optional:
- Per-coefficient sensitivity kernels C0..C4.
- Per-measurement statistical uncertainties: dA0 ... dA4 (if included, fitter will use them; else it estimates σ_i from sample variance of residuals).

Model & Fit
We minimize:
χ²(ε) = Σ_{events,i} [ (A_i^obs − A_i^MC − ε C_i)² / σ_i² ]

Solution:
ε_best = (Σ residual_i * C_i / σ_i²) / (Σ C_i² / σ_i²)

Uncertainty:
σ(ε) = 1 / sqrt(Σ C_i² / σ_i²)

Permutation test:
- Shuffle run/LB labels or residual pairing N times (default 500) to obtain p_global (look-elsewhere guard).

Outputs (JSON):
{
  "epsilon_best": ...,
  "epsilon_uncert": ...,
  "chi2": ...,
  "ndof": ...,
  "chi2_red": ...,
  "p_global": ...,
  "per_run": { run_number: { "n_points": ..., "residual_mean": ... } },
  "config": { ... }
}

Result Classes (LUFT convention):
- bound: p_global ≥ 0.10 or |ε_best| < 1σ
- candidate: p_global < 0.05 but unstable across runs (run spread > threshold)
- signal-quality: p_global < 0.01, stable run-by-run, |ε_best| ≥ 2σ

Usage:
python3 scripts/atlas_angles_coherence_fit.py --input angles.csv --output angles_epsilon.json
Optional flags:
--permutations 1000 --seed 42 --use-errors
--require-kernels (forces kernels presence; else fallback to unity)
--runs-column run --lb-column lb

Next Steps:
1. Generate angles.csv via ATLAS Open Data tutorial (uproot reading muon pairs, compute Collins–Soper coefficients).
2. Run fitter, inspect ε_best and p_global.
3. Integrate ε_coh into time modulation capsule (compare with χ(Ω) maxima).
4. Refine kernels C_i from theory (e.g., parton-level sensitivity) to reduce systematic dilution.

Confounders & Mitigations:
- Incomplete MC normalization → provide scaled A_i_MC from matched kinematics.
- Luminosity-dependent acceptance → include lumi column and weight (future extension).
- Run-dependent detector conditions → examine per-run residual stability.

End Capsule.
