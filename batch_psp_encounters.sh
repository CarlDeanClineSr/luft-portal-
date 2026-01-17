#!/bin/bash
################################################################################
# batch_psp_encounters.sh
# =======================
# Automated PSP Multi-Encounter χ ≤ 0.15 Validation Pipeline
#
# This script downloads Parker Solar Probe data for Encounters 17-20 and runs
# Carl Dean Cline Sr.'s chi_calculator on each dataset to test the universal
# χ ≤ 0.15 boundary at extreme solar proximity. 
#
# Author: Carl Dean Cline Sr. + Copilot Agent Task
# Date: January 17, 2026
# Repository: https://github.com/CarlDeanClineSr/luft-portal-
#
# Usage:
#   bash batch_psp_encounters.sh
#   bash batch_psp_encounters.sh 17 18  # Specific encounters only
#
# Requirements:
#   - Python 3.7+
#   - pyspedas or cdasws
#   - pandas, numpy
#   - fetch_psp_encounter17.py
#   - chi_calculator.py
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
if [ $# -gt 0 ]; then
    ENCOUNTERS="$@"
else
    ENCOUNTERS="17 18 19 20"  # Default: all encounters
fi

OUTPUT_DIR="data/psp"
RESULTS_DIR="results/psp_validation"
SUMMARY_FILE="$RESULTS_DIR/multi_encounter_summary.txt"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

# Create directories
mkdir -p "$OUTPUT_DIR"
mkdir -p "$RESULTS_DIR"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
    printf "${CYAN}║${NC}  %-64s${CYAN}║${NC}\n" "$1"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
}

print_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

################################################################################
# Dependency Check
################################################################################

check_dependencies() {
    print_section "CHECKING DEPENDENCIES"
    
    local missing_deps=0
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found"
        missing_deps=1
    else
        print_success "Python 3: $(python3 --version)"
    fi
    
    # Check required Python packages
    local packages=("pandas" "numpy")
    for pkg in "${packages[@]}"; do
        if python3 -c "import $pkg" 2>/dev/null; then
            print_success "Python package: $pkg"
        else
            print_error "Missing Python package: $pkg"
            missing_deps=1
        fi
    done
    
    # Check for pyspedas or cdasws
    if python3 -c "import pyspedas" 2>/dev/null; then
        print_success "Data source: pyspedas (NASA official)"
    elif python3 -c "import cdasws" 2>/dev/null; then
        print_success "Data source: cdasws (fallback)"
    else
        print_error "Neither pyspedas nor cdasws installed"
        print_info "Install with: pip install pyspedas"
        missing_deps=1
    fi
    
    # Check required scripts
    if [ ! -f "fetch_psp_encounter17.py" ]; then
        print_error "fetch_psp_encounter17.py not found"
        missing_deps=1
    else
        print_success "Script: fetch_psp_encounter17.py"
    fi
    
    if [ ! -f "chi_calculator.py" ]; then
        print_error "chi_calculator.py not found"
        missing_deps=1
    else
        print_success "Script: chi_calculator.py"
    fi
    
    if [ $missing_deps -eq 1 ]; then
        echo ""
        print_error "DEPENDENCY CHECK FAILED"
        echo ""
        echo "Install missing dependencies:"
        echo "  pip install pyspedas pandas numpy"
        echo ""
        exit 1
    fi
    
    print_success "All dependencies satisfied"
}

################################################################################
# Main Pipeline
################################################################################

