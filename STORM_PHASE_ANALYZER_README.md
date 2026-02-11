# Storm Phase Analyzer

A robust storm-phase classification tool for analyzing χ (chi) timeseries data and identifying geomagnetic storm phases.

## Overview

The storm phase analyzer classifies observations into four distinct phases based on χ amplitude relative to the critical boundary (χ ≈ 0.15):

- **PRE**: Points before the first PEAK (pre-storm quiet period)
- **PEAK**: Points where χ is within the boundary band [0.145, 0.155] (storm peak)
- **POST**: Points after the last PEAK (post-storm recovery)
- **UNKNOWN**: Invalid or missing χ values

## Physics Background

The analyzer is based on the critical χ boundary at **χ = 0.15**, which represents a fundamental threshold in magnetosphere dynamics. When χ exceeds this boundary:

- The magnetosphere transitions from quiet to disturbed state
- Geomagnetic storms become probable
- Enhanced coupling between solar wind and magnetosphere occurs

## Usage

### Basic Example

```python
import pandas as pd
from storm_phase_analyzer import analyze_storm_phases

# Load your χ timeseries
df = pd.read_csv('data/cme_heartbeat_log_2025_12.csv')

# Analyze storm phases
summary, df_with_phases = analyze_storm_phases(
    df,
    chi_boundary_min=0.145,
    chi_boundary_max=0.155,
    min_peak_points=3,
)

# Access results
print(f"Storm detected: {summary['has_storm']}")
print(f"Peak observations: {summary['num_peak']}")
print(f"First peak time: {summary['first_peak_time']}")
```

### Command-Line Usage

Run the provided example script:

```bash
python scripts/analyze_storm_phases.py
```

This will:
1. Load data from `data/cme_heartbeat_log_2025_12.csv`
2. Analyze storm phases
3. Save results:
   - `data/cme_heartbeat_log_2025_12_with_phases.csv` (CSV with phase column)
   - `data/storm_phase_summary.json` (JSON summary for dashboard)

## API Reference

### `analyze_storm_phases()`

```python
def analyze_storm_phases(
    df: pd.DataFrame,
    chi_boundary_min: float = 0.145,
    chi_boundary_max: float = 0.155,
    min_peak_points: int = 3,
) -> Tuple[Dict[str, Any], pd.DataFrame]
```

**Parameters:**

- `df` (DataFrame): Input data with columns:
  - `timestamp` or `timestamp_utc`: datetime or string
  - `chi_amplitude`: float
  
- `chi_boundary_min` (float, optional): Lower bound of χ boundary (default: 0.145)

- `chi_boundary_max` (float, optional): Upper bound of χ boundary (default: 0.155)

- `min_peak_points` (int, optional): Minimum PEAK samples to classify as storm (default: 3)

**Returns:**

Tuple of `(summary, df_with_phases)`:

- `summary` (dict): Statistics dictionary with keys:
  - `total_obs`: Total observations
  - `num_pre`: Count of PRE phase points
  - `num_peak`: Count of PEAK phase points
  - `num_post`: Count of POST phase points
  - `num_unknown`: Count of UNKNOWN points
  - `pct_pre`: Percentage of PRE points
  - `pct_peak`: Percentage of PEAK points
  - `pct_post`: Percentage of POST points
  - `pct_unknown`: Percentage of UNKNOWN points
  - `has_storm`: Boolean indicating storm detection
  - `first_peak_time`: ISO timestamp of first peak (or None)
  - `last_peak_time`: ISO timestamp of last peak (or None)
  - `chi_boundary_min`: Lower boundary used
  - `chi_boundary_max`: Upper boundary used

- `df_with_phases` (DataFrame): Input DataFrame with added `phase` column

## Algorithm Details

### Phase Classification Logic

1. **PEAK Detection**: Identifies all points where χ falls within [chi_boundary_min, chi_boundary_max]

2. **Storm Validation**: Checks if at least `min_peak_points` PEAK points exist

3. **Phase Assignment**:
   - If storm exists:
     - Points in boundary band → PEAK
     - Valid points before first PEAK → PRE
     - Valid points after last PEAK → POST
   - If no storm:
     - All valid points → PRE (quiet period)

4. **Unknown Handling**: NaN, infinite, or non-numeric values → UNKNOWN

### Robustness Features

- Handles missing data gracefully
- Converts non-numeric values to UNKNOWN
- Supports alternate column names (`timestamp_utc`)
- Validates input data structure
- Provides comprehensive error messages

## Example Output

### JSON Summary

```json
{
  "total_obs": 1147,
  "num_pre": 92,
  "num_peak": 317,
  "num_post": 5,
  "num_unknown": 733,
  "pct_pre": 8.02,
  "pct_peak": 27.64,
  "pct_post": 0.44,
  "pct_unknown": 63.91,
  "has_storm": true,
  "first_peak_time": "2025-12-03T22:19:00",
  "last_peak_time": "2025-12-28T10:19:00",
  "chi_boundary_min": 0.145,
  "chi_boundary_max": 0.155
}
```

### CSV with Phases

The output CSV includes the original data plus a new `phase` column:

```csv
timestamp_utc,chi_amplitude,...,phase
2025-12-02 00:37:00,0.1183,...,PRE
2025-12-03 22:19:00,0.1487,...,PEAK
2025-12-28 13:14:52,0.1052,...,POST
```

## Testing

Run the comprehensive test suite:

```bash
python tests/test_storm_phase_analyzer.py
```

Tests cover:
- Basic storm classification
- Quiet periods (no storm)
- Insufficient peak points
- Missing/NaN value handling
- Custom boundary parameters
- Alternate column names
- Percentage calculations
- Real data structure compatibility

## Integration with Dashboard

The JSON summary output is designed for direct integration with dashboards:

```python
import json
from pathlib import Path

# Read summary
summary = json.loads(Path('data/storm_phase_summary.json').read_text())

# Use in dashboard
if summary['has_storm']:
    display_storm_alert(summary['first_peak_time'])
    show_phase_distribution(summary)
```

## Future Enhancements

- **Multi-storm detection**: Split observations by time gaps between peak clusters
- **Kp/Dst integration**: Combine χ with geomagnetic indices
- **Magnetosphere coupling**: Apply to magnetometer data
- **Phase transitions**: Track PRE→PEAK→POST transition dynamics
- **Real-time monitoring**: Support streaming data analysis

## Requirements

- Python 3.8+
- pandas
- numpy

## License

See repository LICENSE file.

## Citation

If you use this analyzer in research, please cite:

```
Storm Phase Analyzer -  Portal
https://github.com/CarlDeanClineSr/-portal-
```

## See Also

- `scripts/analyze_historical_storms.py` - Historical storm analysis
- `cme_heartbeat_analysis.py` - CME impact analysis
- `CHI_015_QUICK_REFERENCE.md` - χ = 0.15 physics documentation
