# Collider Foam Mixture — Analysis Plan

Targets
- ATLAS/CMS open Pb+Pb data at 5.02 TeV. Start with event-level multiplicity proxies:
  - Charged tracks within |η|<2.5, pT>0.5 GeV (adjust per dataset doc).
  - Centrality bins (0–10%, …).
  - Quality masks (pileup/vertex/beam flags).

Steps
1) Synthetic validation:
   - Use analyses/collider/multiplicity_sim.py to create M_obs under known (w, k, p, k’, p’).
   - Fit NB baseline and NB+NB mixture. Verify ΔBIC recovery and tail boost stability.
2) Real data ingestion:
   - Use uproot/xAOD readers to build M per event arrays (document cuts).
   - Produce H(M) histograms and centrality-sliced sets.
3) Fitting:
   - Fit NB(k,p) → (k,p), BIC0.
   - Fit mixture (grid over w; alternating fits) → BIC1.
   - Compute ΔBIC = BIC0 − BIC1; bootstrap CIs for parameters.
4) Stability:
   - Rebin (ΔM 3,5,10); refit.
   - Truncated windows: exclude M < 60; refit.
   - Centrality slices refit; tabulate tail boost.
5) Reporting:
   - JSON summary + diagnostics.md per Relay 009 spec.

Caveats
- Time-sideband (Ω ≈ 10^-4 Hz) tests are NOT applicable within single spill; only compare across run periods with proper timing metadata.
- Guard against detector/trigger thresholds biasing tails; document selection.
