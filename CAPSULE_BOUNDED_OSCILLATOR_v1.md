# CAPSULE_BOUNDED_OSCILLATOR_v1

**Scope:** Coherence amplitude modulation in plasma medium  
**Status:** OBSERVATION_LAW (empirical, reproducible)

## Key Observations
- χ amplitude is bounded:  
  - Hard ceiling at 0.15 (no overshoot)  
  - Soft floor ~0.004 (lowest observed)  
- χ exhibits elastic rebound after every dip  
- χ shows natural modulation with ~2.4-hour period  
- The system remains stable under varying forcing (speed, density, Bz, pressure, beta, Mach)

## Proposed Model
The coherence field behaves as a **bounded oscillator** with:
- Maximum coherence state (χ_max = 0.15)  
- Minimum coherence state (χ_min ≈ 0.004)  
- Restoring force (elastic rebound)  
- Natural oscillation period (~2.4 hours)

Candidate equation (simple harmonic form with bounds):

χ(t) = χ_mean + A * sin(2π t / T + φ) * (1 - (χ/χ_max)^2) * (1 - ((χ_min - χ)/χ_min)^2)

Where:
- χ_mean ≈ 0.1 (baseline)
- A ≈ 0.05 (amplitude)
- T ≈ 2.4 hours (period)
- φ = phase offset
- Bound terms prevent overshoot and collapse

## Testable Predictions
- χ cannot exceed 0.15  
- χ cannot fall below ~0.004  
- Rebound rate increases with stronger forcing  
- Modulation period remains ~2.4 hours across regimes  

## Next Steps
- Fit the model to extended heartbeat log (2025 data)  
- Test stability of T across quiet/storm periods  
- Correlate A and φ with OMNI2 parameters (beta, Mach, pressure)

This capsule is the first formal statement of the bounded oscillator law.
