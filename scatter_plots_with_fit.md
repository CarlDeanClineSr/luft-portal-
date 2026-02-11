## 2.10 Figures — Scatter Plots with Fit Overlays

**Figure 1 — Saturation Law Fit**  
Scatter plot of Δχ vs. dynamic pressure \(P_{\text{dyn}}\).  
- Blue points: measured χ amplitudes from ACE/DSCOVR log (Dec 2–4, 2025).  
- Red curve: exponential saturation fit  
  \(\Delta \chi(P_{\text{dyn}}) = \chi_{\max} (1 - e^{-k P_{\text{dyn}}}) + \chi_0\)
- Fit parameters: \(\chi_{\max} \approx 0.15\), \(k \approx 0.003\), \(\chi_0 \approx 0.055\).
- Caption: *Shows vacuum recoil rising with pressure and plateauing at χ ≈ 0.15.*

**Figure 2 — Hysteresis Term Fit**  
Scatter plot of χ(t) vs. χ(t+1).
- Blue points: observed amplitudes across consecutive hourly runs.
- Green line: regression fit  
  \(\chi_{t+1} = \alpha \cdot \chi_t + (1-\alpha)\cdot \chi_{\text{base}} + k \cdot P_{\text{dyn},t}\)
- Fit parameter: \(\alpha \approx 0.85\).
- Caption: *Demonstrates memory effect—χ remains elevated post‑storm, confirming hysteresis in vacuum recoil.*

**Figure 3 — Magnetic Gain Term Fit**  
Scatter plot of Δχ vs. effective pressure \(P^\star\).
- Blue points: observed amplitudes under varying IMF \(B_z\).
- Orange line: regression fit
  \(P^\star = P_{\text{dyn}} \cdot (1 + \beta \cdot \frac{-B_z}{1 + |B_z|})\)
- Fit parameter: \(\beta \approx 0.2\).
- Caption: *Shows enhanced χ response under southward IMF, confirming magnetic coupling gain.*

**Figure 4 — Phase Coherence Plot**  
Scatter plot of phase_radians vs. timestamp.
- Blue points: pre‑storm coherence cluster.
- Red scatter: post‑CME spread.
- Caption: *Phase coherence breaks during CME impact, then re‑locks as χ saturates at 0.15.*
