# Charter Symbiosis Pipeline — How to run (synthetic)

This folder includes minimal, readable modules to validate our LUFT v1 equations:

- JJ switching (MLE scaffold) → f̂, σ_f
- DESI Λ drift bound at Ω ≈ 2π·10⁻⁴ Hz → χ_hat, χ_95
- 7,468 Hz resonance (tri‑site synthetic) → per‑site FAP, cross‑site coherence C, post‑RFI SNR

Quick start (synthetic):
```
python -m scripts.run_charter_pipeline
```

Acceptance targets (v1):
- JJ foam auditor: σ_f ≤ 0.015 on well‑behaved sets (replace scaffold with full likelihood later)
- DESI drift: χ_95 < 0.01 (Ω = 2π·10⁻⁴ Hz)
- 7,468 Hz: each site FAP < 0.01, C > 0.8, SNR ≥ 5, Bonferroni p_eff < 5×10⁻⁴ (on real data)
