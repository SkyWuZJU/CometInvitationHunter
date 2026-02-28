#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_FILE="$ROOT_DIR/.clawdbot/active-tasks.json"
RUNNER="$ROOT_DIR/.clawdbot/run-agent.sh"
MAX_RETRIES="${SWARM_MAX_RETRIES:-3}"

usage() {
  cat <<'EOF'
Usage:
  retry-agent.sh <task-id> [--force]

Notes:
- Retries only failed tasks by default.
- Max retries defaults to 3 (override with SWARM_MAX_RETRIES).
EOF
}

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required" >&2
  exit 1
fi
if ! command -v codex >/dev/null 2>&1; then
  echo "codex is required" >&2
  exit 1
fi
[[ -x "$RUNNER" ]] || { echo "Missing runner: $RUNNER" >&2; exit 1; }

if [[ ! -f "$DB_FILE" ]]; then
  echo "No task registry found: $DB_FILE" >&2
  exit 1
fi

task_id=""
force="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force)
      force="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ -z "$task_id" ]]; then
        task_id="$1"
      else
        echo "Unexpected arg: $1" >&2
        usage >&2
        exit 1
      fi
      shift
      ;;
  esac
done

if [[ -z "$task_id" ]]; then
  usage >&2
  exit 1
fi

entry="$(jq -c --arg id "$task_id" '.[] | select(.task_id==$id)' "$DB_FILE")"
if [[ -z "$entry" ]]; then
  echo "Task not found: $task_id" >&2
  exit 1
fi

status="$(jq -r '.status' <<<"$entry")"
if [[ "$status" != "failed" && "$force" != "true" ]]; then
  echo "Task '$task_id' is '$status'. Use --force to retry anyway." >&2
  exit 1
fi

retries="$(jq -r '.retries // 0' <<<"$entry")"
if (( retries >= MAX_RETRIES )); then
  echo "Retry limit reached for '$task_id' ($retries/$MAX_RETRIES)." >&2
  exit 1
fi

worktree="$(jq -r '.worktree' <<<"$entry")"
prompt_file="$(jq -r '.prompt_file' <<<"$entry")"
log_file="$(jq -r '.log_file' <<<"$entry")"
marker_file="$(jq -r '.marker_file' <<<"$entry")"
mode="$(jq -r '.mode // "full-auto"' <<<"$entry")"
model="$(jq -r '.model // ""' <<<"$entry")"

if [[ ! -d "$worktree" ]]; then
  echo "Worktree missing: $worktree" >&2
  exit 1
fi
if [[ ! -f "$prompt_file" ]]; then
  echo "Prompt file missing: $prompt_file" >&2
  exit 1
fi

prompt_text="$(cat "$prompt_file")"

cmd=(codex exec)
case "$mode" in
  full-auto) cmd+=(--full-auto) ;;
  yolo) cmd+=(--yolo) ;;
  plain) ;;
  *)
    echo "Unknown mode '$mode', falling back to plain." >&2
    ;;
esac
if [[ -n "$model" ]]; then
  cmd+=(--model "$model")
fi
cmd+=("$prompt_text")

rm -f "$marker_file"
nohup "$RUNNER" "$worktree" "$marker_file" "$log_file" "${cmd[@]}" >/dev/null 2>&1 &
pid="$!"

now_ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
now_epoch="$(date +%s)"

updated_json="$(jq \
  --arg id "$task_id" \
  --arg status "running" \
  --arg ts "$now_ts" \
  --argjson epoch "$now_epoch" \
  --argjson pid "$pid" \
  'map(
    if .task_id==$id then
      .status=$status
      | .pid=$pid
      | .exit_code=null
      | .retries=((.retries // 0) + 1)
      | .updated_at=$ts
      | .updated_at_epoch=$epoch
      | .last_checked_at=$ts
      | .last_checked_at_epoch=$epoch
    else
      .
    end
  )' "$DB_FILE")"

printf '%s\n' "$updated_json" > "$DB_FILE"

echo "Retried $task_id (pid=$pid, retries=$((retries + 1))/$MAX_RETRIES)"
