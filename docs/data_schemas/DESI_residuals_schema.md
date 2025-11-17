# DESI Residuals Schema (v1)

Required columns
- t_s (float): time in seconds from a reference epoch (e.g., survey start)
- residual (float): dimensionless residual (z_obs − z_LCDM), or a normalized proxy

Optional columns
- time_utc (string, ISO8601)
- instrument (string)
- site (string)
- group_id (string): night or week block id for block bootstrap
- target_id (string), z (float), airmass/seeing/temp (floats): for covariate controls

Audit
- Include reference epoch and units in a small header or README
- Provide N, period tested (Ω), and any data filters applied
