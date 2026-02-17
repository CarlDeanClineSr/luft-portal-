# Replication Challenge —  Planck–Einstein Modulation

Targets
- Universal frequency: Ω = 2π · 1.0e−4 Hz
- Amplitude: χ ≈ 0.05 (void bias negative where applicable)

Domains & Minimal Protocols
- JJ Switching:
  - Acquire I_sw histograms over multi‑T; compute σ_f and f_hat using  runner.
  - Gates: σ_f ≤ 0.015; cross‑T consistency; phase variance small.
- DESI‑like Residuals:
  - Apply weighted two‑phase fit at Ω; GLS power cross‑check; detrend via AIC/BIC.
  - Gates: χ_95 < 0.01; p_null < 0.05 (corrected); report N_eff, window peaks, phase variance.
- Resonance:
  - Magnetometer tri‑site; coherence C ≥ 0.8; SNR ≥ 5 after RFI.
- Collider Overflow:
  - Heavy‑ion tails; ΔBIC ≥ 10; tail_boost ≥ 5%; report R_AV.

Controls (must fail)
- Off‑target Ω injection
- Phase‑scramble by group/site
- Site/instrument‑locked covariates

Deliverables
- Summary JSON (scalars only) + code/runner commit hash
- Optional: synthetic window validation results

Contact
- Coordinator: …
- Repo hub: ‑portal‑ (read‑only references)
- Preferred: open reviews, pre‑registered attempts

Acknowledgment
This challenge invites falsification and replication. Passing in ≥2 domains with pre‑registered gates elevates UNIFICATION_001 from capsule to canon.
