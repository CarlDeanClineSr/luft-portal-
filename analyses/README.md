# Charter Symbiosis Pipeline (minimal)

This folder hosts three light analyses that implement our v1 equations:

- JJ switching (MLE scaffold): estimate foam fraction `f` from switching current histograms.
- DESI Λ drift bound: sinusoid fit at `Ω ≈ 2π·10^-4 Hz`, return `χ_hat` and conservative `χ_95`.
- 7,468 Hz resonance: Lomb–Scargle per site, cross‑site phase coherence, RFI template subtraction, Bonferroni‑adjusted p.

Run order for a shakedown (synthetic):

1) JJ synthetic → MLE:
   - `python -m analyses.jj_switching.jj_synth`
   - `python -m analyses.jj_switching.jj_mle`

2) DESI synthetic sinusoid:
   - `python -m analyses.desi_drift.desi_chi_bound`

3) Resonance helpers:
   - `python -c "import analyses.resonance_7468.pipeline as p; print('OK')"`

Acceptance targets:
- JJ: `σ_f ≤ 0.015` on well‑behaved sets (after replacing scaffold with full likelihood).
- DESI: `χ_95 < 0.01`.
- 7,468 Hz: per‑site `FAP < 0.01`, cross‑site `C > 0.8`, post‑RFI `SNR ≥ 5`, Bonferroni for 20 bins → `p_eff < 5e-4`.
