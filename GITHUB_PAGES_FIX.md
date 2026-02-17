# GitHub Pages Deployment Fix

## Problem
GitHub Pages builds were being cancelled due to race conditions caused by multiple workflows pushing to the `main` branch simultaneously. Each push triggered a new GitHub Pages build, and concurrent builds would cancel each other.

## Root Causes
1. **Multiple concurrent pushes**: ~20 scheduled workflows push to `main` throughout the day
2. **Automatic GitHub Pages builds**: Each push to `main` triggered a new Pages build
3. **Race condition**: Multiple builds running simultaneously would cancel each other
4. **Excessive deployments**: Pages were being deployed on every push, which was unnecessary

## Solution (Updated: 2026-02-01)

### 1. Scheduled Deployment (Current Fix)
Modified `.github/workflows/pages-deployment.yml` to run on a schedule instead of on every push:
- **Schedule**: Once daily at 00:20 UTC
- **Local time**: 6:20 PM CST (winter) / 7:20 PM CDT (summer)
- **Cron expression**: `'20 0 * * *'`
- **Manual trigger**: Still available via `workflow_dispatch` for on-demand deployments

This approach:
- Eliminates deployment cancellations caused by concurrent pushes
- Reduces unnecessary deployments
- Provides predictable deployment schedule
- Allows manual deployments when needed

### 2. Concurrency Controls (Already in Place)
Concurrency group prevents race conditions:
```yaml
concurrency:
  group: pages-deployment
  cancel-in-progress: false
```
This ensures:
- Only one deployment runs at a time
- New deployments wait in queue instead of canceling in-progress ones
- No more cancelled builds

### 3. Previous Fixes
- Created dedicated Pages deployment workflow
- Removed broken `deploy-site` job from `imperial_unified_engine.yml`
- Removed unnecessary `pages: write` and `id-token: write` permissions from other workflows

## How It Works Now
1. Multiple workflows can push to `main` at any time (no effect on Pages deployment)
2. Pages deployment runs automatically once per day at 00:20 UTC (6:20 PM CST / 7:20 PM CDT)
3. Manual deployments can be triggered via GitHub Actions UI if needed
4. No more cancellations - single daily deployment completes successfully

## Manual Deployment
If you need to deploy Pages before the scheduled time:
1. Go to the GitHub repository
2. Click on "Actions" tab
3. Select "Deploy to GitHub Pages" workflow
4. Click "Run workflow" button
5. Select the branch (main) and click "Run workflow"

## Verification
After this change, you should see:
- GitHub Pages builds run once per day at 00:20 UTC (6:20 PM CST / 7:20 PM CDT)
- No more cancellations due to concurrent pushes
- Successful deployment every day
- Manual deployments work when needed

## Files Changed
- `.github/workflows/pages-deployment.yml` (modified to use schedule trigger)
- `GITHUB_PAGES_FIX.md` (updated documentation)
