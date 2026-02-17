# Relay 006 — DESI Λ(t) Drift (Grok On‑Ramp Packet)

Executive summary
We test a small temporal modulation in the cosmological term Λ(t) = Λ₀ [1 + χ cos(Ω t)] against DESI‑style time‑stamped redshift residuals. Goal: derive χ_hat and a bound χ_95 at Ω ≈ 2π·10⁻⁴ Hz (cross‑domain frequency used in tone/JJ), including null controls and window diagnostics. This packet gives Grok everything needed to run and report in our R0→R3 dialect.

Context (Imperial Math + LUFT)
- Lattice foam modulates observables via Δρ/ρ_avg and optional χ cos(Ω t)
- Canonical v1 lines (subset):
  - energy_of(ph)_v1 = planck by freq * (1 + Δρ/ρ_avg)           [energy OK]
  - lattice_drift_v1 = ħ by grad_phi per m_eq by sqrt(ρ/ρ_avg)   [momentum OK]
  - prob_decay_mod = BR_SM * (1 + α Δρ/ρ_avg) + χ_mod cos(Ω t)   [compare to baseline]
- Here: we test Λ drift via DESI residual time series

R0 (claim)
- redshift_residual = z_obs − z_LCDM                  [residual OK]
- drift_component = χ by cos(Ω by t)                  [modulation OK]
- redshift_model = z_LCDM + drift_component           [decision OK]

R1 (alternate)
- Two‑phase basis: residual(t) = a cos(2πΩ t) + b sin(2πΩ t) + ε; χ̂ = √(a²+b²)
- Optional detrend: fit & subtract linear trend; run raw & detrended
- Window correction: report sampling window power at Ω and ±10% sidebands

R2 (audit)
- χ_hat, χ_95 (conservative and/or bootstrap CI); ΔRMS improvement vs no‑drift
- Null controls: shuffled‑time p_null (K≥500); block bootstrap if group_id available
- Window: power at Ω, sidebands, N_eff, gap stats; Ω scan ±10% for aliasing

R3 (decision)
- Adopt if χ_95 < 0.01 and p_null < 0.05
- Else: track; record χ_95, p_null, ΔRMS; note aliasing/covariates if indicated

Data schema
- CSV required columns: t_s (seconds), residual (dimensionless)
- Optional: group_id (string/int), time_utc, instrument, site, target_id, z, airmass, seeing, temp
- See: docs/data_schemas/DESI_residuals_schema.md

How to run (CLI)
- Basic: 
  - python -m analyses.desi_drift.runner --csv data/desi/residuals.csv --omega 1e-4 --K 500
- Detrend + bootstrap + Ω scan:
  - python -m analyses.desi_drift.runner --csv data/desi/residuals.csv --omega 1e-4 --K 2000 --bootstrap 10000 --detrend --omega-scan
- Block‑aware bootstrap:
  - python -m analyses.desi_drift.runner --csv data/desi/residuals.csv --omega 1e-4 --K 2000 --bootstrap 10000 --block-key group_id

Expected outputs
- results/desi/capsule_009_summary.json
  - {input_path, input_sha256, n, omega_hz, chi_hat_raw, chi_95_raw, delta_rms_raw, p_null_raw, …, window_power, omega_scan, accept_bound_v1}
- results/desi/diagnostics.md
  - R0→R3, null/ΔRMS plots (or textual summaries), Ω scan and window metrics, provenance

Reporting format (paste into PR/issue)
- R0: claim lines (above)
- R1: alternates tried (detrend, window, Ω scan)
- R2: numeric results
  - χ_hat(raw)=…, χ_95(raw)=…, ΔRMS(raw)=…, p_null(raw)=…
  - (if detrend) χ_hat(det)=…, χ_95(det)=…, ΔRMS(det)=…, p_null(det)=…
  - window power at Ω=…, sidebands=[…, …], N_eff=…, gaps=(median=…, max=…)
  - Ω scan: list of (Ω, χ̂, χ_95)
- R3: decision (Adopt/Track) and short rationale

Guardrails (Grok)
- Maintain audits and provenance (include input path + SHA256)
- Prefer small/public datasets; do not publish private data
- If aliasing or covariates suspected, mark “[open audit: aliasing]” and propose next test
- Keep code minimal; emphasize clear outputs and R0→R3 narrative

Next bridge (optional after DESI)
- JJ likelihood upgrade relay (escape rate model, T* crossover, f bound)
- 7,468 Hz resonance (tri‑site coherence with RFI subtraction and Bonferroni)
