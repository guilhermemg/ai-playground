"""
AI Headshots — e-mail após criação de conta (simulação para jornada de pagamento e feedback de geração).
"""

from __future__ import annotations

import os
import secrets
from urllib.parse import urlencode

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field

from .email_templates import generation_complete, payment_receipt, welcome_after_signup
from .outbox import EmailOutbox, OutboxMessage

load_dotenv()

app = FastAPI(
    title="AI Headshots",
    description="Micro-SaaS de fotos profissionais com IA — integração de e-mail simulada",
    version="0.1.0",
)

BASE_URL = os.getenv("AI_HEADSHOTS_BASE_URL", "https://app.ai-headshots.example")
outbox = EmailOutbox()
# token -> email (na prática seria persistido com hash no banco)
_verify_tokens: dict[str, str] = {}


class RegisterAccountBody(BaseModel):
    email: EmailStr
    name: str | None = Field(default=None, max_length=200)


class RegisterAccountResponse(BaseModel):
    user_id: str
    email: str
    message: str
    verification_email_sent: bool
    # Simulação: IDs para inspecionar o que "foi enviado"
    welcome_message_id: str


class OutboxEntry(BaseModel):
    id: str
    to: str
    subject: str
    body: str
    kind: str
    created_at: str


class SimulatePaymentBody(BaseModel):
    email: EmailStr
    order_id: str = "ord_demo_001"
    amount_display: str = "R$ 49,90"


class SimulateGenerationBody(BaseModel):
    email: EmailStr
    job_id: str = "job_demo_001"
    download_hint: str = "Acesse o painel em /dashboard para baixar suas imagens."


def _msg_to_response(m: OutboxMessage) -> OutboxEntry:
    return OutboxEntry(
        id=m.id,
        to=m.to,
        subject=m.subject,
        body=m.body,
        kind=m.kind,
        created_at=m.created_at,
    )


@app.post("/v1/accounts", response_model=RegisterAccountResponse)
def register_account(body: RegisterAccountBody) -> RegisterAccountResponse:
    """
    Cria conta e dispara e-mail de boas-vindas com link de verificação.
    Necessário na jornada de pagamento online (e-mail confirmado) e para canal de feedback sobre geração.
    """
    token = secrets.token_urlsafe(32)
    _verify_tokens[token] = str(body.email)
    params = urlencode({"token": token})
    verify_url = f"{BASE_URL.rstrip('/')}/verify-email?{params}"

    subject, text_body = welcome_after_signup(body.name, verify_url)
    sent = outbox.send(
        str(body.email),
        subject,
        text_body,
        kind="welcome_verification",
        verify_token=token,
    )

    return RegisterAccountResponse(
        user_id=secrets.token_hex(8),
        email=str(body.email),
        message="Conta criada. Verifique seu e-mail para ativar e prosseguir ao pagamento.",
        verification_email_sent=True,
        welcome_message_id=sent.id,
    )


@app.get("/v1/verify-email")
def verify_email(token: str = Query(..., min_length=8)) -> dict:
    """Simula confirmação de e-mail (em produção atualizaria o utilizador na BD)."""
    email = _verify_tokens.pop(token, None)
    if not email:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado.")
    return {"status": "verified", "email": email}


@app.get("/v1/email/outbox", response_model=list[OutboxEntry])
def list_outbox(
    email: EmailStr | None = None,
    kind: str | None = None,
) -> list[OutboxEntry]:
    """Inspecionar e-mails simulados (apenas dev/demo)."""
    return [_msg_to_response(m) for m in outbox.list(to=str(email) if email else None, kind=kind)]


@app.get("/v1/email/outbox/{message_id}", response_model=OutboxEntry)
def get_outbox_message(message_id: str) -> OutboxEntry:
    m = outbox.get(message_id)
    if not m:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada.")
    return _msg_to_response(m)


@app.post("/v1/simulate/payment-email", response_model=OutboxEntry)
def simulate_payment_email(body: SimulatePaymentBody) -> OutboxEntry:
    """Simula recibo de pagamento (jornada pós-cadastro e checkout)."""
    subject, text = payment_receipt(body.order_id, body.amount_display)
    m = outbox.send(str(body.email), subject, text, kind="payment_receipt", order_id=body.order_id)
    return _msg_to_response(m)


@app.post("/v1/simulate/generation-complete-email", response_model=OutboxEntry)
def simulate_generation_email(body: SimulateGenerationBody) -> OutboxEntry:
    """Simula feedback de que as imagens foram geradas."""
    subject, text = generation_complete(body.job_id, body.download_hint)
    m = outbox.send(str(body.email), subject, text, kind="generation_complete", job_id=body.job_id)
    return _msg_to_response(m)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ai-headshots"}
