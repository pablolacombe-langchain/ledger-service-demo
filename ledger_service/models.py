from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

TransactionKind = Literal["deposit", "withdrawal", "transfer_in", "transfer_out"]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


@dataclass
class Account:
    id: str
    owner: str
    currency: str = "CAD"
    balance: float = 0.0  # NOTE: float money. See tickets/LEDGER-163.
    created_at: datetime = field(default_factory=utcnow)


@dataclass
class Transaction:
    id: str
    account_id: str
    kind: TransactionKind
    amount: float
    memo: str = ""
    counterparty_account_id: str | None = None
    created_at: datetime = field(default_factory=utcnow)
