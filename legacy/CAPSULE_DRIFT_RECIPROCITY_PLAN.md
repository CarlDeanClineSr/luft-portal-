# Capsule: Drift Reciprocity & Energy Conservation Test

## Purpose
Establish parameter ranges (α, q, λ, η_damp) where hierarchy amplification does not produce unphysical energy runaway during solar proton forcing.

## Method
1. Input f(t) from solar proton mapping.
2. Compute f_h(t) and ln Γ(t).
3. Simulate reciprocity update over sliding windows:
   f_{n+1} = f_n + λ (v_d/v_ref - 1) - η_damp f_n.
4. Track Lyapunov exponent λ_L via divergence of two close initial values f0, f0+δ.
5. Reject sets where energy_ratio > 0.4 or λ_L > 0.

## Outputs
results/reciprocity_param_scan.json  
figures/reciprocity_stability_map.png

## Pass Criteria
Stable_flag = true; energy_ratio ≤ 0.4; |f| bounded within initial ±3× range.
