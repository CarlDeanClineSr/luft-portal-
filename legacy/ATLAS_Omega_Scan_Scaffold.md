# Capsule: ATLAS Ω-scan Scaffold — LB-level Time Modulation

Purpose
- Provide a minimal, runnable scaffold to test LUFT-style time modulation in ATLAS Open Data (LB-level).
- Model: R(t)=R0[1+χ cos(Ω t+φ)], scan Ω∈[1e−5,1e−3] Hz, report best χ, Ω, φ, and global p via LB shuffles.

Input CSV schema
- Required columns: timestamp (ISO8601 or epoch), rate
- Optional: lumi, prescale (used to correct rate → rate/(lumi·prescale))
- Optional: run, lb (for bookkeeping)

Example (see examples/atlas_lb_example.csv):
timestamp,run,lb,rate,lumi,prescale
2012-06-01T12:00:00Z,203100,1,1832.1,1.2,1
2012-06-01T12:01:00Z,203100,2,1824.0,1.2,1
...

How to run
- From repo root:
  - python3 scripts/atlas_omega_scan.py --input examples/atlas_lb_example.csv --output atlas_omega_scan.json --spectrum-csv atlas_chi_spectrum.csv
- Options:
  - --omega-min, --omega-max, --n-omega, --logspace to control the scan grid
  - --permutations N for LB-shuffle global p (default 200; increase for final studies)
  - --time-col, --rate-col, --lumi-col, --prescale-col to match your CSV

Outputs
- atlas_omega_scan.json:
  {
    "best": {"omega": ..., "chi": ..., "phi": ...},
    "p_global": ...,
    "omega_grid": {...},
    "n_points": ...
  }
- atlas_chi_spectrum.csv: table with omega, chi, phi, a, b, c

Notes
- χ is fractional modulation amplitude relative to baseline a (≈R0).
- Global p accounts for look-elsewhere via LB shuffles (permutation test).
- For production, stratify by run or conditions; apply GRL and corrections when forming the input CSV.
