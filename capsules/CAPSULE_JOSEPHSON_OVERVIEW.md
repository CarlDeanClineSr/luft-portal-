```markdown
# Capsule: Josephson Junction — Physics Overview & LUFT Relevance (CAPSULE-JJ-007)

id: CAPSULE-JJ-007
title: Josephson Junction — Physics Overview & LUFT Relevance
authors: Dr. Carl Dean Cline Sr. (CarlDeanClineSr)
date: 2025-11-11
tags: experiment;jj;metrology;mqm;priority-high
status: draft

summary:
  The Josephson effect (theoretical prediction, 1962) shows coherent, dissipationless transfer of Cooper‑pair current between superconductors through an insulating barrier. This capsule summarizes the core equations (DC/AC Josephson relations), the MQT escape framework, and why Josephson junctions are a high‑gain metrological channel for detecting LUFT foam modulations f (Δρ/ρ).

key_equations:
  - Josephson current:     I_s = I_c sin(Δφ)
  - AC Josephson relation: d(Δφ)/dt = (2e/ħ) V  ⇒  f = (2e/h) V
  - Josephson energy:      E_J = ħ I_c / (2e)
  - Tilted washboard barrier: ΔU(γ) = 2 E_J [ √(1 − γ^2) − γ arccos γ ],  with γ = I/I_c
  - Plasma frequency:      ω_p0 = √(2e I_c / ħ C)
  - WKB exponent (quantum escape): B ≈ (36/5) ΔU / (ħ ω_p)
  - Escape rate (quantum): Γ ≈ A exp(−B),  A ≈ ω_p/(2π) (prefactor, damping dependent)

evidence & references:
  - Classic: Brian D. Josephson (1962) — theoretical paper; Nobel Prize 1973
  - MQT experiments: numerous JJ switching studies (see collapse_demo_notebook_5.ipynb)
  - LUFT repo: /notebooks/collapse_demo_notebook_5.ipynb, /src/collapse.py, /capsules/CAPSULE_JJ_AUDITOR.md

LUFT relevance (why this matters)
  - Josephson junctions convert tiny parameter shifts (E_J, C) into exponential changes in Γ. If LUFT foam modulates local parameters (EJ→EJ(1+f)), the junction's switching statistics provide a laboratory window to measure f with high sensitivity.
  - The AC Josephson frequency–voltage relation links energy scales to precise frequencies (useful for calibration against LUFT frequency atlas).
  - MQT dynamics bind laboratory superconducting devices to the LUFT metrology story: they are a bridge from micro foam hypotheses to reproducible measurements.

minimal_repro_steps (quick)
  1. Open /notebooks/collapse_demo_notebook_5.ipynb and run the synthetic MQT cells to reproduce Γ(I) and injection tests.
  2. Use /scripts/jj_fit_likelihood.py (or the notebook) to perform an MLE for f from switching histograms.
  3. Report f̂ ± σ_f and check robustness across ramp rates and two temperatures (T_low ≪ T* and T_high > T*).

notes_and_caveats:
  - Maintain T << T* for quantum-dominated escape; above the crossover thermal activation can mask the signal.
  - Carefully model prefactors and damping (Q) to avoid attributing prefactor shifts to f.
  - Always report data provenance (device, Ic, C, ramp rate r, and filtering).

contact:
  - Open an issue with label `experiment:jj` to request equipment specs, raw I_sw data, or run parameters.
```
