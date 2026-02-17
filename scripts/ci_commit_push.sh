#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# ci_commit_push.sh — Reusable commit/push helper for GitHub Actions workflows
# =============================================================================
# 
# Usage:
#   scripts/ci_commit_push.sh "<add-globs>" "Commit message"
# 
# Example:
#   scripts/ci_commit_push.sh "results/** figures/**" "Historical OMNI χ validation (2006–2015)"
#
# This script handles the common non-fast-forward push race condition by:
# 1. Fetching and rebasing onto the latest remote main
# 2. Staging and committing only if there are changes
# 3. Pushing with exponential backoff retry logic
#
# Requirements:
# - Must run from within a git repository
# - fetch-depth: 0 recommended in checkout step for clean rebase
# - GITHUB_TOKEN environment variable should be set
# =============================================================================

FILES="${1:-.}"
MSG="${2:-Automated update}"
CSV_CONFLICT_GREP='^data/.*\.csv$'
DASHBOARD_CONFLICT_GREP='^docs/(manifest_master_index\.yaml|manifest_dashboard\.html)$'

resolve_csv_conflicts() {
  local conflicts
  conflicts=$(git diff --name-only --diff-filter=U | grep -E "${CSV_CONFLICT_GREP}" || true)
  if [ -n "${conflicts}" ]; then
    echo "Auto-resolving CSV conflicts with 'ours' strategy..."
    while IFS= read -r path; do
      [ -z "$path" ] && continue
      git checkout --ours -- "$path"
      git add "$path"
    done <<< "${conflicts}"
    return 0
  fi
  return 1
}

resolve_dashboard_conflicts() {
  local conflicts
  conflicts=$(git diff --name-only --diff-filter=U | grep -E "${DASHBOARD_CONFLICT_GREP}" || true)
  if [ -n "${conflicts}" ]; then
    echo "Auto-resolving dashboard conflicts with 'ours' strategy..."
    while IFS= read -r path; do
      [ -z "$path" ] && continue
      git checkout --ours -- "$path"
      git add "$path"
    done <<< "${conflicts}"
    return 0
  fi
  return 1
}

# Configure git identity for the commit
git config --global user.name "engine-bot"
git config --global user.email "engine-bot@users.noreply.github.com"

# Stage files first (using || true to handle cases where globs don't match)
# Note: We intentionally use unquoted ${FILES} to allow word splitting for multiple file patterns
echo "Staging files: ${FILES}"
# shellcheck disable=SC2086
git add ${FILES} || true

# Fetch the latest state of the remote main branch
echo "Fetching latest remote main..."
git fetch origin main

# Re-sync local state with remote; prefer rebase, fall back to merge if conflicts
echo "Rebasing onto origin/main..."
rebase_result=0
git rebase --autostash origin/main || rebase_result=$?

# Check for unmerged files (can happen from either rebase conflicts or autostash conflicts)
if [ $rebase_result -ne 0 ] || git diff --name-only --diff-filter=U | grep -q .; then
  echo "Conflicts detected. Checking for auto-resolvable conflicts..."
  csv_resolved=false
  dashboard_resolved=false
  
  if resolve_csv_conflicts; then
    csv_resolved=true
  fi
  
  if resolve_dashboard_conflicts; then
    dashboard_resolved=true
  fi
  
  if [ "$csv_resolved" = true ] || [ "$dashboard_resolved" = true ]; then
    if git rebase --continue; then
      echo "Rebase completed after auto-resolving conflicts."
    else
      echo "Rebase --continue failed after resolving conflicts. Aborting."
      git rebase --abort 2>/dev/null || true
      exit 1
    fi
  else
    echo "No auto-resolvable conflicts found. Aborting rebase."
    git rebase --abort 2>/dev/null || true
    exit 1
  fi
fi

# Check if there are any staged changes to commit
if git diff --staged --quiet; then
  echo "No changes to commit."
  exit 0
fi

# Commit the staged changes
echo "Committing: ${MSG}"
git commit -m "${MSG}"

# Retry push with exponential backoff to avoid races with other concurrent jobs
echo "Pushing to origin/main with retry logic..."
for i in 1 2 3 4 5; do
  if git push origin HEAD:main; then
    echo "Push succeeded."
    exit 0
  fi
  echo "Push failed (attempt $i). Re-syncing and retrying..."
  pull_result=0
  git pull --rebase --autostash origin main || pull_result=$?
  
  # Check for unmerged files (can happen from either rebase conflicts or autostash conflicts)
  if [ $pull_result -ne 0 ] || git diff --name-only --diff-filter=U | grep -q .; then
    echo "Conflicts detected. Attempting to resolve conflicts..."
    csv_resolved=false
    dashboard_resolved=false
    
    if resolve_csv_conflicts; then
      csv_resolved=true
    fi
    
    if resolve_dashboard_conflicts; then
      dashboard_resolved=true
    fi
    
    if [ "$csv_resolved" = true ] || [ "$dashboard_resolved" = true ]; then
      if git rebase --continue; then
        echo "Rebase continued after resolving conflicts."
      else
        echo "Unable to continue rebase after conflict resolution. Aborting."
        git rebase --abort 2>/dev/null || true
        exit 1
      fi
    else
      echo "No auto-resolvable conflicts found. Aborting."
      git rebase --abort 2>/dev/null || true
      exit 1
    fi
  fi
  sleep $((5 * i))
done

echo "Push failed after 5 retries."
exit 1
