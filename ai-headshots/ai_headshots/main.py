"""FastAPI app: simulated post-signup email journey (welcome, verify, payment, generation)."""

from __future__ import annotations

import os
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field

from ai_headshots.store import OutboxMessage, store

app = FastAPI(
    title="AI Headshots",
    description="Micro-SaaS para fotos profissionais com IA — simulação de e-mails (Linear AI-8).",
    version="0.1.0",
)


def _base_url() -> str:
    return os.getenv("AI_HEADSHOTS_PUBLIC_BASE_URL", "http://localhost:8080").rstrip("/")


def _enqueue(
    to_email: str,
    subject: str,
    body: str,
    kind: str,
    meta: dict[str, Any] | None = None,
) -> OutboxMessage:
    mid = str(uuid.uuid4())
    msg = OutboxMessage(
        id=mid,
        to_email=to_email,
        subject=subject,
        body_text=body,
        kind=kind,
        meta=meta or {},
    )
    return store.enqueue(msg)


# --- Request / response models ---


class AccountCreate(BaseModel):
    email: EmailStr
    name: str | None = Field(default=None, max_length=200)


class AccountResponse(BaseModel):
    id: str
    email: str
    name: str | None
    email_verified: bool
    created_at: str


class VerifyResponse(BaseModel):
    ok: bool
    email_verified: bool
    message: str


class OutboxItemResponse(BaseModel):
    id: str
    to_email: str
    subject: str
    body_text: str
    kind: str
    meta: dict[str, Any]
    created_at: str


class SimulatePaymentBody(BaseModel):
    email: EmailStr
    amount_cents: int = Field(ge=0, description="Valor em centavos")
    currency: str = Field(default="BRL", max_length=8)


class SimulateGenerationBody(BaseModel):
    email: EmailStr
    job_id: str | None = Field(default=None, max_length=128)
    image_count: int = Field(default=12, ge=1, le=500)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/accounts", response_model=AccountResponse)
def create_account(body: AccountCreate) -> AccountResponse:
    try:
        acc = store.create_account(body.email, body.name)
    except ValueError as e:
        if str(e) == "email_already_registered":
            raise HTTPException(status_code=409, detail="Este e-mail já está cadastrado.") from e
        raise

    verify_url = f"{_base_url()}/v1/verify-email?token={acc.verification_token}"
    display_name = acc.name or "Olá"

    subject = "Bem-vindo ao AI Headshots — confirme seu e-mail"
    body_text = f"""{display_name},

Obrigado por criar sua conta no AI Headshots.

Para liberar o pagamento online e receber suas fotos profissionais geradas por IA, confirme seu endereço de e-mail clicando no link abaixo:

{verify_url}

Se você não criou esta conta, ignore este e-mail.

— Equipe AI Headshots
"""
    _enqueue(acc.email, subject, body_text, kind="welcome_verify", meta={"account_id": acc.id})

    return AccountResponse(
        id=acc.id,
        email=acc.email,
        name=acc.name,
        email_verified=acc.email_verified,
        created_at=acc.created_at.isoformat(),
    )


@app.get("/v1/verify-email", response_model=VerifyResponse)
def verify_email(token: str = Query(..., min_length=1)) -> VerifyResponse:
    acc = store.verify_email(token)
    if not acc:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado.")
    return VerifyResponse(
        ok=True,
        email_verified=True,
        message="E-mail confirmado. Você já pode prosseguir com o pagamento.",
    )


@app.get("/v1/email/outbox", response_model=list[OutboxItemResponse])
def list_outbox() -> list[OutboxItemResponse]:
    items = []
    for m in store.list_outbox():
        items.append(
            OutboxItemResponse(
                id=m.id,
                to_email=m.to_email,
                subject=m.subject,
                body_text=m.body_text,
                kind=m.kind,
                meta=m.meta,
                created_at=m.created_at.isoformat(),
            )
        )
    return items


@app.get("/v1/email/outbox/{message_id}", response_model=OutboxItemResponse)
def get_outbox_message(message_id: str) -> OutboxItemResponse:
    m = store.get_outbox(message_id)
    if not m:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada.")
    return OutboxItemResponse(
        id=m.id,
        to_email=m.to_email,
        subject=m.subject,
        body_text=m.body_text,
        kind=m.kind,
        meta=m.meta,
        created_at=m.created_at.isoformat(),
    )


@app.post("/v1/simulate/payment-email", response_model=OutboxItemResponse)
def simulate_payment_email(body: SimulatePaymentBody) -> OutboxItemResponse:
    acc = store.get_account_by_email(body.email)
    if not acc:
        raise HTTPException(status_code=404, detail="Conta não encontrada para este e-mail.")
    if not acc.email_verified:
        raise HTTPException(
            status_code=403,
            detail="Confirme seu e-mail antes de simular o recibo de pagamento.",
        )

    amount = body.amount_cents / 100.0
    subject = "Pagamento confirmado — AI Headshots"
    name_part = f", {acc.name}" if acc.name else ""
    body_text = f"""Olá{name_part},

Recebemos seu pagamento de {amount:.2f} {body.currency}.

Seu pedido está na fila de geração. Você receberá outro e-mail quando suas imagens estiverem prontas.

— Equipe AI Headshots
"""
    msg = _enqueue(
        acc.email,
        subject,
        body_text,
        kind="payment_receipt",
        meta={"account_id": acc.id, "amount_cents": body.amount_cents, "currency": body.currency},
    )
    return OutboxItemResponse(
        id=msg.id,
        to_email=msg.to_email,
        subject=msg.subject,
        body_text=msg.body_text,
        kind=msg.kind,
        meta=msg.meta,
        created_at=msg.created_at.isoformat(),
    )


@app.post("/v1/simulate/generation-complete-email", response_model=OutboxItemResponse)
def simulate_generation_complete(body: SimulateGenerationBody) -> OutboxItemResponse:
    acc = store.get_account_by_email(body.email)
    if not acc:
        raise HTTPException(status_code=404, detail="Conta não encontrada para este e-mail.")

    job = body.job_id or str(uuid.uuid4())
    gallery_url = f"{_base_url()}/app/gallery/{job}"

    subject = "Suas fotos profissionais estão prontas — AI Headshots"
    name_part = f", {acc.name}" if acc.name else ""
    body_text = f"""Olá{name_part},

A geração das suas imagens foi concluída ({body.image_count} variações).

Acesse sua galeria para baixar os arquivos em alta qualidade:

{gallery_url}

Adoraríamos saber o que achou — responda a este e-mail com seu feedback.

— Equipe AI Headshots
"""
    msg = _enqueue(
        acc.email,
        subject,
        body_text,
        kind="generation_complete",
        meta={
            "account_id": acc.id,
            "job_id": job,
            "image_count": body.image_count,
        },
    )
    return OutboxItemResponse(
        id=msg.id,
        to_email=msg.to_email,
        subject=msg.subject,
        body_text=msg.body_text,
        kind=msg.kind,
        meta=msg.meta,
        created_at=msg.created_at.isoformat(),
    )
