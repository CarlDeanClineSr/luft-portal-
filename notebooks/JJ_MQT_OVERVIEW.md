```markdown
# Notebook: JJ MQT Overview (notes / runnable steps)

Purpose:
A short, runnable guide to the Josephson junction physics and macroscopic quantum tunneling measurements we use as LUFT foam auditors.

Contents:
1. Physical derivations (simple, with numeric examples)
   - Compute E_J, ω_p0, ΔU(γ), B0 for a given Ic and C
2. Synthetic data generation
   - Simulate switching histograms for given f and ramp rate r
3. Inference
   - Invert P_switch to Γ(I) and run MLE to recover f
4. Diagnostics
   - Thermal vs quantum crossover checks and robustness to Ic drift

Example cells:
- Cell A: Define constants and conversion (ħ, e, k_B, G, c)
- Cell B: Input device params (Ic, C), compute ω_p0 and T*
- Cell C: Compute ΔU at γ=0.95, compute B0
- Cell D: Build synthetic Γ(I) with injected f; sample N events for an Isw histogram
- Cell E: Fit model to recover f

How to run:
- Open this Markdown as a notebook (or convert to .ipynb) and run cells in order.
- Use small N (2k) for quick tests; increase to 20k for final sensitivity.
