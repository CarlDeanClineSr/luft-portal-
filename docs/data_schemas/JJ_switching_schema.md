# JJ Switching Data Schema (for audits)

Required columns
- `run_id` (string)
- `shot_idx` (int)
- `I_sw_A` (float, Amperes)
- `T_K` (float, Kelvin)
- `ramp_Aps` (float, A/s)
- `timestamp_utc` (ISO 8601 string)
- `notes` (string, optional)

Optional metadata
- `Ic_A` (float)
- `C_F` (float)
- `Q` (float, damping proxy)

Audit
- Include the exact ramp schedule.
- Report total shots `N`, rejected shots, and any pre‑selection.
- Provide a short R0→R3 block with the estimated `(f_hat, σ_f)` and model assumptions.