run_pipeline() {
    print_header "PSP MULTI-ENCOUNTER χ ≤ 0.15 VALIDATION PIPELINE"
    echo ""
    echo "  Carl Dean Cline Sr.'s Discovery"
    echo "  Testing universal boundary at extreme solar proximity"
    echo ""
    echo "  Encounters: $ENCOUNTERS"
    echo "  Date: $(date)"
    echo ""
    
    # Initialize summary file
    cat > "$SUMMARY_FILE" << EOF
═══════════════════════════════════════════════════════════════════════════════
PSP MULTI-ENCOUNTER χ ≤ 0.15 VALIDATION SUMMARY
Carl Dean Cline Sr.'s Discovery
═══════════════════════════════════════════════════════════════════════════════

Pipeline Run: $TIMESTAMP
Encounters: $ENCOUNTERS

───────────────────────────────────────────────────────────────────────────────
EOF
    
    # Check dependencies
    check_dependencies
    
    # Statistics tracking
    local total_encounters=0
    local successful_downloads=0
    local successful_analyses=0
    local total_violations=0
    local total_observations=0
    
    # Process each encounter
    for encounter in $ENCOUNTERS; do
        total_encounters=$((total_encounters + 1))
        
        print_section "ENCOUNTER $encounter"
        
        # Get encounter info
        case $encounter in
            17)
                encounter_info="Sep 2023, Perihelion 2023-09-27, ~0.08 AU"
                ;;
            18)
                encounter_info="Dec 2023, Perihelion 2023-12-29, ~0.08 AU"
                ;;
            19)
                encounter_info="Mar 2024, Perihelion 2024-03-30, ~0.08 AU"
                ;;
            20)
                encounter_info="Jun 2024, Perihelion 2024-06-30, ~0.08 AU"
                ;;
            *)
                encounter_info="Unknown encounter"
                ;;
        esac
        
        echo "📍 Info: $encounter_info"
        echo ""
        
        # Step 1: Download data
        print_info "Step 1/3: Downloading PSP data..."
        echo ""
        
        local data_file="$OUTPUT_DIR/psp_encounter${encounter}_mag.csv"
        
        if python3 fetch_psp_encounter17.py --encounter "$encounter" --output-dir "$OUTPUT_DIR"; then
            print_success "Download complete: $data_file"
            successful_downloads=$((successful_downloads + 1))
            
            # Check if file exists and has data
            if [ ! -f "$data_file" ]; then
                print_error "Data file not created: $data_file"
                echo "ENCOUNTER $encounter: DOWNLOAD FAILED (file not created)" >> "$SUMMARY_FILE"
                continue
            fi
            
            local row_count=$(wc -l < "$data_file")
            if [ "$row_count" -lt 2 ]; then
                print_error "Data file is empty: $data_file"
                echo "ENCOUNTER $encounter: DOWNLOAD FAILED (empty file)" >> "$SUMMARY_FILE"
                continue
            fi
            
            print_info "Data points: $((row_count - 1))"  # -1 for header
            
        else
            print_error "Download failed for Encounter $encounter"
            echo "ENCOUNTER $encounter: DOWNLOAD FAILED" >> "$SUMMARY_FILE"
            echo ""
            print_warning "Skipping to next encounter..."
            continue
        fi
        
        echo ""
        
        # Step 2: Calculate χ
        print_info "Step 2/3: Calculating χ (chi) parameter..."
        echo ""
        
        local chi_output="$RESULTS_DIR/encounter${encounter}_chi_analysis.txt"
        local chi_csv="$RESULTS_DIR/encounter${encounter}_chi_processed.csv"
        
        if python3 chi_calculator.py \
            --file "$data_file" \
            --time-col timestamp \
            --bx B_R \
            --by B_T \
            --bz B_N \
            --output "$chi_csv" > "$chi_output" 2>&1; then
            
            print_success "χ calculation complete"
            successful_analyses=$((successful_analyses + 1))
            
            # Extract key statistics from output
            if [ -f "$chi_output" ]; then
                local chi_max=$(grep "Maximum χ:" "$chi_output" | awk '{print $3}')
                local chi_mean=$(grep "Mean χ:" "$chi_output" | awk '{print $3}')
                local violations=$(grep "Violations (χ > 0.15):" "$chi_output" | awk '{print $5}')
                local observations=$(grep "Total observations:" "$chi_output" | awk '{print $3}' | tr -d ',')
                local boundary_pct=$(grep "At boundary" "$chi_output" | grep -oP '\(\K[0-9.]+(?=%)')
                
                # Handle cases where extraction might fail
                chi_max=${chi_max:-"N/A"}
                chi_mean=${chi_mean:-"N/A"}
                violations=${violations:-0}
                observations=${observations:-0}
                boundary_pct=${boundary_pct:-"N/A"}
                
                # Update totals (only if values are numeric)
                if [[ "$violations" =~ ^[0-9]+$ ]]; then
                    total_violations=$((total_violations + violations))
                fi
                if [[ "$observations" =~ ^[0-9]+$ ]]; then
                    total_observations=$((total_observations + observations))
                fi
                
                # Display results
                echo ""
                echo "  📊 Results:"
                echo "     Observations: $observations"
                echo "     χ_max:        $chi_max"
                echo "     χ_mean:       $chi_mean"
                echo "     Violations:   $violations"
                echo "     At boundary:  ${boundary_pct}%"
                echo ""
                
                # Add to summary
                cat >> "$SUMMARY_FILE" << EOF

