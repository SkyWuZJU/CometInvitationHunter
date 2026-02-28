#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAW_DIR="$ROOT_DIR/.clawdbot"
DB_FILE="$CLAW_DIR/active-tasks.json"

usage() {
  cat <<'EOF'
Usage:
  scripts/swarm.sh spawn <task-id> <prompt text...>
  scripts/swarm.sh check
  scripts/swarm.sh retry <task-id> [--force]
  scripts/swarm.sh cleanup [--hours N]
  scripts/swarm.sh list

Examples:
  scripts/swarm.sh spawn feat-auth "Implement OAuth token refresh and tests"
  scripts/swarm.sh check
  scripts/swarm.sh retry feat-auth
  scripts/swarm.sh cleanup --hours 48
EOF
}

cmd="${1:-help}"
if [[ $# -gt 0 ]]; then
  shift
fi

case "$cmd" in
  spawn)
    "$CLAW_DIR/spawn-agent.sh" "$@"
    ;;
  check)
    "$CLAW_DIR/check-agents.sh" "$@"
    ;;
  retry)
    "$CLAW_DIR/retry-agent.sh" "$@"
    ;;
  cleanup)
    "$CLAW_DIR/cleanup-worktrees.sh" "$@"
    ;;
  list)
    if ! command -v jq >/dev/null 2>&1; then
      echo "jq is required" >&2
      exit 1
    fi
    if [[ ! -f "$DB_FILE" ]] || jq -e 'length == 0' "$DB_FILE" >/dev/null; then
      echo "No swarm tasks yet."
      exit 0
    fi

    printf '%-20s %-8s %-8s %-6s %-18s %s\n' "TASK" "STATUS" "PID" "TRY" "UPDATED" "BRANCH"
    jq -r '.[] | [
      .task_id,
      .status,
      (.pid|tostring),
      (.retries|tostring),
      (.updated_at // "-"),
      .branch
    ] | @tsv' "$DB_FILE" | while IFS=$'\t' read -r task status pid retries updated branch; do
      printf '%-20s %-8s %-8s %-6s %-18s %s\n' "$task" "$status" "$pid" "$retries" "$updated" "$branch"
    done
    ;;
  help|-h|--help)
    usage
    ;;
  *)
    echo "Unknown command: $cmd" >&2
    usage >&2
    exit 1
    ;;
esac
