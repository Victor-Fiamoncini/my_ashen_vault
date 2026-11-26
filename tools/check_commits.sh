#!/bin/sh
# Runs .githooks/commit-msg over every non-merge commit in a range, so CI enforces the same
# commit message rules as the local hook (CONTRIBUTING.md, "Commit messages").
# Usage: tools/check_commits.sh <base>..<head>
set -eu
range="$1"
hook="$(dirname "$0")/../.githooks/commit-msg"
msg=$(mktemp)
trap 'rm -f "$msg"' EXIT
status=0
for c in $(git rev-list --no-merges "$range"); do
  git log -1 --format=%B "$c" >"$msg"
  if ! sh "$hook" "$msg" 2>/dev/null; then
    echo "::error::commit $(git log -1 --format='%h %s' "$c")"
    sh "$hook" "$msg" || true
    status=1
  fi
done
exit $status
