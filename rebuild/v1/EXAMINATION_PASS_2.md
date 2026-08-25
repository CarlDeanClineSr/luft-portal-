# Cline Master Map — Examination Pass 2

## NOAA/DSCOVR-to-CME reconstruction

The legacy chain has been separated into two different observables:

1. **Legacy composite modulation score** — a transformed average of density, speed, and a field-like input, with component caps and a final output clip.
2. **Magnetic χ under the frozen protocol** — `abs(B-B0)/abs(B0)` using a prior-only 24-hour magnetic median.

They are not interchangeable and now have separate field names and reports.

## A. Field mapping repair

The preserved NOAA header is:

```text
time_tag, bx_gsm, by_gsm, bz_gsm, lon_gsm, lat_gsm, bt
```

The old extractor read element 4 as `bt`; element 4 is `lon_gsm`. The reconstruction reads by name and computes the authoritative field magnitude from the vector components.

Across the seven-day archive:

- rows tested: 9,205;
- provider `bt`/vector QC pass rate at 0.02 nT: 100%;
- maximum absolute disagreement: 0.012772 nT.

This confirms that the named `bt` field and the recomputed vector magnitude agree within the printed precision of the stored rows.

## B. Legacy ceiling audit

The legacy estimator had two independent ceilings:

1. density, speed, and field modulation terms were each capped at 0.3;
2. the transformed output was clipped to 0.15.

Because the three capped terms average to no more than 0.3, the transformation cannot exceed 0.155 even when the final 0.15 clip is removed.

On 5,480 matched preserved rows:

| Legacy reconstruction | Exact 0.15 | Above 0.15 | Maximum |
|---|---:|---:|---:|
| Wrong positional field + final clip | 23.16% | 0% | 0.150 |
| Correct named field + final clip | 14.09% | 0% | 0.150 |
| Wrong positional field, no final clip | 0.05% | 23.16% | 0.155 |
| Correct named field, no final clip | 0.13% | 14.00% | 0.155 |

The positional error increased the exact-0.15 pile, while the final clip guaranteed zero recorded values above 0.15. Removing only the final clip would not have removed the 0.155 structural ceiling created by the component caps.

## C. Frozen magnetic protocol

Protocol `CLINE-L1-B24M-TRAIL-v1` uses:

- `B = sqrt(Bx² + By² + Bz²)`;
- prior-only interval `(t−24h, t)`;
- median baseline;
- current point excluded;
- 1,368 of 1,440 expected prior samples required;
- no fallback and no clipping.

## D. Seven-day preserved run

Source magnetic interval: January 29, 2026 21:13 UTC through February 5, 2026 21:10 UTC.

- magnetic rows after cleaning: 9,205;
- full-baseline valid rows: 5,096;
- warm-up rows: 1,371;
- insufficient-coverage rows: 2,738;
- plasma matches: 5,480.

Primary valid-row distribution:

- mean χ: 0.252478;
- median χ: 0.192248;
- 95th percentile: 0.975521;
- maximum χ: 1.637546;
- χ > 0.15: 2,741 / 5,096 = 53.79%;
- 0.145 ≤ χ ≤ 0.155: 54 / 5,096 = 1.06%;
- χ > 0.155: 2,713 / 5,096 = 53.24%.

The maximum occurred February 4, 2026 at 14:40 UTC:

- B = 23.494035 nT;
- B0 = 8.907536 nT;
- baseline coverage = 96.74%;
- χ = 1.637546;
- provider/vector disagreement = 0.005965 nT;
- kinetic classification = `TRANSIENT_KINETIC`.

## E. Independent kinetic split

The split uses density, speed, and a true one-hour speed difference. It does not use χ.

Among rows having both a valid magnetic baseline and a classified kinetic state:

### Steady kinetic

- n = 2,254;
- median χ = 0.272307;
- maximum χ = 1.448314;
- χ > 0.15 = 71.65%;
- boundary-band occupancy = 1.24%.

### Transient kinetic

- n = 391;
- median χ = 0.440966;
- maximum χ = 1.637546;
- χ > 0.15 = 94.12%;
- boundary-band occupancy = 0.26%.

The kinetic split raises χ during identified transients, but the preserved steady subset also contains many values above 0.15 under this exact baseline definition.

## F. Event persistence

Using a two-minute maximum continuity gap:

- χ > 0.15 formed 80 sequences containing 2,741 rows;
- median sequence length was two rows;
- the longest sequence contained 668 rows and covered 668 elapsed minutes;
- the boundary band formed 38 sequences containing 54 rows;
- the median boundary-band sequence was one row;
- the longest boundary-band sequence was seven rows over six elapsed minutes.

In this file and protocol, the 0.145–0.155 band appears as brief crossings rather than a long-duration locked state.

## G. Coverage sensitivity

Changing only the baseline coverage gate did not restore a 0.15 ceiling:

| Required coverage | Valid rows | Median χ | χ > 0.15 | Boundary band | Maximum χ |
|---:|---:|---:|---:|---:|---:|
| 80% | 6,682 | 0.233718 | 59.61% | 1.17% | 1.637546 |
| 85% | 6,610 | 0.236444 | 59.74% | 1.16% | 1.637546 |
| 90% | 6,538 | 0.239869 | 60.23% | 1.07% | 1.637546 |
| 95% | 5,096 | 0.192248 | 53.79% | 1.06% | 1.637546 |

The 95% rule remains canonical. The other rows are a sensitivity audit, not alternative preferred answers.

## H. Short snapshot

The separate DSCOVR-labeled magnetic/plasma snapshot spans only 23 hours 57 minutes.

- magnetic rows: 1,250;
- provider/vector QC pass rate: 100%;
- plasma matches: 1,249;
- primary χ rows: zero.

All rows are correctly marked `WARMUP_LT_24H`. The reconstruction does not substitute a global mean or shorter baseline and call it a 24-hour result.

## I. Current status

The corrected chain is executable and its software tests pass. The preserved seven-day run is a contrary result for a hard χ = 0.15 magnetic ceiling under `CLINE-L1-B24M-TRAIL-v1`.

This does not select the final physical interpretation. It narrows the next examination:

1. trace which exact baseline and observable generated each earlier 0.15 result;
2. rerun identical frozen protocols on longer DSCOVR, ACE, PSP, and MAVEN intervals;
3. test alternative baseline durations only under new protocol IDs;
4. distinguish a distribution edge, preferred state, event threshold, and transformed-score ceiling;
5. preserve every contrary run beside supporting runs.
