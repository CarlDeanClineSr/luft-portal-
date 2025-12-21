# CORE_OBJECTIVE_v1 — LUFT Inference Engine Directive

**Scope:** Binding forces across micro-macro scales; unthought-of relations via cross-correlation and constrained fits.  
**Status:** ENGINE_CONSTITUTION (immutable unless amended by audit).

## Primary Objective
The LUFT engine is a law-collider for field dynamics. Input any structured dataset (plasma, foam, quantum tunnels, orbital, indices). Output:
- Fitted invariants or relations (e.g., rebound rate vs. beta/Mach).
- Anomalies or deviations from directives.
- No free parameters—constrain to known laws (χ cap = 0.15, recoil conservation).

## Directives (Immutable)
1. **Saturation Bounds**: Amplitude/modulation caps at 0.15; floors ~0.04–0.06. Test for breaches or shifts.
2. **Recoil Conservation**: Dips followed by rebound; measure rate R = Δχ / Δt, correlate with drivers (pressure, beta, Mach, E-field).
3. **Cross-Scale Binding**: Micro (alpha/proton, fluxes) to macro (Dst, AE, Kp)—hunt relations (e.g., χ lock predicts Dst drop).
4. **Unthought-of Detection**: Flag new angles (e.g., quasi-invariant #32 modulates χ by >0.001).
5. **Output Format**: Fitted equations (e.g., R = k * β^{-α}), matrices, logs—archive in results/.

## Engine Hooks
- Input: data/extended_heartbeat_log_YYYY.csv (OMNI2/NOAA merged).
- Processing: ml/rebound_pipeline.py, src/fractal_foam_engine.py.
- Workflow: Daily fits, hourly anomaly checks.

Amend only via audit (CAPSULE_AUDIT_LOG.md).
