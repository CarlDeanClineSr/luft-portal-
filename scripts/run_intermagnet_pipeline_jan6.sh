#!/bin/bash
# Full χ pipeline for INTERMAGNET data (Jan 6, 2026)

STATIONS="dou sua"
DATE="20260106"

echo "========================================="
echo "INTERMAGNET χ PIPELINE (Jan 6, 2026)"
echo "========================================="

# Step 1: Fetch data
echo "Step 1: Fetching data..."
bash scripts/fetch_intermagnet_realtime.sh

# Ensure output directories exist
mkdir -p data/intermagnet_csv figures

# Step 2: Convert to CSV
echo "Step 2: Converting to CSV..."
for station in $STATIONS; do
    input_file="data/intermagnet_raw/${station}_${DATE}.min"
    output_file="data/intermagnet_csv/${station}_${DATE}.csv"
    
    if [ -f "$input_file" ]; then
        python scripts/convert_iaga2002_to_csv.py \
            --input "$input_file" \
            --output "$output_file"
    else
        echo "⚠️  Skipping ${station} (no raw file)"
    fi
done

# Step 3: Calculate χ
echo "Step 3: Calculating χ..."
for station in $STATIONS; do
    input_file="data/intermagnet_csv/${station}_${DATE}.csv"
    output_file="data/intermagnet_chi_calculations_${DATE}_${station}.csv"
    
    if [ -f "$input_file" ]; then
        python scripts/compute_chi_from_intermagnet.py \
            --input "$input_file" \
            --output "$output_file"
    else
        echo "⚠️  Skipping ${station} (no CSV file)"
    fi
done

# Step 4: Plot χ time series
echo "Step 4: Plotting χ..."
for station in $STATIONS; do
    input_file="data/intermagnet_chi_calculations_${DATE}_${station}.csv"
    output_file="figures/intermagnet_chi_timeseries_${DATE}_${station}.png"
    
    if [ -f "$input_file" ]; then
        python scripts/plot_intermagnet_chi_timeseries.py \
            --input "$input_file" \
            --output "$output_file"
    else
        echo "⚠️  Skipping ${station} (no χ file)"
    fi
done

echo "========================================="
echo "✅ PIPELINE COMPLETE"
echo "Outputs:"
echo "  - data/intermagnet_chi_calculations_${DATE}_*.csv"
echo "  - figures/intermagnet_chi_timeseries_${DATE}_*.png"
echo "========================================="
