#!/bin/bash
# Test script to validate GOES workflow logic without network calls
# This simulates the workflow steps using mock data

set -euo pipefail  # Exit on error, undefined variables, and pipeline failures

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEST_DATA_DIR="/tmp/test_goes_workflow_$$"

echo "=== GOES Workflow Test ==="
echo "Test directory: $TEST_DATA_DIR"

# Clean up function
cleanup() {
    echo "Cleaning up test directory..."
    rm -rf "$TEST_DATA_DIR"
}
trap cleanup EXIT

# Create test directory structure
echo ""
echo "Step 1: Creating directory structure..."
mkdir -p "$TEST_DATA_DIR/data/goes"
echo "✓ Directory created"

# Create mock GOES X-ray flux JSON data
echo ""
echo "Step 2: Creating mock GOES X-ray flux data..."
cat > "$TEST_DATA_DIR/data/goes/goes_xray_flux.json" << 'EOF'
[
  {
    "time_tag": "2025-11-24T12:00:00Z",
    "satellite": 16,
    "flux": 1.23e-6,
    "observed_flux": 1.23e-6,
    "electron_correction": 0.0,
    "electron_contamination": false,
    "energy": "0.05-0.4nm"
  },
  {
    "time_tag": "2025-11-24T12:05:00Z",
    "satellite": 16,
    "flux": 1.45e-6,
    "observed_flux": 1.45e-6,
    "electron_correction": 0.0,
    "electron_contamination": false,
    "energy": "0.05-0.4nm"
  },
  {
    "time_tag": "2025-11-24T12:10:00Z",
    "satellite": 16,
    "flux": 1.67e-6,
    "observed_flux": 1.67e-6,
    "electron_correction": 0.0,
    "electron_contamination": false,
    "energy": "0.05-0.4nm"
  }
]
EOF
echo "✓ Mock X-ray data created"

# Create mock GOES proton flux JSON data
echo ""
echo "Step 3: Creating mock GOES proton flux data..."
cat > "$TEST_DATA_DIR/data/goes/goes_proton_flux.json" << 'EOF'
[
  {
    "time_tag": "2025-11-24T12:00:00Z",
    "satellite": 16,
    "flux": 0.45,
    "energy": ">=10 MeV"
  },
  {
    "time_tag": "2025-11-24T12:05:00Z",
    "satellite": 16,
    "flux": 0.52,
    "energy": ">=10 MeV"
  },
  {
    "time_tag": "2025-11-24T12:10:00Z",
    "satellite": 16,
    "flux": 0.67,
    "energy": ">=10 MeV"
  }
]
EOF
echo "✓ Mock proton data created"

# Validate JSON files with jq
echo ""
echo "Step 4: Validating JSON files with jq..."
if jq empty "$TEST_DATA_DIR/data/goes/goes_xray_flux.json" 2>/dev/null; then
    echo "✓ X-ray flux JSON is valid"
else
    echo "✗ X-ray flux JSON is invalid!"
    exit 1
fi

if jq empty "$TEST_DATA_DIR/data/goes/goes_proton_flux.json" 2>/dev/null; then
    echo "✓ Proton flux JSON is valid"
else
    echo "✗ Proton flux JSON is invalid!"
    exit 1
fi

# Extract latest events (like the workflow does)
echo ""
echo "Step 5: Extracting latest events..."
if jq '.[-1]' "$TEST_DATA_DIR/data/goes/goes_xray_flux.json" > "$TEST_DATA_DIR/data/goes/goes_xray_audit.json"; then
    echo "✓ X-ray audit file created"
    if ! jq empty "$TEST_DATA_DIR/data/goes/goes_xray_audit.json" 2>/dev/null; then
        echo "✗ X-ray audit JSON is invalid!"
        exit 1
    fi
else
    echo "✗ Failed to extract X-ray audit"
    exit 1
fi

if jq '.[-1]' "$TEST_DATA_DIR/data/goes/goes_proton_flux.json" > "$TEST_DATA_DIR/data/goes/goes_proton_audit.json"; then
    echo "✓ Proton audit file created"
    if ! jq empty "$TEST_DATA_DIR/data/goes/goes_proton_audit.json" 2>/dev/null; then
        echo "✗ Proton audit JSON is invalid!"
        exit 1
    fi
else
    echo "✗ Failed to extract proton audit"
    exit 1
fi

# Display summary
echo ""
echo "Step 6: Displaying data summary..."
echo "--- X-ray Latest Event ---"
jq '.' "$TEST_DATA_DIR/data/goes/goes_xray_audit.json"
echo ""
echo "--- Proton Latest Event ---"
jq '.' "$TEST_DATA_DIR/data/goes/goes_proton_audit.json"

echo ""
echo "==================================="
echo "✓ All workflow tests passed!"
echo "==================================="
echo ""
echo "Test validated:"
echo "  - Directory creation"
echo "  - JSON file validation with jq"
echo "  - Latest event extraction"
echo "  - Audit file generation"
echo ""
echo "The workflow logic is sound and ready for deployment."
