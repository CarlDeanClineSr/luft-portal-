# DSCOVR Historical Data Availability Audit

**Frozen:** 2026-08-25  
**Applies to:** `CDAWEB-DSCOVR-RESTCSV-1M-v1`

## Finding

The definitive DSCOVR products required by the paired historical runner do not share the same full time coverage.

- `DSCOVR_H0_MAG` has archive year directories from 2015 through 2025.
- `DSCOVR_H1_FC` has archive year directories only for 2016 through 2019 in the V1 inventory.

Therefore, a May 2024 analysis cannot honestly be labeled a paired definitive DSCOVR magnetic-plus-Faraday-cup run under this protocol.

## V1 decision

1. May 2024 remains a **DSCOVR magnetic-only** stress test of `chi_B24M`.
2. No kinetic regime labels are generated for that run.
3. The first paired active-event test uses September 2017, when both definitive products coexist.
4. The quiet 30-day selector searches April 2018 through December 2019 and uses only DSCOVR Faraday-cup kinetics during selection.
5. OMNI, Wind, ACE, or NOAA real-time plasma may be analyzed later, but each receives a separate source/clock protocol. They are never silently substituted into this DSCOVR V1 chain.

## Why this matters

Magnetic field magnitude is measured at DSCOVR near L1. An OMNI series may be propagated, shifted, merged, or sourced from other monitors. Pairing those rows without explicitly modeling the time and source transformation would create a new observable while retaining an old label. V1 fails closed instead.
