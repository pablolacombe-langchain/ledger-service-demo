"""In-memory ledger.

Rules:
- Amounts must be positive.
- A transfer needs sufficient funds in the source account.
- Each account may send at most DAILY_TRANSFER_LIMIT per UTC day.
- Statements list an account's transactions newest-first.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ledger_service.models import Account, Transaction, new_id, utcnow

DAILY_TRANSFER_LIMIT = 10_000.0


class LedgerError(Exception):
    """Base class for ledger rule violations."""


class UnknownAccount(LedgerError):
    pass


class InsufficientFunds(LedgerError):
    pass


class DailyLimitExceeded(LedgerError):
    pass


class Ledger:
    def __init__(self) -> None:
        self._accounts: dict[str, Account] = {}
        self._transactions: list[Transaction] = []

    # -- accounts -----------------------------------------------------------

    def open_account(self, owner: str, currency: str = "CAD") -> Account:
        account = Account(id=new_id("acct"), owner=owner, currency=currency)
        self._accounts[account.id] = account
        return account

    def get_account(self, account_id: str) -> Account:
        try:
            return self._accounts[account_id]
        except KeyError as exc:
            raise UnknownAccount(account_id) from exc

    # -- money movement -----------------------------------------------------

    def deposit(self, account_id: str, amount: float, memo: str = "") -> Transaction:
        _check_amount(amount)
        account = self.get_account(account_id)
        account.balance += amount
        return self._record(account.id, "deposit", amount, memo)

    def withdraw(self, account_id: str, amount: float, memo: str = "") -> Transaction:
        _check_amount(amount)
        account = self.get_account(account_id)
        if account.balance < amount:
            raise InsufficientFunds(account_id)
        account.balance -= amount
        return self._record(account.id, "withdrawal", amount, memo)

    def transfer(
        self,
        source_id: str,
        destination_id: str,
        amount: float,
        memo: str = "",
    ) -> tuple[Transaction, Transaction]:
        _check_amount(amount)
        source = self.get_account(source_id)
        destination = self.get_account(destination_id)
        if source.currency != destination.currency:
            raise LedgerError("cross-currency transfers are not supported")
        if source.balance < amount:
            raise InsufficientFunds(source_id)
        if self.sent_today(source_id) + amount > DAILY_TRANSFER_LIMIT:
            raise DailyLimitExceeded(source_id)

        source.balance -= amount
        destination.balance += amount
        out = self._record(source.id, "transfer_out", amount, memo, counterparty=destination.id)
        inbound = self._record(destination.id, "transfer_in", amount, memo, counterparty=source.id)
        return out, inbound

    # -- reporting ----------------------------------------------------------

    def sent_today(self, account_id: str, now: datetime | None = None) -> float:
        now = now or utcnow()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return sum(
            tx.amount
            for tx in self._transactions
            if tx.account_id == account_id
            and tx.kind == "transfer_out"
            and tx.created_at >= start_of_day
        )

    def statement(self, account_id: str, since: datetime | None = None) -> list[Transaction]:
        """Return the account's transactions, newest first.

        ``since`` is accepted so callers can request a partial statement.
        """
        self.get_account(account_id)
        txs = [tx for tx in self._transactions if tx.account_id == account_id]
        # Transactions are appended in creation order, so reversing gives newest-first
        # without relying on timestamp resolution.
        return list(reversed(txs))

    # -- internals ----------------------------------------------------------

    def _record(
        self,
        account_id: str,
        kind: str,
        amount: float,
        memo: str,
        counterparty: str | None = None,
    ) -> Transaction:
        tx = Transaction(
            id=new_id("tx"),
            account_id=account_id,
            kind=kind,  # type: ignore[arg-type]
            amount=amount,
            memo=memo,
            counterparty_account_id=counterparty,
        )
        self._transactions.append(tx)
        return tx


def _check_amount(amount: float) -> None:
    if amount <= 0:
        raise LedgerError("amount must be positive")


def parse_since(value: str | None) -> datetime | None:
    """Parse an ISO-8601 timestamp; naive values are treated as UTC."""
    if value is None:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed
