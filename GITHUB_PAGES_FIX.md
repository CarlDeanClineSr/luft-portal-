# GitHub Pages Deployment Fix

## Problem
GitHub Pages builds were being cancelled due to race conditions caused by multiple workflows pushing to the `main` branch simultaneously. Each push triggered a new GitHub Pages build, and concurrent builds would cancel each other.

## Root Causes
1. **Multiple concurrent pushes**: ~20 scheduled workflows push to `main` throughout the day
2. **Automatic GitHub Pages builds**: Each push to `main` triggered a new Pages build
3. **Race condition**: Multiple builds running simultaneously would cancel each other
4. **Incomplete deployment workflow**: The `imperial_unified_engine.yml` had a broken `deploy-site` job that was missing critical steps

## Solution

### 1. Created Dedicated Pages Deployment Workflow
Created `.github/workflows/pages-deployment.yml` as the single source of truth for GitHub Pages deployment:
- Triggers on push to `main` branch
- Includes proper deployment steps:
  - Checkout repository
  - Setup Pages configuration
  - Upload Pages artifact
  - Deploy to GitHub Pages

### 2. Added Concurrency Controls
Added concurrency group to prevent race conditions:
```yaml
concurrency:
  group: pages-deployment
  cancel-in-progress: false
```
This ensures:
- Only one deployment runs at a time
- New deployments wait in queue instead of canceling in-progress ones
- No more cancelled builds

### 3. Fixed imperial_unified_engine.yml
- Removed the broken `deploy-site` job
- Removed unnecessary `pages: write` and `id-token: write` permissions
- This workflow now only handles data sync, letting the dedicated pages workflow handle deployment

## How It Works Now
1. Multiple workflows can push to `main` at any time
2. Each push triggers the `pages-deployment.yml` workflow
3. Concurrency controls ensure deployments run sequentially, not simultaneously
4. No more cancellations - deployments complete successfully

## Verification
After merging this PR, you should see:
- GitHub Pages builds complete successfully without cancellation
- Only one "pages build and deployment" running at a time
- Queued deployments wait for the current one to finish

## Files Changed
- `.github/workflows/pages-deployment.yml` (new)
- `.github/workflows/imperial_unified_engine.yml` (modified)
