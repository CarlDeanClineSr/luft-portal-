# Legacy CME estimator audit

- Matched magnetic/plasma rows: `5480`
- Header: `['time_tag', 'bx_gsm', 'by_gsm', 'bz_gsm', 'lon_gsm', 'lat_gsm', 'bt']`
- Legacy positional element 4 is `lon_gsm`, not `bt`.
- Named `bt` is at element 6.

## Two separate ceiling mechanisms

1. Each density, speed, and BT modulation contribution is capped at `0.3`.
2. The transformed score is then clipped to `[0.01, 0.15]`.

Because the average of three capped components cannot exceed 0.3, the transformed score cannot exceed `0.155` even when the final 0.15 clip is removed.

## Reproduction

| Variant | n | Median | Max | Exact 0.15 fraction | Above 0.15 fraction |
|---|---:|---:|---:|---:|---:|
| `legacy_wrong_field_clipped` | 5480 | 0.140250 | 0.150000 | 0.231569 | 0.000000 |
| `legacy_correct_field_clipped` | 5480 | 0.126896 | 0.150000 | 0.140876 | 0.000000 |
| `legacy_wrong_field_no_final_clip` | 5480 | 0.140250 | 0.155000 | 0.000547 | 0.231569 |
| `legacy_correct_field_no_final_clip` | 5480 | 0.126896 | 0.155000 | 0.001277 | 0.139964 |

## Status

The legacy value is a bounded composite pressure/modulation score. It is not the same observable as magnetic `abs(B-B0)/B0` and should be retained under a separate field name rather than reused as magnetic χ.
