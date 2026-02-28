#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_FILE="$ROOT_DIR/.clawdbot/active-tasks.json"

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required" >&2
  exit 1
fi

if [[ ! -f "$DB_FILE" ]]; then
  printf '[]\n' > "$DB_FILE"
fi

if jq -e 'length == 0' "$DB_FILE" >/dev/null; then
  echo "No swarm tasks yet."
  exit 0
fi

now_ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
now_epoch="$(date +%s)"

summarize_ci() {
  local pr_number="$1"
  local view_json statuses

  view_json="$(cd "$ROOT_DIR" && gh pr view "$pr_number" --json statusCheckRollup 2>/dev/null || true)"
  if [[ -z "$view_json" ]]; then
    echo "unknown"
    return
  fi

  statuses="$(jq -r '[.statusCheckRollup[]? | (.conclusion // .state // .status // "UNKNOWN")] | join(" ")' <<<"$view_json")"

  if [[ -z "$statuses" ]]; then
    echo "none"
  elif grep -Eq 'FAIL|ERROR|CANCEL|TIMEOUT|ACTION_REQUIRED|STARTUP_FAILURE' <<<"$statuses"; then
    echo "failing"
  elif grep -Eq 'PENDING|IN_PROGRESS|QUEUED|WAITING|REQUESTED' <<<"$statuses"; then
    echo "pending"
  elif grep -Eq 'SUCCESS|NEUTRAL|SKIPPED' <<<"$statuses"; then
    echo "passing"
  else
    echo "mixed"
  fi
}

tmp_entries="$(mktemp)"
trap 'rm -f "$tmp_entries"' EXIT

printf '%-20s %-8s %-8s %-6s %-10s %s\n' "TASK" "STATUS" "PID" "TRY" "CI" "PR"

while IFS= read -r entry; do
  task_id="$(jq -r '.task_id' <<<"$entry")"
  status="$(jq -r '.status' <<<"$entry")"
  pid="$(jq -r '.pid // 0' <<<"$entry")"
  retries="$(jq -r '.retries // 0' <<<"$entry")"
  marker_file="$(jq -r '.marker_file' <<<"$entry")"
  branch="$(jq -r '.branch' <<<"$entry")"

  updated_entry="$entry"

  # Transition running task to done/failed when process exits.
  if [[ "$status" == "running" ]]; then
    if [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
      :
    else
      exit_code=1
      if [[ -f "$marker_file" ]]; then
        exit_code="$(jq -r '.exit_code // 1' "$marker_file" 2>/dev/null || echo 1)"
      fi

      if [[ "$exit_code" == "0" ]]; then
        status="done"
      else
        status="failed"
      fi

      updated_entry="$(jq \
        --arg status "$status" \
        --arg ts "$now_ts" \
        --argjson epoch "$now_epoch" \
        --argjson exit_code "$exit_code" \
        '.status=$status
         | .exit_code=$exit_code
         | .updated_at=$ts
         | .updated_at_epoch=$epoch' <<<"$updated_entry")"
    fi
  fi

  ci_status="$(jq -r '.ci_status // "n/a"' <<<"$updated_entry")"
  pr_number="$(jq -r '.pr_number // empty' <<<"$updated_entry")"
  pr_url="$(jq -r '.pr_url // empty' <<<"$updated_entry")"

  # Best-effort PR and CI enrichment.
  if command -v gh >/dev/null 2>&1 && git -C "$ROOT_DIR" remote get-url origin >/dev/null 2>&1; then
    pr_json="$(cd "$ROOT_DIR" && gh pr list --head "$branch" --state all --limit 1 --json number,url,state 2>/dev/null || true)"
    if [[ -n "$pr_json" ]] && [[ "$(jq -r 'length' <<<"$pr_json")" != "0" ]]; then
      pr_number="$(jq -r '.[0].number' <<<"$pr_json")"
      pr_url="$(jq -r '.[0].url' <<<"$pr_json")"
      ci_status="$(summarize_ci "$pr_number")"

      updated_entry="$(jq \
        --argjson pr_number "$pr_number" \
        --arg pr_url "$pr_url" \
        --arg ci_status "$ci_status" \
        '.pr_number=$pr_number | .pr_url=$pr_url | .ci_status=$ci_status' <<<"$updated_entry")"
    else
      updated_entry="$(jq --arg ci_status "$ci_status" '.ci_status=$ci_status' <<<"$updated_entry")"
    fi
  fi

  updated_entry="$(jq --arg ts "$now_ts" --argjson epoch "$now_epoch" '.last_checked_at=$ts | .last_checked_at_epoch=$epoch' <<<"$updated_entry")"

  status="$(jq -r '.status' <<<"$updated_entry")"
  pid="$(jq -r '.pid // 0' <<<"$updated_entry")"
  retries="$(jq -r '.retries // 0' <<<"$updated_entry")"
  ci_status="$(jq -r '.ci_status // "n/a"' <<<"$updated_entry")"
  pr_number="$(jq -r '.pr_number // empty' <<<"$updated_entry")"

  if [[ -n "$pr_number" ]]; then
    pr_cell="#$pr_number"
  else
    pr_cell="-"
  fi

  printf '%-20s %-8s %-8s %-6s %-10s %s\n' "$task_id" "$status" "$pid" "$retries" "$ci_status" "$pr_cell"
  printf '%s\n' "$updated_entry" >> "$tmp_entries"
done < <(jq -c '.[]' "$DB_FILE")

jq -s '.' "$tmp_entries" > "$DB_FILE"
