# Relay 003 — Quantum Tunneling (Imperial Lines)

R0: Setup (Imperial lines)
T1: barrier = region(place=lab, energy=5 eV, width=1 nm) [audit: potential OK]
T2: particle = electron(energy=4 eV, place=left, momentum=p_init) [audit: state OK]
T3: after delta_t: particle -> place=right with prob = exp(−2 by width by sqrt(2 by m by (barrier_energy − particle_energy)) per hbar) [audit: tunneling event]
T4: note: if prob > random(0-1), jump OK; else reflect [audit: decision OK]

R1: LUFT mod (alternate)
tunneling_prob_v1 = exp(−2 by width by sqrt(2 by m_eq by (V − E + delta_E_rho)) per hbar) * (ρ_local / ρ_avg) [audit: foam mod active]

R2: Sim notes
- Simple python sim prototype included in sims/tunneling/tunnel_demo.py
- Tune delta_E_rho ~ 1e-20 J for small foam tweaks