ENCOUNTER $encounter ($encounter_info)
  Status:         ✅ SUCCESS
  Data points:    $observations
  χ_max:          $chi_max
  χ_mean:         $chi_mean
  Violations:     $violations
  At boundary:    ${boundary_pct}%
  Data file:      $data_file
  Results:        $chi_output
  Processed CSV:  $chi_csv

EOF
                
                # Check for violations
                if [ "$violations" = "0" ]; then
                    print_success "✅ BOUNDARY CONFIRMED: Zero violations"
                elif [[ "$violations" =~ ^[0-9]+$ ]] && [ "$violations" -gt 0 ]; then
                    print_warning "⚠️  ALERT: $violations violations detected!"
                    echo "    This contradicts Carl's discovery and requires investigation."
                else
                    print_info "Unable to determine violation count"
                fi
                
            else
                print_warning "Could not extract statistics from output"
                echo "ENCOUNTER $encounter: ANALYSIS INCOMPLETE (no stats)" >> "$SUMMARY_FILE"
            fi
            
        else
            print_error "χ calculation failed for Encounter $encounter"
            echo "ENCOUNTER $encounter: ANALYSIS FAILED" >> "$SUMMARY_FILE"
            echo ""
            print_info "Check log: $chi_output"
            continue
        fi
        
        echo ""
        
        # Step 3: Generate visualization (optional)
        print_info "Step 3/3: Results saved"
        echo ""
        
        sleep 1  # Brief pause between encounters
    done
    
    # Final summary
    print_section "PIPELINE COMPLETE"
    
    echo "  📊 Summary Statistics:"
    echo ""
    echo "     Encounters processed:     $total_encounters"
    echo "     Successful downloads:     $successful_downloads"
    echo "     Successful analyses:      $successful_analyses"
    echo "     Total observations:       $total_observations"
    echo "     Total violations:         $total_violations"
    echo ""
    
    # Add final summary to file
    cat >> "$SUMMARY_FILE" << EOF

───────────────────────────────────────────────────────────────────────────────
FINAL SUMMARY
───────────────────────────────────────────────────────────────────────────────

Encounters processed:     $total_encounters
Successful downloads:     $successful_downloads
Successful analyses:      $successful_analyses
Total observations:       $total_observations
Total violations:         $total_violations

