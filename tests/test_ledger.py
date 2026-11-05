from datetime import datetime, timedelta, timezone

import pytest

from ledger_service import (
    DailyLimitExceeded,
    InsufficientFunds,
    Ledger,
    LedgerError,
    UnknownAccount,
)
from ledger_service.ledger import DAILY_TRANSFER_LIMIT, parse_since


@pytest.fixture
def ledger() -> Ledger:
    return Ledger()


def test_open_account_starts_empty(ledger: Ledger) -> None:
    acct = ledger.open_account("Ada")
    assert acct.balance == 0
    assert acct.currency == "CAD"
    assert ledger.get_account(acct.id) is acct


def test_unknown_account(ledger: Ledger) -> None:
    with pytest.raises(UnknownAccount):
        ledger.get_account("acct_missing")


def test_deposit_and_withdraw(ledger: Ledger) -> None:
    acct = ledger.open_account("Ada")
    ledger.deposit(acct.id, 100)
    ledger.withdraw(acct.id, 40)
    assert acct.balance == 60


def test_amounts_must_be_positive(ledger: Ledger) -> None:
    acct = ledger.open_account("Ada")
    with pytest.raises(LedgerError):
        ledger.deposit(acct.id, 0)
    with pytest.raises(LedgerError):
        ledger.deposit(acct.id, -5)


def test_transfer_moves_money_and_records_both_sides(ledger: Ledger) -> None:
    a = ledger.open_account("Ada")
    b = ledger.open_account("Grace")
    ledger.deposit(a.id, 500)
    out, inbound = ledger.transfer(a.id, b.id, 125, memo="rent")

    assert a.balance == 375
    assert b.balance == 125
    assert out.kind == "transfer_out" and out.counterparty_account_id == b.id
    assert inbound.kind == "transfer_in" and inbound.counterparty_account_id == a.id


def test_transfer_requires_funds(ledger: Ledger) -> None:
    a = ledger.open_account("Ada")
    b = ledger.open_account("Grace")
    ledger.deposit(a.id, 10)
    with pytest.raises(InsufficientFunds):
        ledger.transfer(a.id, b.id, 11)


def test_daily_transfer_limit(ledger: Ledger) -> None:
    a = ledger.open_account("Ada")
    b = ledger.open_account("Grace")
    ledger.deposit(a.id, DAILY_TRANSFER_LIMIT * 2)
    ledger.transfer(a.id, b.id, DAILY_TRANSFER_LIMIT)
    with pytest.raises(DailyLimitExceeded):
        ledger.transfer(a.id, b.id, 0.01)


def test_statement_is_newest_first(ledger: Ledger) -> None:
    a = ledger.open_account("Ada")
    first = ledger.deposit(a.id, 1, memo="first")
    second = ledger.deposit(a.id, 2, memo="second")
    txs = ledger.statement(a.id)
    assert [tx.id for tx in txs] == [second.id, first.id]


def test_statement_since_is_inclusive_and_newest_first(ledger: Ledger) -> None:
    a = ledger.open_account("Ada")
    first = ledger.deposit(a.id, 1, memo="first")
    second = ledger.deposit(a.id, 2, memo="second")
    third = ledger.deposit(a.id, 3, memo="third")
    base = first.created_at
    second.created_at = base + timedelta(seconds=10)
    third.created_at = base + timedelta(seconds=20)

    txs = ledger.statement(a.id, since=second.created_at)
    assert [tx.id for tx in txs] == [third.id, second.id]

    after_all = ledger.statement(a.id, since=third.created_at + timedelta(seconds=1))
    assert after_all == []


def test_statement_since_accepts_parsed_naive_timestamp(ledger: Ledger) -> None:
    a = ledger.open_account("Ada")
    old = ledger.deposit(a.id, 1)
    new = ledger.deposit(a.id, 2)
    old.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    new.created_at = datetime(2024, 1, 3, tzinfo=timezone.utc)

    txs = ledger.statement(a.id, since=parse_since("2024-01-02T00:00:00"))
    assert [tx.id for tx in txs] == [new.id]
