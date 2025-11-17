# Capsule 008 — Charter Coherence Bridge

Objective
Bridge micro coherence (tone drift @ 7,468 Hz, JJ tunneling, entanglement) with macro coherence (DESI/JWST drift, Λ phenomenology) under the same LUFT modulation parameters `(Δρ/ρ_avg, χ, Ω)`.

Imperial v1 (recap)
- `lattice_drift_v1 = ħ by grad_phi per m_eq by sqrt(ρ_local/ρ_avg) [momentum OK]`
- `tunneling_prob_v1 = exp(−2 by w by sqrt(2 m_eq (V−E+δE_ρ)) / ħ) * (ρ_local/ρ_avg) [foam mod active]`
- `prob_sync_v1 = 1 − |Δρ/ρ_avg| [decoherence active]`
- `prob_decay_mod = BR_SM * (1 + α Δρ/ρ_avg) + χ_mod cos(Ω t)`

Ledger (five fields + Foam Audit)
- Foam Audit fields: `delta_rho_over_rho_avg`, `chi_mod`, `omega_used`

Success looks like
- Recovered `(f, χ)` consistent across ≥2 micro domains and one macro domain within stated uncertainties.
- For resonance: multi‑site coherence `C>0.8`, per‑site `FAP<0.01`, SNR≥5 post‑RFI, Bonferroni p<5e-4.

Notes
- Trial factors and window functions must be reported.
- Use Poisson likelihood for low‑count channels (NA62), OLS/GLS with shuffles for DESI time series.
