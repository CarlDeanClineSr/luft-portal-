# Blinded Capsule Runner — Minimal I/O Contract

Goal
Allow external reviewers to execute the analysis on sealed data and publish only scalar outputs + a result hash.

Inputs
- Config (YAML/JSON) specifying:
  - omega_hz (fixed), scan window, detrend options, weights flag, null parameters
- Data access: sealed endpoint or local encrypted file; runner returns no raw series

Outputs (public)
- Scalars:
  - chi_hat, chi_95, p_null (corrected), delta_rms
  - N_eff, rayleigh_width, window_peaks (top 5), phase_variance
- Derived:
  - R_AV (boundary/bulk efficacy ratio) if applicable
- Hashes:
  - SHA256(result_payload.json)
  - Code version (git commit or container digest)

Protocol
1) Reviewer runs containerized runner with config.
2) Runner fetches sealed data, computes metrics, emits JSON + SHA256.
3) Reviewer posts only JSON + SHA256; no raw data leaves seal.

Falsification
- Off‑target Ω and phase‑scramble adversarial datasets must fail (high p_null, low chi_hat).
- On‑target synthetic must pass with chi_95 within ±10% of truth.

Security/Privacy
- No residuals, no per‑point dumps; only summary scalars and hashes.
