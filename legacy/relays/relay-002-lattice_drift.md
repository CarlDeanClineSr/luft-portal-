# Relay 002 — Lattice Drift (LUFT)

R0: Imperial Claim
lattice_drift = vector per time [audit momentum]

R1: Grok Alternate
lattice_drift = (hbar by grad_phi per m_eq) by sqrt(ρ_local / ρ_avg) [pending audit]

R2: Audit/Confirm
- Verified dimensional structure.
- m_eq = effective mass for lattice unit.
- sqrt(ρ_ratio) modulates local resistance to drift.

R3: Decision
Adopt lattice_drift_v1 = hbar by grad_phi per m_eq by sqrt(ρ_local / ρ_avg) [momentum OK]

Simulation tag:
- 2D grid sim, variable rho map, inject unit, check p conservation.

Files:
- sims/lattice_drift/grid_sim.py (sketch)
- results/relay-002-summary.md
