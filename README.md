# ledger-service — Open SWE software-factory demo

A small, realistic Python service plus three Jira-style tickets, built so a coding agent (Open SWE) can take a ticket → plan → implement in a sandbox → open a PR, the same loop many teams run by hand on developer laptops.

```
ledger_service/   FastAPI app + in-memory ledger (accounts, deposits, transfers, statements)
tests/            pytest suite (13 tests, all green on main)
tickets/          LEDGER-142 (bug) · LEDGER-157 (feature) · LEDGER-163 (refactor)
AGENTS.md         repo instructions the agent reads (conventions, checks, guardrails)
.github/          CI running pytest on every PR
scripts/          open_tickets.sh — turns tickets/ into GitHub issues
```

## Run it locally

```bash
uv sync --extra dev
uv run pytest
uv run uvicorn ledger_service.api:app --reload   # http://127.0.0.1:8000/docs
```

## Demo runbook (do the night before)

1. **Push to GitHub.** Done: [pablolacombe-langchain/ledger-service-demo](https://github.com/pablolacombe-langchain/ledger-service-demo). The Open SWE GitHub App must be installed on this account and the repo must be in the deployment's allowed orgs.
2. **Open the tickets as issues:** `gh label create demo` once, then `scripts/open_tickets.sh`. Done: issues #1–#3.
3. **Pre-run one ticket** so a finished thread, trace and PR exist before the call (sandbox + model time is 5–15 min): comment `@openswe` on the LEDGER-142 issue, or start it from the Open SWE dashboard with `repo:pablolacombe-langchain/ledger-service-demo`.
4. **Check the trace** in LangSmith (`open-swe-agent` project): plan → `execute` calls in the sandbox (`uv sync`, `pytest`) → file edits → PR. Bookmark it.
5. **During the call**, kick off LEDGER-157 live, then switch to the pre-run LEDGER-142 thread/trace/PR while it works. Come back at the end to show progress.

## Why these three tickets

| Ticket | Shape | What it shows |
|---|---|---|
| LEDGER-142 | one-line bug, tests missing | plan → test-first → small PR; CI green |
| LEDGER-157 | feature across models, core, API | planning, subagents, larger diff, review |
| LEDGER-163 | cross-cutting refactor | validation in the sandbox, split commits, human review gate |

## Mapping to a typical manual flow

| Manual step | Here |
|---|---|
| Jira ticket | GitHub issue (Jira → HTTP channel/webhook in MDA) |
| Repo + plan | Open SWE workspace, `AGENTS.md`, planning + subagents |
| Human clarify/approve | thread replies; approval before workflow-file changes |
| Coding agent on laptops | per-thread LangSmith sandbox, many in parallel |
| PR | GitHub delivery, Open SWE Review, `/baby-sit` CI monitoring |
