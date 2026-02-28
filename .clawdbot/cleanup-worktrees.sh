#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_FILE="$ROOT_DIR/.clawdbot/active-tasks.json"

usage() {
  cat <<'EOF'
Usage:
  cleanup-worktrees.sh [--hours N]

Removes local worktrees for tasks with status=done and updated_at older than N hours.
Default N is 24.
EOF
}

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required" >&2
  exit 1
fi

hours=24
while [[ $# -gt 0 ]]; do
  case "$1" in
    --hours)
      hours="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ ! "$hours" =~ ^[0-9]+$ ]]; then
  echo "--hours must be a non-negative integer" >&2
  exit 1
fi

if [[ ! -f "$DB_FILE" ]]; then
  echo "No task registry found: $DB_FILE"
  exit 0
fi

if jq -e 'length == 0' "$DB_FILE" >/dev/null; then
  echo "No swarm tasks to clean."
  exit 0
fi

now_epoch="$(date +%s)"
cutoff_epoch=$((now_epoch - (hours * 3600)))
now_ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

removed_count=0
tmp_entries="$(mktemp)"
trap 'rm -f "$tmp_entries"' EXIT

while IFS= read -r entry; do
  status="$(jq -r '.status' <<<"$entry")"
  updated_epoch="$(jq -r '.updated_at_epoch // 0' <<<"$entry")"
  worktree="$(jq -r '.worktree // ""' <<<"$entry")"
  task_id="$(jq -r '.task_id' <<<"$entry")"

  updated_entry="$entry"

  if [[ "$status" == "done" ]] && (( updated_epoch > 0 && updated_epoch <= cutoff_epoch )); then
    if [[ -n "$worktree" && -d "$worktree" ]]; then
      if git -C "$ROOT_DIR" worktree remove --force "$worktree" >/dev/null 2>&1; then
        updated_entry="$(jq \
          --arg ts "$now_ts" \
          --argjson epoch "$now_epoch" \
          '.worktree_removed=true
           | .worktree_removed_at=$ts
           | .worktree_removed_at_epoch=$epoch' <<<"$updated_entry")"
        removed_count=$((removed_count + 1))
        echo "Removed worktree for $task_id"
      fi
    fi
  fi

  printf '%s\n' "$updated_entry" >> "$tmp_entries"
done < <(jq -c '.[]' "$DB_FILE")

jq -s '.' "$tmp_entries" > "$DB_FILE"

echo "Cleanup complete. Removed $removed_count worktree(s)."
