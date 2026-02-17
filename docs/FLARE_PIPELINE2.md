# LUFT Flare Foam Pipeline Overview

This page is a **pointer**, not a theory document.  
It tells a future reader WHERE the flare→foam→escape‑rate pipeline lives.

## 1. Main Physics Capsule

The full description of the X5.1 flare foam pipeline is in:

- `capsules/CAPSULE_FLARE_FOAM_PIPELINE.md`

That capsule contains:

- Event description (X5.1 flare, AR4274, 2025‑11‑11),
- Mapping from GOES proton flux \(\Phi(t)\) to foam \(f(t)\),
- Mapping from \(\Delta B(t)\) to effective mass \(m_\text{eq}(t)\),
- Escape‑rate model \(\Gamma(t) = \Gamma_0 \exp[-(B_0/2 + \kappa) f(t)]\),
- Experimental checklist (JJ, coils, clocks, particle echoes).

If you want the **physics and parameters**, read that capsule first.

## 2. Minimal Code Skeletons

The basic Python building blocks for running the flare foam pipeline are:

- `src/data_ingest_goes.py`
  - Function `load_goes_proton_csv(path, time_col="time", flux_col="flux_pfu")`
  - Returns a time‑indexed Series `phi_pfu(t)` from a GOES CSV file.

- `src/flare_mapping.py`
  - `map_flux_to_foam(phi, phi_ref=100.0, f0=0.0, alpha=-0.05)`
    - Maps GOES proton flux to foam parameter `f_foam(t)`.
  - `map_dB_to_meq(dB, meq0=1.0, B0=1.0, beta=0.1)`
    - Optional: maps geomagnetic perturbation ΔB(t) to effective mass `m_eq(t)`.

- `src/jj_gamma_model.py`
  - `gamma_from_foam(f, gamma0=1.0, B0=17.0, kappa=0.0)`
    - Computes `Gamma(t)` and `ln_Gamma(t)` from foam parameter `f(t)`.

These scripts are **intentionally minimal**. They implement the mappings described in the capsule; they do not fetch external data or plot by themselves.

## 3. Typical Usage (Local Run)

Example (pseudocode) run on a local machine, assuming you have a GOES CSV:

```python
from src.data_ingest_goes import load_goes_proton_csv
from src.flare_mapping import map_flux_to_foam
from src.jj_gamma_model import gamma_from_foam

# 1) Load GOES proton flux (>10 MeV) from CSV
phi = load_goes_proton_csv("data/goes_flux.csv", time_col="time", flux_col="flux_pfu")

# 2) Map flux to foam parameter f(t)
f = map_flux_to_foam(phi, phi_ref=100.0, f0=0.0, alpha=-0.05)  # tune alpha as needed

# 3) Compute escape rate Γ(t) and ln Γ(t)
df_gamma = gamma_from_foam(f, gamma0=1.0, B0=17.0, kappa=0.0)

# 4) Save results
df_gamma.to_csv("out/flare_gamma_timeseries.csv")
```

This is enough for an auditor to see:

- How \(\Phi(t)\) became \(f(t)\),
- How \(f(t)\) became \(\Gamma(t)\).

## 4. Relation to Workflows

If a GitHub Actions workflow called **“LUFT Flare Foam Audit”** exists, it should:

- Assume a GOES CSV is already in `data/goes_flux.csv`,
- Run the code sequence above (or an equivalent script),
- Save outputs under `out/` for later inspection.

See `.github/workflows/luft_flare_foam_audit.yml` (or similar) for automation details.

---
This document is deliberately short.  
It exists to **connect**:

- The **capsule** (physics + parameters),
- The **code** (Python skeletons),
- The **workflow** (automated runs).

No new theory is introduced here.
