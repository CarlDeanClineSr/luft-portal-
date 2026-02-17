# Capsule 009 — Λ(t) DESI Bridge

Objective
Bound or detect a small temporal modulation in the cosmological term using DESI time-stamped redshift residuals:
Λ(t) = Λ0 · [1 + χ · cos(Ω t)]
We test whether the same Ω, χ scale found in micro domains (tone/JJ) improves DESI residuals beyond chance.

Imperial v1 lines
R0 (claim)
- redshift_residual = z_obs − z_LCDM                                 [audit: residual OK]
- drift_component = χ by cos(Ω by t)                                  [audit: modulation OK]
- redshift_model = z_LCDM + drift_component                           [decision OK]

R1 (alternate)
- drift_component_v1 = χ_c by cos(Ω t + φ) + χ_s by sin(Ω t + φ)      [audit: two-phase basis]
- window_correction = LS_window(t, Ω)                                  [audit: spectral window]

R2 (audit)
- Dimensional/units OK (dimensionless residuals)
- Null controls:
  - shuffled-time null (permute t): χ_null distribution
  - block bootstrap (night/week blocks) to respect cadence
  - spectral window: report leakage at Ω and sidebands
- Diagnostics:
  - amplitude χ_hat, conservative χ_95
  - residual RMS reduction ΔRMS vs base
  - p-value vs null χ distribution

R3 (decision)
- Adopt bound if χ_95 < 0.01 at Ω (target); else report χ_95 and ΔRMS, track for follow-up.

Model & cadence notes
- Use two-parameter cosine/sine basis to absorb phase uncertainty.
- Observational cadence induces spectral leakage; compute and report the Lomb–Scargle window power at Ω and ±ΔΩ sidebands.
- If multi-instrument timestamps exist, fit per-instrument, then meta-analyze (inverse-variance).

Data expectation (see schema doc)
- Table with: time_utc (ISO8601), t_s (seconds since epoch or survey start), residual (dimensionless), z (optional), target_id (optional), instrument/site (optional).

Acceptance criteria
- Primary: χ_95 < 0.01 at Ω ≃ 2π·10^−4 Hz (v1 cross-domain Ω); report sensitivity to Ω grid ±10%.
- Secondary: ΔRMS improvement beyond shuffled-time 95% envelope; report (ΔRMS, p_null).

Outputs
- results/desi/capsule_009_summary.json:
  { "omega_hz": Ω, "chi_hat": ..., "chi_95": ..., "delta_rms": ..., "p_null": ..., "n": N }
- results/desi/diagnostics.md:
  - R0→R3 block
  - LS spectra of residual and window
  - Null distributions (χ, ΔRMS)
  - Decision and bound

Caveats
- Systematics (zero-point drifts, environmental correlations) can mimic χ; include covariates if available (airmass, seeing, CCD temperature) and test robustness by regression residualization.
