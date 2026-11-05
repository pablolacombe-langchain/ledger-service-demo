# LEDGER-157 · Holds on funds and available balance

**Type:** Story · **Priority:** Medium · **Component:** ledger-service / core + API

## Summary

Operations needs to place a temporary hold on part of an account's balance (for example while a payment is pending review). A held amount still counts toward the ledger balance but cannot be transferred or withdrawn.

## Requirements

1. `POST /accounts/{id}/holds` with `{"amount": 50.0, "reason": "pending review"}` creates a hold and returns `201` with the hold (`id`, `account_id`, `amount`, `reason`, `created_at`, `released_at: null`).
2. `DELETE /accounts/{id}/holds/{hold_id}` releases the hold (`204`). Releasing twice is a `409`.
3. `GET /accounts/{id}` gains an `available_balance` field: `balance - sum(active holds)`.
4. `withdraw` and `transfer` check **available** balance, not `balance`. Insufficient available funds → `InsufficientFunds` / HTTP `409`.
5. A hold larger than the current available balance is rejected with `409`.

## Acceptance criteria

- [ ] Core logic lives in `Ledger` (new `Hold` dataclass in `models.py`).
- [ ] Routes added to `ledger_service/api.py`, following the existing error mapping.
- [ ] Unit tests for place / release / double-release / transfer blocked by hold.
- [ ] API tests for each route.
- [ ] `AGENTS.md` updated if a new rule needs recording.

## Out of scope

Expiry on holds, partial release.
