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

# Configure git identity for the commit
git config --global user.name "engine-bot"
git config --global user.email "engine-bot@users.noreply.github.com"

# Fetch the latest state of the remote main branch
echo "Fetching latest remote main..."
git fetch origin main

# Re-sync local state with remote; prefer rebase, fall back to merge if conflicts
echo "Rebasing onto origin/main..."
if ! git rebase --autostash origin/main; then
  echo "Rebase failed. Checking for CSV conflicts..."
  if resolve_csv_conflicts && git rebase --continue; then
    echo "Rebase completed after auto-resolving CSV conflicts."
  else
    echo "Non-CSV conflict or unresolved rebase. Aborting."
    git rebase --abort 2>/dev/null || true
    exit 1
  fi
fi

# Stage files (using || true to handle cases where globs don't match)
# Note: We intentionally use unquoted ${FILES} to allow word splitting for multiple file patterns
echo "Staging files: ${FILES}"
# shellcheck disable=SC2086
git add ${FILES} || true

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
  if ! git pull --rebase --autostash origin main; then
    echo "Pull --rebase failed. Attempting to resolve CSV conflicts..."
    if resolve_csv_conflicts && git rebase --continue; then
      echo "Rebase continued after resolving CSV conflicts."
    else
      echo "Unable to resolve conflicts during pull. Aborting."
      git rebase --abort 2>/dev/null || true
      exit 1
    fi
  fi
  sleep $((5 * i))
done

echo "Push failed after 5 retries."
exit 1
