#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_FILE="$ROOT_DIR/.clawdbot/active-tasks.json"
PROMPTS_DIR="$ROOT_DIR/.clawdbot/prompts"
LOGS_DIR="$ROOT_DIR/.clawdbot/logs"
WORKTREES_DIR="$ROOT_DIR/.worktrees"
RUNNER="$ROOT_DIR/.clawdbot/run-agent.sh"

usage() {
  cat <<'EOF'
Usage:
  spawn-agent.sh <task-id> <prompt text...>
  spawn-agent.sh --id <task-id> --prompt "..." [--agent codex] [--model MODEL] [--mode full-auto|yolo|plain] [--base REF]

Notes:
- Only --agent codex is currently supported.
- Base ref defaults to origin/main when available, otherwise main.
EOF
}

require_bin() {
  local bin="$1"
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "$bin is required" >&2
    exit 1
  fi
}

require_bin jq
require_bin git
require_bin codex
[[ -x "$RUNNER" ]] || { echo "Missing runner: $RUNNER" >&2; exit 1; }

task_id=""
prompt_text=""
agent="codex"
model="${SWARM_CODEX_MODEL:-gpt-5.3-codex}"
mode="${SWARM_CODEX_MODE:-full-auto}"
base_ref=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --id)
      task_id="${2:-}"
      shift 2
      ;;
    --prompt)
      prompt_text="${2:-}"
      shift 2
      ;;
    --agent)
      agent="${2:-}"
      shift 2
      ;;
    --model)
      model="${2:-}"
      shift 2
      ;;
    --mode)
      mode="${2:-}"
      shift 2
      ;;
    --base)
      base_ref="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    *)
      break
      ;;
  esac
done

if [[ -z "$task_id" && $# -gt 0 ]]; then
  task_id="$1"
  shift
fi

if [[ -z "$prompt_text" && $# -gt 0 ]]; then
  prompt_text="$*"
fi

if [[ -z "$task_id" || -z "$prompt_text" ]]; then
  usage >&2
  exit 1
fi

if [[ ! "$task_id" =~ ^[a-zA-Z0-9._-]+$ ]]; then
  echo "Invalid task-id: use only [a-zA-Z0-9._-]" >&2
  exit 1
fi

if [[ "$agent" != "codex" ]]; then
  echo "Unsupported agent '$agent'. Only 'codex' is supported for now." >&2
  exit 1
fi

case "$mode" in
  full-auto|yolo|plain) ;;
  *)
    echo "Invalid mode '$mode'. Use: full-auto | yolo | plain" >&2
    exit 1
    ;;
esac

mkdir -p "$PROMPTS_DIR" "$LOGS_DIR" "$WORKTREES_DIR"
[[ -f "$DB_FILE" ]] || printf '[]\n' > "$DB_FILE"

if jq -e --arg id "$task_id" '.[] | select(.task_id==$id)' "$DB_FILE" >/dev/null; then
  echo "Task already exists: $task_id" >&2
  exit 1
fi

if [[ -z "$base_ref" ]]; then
  base_ref="main"
  if git -C "$ROOT_DIR" remote get-url origin >/dev/null 2>&1; then
    git -C "$ROOT_DIR" fetch origin main:refs/remotes/origin/main >/dev/null 2>&1 || true
    if git -C "$ROOT_DIR" show-ref --verify --quiet refs/remotes/origin/main; then
      base_ref="origin/main"
    fi
  fi
fi

if ! git -C "$ROOT_DIR" rev-parse --verify "$base_ref" >/dev/null 2>&1; then
  echo "Base ref not found: $base_ref" >&2
  exit 1
fi

branch="swarm/$task_id"
worktree="$WORKTREES_DIR/$task_id"
prompt_file="$PROMPTS_DIR/$task_id.md"
log_file="$LOGS_DIR/$task_id.log"
marker_file="$LOGS_DIR/$task_id.exit.json"

if [[ -d "$worktree" ]]; then
  echo "Worktree already exists: $worktree" >&2
  exit 1
fi
if git -C "$ROOT_DIR" show-ref --verify --quiet "refs/heads/$branch"; then
  echo "Branch already exists: $branch" >&2
  exit 1
fi

git -C "$ROOT_DIR" worktree add -b "$branch" "$worktree" "$base_ref" >/dev/null

created_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
created_at_epoch="$(date +%s)"

cat > "$prompt_file" <<EOF
# Task: $task_id
# Agent: $agent
# Created: $created_at

$prompt_text
EOF

rm -f "$marker_file"

cmd=(codex exec)
case "$mode" in
  full-auto) cmd+=(--full-auto) ;;
  yolo) cmd+=(--yolo) ;;
  plain) ;;
esac
if [[ -n "$model" ]]; then
  cmd+=(--model "$model")
fi
cmd+=("$prompt_text")

nohup "$RUNNER" "$worktree" "$marker_file" "$log_file" "${cmd[@]}" >/dev/null 2>&1 &
pid="$!"

command_preview="$(printf '%q ' "${cmd[@]}")"

updated_json="$(jq \
  --arg task_id "$task_id" \
  --arg agent "$agent" \
  --arg model "$model" \
  --arg mode "$mode" \
  --arg branch "$branch" \
  --arg base_ref "$base_ref" \
  --arg worktree "$worktree" \
  --arg prompt_file "$prompt_file" \
  --arg log_file "$log_file" \
  --arg marker_file "$marker_file" \
  --arg status "running" \
  --arg command_preview "$command_preview" \
  --arg created_at "$created_at" \
  --arg updated_at "$created_at" \
  --argjson created_at_epoch "$created_at_epoch" \
  --argjson updated_at_epoch "$created_at_epoch" \
  --argjson retries 0 \
  --argjson pid "$pid" \
  '. + [{
    task_id:$task_id,
    agent:$agent,
    model:$model,
    mode:$mode,
    branch:$branch,
    base_ref:$base_ref,
    worktree:$worktree,
    prompt_file:$prompt_file,
    log_file:$log_file,
    marker_file:$marker_file,
    status:$status,
    pid:$pid,
    retries:$retries,
    command_preview:$command_preview,
    created_at:$created_at,
    created_at_epoch:$created_at_epoch,
    updated_at:$updated_at,
    updated_at_epoch:$updated_at_epoch,
    last_checked_at:$updated_at,
    last_checked_at_epoch:$updated_at_epoch
  }]' \
  "$DB_FILE")"
printf '%s\n' "$updated_json" > "$DB_FILE"

echo "Spawned $task_id (pid=$pid, branch=$branch, base=$base_ref, mode=$mode)"
