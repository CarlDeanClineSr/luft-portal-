# 📑 Capsule Insert — Saturation & Hysteresis Law

## 2.6 Saturation Law

**Observation:**  
During the Dec 2–4 CME sequence, χ amplitude rose linearly with dynamic pressure up to ~20 nPa, then plateaued at χ ≈ 0.15 despite continued increases in density and velocity. This indicates a saturation threshold in the vacuum recoil.

**Equation:**  
\[
\Delta \chi(P_{\text{dyn}}) = \chi_{\max} \left(1 - e^{-k P_{\text{dyn}}}\right) + \chi_0
\]

- \(\chi_{\max}\) = maximum vacuum amplitude (observed ≈ 0.15)  
- \(k\) = saturation coefficient (fit from rise region)  
- \(\chi_0\) = baseline amplitude (≈ 0.055)

## 2.7 Hysteresis Term

**Observation:**  
Post‑storm χ remained elevated above baseline, showing memory of prior peaks. This hysteresis is visible in the undershoot (χ = 0.0877) followed by recovery to χ = 0.15.

**Equation (discrete memory):**  
\[
\chi_{t+1} = \alpha \cdot \chi_t + (1-\alpha)\cdot \chi_{\text{base}} + k \cdot P_{\text{dyn},t}
\]

- \(\alpha\) = memory coefficient (expected 0.7–0.95)  
- \(\chi_{\text{base}}\) = baseline amplitude (≈ 0.055)  
- \(k\) = linear gain term

## 2.8 Magnetic Gain Term

**Observation:**  
Southward IMF (\(B_z < 0\)) amplified χ responses at similar pressures. Example: χ = 0.1365 at \(B_z = -13.56\) nT.

**Equation:**  
\[
P^\star = P_{\text{dyn}} \cdot \left(1 + \beta \cdot \frac{-B_z}{1 + |B_z|}\right)
\]

- \(P^\star\) = effective pressure including magnetic gain  
- \(\beta\) = coupling coefficient (fit from regression)

## 2.9 Summary

- Linear law holds in rise region.
- Saturation law explains plateau at χ ≈ 0.15.
- Hysteresis term captures memory and undershoot.
- Magnetic gain term improves fit under southward IMF.
- Together, these extend the  recoil law into a full system‑level equation.
