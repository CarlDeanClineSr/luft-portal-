# CLINE L1 Rebuild — Implementation Status

**Date:** 2026-08-25  
**Canonical analysis:** `CLINE-L1-B24M-TRAIL-v1`  
**Code version:** `1.1.0`

## Completed

- Preserved the original V1 ZIP in an isolated Google Drive audit folder.
- Created GitHub branch `rebuild-v1-clean`; `main` and all legacy paths remain untouched.
- Extended the canonical chain to accept one truthful magnetic frame per input: GSM or GSE.
- Prohibited silent GSE-to-GSM relabeling.
- Preserved unclipped `chi_B24M` values above 0.15, 1.0, and 2.0.
- Added a downstream migration manifest and fail-closed input guard.
- Added NASA CDAWeb REST-CSV historical ingestion with source descriptors, raw bytes, SHA-256 hashes, quality metadata, and chunk manifests.
- Audited source coverage before pairing instruments.
- Configured May 2024 as a magnetic-only stress run.
- Configured September 2017 as a paired definitive MAG/Faraday-cup active-event run.
- Added a kinetic-only quiet-window selector over the shared 2018–2019 archive; magnetic χ is not used in selection.
- Added manual historical-run and clean-CI GitHub workflows.
- Re-ran the preserved seven-day February 2026 source through version 1.1.0; results match the V1 audit.
- Passed all 23 local tests.

## Regression result

| Statistic | Version 1.1.0 result |
|---|---:|
| Baseline-valid rows | 5,096 |
| Median χ | 0.1922484459 |
| Mean χ | 0.2524783594 |
| Maximum χ | 1.6375459001 |
| Fraction χ > 0.15 | 0.5378728414 |
| Fraction in 0.145–0.155 | 0.0105965463 |

## Two additional integrity safeguards

### Average magnitude versus magnitude of average

The definitive historical MAG product reports `B1F1` as an average field magnitude and `B1GSE` as an averaged vector. The magnitude of an averaged vector need not equal the average of native magnitudes. The ingest records their difference as a diagnostic and flags materially negative differences, but it does not impose an invalid equality filter.

### Coverage before pairing

Definitive `DSCOVR_H1_FC` Faraday-cup files end in 2019 in the frozen archive inventory, while `DSCOVR_H0_MAG` continues through 2024. May 2024 is therefore magnetic-only. OMNI, Wind, ACE, or NOAA real-time plasma is not silently inserted and called DSCOVR H1.

## Not yet executed

The current tool runtime could not reach NASA CDAWeb because external DNS was unavailable. Consequently, the historical downloads have been **implemented and contract-tested but are not represented as completed observational runs**.

They are ready for:

- `CLINE_HISTORICAL_STRESS_RUNS_V1_COLAB.ipynb`;
- the branch-only manual GitHub workflow; or
- a local environment with network access.

## Merge gate

Do not merge into `main` until all three historical runs produce preserved source descriptors, raw chunk hashes, canonical inputs, row-level `chi_B24M`, summaries, charts, and a numerical cross-epoch comparison.
