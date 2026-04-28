"""Jornada: cadastro → e-mail de boas-vindas → (simulação) pagamento e geração."""

import re

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_register_sends_welcome_to_outbox():
    r = client.post(
        "/v1/accounts",
        json={"email": "user@example.com", "name": "Maria"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["verification_email_sent"] is True
    mid = data["welcome_message_id"]

    m = client.get(f"/v1/email/outbox/{mid}")
    assert m.status_code == 200
    body = m.json()
    assert body["to"] == "user@example.com"
    assert "Bem-vindo" in body["subject"] or "Bem-vindo" in body["body"]
    assert "verify-email" in body["body"]


def test_verify_email_with_token_from_welcome_body():
    client.post("/v1/accounts", json={"email": "verify@example.com"})
    listed = client.get("/v1/email/outbox", params={"email": "verify@example.com"})
    items = listed.json()
    assert len(items) >= 1
    full = client.get(f"/v1/email/outbox/{items[0]['id']}").json()
    m = re.search(r"token=([^&\s]+)", full["body"])
    assert m, "expected verify link with token in email body"
    token = m.group(1)
    vr = client.get("/v1/verify-email", params={"token": token})
    assert vr.status_code == 200
    assert vr.json()["email"] == "verify@example.com"


def test_simulate_payment_and_generation():
    client.post("/v1/accounts", json={"email": "flow@example.com"})
    p = client.post(
        "/v1/simulate/payment-email",
        json={"email": "flow@example.com", "order_id": "O1", "amount_display": "R$ 10,00"},
    )
    assert p.status_code == 200
    assert "Pagamento" in p.json()["subject"] or "pagamento" in p.json()["body"].lower()

    g = client.post(
        "/v1/simulate/generation-complete-email",
        json={"email": "flow@example.com", "job_id": "J1"},
    )
    assert g.status_code == 200
    body_l = g.json()["body"].lower()
    assert "concluída" in body_l or "prontas" in body_l
