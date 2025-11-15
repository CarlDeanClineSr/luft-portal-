# Capsule: CERN Mode — ATLAS Open Data LB-level Ω-Scan and ε_coh Fit

Purpose: Adapt the flux→coherence framework to ATLAS Open Data: time-binned (lumiblock-level) observables, scanning modulation frequencies Ω ∈ [1e−5, 1e−3] Hz and fitting a LUFT-like coherence parameter ε_coh across runs.

Data & Selections:
- Channels: Z→μμ (stable), Z→ee (cross-check)
- Binning: LB-level per-run, good-run-list filtered
- Corrections: luminosity and trigger prescales applied

Models:
- Time modulation: R(t)=R0[1+χ cos(Ω t+φ)] → scan Ω grid; permutation LB-shuffle (N=1000) for global p
- Coherence: A_i residual model A_i^obs = A_i^MC + ε_coh C_i; joint χ² across runs

Outputs:
- χ(Ω) spectrum with global max + null bands
- ε_coh best-fit with uncertainty; cross-run stability test

Next Steps:
1) Prepare LB CSV from ATLAS tutorials (ROOT via uproot) with columns {timestamp, rate, A_i, …}
2) Reuse fitter structure to estimate ε_coh with LB jitter J(t)
3) Report bound/candidate/signal-quality per LUFT convention
