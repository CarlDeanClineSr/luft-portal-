# CLINE L1 Frozen Baseline Protocol V1

**Protocol ID:** `CLINE-L1-B24M-TRAIL-v1`  
**Version:** `1.0.0`  
**Purpose:** Establish one reproducible NOAA L1 magnetic-to-CME reduction path without positional field assumptions, future-data leakage, fallback baselines, or χ clipping.

This is a data-reduction contract. It does not declare what the resulting distribution means physically.

## 1. Magnetic input contract

The magnetic source must provide named columns:

- `time_tag` — timestamp, parsed as UTC;
- `bx_gsm`, `by_gsm`, `bz_gsm` — magnetic vector components in nT;
- `bt` — provider total field in nT, optional for calculation but retained for quality control;
- `lon_gsm`, `lat_gsm` — optional directional coordinates.

Fields are accessed by **column name only**. No row position may be interpreted as a physical field.

The authoritative magnitude is recomputed as

\[
B(t)=\sqrt{B_x(t)^2+B_y(t)^2+B_z(t)^2}.
\]

Provider `bt` is compared with the recomputed magnitude. The V1 absolute tolerance is `0.02 nT`, chosen to accommodate the printed precision of the preserved NOAA rows. A failed check is recorded; the row is not silently repaired with another column.

## 2. Cleaning contract

1. Parse `time_tag` as UTC.
2. Convert required measurements to numeric values.
3. Reject rows missing time or any required vector component.
4. Sort by timestamp.
5. Remove duplicate timestamps, retaining the last stored row.
6. Preserve counts of every rejected or duplicate row.

No interpolation, smoothing, resampling, or forward filling occurs before χ is computed.

## 3. Frozen baseline

The baseline is named **B24M-TRAIL**:

\[
B_0(t)=\operatorname{median}\{B(\tau):t-24\mathrm{h}<\tau<t\}.
\]

Properties:

- trailing, not centered;
- prior data only;
- current sample excluded;
- no future samples;
- no global-mean fallback;
- no fixed 5 nT fallback;
- no partial-window result presented as a full baseline.

For one-minute telemetry, a complete window contains 1,440 expected samples. V1 requires at least 95% coverage:

\[
N_{\min}=\lceil0.95\times1440\rceil=1368.
\]

The timestamp must also be at least 24 hours after the first retained source row. Rows that fail these conditions remain in the output with one of these states:

- `WARMUP_LT_24H`;
- `INSUFFICIENT_COVERAGE`;
- `NONPOSITIVE_BASELINE`;
- `VALID`.

Only `VALID` rows enter primary χ statistics.

## 4. Magnetic χ

For valid baseline rows:

\[
\chi_{B24M}(t)=\frac{|B(t)-B_0(t)|}{|B_0(t)|}.
\]

**No lower cap, upper cap, compression, saturation transform, or replacement is applied.** Values such as 0.2, 0.8, or 1.6 remain 0.2, 0.8, or 1.6.

The descriptive bands retained from the working program are:

- `BELOW`: χ < 0.145;
- `AT_BOUNDARY`: 0.145 ≤ χ ≤ 0.155;
- `ABOVE_BAND`: χ > 0.155.

A separate Boolean records χ > 0.15. The theoretical value and the operational tolerance band are therefore not collapsed into one condition.

## 5. Plasma join

The optional plasma source must provide:

- `time_tag`;
- `density` in particles/cm³;
- `speed` in km/s;
- `temperature`, optional.

Plasma is matched to each magnetic row by nearest UTC timestamp within 90 seconds. The actual matched plasma timestamp and absolute time offset are retained.

## 6. Independent kinetic separator

The kinetic regime does not use χ. It is a classification layer, not part of the χ calculation.

A row is `TRANSIENT_KINETIC` when all required kinetic inputs are available and at least one condition is true:

- speed > 600 km/s;
- density > 15 particles/cm³;
- |speed(t) − speed(t−1 hour)| > 50 km/s.

The one-hour speed comparison is matched by time within two minutes. It is not a one-minute difference mislabeled as an hourly jump.

Rows with the needed present-time values but without a valid one-hour prior speed remain `UNCLASSIFIED` rather than being silently called steady.

The following magnetic conditions are retained as supporting context only and do not determine the blind kinetic regime:

- Bz ≤ −10 nT;
- total B ≥ 15 nT.

## 7. Required outputs

Each run writes:

- row-level CSV with raw values, baseline, χ, quality flags, and kinetic classification;
- JSON summary with protocol parameters and input SHA-256 hashes;
- Markdown report generated from numerical fields;
- χ time-series and histogram charts when primary rows exist.

The report may state that a numerical criterion was or was not met. It may not hard-code “confirmed,” “disproved,” or a physical mechanism independently of the stored numbers.

## 8. Version rule

Changing any of the following requires a new protocol ID/version:

- magnetic magnitude definition;
- baseline statistic, duration, direction, or inclusion rule;
- coverage threshold;
- cleaning or interpolation rule;
- χ formula;
- kinetic thresholds;
- classification bands.

V1 results must never be silently overwritten by a changed formula under the same name.
