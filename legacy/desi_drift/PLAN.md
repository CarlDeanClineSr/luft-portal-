# DESI Λ(t) Drift — Analysis Plan (v1)

Goal
Estimate χ (and bound χ_95) in Λ(t) = Λ0 [1 + χ cos(Ω t)] using DESI-like residuals with timestamps.

Inputs
- CSV with columns:
  - t_s: seconds from reference epoch (float)
  - residual: dimensionless redshift residual (float)
  - (optional) group_id/instrument/site for block/bootstrap
- Ω: test frequency in Hz (default 1e-4); also scan ±10% to assess sensitivity.

Method
1) Two-phase fit:
   residual(t) = a cos(2πΩ t) + b sin(2πΩ t) + ε
   χ_hat = sqrt(a^2 + b^2)
2) Diagnostics:
   - Predict residuals; compute ε = y − y_hat; σ = std(ε)
   - Conservative χ_95 = χ_hat + 1.96 · σ / sqrt(N/2)
3) Null controls:
   - Shuffle times (permute t_s K times): get χ_null distribution, p_null = P(χ_null ≥ χ_hat)
   - Block bootstrap: resample by night/week blocks to preserve cadence; recompute χ_hat
   - Spectral window: LS on sampling pattern (unit samples at t_s); report window power at Ω
4) Report:
   - chi_hat, chi_95, p_null, ΔRMS vs base (no drift model), N
   - Sensitivity to Ω±10%, instrument subgroup analyses (if available)

Acceptance
- χ_95 < 0.01 → bound accepted at Ω
- If not, report chi_95 and ΔRMS with null envelopes; track Ω dependence

Files (suggested)
- desi_loader.py: load CSV, center t, return arrays
- desi_bound.py: fit + bound
- desi_null_tests.py: shuffled null, block bootstrap, window LS
- results/desi/: JSON + diagnostics.md
