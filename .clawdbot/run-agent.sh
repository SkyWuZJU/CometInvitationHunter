#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 4 ]]; then
  echo "Usage: $0 <worktree> <marker-file> <log-file> <command...>" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required" >&2
  exit 1
fi

worktree="$1"
marker_file="$2"
log_file="$3"
shift 3

mkdir -p "$(dirname "$marker_file")" "$(dirname "$log_file")"

set +e
(
  cd "$worktree"
  "$@"
) >>"$log_file" 2>&1
exit_code=$?
set -e

completed_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
completed_at_epoch="$(date +%s)"

jq -n \
  --argjson exit_code "$exit_code" \
  --arg completed_at "$completed_at" \
  --argjson completed_at_epoch "$completed_at_epoch" \
  '{
    exit_code: $exit_code,
    completed_at: $completed_at,
    completed_at_epoch: $completed_at_epoch
  }' > "$marker_file"

exit "$exit_code"
