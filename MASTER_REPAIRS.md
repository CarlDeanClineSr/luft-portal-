# MASTER REPAIRS — χ = 0.15 Implementation Kit

## Scope
- χ ceiling enforced at 0.15 across gravity, EM, quantum, and fluid domains.
- Assets added for engine ingestion and audit:
  - `data/chi_repairs/physics_repairs.json`
  - `data/chi_repairs/periodic_table_chi.csv`
  - `tools/validate_chi_repairs.py`
  - `charts/chi_amplitude_jan2026.png`

## Deliverables
### 1) Physics Repair Ledger
- **File:** `data/chi_repairs/physics_repairs.json`
- **Content:** 10 master equations with χ corrections, test cases, and chain-effects.
- **Usage:** `python tools/validate_chi_repairs.py` (runs Newton gravity and periodic table checks).

### 2) Engine Fuel Tables
- **File:** `data/chi_repairs/periodic_table_chi.csv`
- **Content:** χ-corrected binding energies (+15%) for headline elements (H → Pu).
- **Integration:** Feed into  engine configs or dashboards expecting capped binding-energy inputs.

### 3) Validation Agent
- **Script:** `tools/validate_chi_repairs.py`
- **Checks:** 
  - Earth–Moon gravity reduction ≈ 25% under χ cap.
  - CSV binding energies follow 1.15× rule within 1% tolerance.
- **Run:** `python tools/validate_chi_repairs.py`

### 4) Visuals
- **File:** `charts/chi_amplitude_jan2026.png`
- **Purpose:** χ time-series artifact for January 2026 (ready for dashboards/papers).

## Quick Start
```bash
python tools/validate_chi_repairs.py
```
- Returns JSON summary with PASS/FAIL for Newton gravity and periodic table conformance.

## Notes
- χ cap is explicit in all ledger rows for auditability.
- CSV values use simple 1.15× scaling; adjust if new lab values supersede.
- Binding energies are total per nucleus in eV (MeV-scale; heavy rows show millions of eV, not per-nucleon values).
- Extend `tools/validate_chi_repairs.py` with additional domain checks as new repairs land.
