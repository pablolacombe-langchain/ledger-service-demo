from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from ledger_service import api


@pytest.fixture
def client() -> TestClient:
    api.ledger = api.Ledger()  # fresh ledger per test
    return TestClient(api.app)


def _open(client: TestClient, owner: str) -> str:
    resp = client.post("/accounts", json={"owner": owner})
    assert resp.status_code == 201
    return resp.json()["id"]


def test_healthz(client: TestClient) -> None:
    assert client.get("/healthz").json() == {"status": "ok"}


def test_open_and_fetch_account(client: TestClient) -> None:
    acct_id = _open(client, "Ada")
    resp = client.get(f"/accounts/{acct_id}")
    assert resp.status_code == 200
    assert resp.json()["owner"] == "Ada"
    assert resp.json()["balance"] == 0


def test_unknown_account_is_404(client: TestClient) -> None:
    assert client.get("/accounts/acct_nope").status_code == 404


def test_deposit_then_transfer(client: TestClient) -> None:
    a = _open(client, "Ada")
    b = _open(client, "Grace")
    assert client.post(f"/accounts/{a}/deposits", json={"amount": 300}).status_code == 201

    resp = client.post(
        "/transfers",
        json={"source_account_id": a, "destination_account_id": b, "amount": 100, "memo": "lunch"},
    )
    assert resp.status_code == 201
    kinds = {tx["kind"] for tx in resp.json()}
    assert kinds == {"transfer_out", "transfer_in"}
    assert client.get(f"/accounts/{a}").json()["balance"] == 200
    assert client.get(f"/accounts/{b}").json()["balance"] == 100


def test_insufficient_funds_is_409(client: TestClient) -> None:
    a = _open(client, "Ada")
    b = _open(client, "Grace")
    resp = client.post(
        "/transfers",
        json={"source_account_id": a, "destination_account_id": b, "amount": 1},
    )
    assert resp.status_code == 409


def test_statement_lists_transactions(client: TestClient) -> None:
    a = _open(client, "Ada")
    client.post(f"/accounts/{a}/deposits", json={"amount": 5, "memo": "one"})
    client.post(f"/accounts/{a}/deposits", json={"amount": 6, "memo": "two"})
    resp = client.get(f"/accounts/{a}/statement")
    assert resp.status_code == 200
    assert [tx["memo"] for tx in resp.json()] == ["two", "one"]


def test_statement_rejects_bad_since(client: TestClient) -> None:
    a = _open(client, "Ada")
    assert client.get(f"/accounts/{a}/statement", params={"since": "yesterday"}).status_code == 422


def test_statement_since_filters_transactions(client: TestClient) -> None:
    a = _open(client, "Ada")
    client.post(f"/accounts/{a}/deposits", json={"amount": 5, "memo": "one"})
    second = client.post(f"/accounts/{a}/deposits", json={"amount": 6, "memo": "two"}).json()
    # Make the ordering of timestamps deterministic regardless of clock resolution.
    first_tx, second_tx = api.ledger._transactions
    first_tx.created_at = second_tx.created_at - timedelta(seconds=5)

    resp = client.get(f"/accounts/{a}/statement", params={"since": second["created_at"]})
    assert resp.status_code == 200
    assert [tx["memo"] for tx in resp.json()] == ["two"]

    # Without ``since`` the full history is still returned.
    full = client.get(f"/accounts/{a}/statement")
    assert [tx["memo"] for tx in full.json()] == ["two", "one"]
