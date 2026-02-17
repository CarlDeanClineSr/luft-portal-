#!/usr/bin/env bash
set -euo pipefail

pathspec_string="${1:-}"
commit_message="${2:-chore: automated update}"

if [[ -z "$pathspec_string" ]]; then
  echo "No pathspec provided; nothing to commit."
  exit 0
fi

read -r -a pathspecs <<< "$pathspec_string"
git add -- "${pathspecs[@]}" || true

if git diff --cached --quiet; then
  echo "No changes detected for: $pathspec_string"
  exit 0
fi

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

git commit -m "$commit_message"
git push
