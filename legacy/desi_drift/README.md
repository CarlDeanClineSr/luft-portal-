# Capsule 009 — DESI Λ(t) Drift Runner

Purpose
Estimate and bound a small temporal modulation in the cosmological term:
Λ(t) = Λ₀ · [1 + χ · cos(Ω t)]
using DESI‑style time‑stamped redshift residuals. This runner fits χ at a target Ω (cross‑domain candidate ≈ 2π·10⁻⁴ Hz), performs null controls, optional bootstrap CIs, window diagnostics, and emits a clean R0→R3 decision summary.

Prereqs
- Python 3.9+; numpy, pandas
- astropy (optional; enables spectral window metrics via Lomb–Scargle)

Input schema
- CSV columns (required): 
  - t_s (float): seconds since reference epoch (runner centers time internally)
  - residual (float): dimensionless redshift residual (z_obs − z_LCDM), or normalized proxy
- Optional:
  - group_id (string/int): night/week block for block‑aware bootstrap
  - time_utc, instrument, site, target_id, z, airmass, seeing, temp
- See docs/data_schemas/DESI_residuals_schema.md

Quick start
- Synthetic sanity (already available):
  - python -m analyses.desi_drift.desi_synth
  - Writes data/synthetic/desi/desi_residuals_synth.csv
- Real/public CSV run (basic):
  - python -m analyses.desi_drift.runner --csv data/desi/residuals.csv --omega 1e-4 --K 500
- With detrend + bootstrap + Ω scan:
  - python -m analyses.desi_drift.runner --csv data/desi/residuals.csv --omega 1e-4 --K 2000 --bootstrap 10000 --detrend --omega-scan
- Block‑aware bootstrap (if CSV has group_id):
  - python -m analyses.desi_drift.runner --csv data/desi/residuals.csv --omega 1e-4 --K 2000 --bootstrap 10000 --block-key group_id

CLI flags
- --csv PATH            Input CSV (t_s,residual; optional group_id)
- --omega FLOAT         Test frequency Ω (Hz); default 1e-4
- --K INT               Shuffled‑time null iterations; default 500
- --bootstrap INT       Bootstrap resamples for CI (0 to skip)
- --block-key NAME      Use this column for block‑aware bootstrap (e.g., group_id)
- --detrend             Fit also with linear detrend (report raw & detrended)
- --omega-scan          Scan Ω in ±10% (11 points)
- --outdir PATH         Output dir (default results/desi)

Outputs
- results/desi/capsule_009_summary.json
  - input_path, input_sha256, n
  - omega_hz
  - chi_hat_raw, chi_95_raw, delta_rms_raw, p_null_raw, chi_null_mean_raw
  - chi_hat_detrended, chi_95_detrended, delta_rms_detrended, p_null_detrended (if --detrend)
  - bootstrap_raw {chi_05, chi_50, chi_95}; bootstrap_detrended (if --bootstrap & --detrend)
  - window_power {omega_hz, power, sidebands, n_eff, gap_stats}
  - omega_scan [{omega_hz, chi_hat, chi_95}] (if --omega-scan)
  - accept_bound_v1 (bool decision)
- results/desi/diagnostics.md
  - R0→R3 block, parameter table, null χ histogram summary, ΔRMS vs null, Ω scan, window metrics, provenance

Acceptance criteria (v1)
- Primary: χ_95 < 0.01 at Ω ≈ 2π·10⁻⁴ Hz and p_null < 0.05 (raw); adopt bound
- Otherwise: track (log χ_95, p_null, ΔRMS; note alias/covariates)

Method notes
- Phase‑invariant two‑parameter fit: residual(t) = a cos(2πΩ t) + b sin(2πΩ t); χ̂ = √(a² + b²)
- Optional linear detrend: report both raw and detrended fits
- Bootstrap CI: plain or block‑aware (if group_id); default 10k resamples recommended
- Spectral window: Lomb–Scargle on sampling pattern; report power at Ω, ±10% sidebands, N_eff, gap stats
- Ω scan: stability check across ±10%

Troubleshooting
- Empty outputs or NaNs: check column names (t_s,residual), sufficient N
- p_null ~ 0.5 and small ΔRMS: likely null; consider more K, detrend or covariates
- Unstable Ω scan & strong sidebands: aliasing; note open audit and consider alternate Ω or window corrections
- Units: ensure t_s in seconds; large magnitude values can harm conditioning (runner centers time internally)

Provenance & audit
- JSON includes input SHA256; diagnostics.md records the exact command context
- Keep CSVs small/public for reproducibility; document the reference epoch
