#!/usr/bin/env bash
# Open each ticket under tickets/ as a GitHub issue on the current repo.
# Requires: gh CLI, authenticated, run from the repo root.
# Usage: scripts/open_tickets.sh [--label demo]
set -euo pipefail

LABEL="${2:-demo}"

for f in tickets/*.md; do
  title="$(head -1 "$f" | sed 's/^# //')"
  body="$(tail -n +2 "$f")"
  echo "Opening: $title"
  gh issue create --title "$title" --body "$body" --label "$LABEL" >/dev/null
done

echo "Done. Trigger Open SWE by commenting '@openswe' on an issue, or from the dashboard."
