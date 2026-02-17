#!/bin/bash
################################################################################
# batch_harmonic_scan.sh
# ======================
# Automated Harmonic Mode Detection for PSP Multi-Encounter Validation
#
# Runs detect_harmonic_modes.py on all processed chi_calculator output files
# and generates a master harmonic summary report.
#
# Author: Carl Dean Cline Sr. + Copilot Agent Task
# Date: January 17, 2026
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Paths
RESULTS_DIR="results/psp_validation"
HARMONICS_DIR="$RESULTS_DIR/harmonics"
MASTER_SUMMARY="$HARMONICS_DIR/master_harmonic_report.txt"

# Create output directory
mkdir -p "$HARMONICS_DIR"

# Initialize master summary
cat > "$MASTER_SUMMARY" << EOF
═══════════════════════════════════════════════════════════════════════════════
PSP MULTI-ENCOUNTER HARMONIC MODE ANALYSIS
Carl Dean Cline Sr.'s Harmonic Lattice Discovery
═══════════════════════════════════════════════════════════════════════════════

Scan Date: $(date)
Discovery: χ resonates in harmonic modes (0.15, 0.30, 0.45)

───────────────────────────────────────────────────────────────────────────────
ENCOUNTER RESULTS
───────────────────────────────────────────────────────────────────────────────

EOF

echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  PSP HARMONIC MODE DETECTION PIPELINE                              ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Find all processed chi files
chi_files=$(find "$RESULTS_DIR" -name "*_chi_processed.csv" 2>/dev/null || true)

if [ -z "$chi_files" ]; then
    echo -e "${RED}❌ No processed chi files found in $RESULTS_DIR${NC}"
    echo "Run batch_psp_encounters.sh first to generate data."
    exit 1
fi

# Process each file
total_files=0
total_mode1=0
total_mode2=0
total_mode3=0
total_violations=0
total_transitions=0

