"""HTTP API for the ledger service.

Run locally with:  uv run uvicorn ledger_service.api:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from ledger_service.ledger import (
    DailyLimitExceeded,
    InsufficientFunds,
    Ledger,
    LedgerError,
    UnknownAccount,
    parse_since,
)
from ledger_service.models import Account, Transaction

app = FastAPI(title="ledger-service", version="0.1.0")
ledger = Ledger()


# -- schemas ----------------------------------------------------------------


class OpenAccountRequest(BaseModel):
    owner: str = Field(min_length=1)
    currency: str = "CAD"


class MoneyRequest(BaseModel):
    amount: float = Field(gt=0)
    memo: str = ""


class TransferRequest(BaseModel):
    source_account_id: str
    destination_account_id: str
    amount: float = Field(gt=0)
    memo: str = ""


class AccountResponse(BaseModel):
    id: str
    owner: str
    currency: str
    balance: float

    @classmethod
    def from_account(cls, account: Account) -> "AccountResponse":
        return cls(
            id=account.id,
            owner=account.owner,
            currency=account.currency,
            balance=account.balance,
        )


class TransactionResponse(BaseModel):
    id: str
    account_id: str
    kind: str
    amount: float
    memo: str
    counterparty_account_id: str | None
    created_at: str

    @classmethod
    def from_transaction(cls, tx: Transaction) -> "TransactionResponse":
        return cls(
            id=tx.id,
            account_id=tx.account_id,
            kind=tx.kind,
            amount=tx.amount,
            memo=tx.memo,
            counterparty_account_id=tx.counterparty_account_id,
            created_at=tx.created_at.isoformat(),
        )


# -- error mapping ----------------------------------------------------------


def _raise_http(exc: LedgerError) -> None:
    if isinstance(exc, UnknownAccount):
        raise HTTPException(status_code=404, detail=f"unknown account: {exc}")
    if isinstance(exc, InsufficientFunds):
        raise HTTPException(status_code=409, detail="insufficient funds")
    if isinstance(exc, DailyLimitExceeded):
        raise HTTPException(status_code=409, detail="daily transfer limit exceeded")
    raise HTTPException(status_code=400, detail=str(exc))


# -- routes -----------------------------------------------------------------


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/accounts", response_model=AccountResponse, status_code=201)
def open_account(body: OpenAccountRequest) -> AccountResponse:
    return AccountResponse.from_account(ledger.open_account(body.owner, body.currency))


@app.get("/accounts/{account_id}", response_model=AccountResponse)
def get_account(account_id: str) -> AccountResponse:
    try:
        return AccountResponse.from_account(ledger.get_account(account_id))
    except LedgerError as exc:
        _raise_http(exc)
        raise  # unreachable; keeps type checkers happy


@app.post("/accounts/{account_id}/deposits", response_model=TransactionResponse, status_code=201)
def deposit(account_id: str, body: MoneyRequest) -> TransactionResponse:
    try:
        return TransactionResponse.from_transaction(ledger.deposit(account_id, body.amount, body.memo))
    except LedgerError as exc:
        _raise_http(exc)
        raise


@app.post("/transfers", response_model=list[TransactionResponse], status_code=201)
def transfer(body: TransferRequest) -> list[TransactionResponse]:
    try:
        out, inbound = ledger.transfer(
            body.source_account_id,
            body.destination_account_id,
            body.amount,
            body.memo,
        )
    except LedgerError as exc:
        _raise_http(exc)
        raise
    return [TransactionResponse.from_transaction(out), TransactionResponse.from_transaction(inbound)]


@app.get("/accounts/{account_id}/statement", response_model=list[TransactionResponse])
def statement(
    account_id: str,
    since: str | None = Query(default=None, description="ISO-8601 timestamp; only return transactions at or after it"),
) -> list[TransactionResponse]:
    try:
        txs = ledger.statement(account_id, since=parse_since(since))
    except ValueError:
        raise HTTPException(status_code=422, detail="since must be an ISO-8601 timestamp")
    except LedgerError as exc:
        _raise_http(exc)
        raise
    return [TransactionResponse.from_transaction(tx) for tx in txs]
