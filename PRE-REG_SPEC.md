#  Pre‑registration (Lite) — Fixed Analysis Manifest

Purpose
Freeze target frequency, filters, weighting, and decision thresholds before any reveal, then publish this file’s SHA256 hash. On unseal, show the same file; the hash proves no “tuning drift.”

Scope
- Domain(s): DESI Λ drift residuals; JJ escape rates; Resonance; Collider overflow (if applicable)
- Target frequency: Ω = 2π · 1.0e−4 Hz
- Frequency scan: ±10% around Ω with resolution δΩ = 1/T (Rayleigh width), step ≤ 0.5 δΩ
- Detrend options: {none, linear, quadratic}; select by AIC/BIC; record selection
- Weights: inverse‑variance if per‑point σ available, else unweighted; robust option via Huber
- Cross‑check: Generalized Lomb–Scargle (GLS) power at Ω and local neighborhood
- Window: report top 5 window peaks in [0.8Ω, 1.2Ω]; list daily/sidereal/lunar aliases if present
- Nulls:
  - Shuffled‑time null (≥ 2,000 shuffles)
  - Block bootstrap preserving gaps (≥ 10,000 draws)
  - Adversarial controls: off‑target Ω injection; phase‑scramble by group; site/instrument‑locked signals
- Phase coherence: report group‑wise phase and variance after timebase normalization
- Multiple testing: Bonferroni/Holm if >1 tested frequency
- Decision gates:
  - DESI: χ_95 < 0.01 and p_null < 0.05 (corrected)
  - JJ: σ_f ≤ 0.015 (multi‑T consistency)
  - Resonance: C ≥ 0.8 and SNR ≥ 5 (post‑RFI)
  - Collider: ΔBIC ≥ 10 and tail_boost ≥ 5%
  - Cross‑domain: consistent R_AV slope sign in ≥2 domains, p_null < 0.05

Outputs (no raw data)
- Scalars: χ_hat, χ_95, p_null, ΔRMS, N_eff, Rayleigh width, top window peaks, phase variance
- Hash: SHA256(PRE-REG_SPEC.md)

Sign
- Author: …
- Date: …
- SHA256: …
