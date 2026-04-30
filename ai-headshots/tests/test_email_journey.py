"""Tests for AI-8 email journey simulation."""

from fastapi.testclient import TestClient

from ai_headshots.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_account_creation_welcome_in_outbox():
    r = client.post("/v1/accounts", json={"email": "user@example.com", "name": "Test User"})
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "user@example.com"
    assert data["email_verified"] is False

    out = client.get("/v1/email/outbox")
    assert out.status_code == 200
    messages = out.json()
    assert len(messages) == 1
    assert messages[0]["kind"] == "welcome_verify"
    assert "confirme" in messages[0]["body_text"].lower()
    assert messages[0]["to_email"] == "user@example.com"


def test_verify_email():
    client.post("/v1/accounts", json={"email": "verify@example.com"})
    out = client.get("/v1/email/outbox").json()
    assert len(out) == 1
    # Token is in body - extract from stored meta via second account pattern: get from outbox body
    body = out[0]["body_text"]
    assert "/v1/verify-email?token=" in body
    token = body.split("token=")[1].split()[0]

    r = client.get(f"/v1/verify-email?token={token}")
    assert r.status_code == 200
    assert r.json()["email_verified"] is True


def test_duplicate_email():
    client.post("/v1/accounts", json={"email": "dup@example.com"})
    r = client.post("/v1/accounts", json={"email": "dup@example.com"})
    assert r.status_code == 409


def test_payment_requires_verification():
    client.post("/v1/accounts", json={"email": "pay@example.com"})
    r = client.post(
        "/v1/simulate/payment-email",
        json={"email": "pay@example.com", "amount_cents": 9900},
    )
    assert r.status_code == 403


def test_payment_after_verify():
    client.post("/v1/accounts", json={"email": "okpay@example.com", "name": "Cliente"})
    body = client.get("/v1/email/outbox").json()[0]["body_text"]
    token = body.split("token=")[1].split()[0]
    client.get(f"/v1/verify-email?token={token}")

    r = client.post(
        "/v1/simulate/payment-email",
        json={"email": "okpay@example.com", "amount_cents": 4990, "currency": "BRL"},
    )
    assert r.status_code == 200
    assert r.json()["kind"] == "payment_receipt"


def test_generation_email():
    client.post("/v1/accounts", json={"email": "gen@example.com"})
    r = client.post(
        "/v1/simulate/generation-complete-email",
        json={"email": "gen@example.com", "image_count": 8},
    )
    assert r.status_code == 200
    j = r.json()
    assert j["kind"] == "generation_complete"
    assert "galeria" in j["body_text"].lower()


def test_get_outbox_by_id():
    client.post("/v1/accounts", json={"email": "byid@example.com"})
    mid = client.get("/v1/email/outbox").json()[0]["id"]
    r = client.get(f"/v1/email/outbox/{mid}")
    assert r.status_code == 200
    assert r.json()["id"] == mid
