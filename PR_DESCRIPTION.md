# Pull Request: Merge Normalized ACE Audit Data and Charting Pipeline

## Summary of Changes

This PR merges the normalized ACE audit data processing pipeline and chart generation system from the data normalization work into main. The changes add:

1. **Normalization Pipeline**: Script to convert raw ACE audit JSON arrays to normalized objects with named fields
2. **Computed Fields**: Dynamic pressure (P_dyn) and χ amplitude calculations 
3. **Chart Generation**: Example charts and cycle-specific visualizations
4. **Animation**: Animated GIF combining multiple cycle charts
5. **Data Provenance**: All original raw data preserved in `original_row` fields

## Files Added

### Scripts
- `scripts/normalize_audit.py` - Converts raw JSON arrays to normalized object format
- `scripts/create_gif_luft.py` - Creates animated GIF from cycle charts
- `scripts/compute_pdyn_chi.py` - (Already present) Computes P_dyn and χ fields
- `scripts/make_example_chart.py` - (Already present) Generates example chart
- `scripts/save_cycle_charts.py` - (Already present) Generates numbered cycle charts

### Data Files
- `data/ace_plasma_audit_normalized.json` - Normalized plasma data with named fields
- `data/ace_mag_audit_normalized.json` - Normalized magnetometer data with named fields  
- `data/ace_plasma_audit_normalized_with_chi.json` - Safety copy with computed P_dyn and χ

### Generated Charts
- `charts/chart_example_chi.png` - Example χ amplitude visualization
- `charts/chart_cycle_1.png` - Cycle 1 specific chart
- `charts/luft_relay.gif` - Animated GIF combining cycle charts

## Pipeline Execution

The following commands were executed to generate the artifacts in this PR:

```bash
# 1. Normalize raw audit data
python3 scripts/normalize_audit.py

# 2. Compute dynamic pressure and χ amplitude
python3 scripts/compute_pdyn_chi.py

# 3. Generate example chart
python3 scripts/make_example_chart.py

# 4. Generate cycle-specific chart
python3 scripts/save_cycle_charts.py --cycle 1

# 5. Create animated GIF
python3 scripts/create_gif_luft.py
```

## Data Provenance

✅ **Original raw data preserved**: All normalized JSON objects include an `original_row` field containing the complete original raw array data. This ensures full traceability and provenance.

## Anomaly Flags

⚠️ **Magnetometer anomalies preserved unchanged**: The normalized magnetometer data includes an `anomaly_flag` field set to `"preserved_unchanged"` to indicate that anomalous magnetic field values from the source data are intentionally left as-is and not corrected.

## Workflow Files

✅ **No workflow modifications**: No changes were made to any `.github/workflows` files as required.

## Requirements

### Python Packages Required

To reproduce locally, install the following Python packages:

```bash
pip install matplotlib imageio
```

Or using a requirements file (if added):

```bash
pip install -r requirements.txt
```

## Reproduction Instructions

To reproduce this pipeline locally:

### Prerequisites
```bash
# Ensure Python 3.8+ is installed
python3 --version

# Install required packages
pip install matplotlib imageio
```

### Run the Pipeline
```bash
# Clone the repository
git clone https://github.com/CarlDeanClineSr/-portal-.git
cd -portal-

# Checkout this branch
git checkout data-normalize

# Execute the normalization and computation pipeline
python3 scripts/normalize_audit.py
python3 scripts/compute_pdyn_chi.py
python3 scripts/make_example_chart.py
python3 scripts/save_cycle_charts.py --cycle 1
python3 scripts/create_gif_luft.py

# Verify outputs
ls -lh data/*normalized*.json
ls -lh charts/*.png charts/*.gif
```

### Expected Outputs
- `data/ace_plasma_audit_normalized.json` - Normalized plasma audit data
- `data/ace_mag_audit_normalized.json` - Normalized mag audit data
- `data/ace_plasma_audit_normalized_with_chi.json` - Safety copy with P_dyn and χ
- `charts/chart_example_chi.png` - Example chart (65 KB)
- `charts/chart_cycle_1.png` - Cycle 1 chart (122 KB)
- `charts/luft_relay.gif` - Animated GIF (56 KB)

## Testing

All scripts were tested in the runner environment:
- ✅ Normalization completed successfully for 1 plasma and 1 mag record
- ✅ P_dyn and χ calculations completed without errors
- ✅ Charts generated successfully in PNG format at 200-300 DPI
- ✅ GIF created successfully with 1 frame (infinite loop)

## Notes

- The current data files contain single records for demonstration purposes
- The pipeline is designed to handle multiple records (arrays of objects)
- Chart generation uses matplotlib with appropriate figure sizes and DPI
- GIF creation uses imageio with 0.5s frame duration and infinite loop
- All timestamps are in UTC format: `YYYY-MM-DD HH:MM:SS.fff`

## Review Checklist

- [x] Normalization script created and tested
- [x] GIF creation script created and tested
- [x] Normalized JSON files generated
- [x] Computed fields (P_dyn, χ) added
- [x] Example chart generated
- [x] Cycle chart generated
- [x] Animated GIF created
- [x] Original data preserved in `original_row` fields
- [x] Anomaly flags added for mag data
- [x] No workflow files modified
- [x] Reproduction instructions provided
- [x] Python dependencies documented

## Next Steps

After merging this PR:
1. Consider adding more cycle data for richer animations
2. Add error handling for edge cases in normalization
3. Consider adding a requirements.txt file for easier dependency management
4. Add unit tests for normalization and computation functions
5. Document the data schema in a separate README

---

**Do Not Merge Yet** - This PR is ready for Carl's review. Please review the generated artifacts and pipeline before merging.