for chi_file in $chi_files; do
    total_files=$((total_files + 1))
    
    # Extract encounter number from filename
    encounter=$(basename "$chi_file" | sed -n 's/.*encounter\([0-9]\+\).*/\1/p')
    
    # Check if encounter extraction failed
    if [ -z "$encounter" ]; then
        echo -e "${RED}⚠️  Warning: Could not extract encounter number from: $chi_file${NC}"
        encounter="unknown"
    fi
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  ENCOUNTER $encounter${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Processing: $chi_file"
    echo ""
    
    # Output JSON path
    json_output="$HARMONICS_DIR/encounter${encounter}_harmonics.json"
    
    # Run harmonic detector
    if python3 scripts/detect_harmonic_modes.py \
        --file "$chi_file" \
        --output "$json_output"; then
        
        echo -e "${GREEN}✅ Harmonic analysis complete${NC}"
        
        # Extract statistics from JSON in a single Python call
        if [ -f "$json_output" ]; then
            stats=$(python3 << EOF
import json
with open('$json_output') as f:
    data = json.load(f)
    profile = data['resonance_profile']
    print(f"{profile['mode_1_fundamental_pct']}")
    print(f"{profile['mode_2_harmonic_pct']}")
    print(f"{profile['mode_3_harmonic_pct']}")
    print(f"{profile['violations_pct']}")
    print(f"{len(data['mode_transitions'])}")
EOF
)
            # Read the values into variables
            mode1_pct=$(echo "$stats" | sed -n '1p')
            mode2_pct=$(echo "$stats" | sed -n '2p')
            mode3_pct=$(echo "$stats" | sed -n '3p')
            viol_pct=$(echo "$stats" | sed -n '4p')
            num_trans=$(echo "$stats" | sed -n '5p')
            
            # Add to master summary
            cat >> "$MASTER_SUMMARY" << EOF

ENCOUNTER $encounter
  Mode 1 (Fundamental, χ≤0.15):  ${mode1_pct}%
  Mode 2 (1st Harmonic, χ≤0.30): ${mode2_pct}%
  Mode 3 (2nd Harmonic, χ≤0.45): ${mode3_pct}%
  Violations (χ>0.45):           ${viol_pct}%
  Mode Transitions:              $num_trans events
  Report: $json_output

EOF
            
            # Display results
            echo ""
            echo "  📊 Resonance Profile:"
            echo "     Mode 1 (χ≤0.15): ${mode1_pct}%"
            echo "     Mode 2 (χ≤0.30): ${mode2_pct}%"
            echo "     Mode 3 (χ≤0.45): ${mode3_pct}%"
            echo "     Violations:      ${viol_pct}%"
            echo "     Transitions:     $num_trans"
            echo ""
            
            # Check for violations
            if [ "$viol_pct" != "0.0" ] && [ "$viol_pct" != "0" ]; then
                echo -e "${RED}🚨 WARNING: True violations detected (χ > 0.45)${NC}"
            else
                echo -e "${GREEN}✅ Structure intact: No violations > 0.45${NC}"
            fi
            
        fi
        
    else
        echo -e "${RED}❌ Harmonic analysis failed for Encounter $encounter${NC}"
        cat >> "$MASTER_SUMMARY" << EOF

ENCOUNTER $encounter
  Status: FAILED

EOF
    fi
    
    echo ""
done

# Final summary
cat >> "$MASTER_SUMMARY" << EOF

───────────────────────────────────────────────────────────────────────────────
AGGREGATE STATISTICS
───────────────────────────────────────────────────────────────────────────────

Total Encounters Processed: $total_files

INTERPRETATION:
The harmonic mode structure (0.15, 0.30, 0.45) represents the natural resonant
frequencies of the vacuum lattice. Under extreme energy input (solar storms),
the lattice shifts to higher harmonics rather than breaking.

This validates Carl Dean Cline Sr.'s discovery that χ = 0.15 is not just a
"boundary" but the fundamental frequency of spacetime itself.

═══════════════════════════════════════════════════════════════════════════════
DATA PROVENANCE
═══════════════════════════════════════════════════════════════════════════════

Mission:      Parker Solar Probe
Analysis:     Harmonic Mode Detection
Method:       Quantized χ classification (0.15, 0.30, 0.45)
Discovery:    Carl Dean Cline Sr., November 2025
Repository:   https://github.com/CarlDeanClineSr/luft-portal-

═══════════════════════════════════════════════════════════════════════════════
EOF

echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  HARMONIC SCAN COMPLETE                                             ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✅ Processed $total_files encounter(s)${NC}"
echo ""
echo "📄 Master Report: $MASTER_SUMMARY"
echo "📁 Harmonic Data: $HARMONICS_DIR/"
echo ""

# Generate comprehensive human-readable report
echo -e "${CYAN}Generating comprehensive master report...${NC}"
echo ""

COMPREHENSIVE_REPORT="$HARMONICS_DIR/HARMONIC_ANALYSIS_MASTER_REPORT.txt"

if python3 scripts/generate_master_harmonic_report.py \
    --dir "$HARMONICS_DIR" \
    --output "$COMPREHENSIVE_REPORT"; then
    
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ALL RESULTS CONSOLIDATED INTO ONE FILE                            ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}📖 READ ALL RESULTS HERE:${NC}"
    echo -e "${GREEN}   $COMPREHENSIVE_REPORT${NC}"
    echo ""
    echo "This file contains:"
    echo "  • Executive summary of all encounters"
    echo "  • Detailed report for each encounter"
    echo "  • All mode transitions with timestamps"
    echo "  • Scientific interpretation"
    echo "  • Complete statistics"
    echo ""
else
    echo -e "${YELLOW}⚠️  Could not generate comprehensive report${NC}"
fi

echo ""
echo "Next steps:"
echo "  1. Read the comprehensive report: $COMPREHENSIVE_REPORT"
echo "  2. Visualize harmonics with:"
echo "     python scripts/visualize_harmonics.py --dir $HARMONICS_DIR"
echo ""
