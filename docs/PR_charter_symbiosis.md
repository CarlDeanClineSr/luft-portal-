# Charter Symbiosis Pipeline — end‑to‑end synthetic + exemplar validation

This PR adds a minimal, readable pipeline to validate our adopted LUFT v1 equations across three domains:
- JJ foam auditor (switching histograms → f̂, σ_f)
- DESI Λ drift bound (χ at Ω ≈ 2π·10⁻⁴ Hz)
- 7,468 Hz resonance protocol (Lomb–Scargle, cross‑site coherence, RFI subtraction, Bonferroni)

Key files:
- analyses/jj_switching/jj_synth.py — synthetic I_sw generator
- analyses/jj_switching/jj_mle.py — scaffold MLE (mean‑shift proxy; replace with full switching likelihood)
- analyses/desi_drift/desi_synth.py — synthetic DESI‑like residuals
- analyses/desi_drift/desi_chi_bound.py — amplitude fit and χ_95 bound
- analyses/resonance_7468/synth_tri_site.py — synthetic tri‑site time series
- analyses/resonance_7468/pipeline.py — LS per‑site, phase coherence, RFI projection
- analyses/common/io.py — tiny CSV/NPY helpers
- scripts/run_charter_pipeline.py — orchestrates all three analyses and prints acceptance checks

Acceptance criteria (v1):
- JJ foam auditor: σ_f ≤ 0.015 on well‑behaved synthetic (after replacing scaffold with full likelihood)
- DESI drift: χ_95 < 0.01 at Ω = 2π·10⁻⁴ Hz on synthetic with χ_true≈0.008
- 7,468 Hz: per‑site FAP < 0.01, cross‑site coherence C > 0.8, post‑RFI SNR ≥ 5; Bonferroni for 20 bins ⇒ p_eff < 5×10⁻⁴

Notes:
- The JJ MLE here uses a mean‑shift proxy for speed; the file is structured so the inner likelihood can be swapped for a full switching‑rate model (Caldeira–Leggett corrected).
- DESI drift bound includes a conservative amplitude bound; production should include cadence/window modeling.
- Resonance pipeline includes a crude RFI projection (template regression) and a simple DFT‑based coherence check.

Run (synthetic shakedown):
```
python -m scripts.run_charter_pipeline
```

Outputs print to stdout with PASS/FAIL checks and small JSON summaries under `results/charter/`.
