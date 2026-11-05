# LEDGER-142 · Statement endpoint ignores the `since` filter

**Type:** Bug · **Priority:** High · **Component:** ledger-service / API

## Summary

`GET /accounts/{id}/statement?since=<timestamp>` returns the full history. The `since` parameter is parsed and validated but never applied.

## Steps to reproduce

1. Open an account and make two deposits a few seconds apart.
2. Call `GET /accounts/{id}/statement?since=<timestamp between the two deposits>`.
3. Both deposits are returned. Only the second one should be.

## Expected behaviour

Only transactions with `created_at >= since` are returned, still newest-first. Requests without `since` are unchanged.

## Acceptance criteria

- [ ] `Ledger.statement(account_id, since=...)` applies the filter.
- [ ] A unit test in `tests/test_ledger.py` covers `since` (inclusive boundary).
- [ ] An API test in `tests/test_api.py` covers `?since=`.
- [ ] Existing tests still pass (`uv run pytest`).

## Notes

`parse_since()` in `ledger_service/ledger.py` already normalises naive timestamps to UTC; reuse it rather than re-parsing in the route.
