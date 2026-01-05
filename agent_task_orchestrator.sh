#!/usr/bin/env bash
set -euo pipefail

echo "=== Cline-Pack Momentum Test Pipeline ==="
echo "Start: $(date -u)"

run_if_exists() {
  local script="$1"
  shift || true
  if [ -f "$script" ]; then
    echo "Running $script $*"
    python "$script" "$@"
  else
    echo "Skipping $script (not found)"
  fi
}

run_if_exists "scripts/dscovr_ingest.py"
run_if_exists "scripts/usgs_mag_ingest.py"
run_if_exists "scripts/chi_at_boundary_updater.py"

python momentum_recoil_detector.py
python magnetic_wake_analyzer.py
python cline_pack_correlation.py

count_events() {
  local file="$1"
  if [ ! -f "$file" ]; then
    echo 0
    return
  fi
  local lines
  lines=$(wc -l < "$file")
  if [ "$lines" -le 1 ]; then
    echo 0
  else
    echo $((lines - 1))
  fi
}

mkdir -p reports
report="reports/momentum_test_summary_$(date -u +%Y%m%d).md"
plasma_count=$(count_events results/momentum_recoil_events.csv)
mag_count=$(count_events results/magnetic_wake_rotations.csv)
high_conf=$( [ -f results/cline_pack_correlated_events.csv ] && grep -c "High-Confidence Cline" results/cline_pack_correlated_events.csv || echo 0 )

cat > "$report" <<EOF
# Cline-Pack Momentum Test Report
**Generated (UTC):** $(date -u +%Y-%m-%dT%H:%M:%SZ)

- Plasma recoil events: $plasma_count
- Magnetic wake rotations: $mag_count
- High-Confidence Cline events: $high_conf

EOF

echo "Report written to $report"
echo "=== Pipeline complete ==="
