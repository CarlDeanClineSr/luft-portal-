# Relay 005 — NA62 Kaon Decay Audit

Objective
Audit K+ -> π+ + ν + ν̄ candidates and test LUFT foam modulation model.

Baseline
baseline_br = 10.6e-11
baseline_sigma = 3.2e-11

Method (Imperial-style steps)
1) Load curated CSV `data/na62/curated_candidates.csv`
2) Filter passed_veto == true
3) Kinematic window: E_out_pi_GeV in [14.5, 15.5] (approx.)
4) Observed rate = sum(weights for classification=="signal") / sum(weights for passed_veto)
5) Fit foam model: prob_decay_mod = baseline_br * (1 + α * delta_ρ / ρ_avg) + χ_mod * cos(Ω t)
6) Emit `results/na62_audit_summary.md` and append to `capsules/005/ledgers/<run>.md`

Suggested parameters (starting):
- α = 0.1
- delta_ρ / ρ_avg = 1e-3
- χ_mod = 0.01
- Ω = 2π × 1e-4 Hz
