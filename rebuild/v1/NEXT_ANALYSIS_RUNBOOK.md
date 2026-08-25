# CLINE L1 Rebuild V1 — Operating Runbook

This file fixes the order of operations after the NOAA/DSCOVR-to-CME audit. It is intentionally conservative: preserve first, identify the observable, test software, then interpret measured output.

## 1. Protected records

- Legacy files on `main` are historical provenance and are not overwritten.
- The complete timestamped V1 audit package is preserved in Google Drive under `LUFT_CLINE/rebuild_v1_audit/`.
- Corrected development occurs on `rebuild-v1-clean`.
- The canonical magnetic observable is `chi_B24M` under `CLINE-L1-B24M-TRAIL-v1`.
- The historical ingest protocol is `CDAWEB-DSCOVR-1M-MEAN-v1`.

## 2. Canonical analysis order

1. Acquire raw MAG and plasma records.
2. Save source metadata and SHA-256 before transformation.
3. Resolve fields by exact header name, never by row position.
4. Preserve coordinate frame truthfully; do not rename GSE as GSM.
5. Apply native quality flags before aggregation.
6. Reduce valid one-second MAG vectors to one-minute component means.
7. Recompute magnitude from the aggregated vector.
8. Apply the prior-only trailing 24-hour median with the 95% coverage gate.
9. Preserve all finite `chi_B24M` values; clipping is prohibited.
10. Classify kinetic conditions without using chi.
11. Summarize the complete distribution, including contrary results.
12. Run transition analysis only after the canonical output exists.

## 3. Required controls

Every observational run must contain:

- warm-up rows marked invalid for canonical chi;
- cadence and coverage diagnostics;
- provider/vector magnitude comparison where provider magnitude exists;
- missing-value counts and quality-flag counts;
- steady/transient classification independent of chi;
- percentiles rather than maximum alone;
- boundary-band occupancy reported descriptively, not as confirmation;
- sequence-duration analysis for threshold crossings;
- source, code, parameter, and output hashes.

## 4. Historical stress runs

### May 2024 storm

Run ID: `gannon_storm_may_2024`

Purpose: measure the upper tail and transition behavior under extreme driving. The event run includes the prior 24 hours required by the frozen baseline.

### Quiet solar-minimum interval

Run ID: `quiet_solar_minimum_scan`

Purpose: select a 30-day window using only kinetic measurements, then calculate chi afterward. Chi must not participate in quiet-window selection.

Both workflows upload complete artifacts and commit only a compact status/log-tail record to the isolated branch.

## 5. Downstream quarantine

A downstream module remains quarantined until it explicitly declares:

```text
STATUS: PENDING_RERUN
LEGACY_INPUT: legacy_composite_score_v1
NEW_TARGET: chi_B24M
PROTOCOL: CLINE-L1-B24M-TRAIL-v1
```

`downstream_input_guard.py` must reject generic `chi` and legacy-only input when a canonical rerun is requested.

## 6. Physical transition questions

`physical_transition_analysis.py` examines the continuous distribution without imposing a replacement law. Initial outputs are:

- proton beta;
- dynamic pressure;
- Alfven speed and Alfven Mach number;
- rank correlations with chi;
- chi summaries by beta band and kinetic regime;
- descriptive power-spectrum slopes for B and chi.

These quantities are measurements or transformations. A physical interpretation is written only after the numerical outputs and controls are available.

## 7. Status vocabulary

Use only the following evidence states in the Master Map:

```text
RAW
EXPLORATORY
SYNTHETIC_DEMO
SOFTWARE_TEST
OBSERVATIONAL_RUN
CIRCULAR
BROKEN_INPUT
SUPERSEDED
CONTRARY_RESULT
PENDING_RERUN
REPLICATED
READY_FOR_RERUN
```

A result is never deleted because it is contrary. It is linked to its exact observable, protocol, data range, and code version.
