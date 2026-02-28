# .clawdbot Agent Swarm Toolkit (Lean)

Minimal local orchestration for parallel coding tasks with isolated git worktrees.

## Architecture

- **Orchestrator scripts** (`.clawdbot/*.sh`) manage lifecycle.
- **Workers** are background `codex` runs (one per task).
- **Registry** is `.clawdbot/active-tasks.json` (single source of truth).
- **Isolation** is via git worktrees under `.worktrees/<task-id>`.

No heavy queue or database. Just bash + `jq` + git.

## What’s Included

- `.clawdbot/spawn-agent.sh` — create worktree + branch, store metadata, launch codex.
- `.clawdbot/check-agents.sh` — deterministic status check (PID + exit marker), best-effort PR/CI summary via `gh`.
- `.clawdbot/retry-agent.sh` — retry failed task (max 3 by default).
- `.clawdbot/cleanup-worktrees.sh` — remove done worktrees older than N hours.
- `.clawdbot/run-agent.sh` — background worker wrapper writes exit marker JSON.
- `scripts/swarm.sh` — friendly wrapper (`spawn|check|retry|cleanup|list`).

## Quick Start

From repo root:

```bash
# 1) Spawn a task (creates branch swarm/<task-id> and .worktrees/<task-id>)
scripts/swarm.sh spawn bugfix-login "Fix OAuth callback edge case and add tests."

# 2) Check status (updates registry and prints concise table)
scripts/swarm.sh check

# 3) Retry a failed task
scripts/swarm.sh retry bugfix-login

# 4) Remove stale done worktrees (older than 24h by default)
scripts/swarm.sh cleanup --hours 24

# 5) List current registry entries
scripts/swarm.sh list
```

## Definition of Done (recommended)

Treat a task as "ready for merge" only when:

1. PR exists
2. CI is passing
3. Required tests pass locally/in CI
4. Any required screenshots/docs are attached (if UI changed)

## Notes

- `tmux` is optional and **not required** by this toolkit.
- Current implementation supports `--agent codex` only.
- Default spawn mode is `full-auto` (`codex exec --full-auto ...`).
