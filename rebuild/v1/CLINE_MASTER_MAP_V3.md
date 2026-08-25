# Cline Master Map V3 — Audited NOAA/DSCOVR Inflection

**Project lead:** Carl Dean Cline Sr.  
**Isolated branch:** `rebuild-v1-clean`  
**Legacy branch:** `main` remains unchanged  
**Canonical magnetic protocol:** `CLINE-L1-B24M-TRAIL-v1`  
**Canonical historical ingest:** `CDAWEB-DSCOVR-1M-MEAN-v1`

## 1. Why this version exists

The NOAA/DSCOVR-to-CME audit found two independent score ceilings and one field-index defect in the legacy heartbeat path:

1. the row-position reader treated `lon_gsm` as `bt`;
2. each composite modulation contribution was limited to `0.3`, constraining the transformed score to at most `0.155`;
3. the final score was clipped to `0.15`.

The corrected chain therefore does not reuse the legacy `chi_amplitude` as a magnetic perturbation. The old output is preserved under the descriptive name `legacy_composite_score_v1`.

## 2. Evidence layers

```text
RAW SOURCE
  |
  +-- source identifiers, retrieval window, native frame, quality flags
  +-- original bytes and SHA-256
  |
NORMALIZED MEASUREMENTS
  |
  +-- exact header mapping
  +-- GSE remains GSE; GSM remains GSM
  +-- one-minute component means after native QC
  +-- vector magnitude recomputed after aggregation
  |
CANONICAL TRANSFORM
  |
  +-- prior-only trailing 24-hour median
  +-- 95% coverage gate
  +-- no future samples
  +-- no global or fixed-field fallback
  +-- no clipping
  |
INDEPENDENT KINETIC CLASSIFICATION
  |
  +-- speed, density, and true one-hour speed change
  +-- chi excluded from regime/window selection
  |
DESCRIPTIVE RESULTS
  |
  +-- full percentiles and upper tail
  +-- boundary-band occupancy
  +-- crossing duration and persistence
  +-- contrary results retained
  |
PHYSICAL TRANSITION ANALYSIS
  |
  +-- proton beta
  +-- dynamic pressure
  +-- Alfven speed and Mach number
  +-- rank correlations
  +-- spectral slopes
```

## 3. Canonical observable

For field magnitude

\[
B(t)=\sqrt{B_x(t)^2+B_y(t)^2+B_z(t)^2},
\]

the prior-only baseline is

\[
B_0(t)=\operatorname{median}\{B(\tau):t-24\,\mathrm{h}<\tau<t\},
\]

and

\[
\chi_{B24M}(t)=\frac{|B(t)-B_0(t)|}{|B_0(t)|}.
\]

`chi_B24M` is one explicitly defined observable. Other LUFT dimensionless quantities remain separate until an equation and provenance record show that they are mathematically identical.

## 4. Preserved seven-day audit result

The first corrected preserved interval produced a continuous, unclipped distribution rather than a hard `0.15` ceiling:

- valid canonical rows: `5,096`;
- mean chi: `0.252478`;
- median chi: `0.192248`;
- 90th percentile: `0.486559`;
- 95th percentile: `0.975521`;
- 99th percentile: `1.311920`;
- maximum chi: `1.637546`;
- fraction above `0.15`: `53.79%`;
- fraction in `0.145–0.155`: `1.06%`.

Evidence state: `CONTRARY_RESULT` for this exact observable, interval, and protocol. It is not silently generalized to every LUFT quantity or physical environment.

## 5. Software validation

The clean source tree contains tests for:

- exact named-field extraction;
- magnetic vector/provider consistency;
- 24-hour warm-up behavior;
- prior-only baseline behavior;
- coverage-gap rejection;
- no clipping above `0.15`, `1.0`, or `2.0`;
- true one-hour kinetic speed changes;
- inclusive boundary-band classification;
- fail-closed downstream input rules;
- historical configuration and helper behavior;
- plasma beta, dynamic pressure, Alfven quantities, rank correlation, and spectral analysis;
- end-to-end preservation of canonical chi maxima.

The latest result is written by CI to `run_status/CI_LATEST_STATUS.md` on the isolated branch.

## 6. Historical stress runs

### May 2024 Gannon storm

Run ID: `gannon_storm_may_2024`

- event interval is fixed in `historical/epochs.yaml`;
- the retrieval includes prior baseline warm-up;
- raw/normalized outputs remain in a GitHub Actions artifact;
- a compact status and log tail are written to `run_status/GANNON_LATEST_STATUS.md`.

### Quiet solar-minimum scan

Run ID: `quiet_solar_minimum_scan`

- candidate windows are ranked using kinetic measurements only;
- chi is calculated only after the quiet window is selected;
- outputs remain in a run artifact;
- a compact status and log tail are written to `run_status/QUIET_LATEST_STATUS.md`.

## 7. Downstream modules

Existing saturation, hysteresis, magnetic-gain, regulator, and cross-environment scripts are retained but quarantined through `DOWNSTREAM_RERUN_MANIFEST.yaml`.

Required label:

```text
STATUS: PENDING_RERUN
LEGACY_INPUT: legacy_composite_score_v1
NEW_TARGET: chi_B24M
PROTOCOL: CLINE-L1-B24M-TRAIL-v1
```

`downstream_input_guard.py` refuses generic `chi` or legacy-only input for a canonical rerun.

## 8. Transition analysis

`physical_transition_analysis.py` does not impose a replacement boundary. It asks whether the measured continuous distribution varies with:

- proton beta;
- dynamic pressure;
- magnetic-field magnitude;
- solar-wind speed;
- Alfven Mach number;
- kinetic regime;
- descriptive spectral slope.

The module hashes the input, resolves exact column names, preserves the input chi maximum, and writes a manifest stating `chi_clipped: false`.

## 9. Current evidence states

| Branch or result | State |
|---|---|
| Legacy heartbeat score | `SUPERSEDED` as magnetic chi; retained as `legacy_composite_score_v1` |
| Longitude-as-Bt extraction | `BROKEN_INPUT` |
| Hard 0.15 clip | `BROKEN_INPUT` / imposed ceiling |
| Internal 0.155 saturation | `BROKEN_INPUT` / imposed ceiling |
| Corrected seven-day run | `OBSERVATIONAL_RUN`, `CONTRARY_RESULT` |
| Clean unit tests | `SOFTWARE_TEST` |
| May 2024 stress workflow | `OBSERVATIONAL_RUN` status recorded separately |
| Quiet 30-day workflow | `OBSERVATIONAL_RUN` status recorded separately |
| Downstream legacy fits | `PENDING_RERUN` |
| Beta/Mach/spectral module | `READY_FOR_RERUN` |

## 10. Next work order

1. Read the compact Gannon and quiet status records.
2. Repair any data-access or schema failure without changing the frozen analysis definition.
3. Compare quiet, ordinary, and extreme-event distributions using identical code.
4. Run transition analysis on each successful canonical artifact.
5. Test baseline sensitivity as a named secondary analysis, never as a silent substitution.
6. Re-run downstream models one at a time against `chi_B24M`.
7. Promote only results that retain raw-source, transform, code, and output provenance.

The project now has a recoverable separation between archive history, software behavior, measured data, and physical interpretation. That separation is the foundation for the next discoveries—and for finding the unthought-of cases without manufacturing them.