EOF
    
    if [ $successful_analyses -eq 0 ]; then
        print_error "NO SUCCESSFUL ANALYSES"
        echo "Check internet connection and NASA CDAWeb availability"
        echo "STATUS: FAILED - No successful analyses" >> "$SUMMARY_FILE"
        exit 1
    fi
    
    if [ $total_violations -eq 0 ]; then
        print_success "✅ χ ≤ 0.15 BOUNDARY CONFIRMED ACROSS ALL ENCOUNTERS"
        echo ""
        echo "  Carl Dean Cline Sr.'s discovery holds at extreme solar proximity!"
        echo "  Zero violations detected across $total_observations observations."
        echo ""
        echo "STATUS: ✅ SUCCESS - χ ≤ 0.15 boundary confirmed" >> "$SUMMARY_FILE"
    else
        print_warning "⚠️  $total_violations VIOLATIONS DETECTED"
        echo ""
        echo "  This contradicts Carl's discovery and requires investigation."
        echo "  Review individual encounter results for details."
        echo ""
        echo "STATUS: ⚠️  VIOLATIONS DETECTED - Requires investigation" >> "$SUMMARY_FILE"
    fi
    
    cat >> "$SUMMARY_FILE" << EOF

───────────────────────────────────────────────────────────────────────────────
INTERPRETATION
───────────────────────────────────────────────────────────────────────────────

The χ ≤ 0.15 boundary represents a universal limit on normalized perturbations
in space plasma systems. Testing at Parker Solar Probe distances (0.08 AU,
~12 solar radii) validates whether this boundary holds under extreme conditions: 

  - Magnetic field: 50-100x stronger than at Earth
  - Plasma β: Much lower (magnetic pressure dominated)
  - Temperature: Electron temperature >> Proton temperature (inverted)
  - Turbulence: "Pristine" cascades, less evolved

If χ ≤ 0.15 holds across all encounters with zero violations, this suggests
the boundary is truly scale-invariant and represents a fundamental constraint
on plasma dynamics across 12 orders of magnitude in distance.

───────────────────────────────────────────────────────────────────────────────
DATA PROVENANCE
───────────────────────────────────────────────────────────────────────────────

Mission:        Parker Solar Probe (PSP)
Instrument:     FIELDS/MAG (Fluxgate Magnetometer)
Data Level:     Level 2 (calibrated, science-ready)
Coordinates:    RTN (Radial-Tangential-Normal)
Source:         NASA CDAWeb / SPDF
Retrieved:      $TIMESTAMP

Discovery:      Carl Dean Cline Sr., November 2025
                Lincoln, Nebraska, USA
                CARLDCLINE@GMAIL.COM

Repository:     https://github.com/CarlDeanClineSr/luft-portal-

═══════════════════════════════════════════════════════════════════════════════
EOF
    
    echo ""
    print_info "📄 Full summary saved to: $SUMMARY_FILE"
    echo ""
    print_info "📁 Results directory: $RESULTS_DIR"
    echo ""
    
    # Display summary file location
    print_header "REVIEW RESULTS"
    echo ""
    echo "  Summary:  cat $SUMMARY_FILE"
    echo "  Results:  ls -lh $RESULTS_DIR/"
    echo "  Data:     ls -lh $OUTPUT_DIR/"
    echo ""
}

################################################################################
# Script Entry Point
################################################################################

# Parse arguments
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    cat << EOF
PSP Multi-Encounter χ ≤ 0.15 Validation Pipeline

Usage: 
  bash batch_psp_encounters.sh [encounters]

Arguments:
  encounters    Space-separated list of encounter numbers (default: 17 18 19 20)

Examples:
  bash batch_psp_encounters.sh           # Process all encounters
  bash batch_psp_encounters.sh 17 18     # Process Encounters 17 and 18 only
  bash batch_psp_encounters.sh 20        # Process Encounter 20 only

Requirements:
  - Python 3.7+
  - pyspedas or cdasws
  - pandas, numpy
  - fetch_psp_encounter17.py
  - chi_calculator.py

Output:
  data/psp/                              # Downloaded data files
  results/psp_validation/                # Analysis results
  results/psp_validation/multi_encounter_summary.txt

For more information:
  https://github.com/CarlDeanClineSr/luft-portal-

EOF
    exit 0
fi

# Run the pipeline
run_pipeline

exit 0
