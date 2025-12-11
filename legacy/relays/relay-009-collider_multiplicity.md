# Relay 009 — Heavy-Ion Multiplicity Tails (Foam Mixture Audit)

Objective
Test whether LUFT foam modulation improves the description of high-multiplicity tails in heavy-ion (Pb+Pb) collisions, beyond a single Negative Binomial (NB) baseline.

Imperial v1 (claims)
- multiplicity_base_v1 = NB(k, p)                                              [count OK]
- multiplicity_foam_v1 = NB(k', p') by exp(−κ |f|)                              [count OK, foam mod active]
- multiplicity_mix_v1 = w by multiplicity_base_v1 + (1 − w) by multiplicity_foam_v1  [decision OK]
- foam_hierarchy_v1 = f_h = exp(α by log(M_raw per M_ref)) by f                 [unitless OK]
- M_map_v1 = M_obs = M_0 by (1 + γ by f_h) by exp(−κ |f|)                       [unitless OK]

Data (public, proxies)
- ATLAS Open Data Pb+Pb 5.02 TeV (Run 2) DAOD/xAOD-style multiplicity proxies; or CMS open sets. Start with event-level track counts (|η| and pT thresholds per dataset docs), centrality bins, and quality masks.
- Synthetic path allowed if public access is delayed; replace with real once available.

Method
1) Build multiplicity histogram H(M) with stable binning (e.g., ΔM = 5).
2) Fit NB(k,p) baseline (MLE or MoM) → L0, BIC0.
3) Fit mixture NB + NB' with parameters (w, k, p, k', p'), plus optional f-mod map via M_map_v1:
   - Option A (pure mixture): no M_map; two NB components
   - Option B (foam map): reparameterize NB' mean via f, f_h, (γ, κ, α) and M_ref (e.g., 150)
   Compute L1, BIC1; Bayes factor via ΔBIC = BIC0 − BIC1.
4) Tail stability:
   - Refit under rebinning (ΔM = 3, 10) and truncated fit windows (exclude M < 60).
   - Report tail boost: ⟨M_obs⟩_tail / ⟨M_base⟩_tail − 1 for M > M_ref.
5) Cross-checks:
   - Centrality slices
   - KNO scaling residuals (M / ⟨M⟩ histogram shape)
   - Bootstrap confidence for w and tail boost.

Acceptance (v1)
- Evidence for foam mixture if:
  - ΔBIC ≥ 10 (strong) and
  - P(foam component > 0) ≥ 0.7 and
  - Tail boost ≥ 5% stable under rebinning and centrality slice shifts.
- Otherwise TRACK with bounds on (w, γ, κ, α).

Outputs
- results/collider/relay009_summary.json:
  { "k":..., "p":..., "k2":..., "p2":..., "w":..., "gamma":..., "kappa":..., "alpha":..., "M_ref":..., "delta_BIC":..., "tail_boost":..., "stability": { "rebin":..., "window":... } }
- results/collider/diagnostics.md:
  - R0→R3 block, fit residuals, KNO plots, rebin/window stability, centrality slice table.

R0→R3
- R0: claims above; dataset + selection summary
- R1: alternates (pure mixture vs foam map; different M_ref; KNO-constrained NB)
- R2: fits, ΔBIC, stability, bootstrap intervals
- R3: Decision (Adopt/Track) with numeric criteria

Notes
- Use Poisson–gamma NB parameterization; guard against overfit (BIC/AIC).
- Do not interpret time-sidebands (Ω ~ 10^-4 Hz) inside single-run collider spills; only consider run-to-run drifts with coherent scheduling metadata (TRACK aliasing by default).
