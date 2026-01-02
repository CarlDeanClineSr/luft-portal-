#!/bin/bash
# Automated Engine Discovery Sweep
# Runs all discovery queries and compiles results
# Author: LUFT Portal Engine
# Date: 2026-01-02

echo "========================================="
echo "LUFT ENGINE DISCOVERY SWEEP"
echo "Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
echo "========================================="

# Create output directory
OUTPUT_DIR="results/discovery_sweep_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_DIR"

echo ""
echo "📁 Output directory: $OUTPUT_DIR"
echo ""

# ============================================
# 1. CROSS-DOMAIN LINK ANALYSIS
# ============================================
echo "🔍 Step 1: Analyzing cross-domain links..."
if [ -f "link_graph_analyzer.py" ]; then
    python link_graph_analyzer.py \
      --query "cross-domain" \
      --min-connections 5 \
      --output "$OUTPUT_DIR/cross_domain_links.json" \
      > "$OUTPUT_DIR/link_analysis.log" 2>&1 || echo "⚠️ Link analysis failed (continuing)"
    
    if [ -f "$OUTPUT_DIR/cross_domain_links.json" ]; then
        echo "✅ Cross-domain links analyzed"
    else
        echo "⚠️ No cross-domain links found"
    fi
else
    echo "⚠️ link_graph_analyzer.py not found, skipping"
fi

# ============================================
# 2. META-INTELLIGENCE ANOMALY SCAN
# ============================================
echo ""
echo "🔍 Step 2: Scanning meta-intelligence for anomalies..."
if [ -d "reports/meta_intelligence" ]; then
    grep -r "anomaly" reports/meta_intelligence* > "$OUTPUT_DIR/anomalies_raw.txt" 2>/dev/null || echo "" > "$OUTPUT_DIR/anomalies_raw.txt"
    grep -r "correlation" reports/meta_intelligence* > "$OUTPUT_DIR/correlations_raw.txt" 2>/dev/null || echo "" > "$OUTPUT_DIR/correlations_raw.txt"
    
    # Count findings
    ANOMALY_COUNT=$(wc -l < "$OUTPUT_DIR/anomalies_raw.txt" | tr -d ' ')
    CORR_COUNT=$(wc -l < "$OUTPUT_DIR/correlations_raw.txt" | tr -d ' ')
    
    echo "✅ Anomalies found: $ANOMALY_COUNT"
    echo "✅ Correlations found: $CORR_COUNT"
else
    echo "⚠️ reports/meta_intelligence directory not found"
    ANOMALY_COUNT=0
    CORR_COUNT=0
fi

# ============================================
# 3. NUMERICAL PATTERN EXTRACTION
# ============================================
echo ""
echo "🔍 Step 3: Extracting numerical patterns..."
if [ -f "data/chi_boundary_tracking.jsonl" ] && [ -f "scripts/pattern_extractor.py" ]; then
    python scripts/pattern_extractor.py \
      --input data/chi_boundary_tracking.jsonl \
      --output "$OUTPUT_DIR/numerical_patterns.json" \
      > "$OUTPUT_DIR/pattern_extraction.log" 2>&1 || echo "⚠️ Pattern extraction failed"
    
    if [ -f "$OUTPUT_DIR/numerical_patterns.json" ]; then
        echo "✅ Patterns extracted"
    else
        echo "⚠️ Pattern extraction failed"
    fi
else
    echo "⚠️ Required files not found, skipping pattern extraction"
fi

# ============================================
# 4. TEMPORAL PATTERN MINING
# ============================================
echo ""
echo "🔍 Step 4: Mining temporal patterns..."
if [ -f "data/chi_boundary_tracking.jsonl" ] && [ -f "scripts/temporal_miner.py" ]; then
    python scripts/temporal_miner.py \
      --input data/chi_boundary_tracking.jsonl \
      --output "$OUTPUT_DIR/temporal_patterns.csv" \
      > "$OUTPUT_DIR/temporal_mining.log" 2>&1 || echo "⚠️ Temporal mining failed"
    
    if [ -f "$OUTPUT_DIR/temporal_patterns.csv" ]; then
        echo "✅ Temporal patterns identified"
    else
        echo "⚠️ Temporal mining failed"
    fi
