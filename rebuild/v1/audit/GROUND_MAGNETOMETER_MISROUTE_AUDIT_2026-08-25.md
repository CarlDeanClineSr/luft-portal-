# Ground-Magnetometer-Like CSV Audit — 2026-08-25

## Status

`SOURCE_UNRESOLVED_GROUND_MAGNETOMETER_LIKE`

Preserve the artifact. Do not delete it, relabel it as DSCOVR, or use it in L1 plasma equations.

## Observed signature

The surfaced table has the schema:

```text
time,F,B,baseline,chi
```

and contains total-field values around 51,300 nT, including approximately:

```text
2024-05-10T00:00:00Z  F=51312.699  B=51312.699
2024-05-10T21:47:00Z  F=51723.700  B=51723.700
```

Within the LUFT archive, a column named `F` paired with a total-field magnitude of this scale is a terrestrial magnetometer signature, not a canonical DSCOVR L1 vector product. The generic derived column `chi` also fails the rebuilt observable contract, which requires `chi_B24M`.

## Important separation of causes

The table is wrong for the canonical L1 plasma-transition path, but it was **not shown to have been downloaded by the latest clean Gannon workflow**.

The latest recorded clean Gannon job stopped before data access because its workflow invoked an undefined run name:

```text
gannon_storm_may_2024
```

while the frozen epoch manifest defines:

```text
gannon_may_2024_dscovr_mag_only
```

The clean historical downloader was already configured for the NASA CDAWeb dataset `DSCOVR_H0_MAG`, variables `B1GSE`, `B1F1`, and `FLAG1`. Therefore two independent issues existed:

1. an unresolved ground-magnetometer-like file elsewhere in the archive;
2. a clean-branch workflow run-name mismatch that prevented the Gannon download from starting.

They must not be collapsed into one explanation.

## Repairs applied

- Corrected both Gannon workflows to invoke `gannon_may_2024_dscovr_mag_only`.
- Added `historical/source_identity_guard.py` before canonical baseline processing.
- Required exact `source_dataset=DSCOVR_H0_MAG` provenance.
- Required exact `ingest_protocol=CDAWEB-DSCOVR-RESTCSV-1M-v1` provenance.
- Required one complete, truthful magnetic vector frame.
- Added an engineering quarantine stop at 1000 nT for an automated L1 run. This is not a physical boundary and does not clip data.
- Rejected terrestrial `F` layouts and generic `B/baseline/chi` layouts.
- Required downstream transition analysis to consume `chi_B24M`, not generic `chi`.
- Added tests showing that a renamed 51,300 nT file is still rejected.

## May 2024 scope

The frozen V1 data-availability audit supports definitive DSCOVR magnetic data for May 2024 but not a matching definitive DSCOVR Faraday-cup product under the same frozen source contract. The Gannon run therefore remains explicitly **magnetic-only**. No proton beta, Alfvén speed, Alfvén Mach number, or kinetic-regime result may be reported from that run unless a separately named, provenance-controlled plasma source is introduced under a new protocol version.

## Evidence rule

A successful future Gannon result must carry all of the following in its manifest:

```text
source_dataset: DSCOVR_H0_MAG
ingest_protocol: CDAWEB-DSCOVR-RESTCSV-1M-v1
coordinate_frame: GSE
source_identity_guard.verdict: PASS
paired_plasma: false
analysis_protocol: CLINE-L1-B24M-TRAIL-v1
observable: chi_B24M
chi_clipped: false
```

Until then, the ground-like table remains a provenance finding, not a DSCOVR result.
