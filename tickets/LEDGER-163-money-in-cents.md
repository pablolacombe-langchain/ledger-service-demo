# LEDGER-163 · Store money as integer cents

**Type:** Tech debt · **Priority:** Medium · **Component:** ledger-service / core

## Summary

Balances and amounts are Python floats. Repeated transfers of amounts like `0.10` drift (`0.1 + 0.2 != 0.3`), and the daily-limit check can be off by a cent. Move internal money handling to integer cents while keeping the public API unchanged (JSON still uses decimal dollars, e.g. `12.34`).

## Requirements

1. `Account.balance`, `Transaction.amount` and `DAILY_TRANSFER_LIMIT` become integer cents internally.
2. Add `to_cents(value: float | str) -> int` and `to_dollars(cents: int) -> float` helpers (round half-up, reject more than 2 decimals).
3. API request/response models keep accepting and returning dollars; conversion happens at the boundary.
4. No behaviour change for callers. All existing tests must pass unchanged, except where they assert on internal types.

## Acceptance criteria

- [ ] Property-style test: 1,000 transfers of `0.10` leave balances exact.
- [ ] Amounts with more than two decimals are rejected with `400`.
- [ ] `AGENTS.md` money rule updated.
- [ ] Changes split into small commits (models → ledger → api → tests) so review is easy.
