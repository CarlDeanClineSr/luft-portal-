#!/bin/bash

# TARGET: Parker Solar Probe (SCID 96)
# MISSION: Validate Expansion Cycle (Enc 17-20)

mkdir -p data/psp
mkdir -p results/psp_validation

# Encounter List: ID | Start | End
ENCOUNTERS=(
    "17|2023-09-22|2023-10-02"
    "18|2023-12-24|2024-01-03"
    "19|2024-03-25|2024-04-04"
    "20|2024-06-25|2024-07-05"
)

for entry in "${ENCOUNTERS[@]}"; do
    IFS="|" read -r ID START END <<< "$entry"
    
    RAW_FILE="data/psp/psp_encounter${ID}_mag.csv"
    CHI_FILE="results/psp_validation/encounter${ID}_chi.csv"
    
    echo ">>> PROCESSING ENCOUNTER $ID ($START)"
    
    # 1. Fetch
    if [ ! -f "$RAW_FILE" ]; then
        python3 scripts/fetch_psp_encounter17.py --encounter "$ID" --start "$START" --end "$END" --output "data/psp"
    fi
    
    # 2. Analyze
    if [ -f "$RAW_FILE" ]; then
        python3 scripts/chi_calculator.py --file "$RAW_FILE" --output "$CHI_FILE" --quiet
    fi
    
    echo ">>> Encounter $ID Complete."
done
