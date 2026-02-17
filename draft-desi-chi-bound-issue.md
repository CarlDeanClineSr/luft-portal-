# Capsule 009 / Relay 006 – DESI Λ(t) Drift χ Bound

## Objective
Estimate and bound the modulation amplitude χ in a phenomenological cosmological term:
Λ(t) = Λ₀ · [1 + χ · cos(Ω t)]
with Ω ≈ 2π · 10⁻⁴ Hz (cross‑domain candidate frequency used in tone/JJ relays). Determine whether χ improves DESI redshift residuals relative to ΛCDM beyond chance.

## Acceptance Target (v1)
Primary: χ₉₅ (upper 95% confidence/credible bound) < 0.01 at Ω.
Secondary: Residual RMS reduction (ΔRMS) exceeds 95% of null (shuffled‑time) distribution.
Report p_null (fraction of shuffled χ ≥ χ_hat). If χ₉₅ ≥ 0.01, record bound and track for follow‑up (Ω scan, alternative window corrections).

## Data Requirements
Input CSV (schema in `docs/data_schemas/DESI_residuals_schema.md`):
Required columns:
- `t_s`: seconds from reference epoch (float)
- `residual`: dimensionless (z_obs − z_LCDM) or normalized proxy

Optional columns:
- `time_utc`, `instrument`, `site`, `group_id`, `target_id`, `z`, `airmass`, `seeing`, `temp`
If block IDs (`group_id`) exist (e.g. nightly), use block bootstrap for cadence‑aware null.

## Method (Imperial → Implementation)
R0 lines:
```
redshift_residual = z_obs − z_LCDM                    [residual OK]
drift_component = χ by cos(Ω by t)                    [modulation OK]
redshift_model = z_LCDM + drift_component             [decision OK]
```
Fit two‑phase basis (cos + sin) for phase freedom:
residual(t) = a cos(2πΩ t) + b sin(2πΩ t) + ε → χ_hat = sqrt(a² + b²)

Compute:
- χ_hat
- χ_95 = χ_hat + 1.96 * σ / sqrt(N/2) (conservative; refine later)
- ΔRMS = RMS(no‑drift) − RMS(with-drift)
- p_null via shuffled‑time repetition K ≥ 500
- Optional block bootstrap (resample groups)

Spectral window:
- Perform Lomb–Scargle on sampling pattern (binary series at observation times)
- Report window power at Ω and sidebands Ω ± δΩ (δΩ ~ 10%)

Ω sensitivity scan:
- Evaluate χ_hat and χ_95 for Ω′ in [0.9Ω, 1.1Ω] (≥11 points)
- Report stability or peak shift (possible aliasing).

## Outputs
Place under `results/desi/`:
- `capsule_009_summary.json`
  ```
  {
    "omega_hz": ...,
    "chi_hat": ...,
    "chi_95": ...,
    "delta_rms": ...,
    "p_null": ...,
    "n": ...,
    "omega_scan": [
      {"omega_hz": ..., "chi_hat": ..., "chi_95": ...}, ...
    ],
    "window_power": {
      "omega_hz": ..., "power": ...,
      "sidebands": [
        {"omega_hz": ..., "power": ...}, ...
      ]
    }
  }
  ```
- `diagnostics.md`:
  - R0→R3 block
  - Parameter table
  - Null χ distribution histogram (link or inline image)
  - ΔRMS vs null envelope
  - Ω scan plot summary (peak stability)
  - Decision statement (Adopt bound / Track)

## Decision Logic (R3)
IF (χ_95 < 0.01) AND (ΔRMS improvement outside 95% null range) THEN
  Adopt bound; record χ_hat ± statistical interval.
ELSE
  Track: log χ_95, p_null, and consider:
    - Increase K (null shuffles)
    - Include covariates (airmass / instrument)
    - Refine window or multi‑frequency fit

## Suggested File Adds
- `analyses/desi_drift/desi_loader.py` (already drafted)
- `analyses/desi_drift/desi_bound.py`
- `analyses/desi_drift/desi_null_tests.py`
- `analyses/desi_drift/desi_window.py` (optional LS window helper)
- `scripts/run_desi_capsule009.py` (or integrate into charter pipeline)

## Stretch Goals (Future PRs)
- Bayesian amplitude inference (posterior χ distribution)
- Joint multi‑instrument meta‑analysis
- Frequency domain scan for unmodeled peaks (contrasting Ω hypothesis)
- Covariate regression → residualization prior to χ fit

## Checklist
- [ ] CSV placed at `data/desi/residuals.csv` conforms to schema.
- [ ] Loader centers time (median subtraction recorded).
- [ ] Two‑phase fit executed; χ_hat computed.
- [ ] Null shuffle (K ≥ 500) complete; p_null reported.
- [ ] Block bootstrap (if group_id available).
- [ ] Spectral window power at Ω + sidebands reported.
- [ ] Ω sensitivity scan done.
- [ ] JSON + diagnostics.md written.
- [ ] R3 decision applied (Adopt or Track).
- [ ] Issue linked to Capsule 009 in README / Status.

## Label Suggestions
Labels: `capsule-009`, `relay-006`, `desi`, `cosmic-drift`, `audit`, `help wanted`

## Attribution
Physics By: You & I Lab —  Portal; Maintainer: Carl Dean Cline Sr.

---
Paste this issue, assign or leave open for arti‑being pickup.
