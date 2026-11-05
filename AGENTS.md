# AGENTS.md — ledger-service

Instructions for coding agents (Open SWE, dcode, Managed Deep Agents) working in this repo. Humans: read it too.

## What this is

A small FastAPI ledger: accounts, deposits, withdrawals, transfers, statements. Core rules live in `ledger_service/ledger.py`; HTTP routes in `ledger_service/api.py`; data shapes in `ledger_service/models.py`. State is in-memory on purpose.

## Setup and checks

```bash
uv sync --extra dev
uv run pytest            # must pass before you open a PR
uv run uvicorn ledger_service.api:app --reload   # optional, manual check
```

## Working on a ticket

1. Read the ticket in `tickets/` (or the GitHub issue). Restate the acceptance criteria in your plan.
2. Write or update tests first when the ticket describes behaviour. Put core tests in `tests/test_ledger.py`, HTTP tests in `tests/test_api.py`.
3. Keep business rules in `Ledger`, not in routes. Routes validate input, call the ledger, map `LedgerError` subclasses to HTTP status codes via `_raise_http`.
4. Run the full test suite. Do not weaken or delete existing tests to make a change pass.
5. Open a PR titled `<TICKET-KEY>: <short summary>` with a description that lists what changed and how it was verified. Link the ticket.

## Conventions

- Python 3.11+, type hints everywhere, `from __future__ import annotations`.
- Money: amounts are positive; see `tickets/LEDGER-163` for the planned move to integer cents. Until then, do not introduce new float arithmetic shortcuts.
- Error mapping: `UnknownAccount → 404`, `InsufficientFunds → 409`, `DailyLimitExceeded → 409`, other `LedgerError → 400`.
- Statements are newest-first.
- Dates are timezone-aware UTC (`utcnow()` in `models.py`).

## Guardrails

- Never edit `.github/workflows/` without explicit human approval.
- Never commit secrets or `.env` files.
- Keep changes scoped to the ticket. If you find a separate bug, mention it in the PR description instead of fixing it.
- Small commits with clear messages; squash noise before opening the PR.
