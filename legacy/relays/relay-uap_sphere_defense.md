# Relay — UAP Sphere Defense/Deflection (Mechanism Audit)

R0 (claim)
- field_pressure_v1 = p_B = B by B per (2 by mu_0) [pressure OK]
- deflect_gate_v1 = reflect = sigmoid(k by (p_B − p_dynamic)) [decision OK]
- mass_drop_v1 = m_eq = m_0 (1 − δ |Δρ/ρ_avg|) [mass/energy note]
- lorentz_thrust_v1 = F = ∫ j by B sin(theta) dV [momentum OK]
- portal_mod_v1 = epsilon_eff = epsilon_0 by (1 + χ by φ) [EM response]

R1 (alternates)
- soft_barrier_v1 = reflect ≈ 1/(1 + exp(−kΔp)); asymmetry_v1 = reflect * (1 + η sign(dB/dt))
- sheath_radius_v1 ≈ sqrt(2 by mu_0 by P_plasma) per B  [audit: scale check]

R2 (audit)
- Dimensional checks OK (pressure, force).
- Predicted observables: RF notching/rotation; magnetometer spikes (10–1000 nT, short range); optical ion lines; thermal annulus.
- Deflection threshold: p_B > p_dynamic ≈ 0.5 ρ_air v^2 (or local blast overpressure).

R3 (decision)
- Adopt test plan: vacuum‑plasma bounce + EM scattering + magnetometer co‑logging. Track mass_drop_v1 as LUFT parameter; portal_mod_v1 as EM surrogate.
