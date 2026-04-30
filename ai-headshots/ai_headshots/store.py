"""In-memory persistence for demo: accounts, verification, outbox."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Account:
    id: str
    email: str
    name: str | None
    email_verified: bool
    verification_token: str
    created_at: datetime


@dataclass
class OutboxMessage:
    id: str
    to_email: str
    subject: str
    body_text: str
    kind: str
    meta: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)


class HeadshotsStore:
    """Thread-safe in-memory store."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._accounts: dict[str, Account] = {}  # by account id
        self._by_email: dict[str, str] = {}  # email lower -> account id
        self._token_to_account: dict[str, str] = {}  # token -> account id
        self._outbox: dict[str, OutboxMessage] = {}
        self._outbox_order: list[str] = []

    def create_account(self, email: str, name: str | None) -> Account:
        email_norm = email.strip().lower()
        with self._lock:
            if email_norm in self._by_email:
                raise ValueError("email_already_registered")
            aid = str(uuid.uuid4())
            token = str(uuid.uuid4())
            acc = Account(
                id=aid,
                email=email_norm,
                name=name.strip() if name else None,
                email_verified=False,
                verification_token=token,
                created_at=_utcnow(),
            )
            self._accounts[aid] = acc
            self._by_email[email_norm] = aid
            self._token_to_account[token] = aid
            return acc

    def get_account_by_token(self, token: str) -> Account | None:
        with self._lock:
            aid = self._token_to_account.get(token)
            if not aid:
                return None
            return self._accounts.get(aid)

    def verify_email(self, token: str) -> Account | None:
        with self._lock:
            aid = self._token_to_account.get(token)
            if not aid:
                return None
            acc = self._accounts.get(aid)
            if not acc:
                return None
            if acc.email_verified:
                return acc
            acc.email_verified = True
            return acc

    def get_account(self, account_id: str) -> Account | None:
        with self._lock:
            return self._accounts.get(account_id)

    def get_account_by_email(self, email: str) -> Account | None:
        email_norm = email.strip().lower()
        with self._lock:
            aid = self._by_email.get(email_norm)
            if not aid:
                return None
            return self._accounts.get(aid)

    def enqueue(self, msg: OutboxMessage) -> OutboxMessage:
        with self._lock:
            self._outbox[msg.id] = msg
            self._outbox_order.append(msg.id)
        return msg

    def list_outbox(self) -> list[OutboxMessage]:
        with self._lock:
            return [self._outbox[i] for i in self._outbox_order if i in self._outbox]

    def get_outbox(self, message_id: str) -> OutboxMessage | None:
        with self._lock:
            return self._outbox.get(message_id)

    def reset_for_testing(self) -> None:
        """Clear all state (pytest only)."""
        with self._lock:
            self._accounts.clear()
            self._by_email.clear()
            self._token_to_account.clear()
            self._outbox.clear()
            self._outbox_order.clear()


store = HeadshotsStore()
