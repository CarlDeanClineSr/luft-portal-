# WORKFLOW FIXES - Correcting Agent's Broken Changes

## Problem

Previous agent deleted 6 Python files but left 3 workflows calling them, causing failures.

## Broken Workflows (FIXED)

### 1. `.github/workflows/daily_maven_mars.yml`
**Problem:** Called deleted `tools/fetch_maven_mars.py` (used standard plasma calculations)

**Fix Applied:**
- Disabled automatic schedule (was failing daily at 05:00 UTC)
- Changed to use existing MAVEN data at `data/maven_mars/`
- Calls `tools/analyze_mars_chi.py` for χ-framework analysis
- Can still be triggered manually via workflow_dispatch

**Rationale:** MAVEN data already in repository. No need to fetch with standard physics formulas.

### 2. `.github/workflows/maven_realtime_10min.yml`
**Problem:** Called deleted `tools/fetch_maven_mars.py` every 10 minutes

**Fix Applied:**
- Disabled automatic schedule (was failing every 10 minutes)
- Simplified to validation-only workflow
- Documents how to add new data properly
- Can be triggered manually to check data status

**Rationale:** Was running every 10 minutes calling non-existent script. Existing data is sufficient.

### 3. `.github/workflows/physics_repairs.yml`
**Problem:** Called deleted `scripts/psp_ingest_validate.py` (used standard plasma calculations)

**Fix Applied:**
- Disabled automatic schedule (was failing every 6 hours)
- Simplified to data validation workflow
- Documents steps to re-enable with χ-framework compliant script
- Can be triggered manually to check PSP data status

**Rationale:** PSP data already exists at `data/psp/`. Script deletion broke workflow.

## What Still Works

**36 workflows fixed by previous agent:**
- ✅ Git rebase added correctly (prevents concurrent push conflicts)
- ✅ Bot naming standardized to `github-actions[bot]`
- ✅ All other workflows functional

**Data ingestion workflows (unaffected by deletions):**
- ✅ GOES X-ray and particle data
- ✅ DSCOVR solar wind
- ✅ CME heartbeat logging
- ✅ Magnetometer networks
- ✅ Solar wind monitoring
- ✅ All other real-time data streams

## Imperial Lexicon Guard Status

**Properly configured - will NOT break legitimate content:**
- ✅ Excludes `papers/` directory (research papers can mention standard terms)
- ✅ Excludes `capsules/` directory (documentation safe)
- ✅ Excludes `docs/` directory (all documentation safe)
- ✅ Excludes `data/` directory (data files safe)
- ✅ Excludes `analyses/` directory (analysis files safe)
- ✅ Only scans `.py`, `.yml`, `.yaml` files in root and scripts/tools
- ✅ Runs as WARNING only for CDAWeb imports (not blocking)

**Guard correctly blocks in source code only:**
- Python scripts using standard plasma formulas
- Workflow files calling standard physics libraries
- New code files introducing standard model terminology

## Core Imperial Physics Files

**Verified UNTOUCHED by all changes:**
- ✅ `imperial_constants_v1_0.py` - Core χ = 0.15 framework
- ✅ `chi_calculator.py` - Boundary validation tool
- ✅ `engine_core.py` - Imperial Math engine
- ✅ `chi_015_directive.yaml` - Framework rules
- ✅ `universal_boundary_engine.py` - Discovery validation

## Summary

**Fixed:** 3 broken workflows (disabled automatic runs, kept manual trigger)
**Preserved:** 36 workflow fixes from previous agent
**Protected:** Core Imperial Physics files unchanged
**Safeguarded:** Papers and documentation won't be blocked by guard

**Status:** Repository workflows now functional. No scripts calling deleted files.