else
    echo "⚠️ Required files not found, skipping temporal mining"
fi

# ============================================
# 5. FUNDAMENTAL CONSTANT CROSS-CHECK
# ============================================
echo ""
echo "🔍 Step 5: Cross-checking against fundamental constants..."
if [ -f "data/chi_boundary_tracking.jsonl" ] && [ -f "configs/fundamental_constants.json" ] && [ -f "scripts/constant_matcher.py" ]; then
    python scripts/constant_matcher.py \
      --chi-data data/chi_boundary_tracking.jsonl \
      --constants configs/fundamental_constants.json \
      --output "$OUTPUT_DIR/constant_matches.txt" \
      > "$OUTPUT_DIR/constant_matching.log" 2>&1 || echo "⚠️ Constant matching failed"
    
    if [ -f "$OUTPUT_DIR/constant_matches.txt" ]; then
        MATCHES=$(grep -c "Matches:" "$OUTPUT_DIR/constant_matches.txt" 2>/dev/null || echo "0")
        echo "✅ Constant matching complete: $MATCHES matches"
    else
        echo "⚠️ No constant matches"
        MATCHES=0
    fi
else
    echo "⚠️ Required files not found, skipping constant matching"
    MATCHES=0
fi

# ============================================
# 6. GENERATE SUMMARY REPORT
# ============================================
echo ""
echo "📊 Step 6: Generating summary report..."

# Count cross-domain links if file exists
if [ -f "$OUTPUT_DIR/cross_domain_links.json" ]; then
    LINK_COUNT=$(grep -c "}" "$OUTPUT_DIR/cross_domain_links.json" 2>/dev/null || echo "0")
else
    LINK_COUNT=0
fi

cat > "$OUTPUT_DIR/DISCOVERY_SUMMARY.md" << EOF
# Engine Discovery Sweep Summary
**Date:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")

## Results

### Cross-Domain Links
- **Files analyzed:** $LINK_COUNT
- **Status:** $([ -f "$OUTPUT_DIR/cross_domain_links.json" ] && echo "✅ Complete" || echo "⚠️ Not available")

### Anomalies & Correlations
- **Anomalies flagged:** $ANOMALY_COUNT
- **Correlations detected:** $CORR_COUNT

### Numerical Patterns
- **Status:** $([ -f "$OUTPUT_DIR/numerical_patterns.json" ] && echo "✅ Complete" || echo "⚠️ Not available")
- **See:** \`$OUTPUT_DIR/numerical_patterns.json\`

### Temporal Patterns
- **Status:** $([ -f "$OUTPUT_DIR/temporal_patterns.csv" ] && echo "✅ Complete" || echo "⚠️ Not available")
- **See:** \`$OUTPUT_DIR/temporal_patterns.csv\`

### Fundamental Constant Matches
- **Matches found:** $MATCHES
- **Status:** $([ -f "$OUTPUT_DIR/constant_matches.txt" ] && echo "✅ Complete" || echo "⚠️ Not available")
- **See:** \`$OUTPUT_DIR/constant_matches.txt\`

---

## Next Steps
1. Review flagged anomalies
2. Validate constant matches
3. Plot temporal patterns
4. Cross-reference with papers

**Status:** SWEEP COMPLETE  
**Output:** \`$OUTPUT_DIR\`
EOF

echo "✅ Summary report generated"

echo ""
echo "========================================="
echo "✅ DISCOVERY SWEEP COMPLETE"
echo "========================================="
echo ""
echo "Results saved to: $OUTPUT_DIR"
echo ""
echo "Next: Review $OUTPUT_DIR/DISCOVERY_SUMMARY.md"
echo ""
