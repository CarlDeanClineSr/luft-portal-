# Tests Directory

This directory contains test scripts for validating LUFT portal workflows and functionality.

## GOES Workflow Tests

### test_goes_workflow.sh

Tests the GOES data audit workflow logic without requiring network access.

**What it tests:**
- Directory creation (data/goes)
- JSON file validation with jq
- Latest event extraction from GOES data
- Audit file generation

**How to run:**
```bash
./tests/test_goes_workflow.sh
```

**Expected output:**
The test creates mock GOES X-ray and proton flux data, validates the JSON structure, extracts the latest events, and generates audit files - all operations performed by the actual workflow.

## Adding New Tests

When adding new test scripts:
1. Make them executable: `chmod +x tests/your_test.sh`
2. Use clear step-by-step output with ✓/✗ indicators
3. Clean up temporary files in a trap handler
4. Return appropriate exit codes (0 for success, non-zero for failure)
