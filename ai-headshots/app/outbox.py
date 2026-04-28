"""In-memory email outbox for dev/demo; swap for SendGrid, SES, Resend, etc. in production."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any


@dataclass
class OutboxMessage:
    id: str
    to: str
    subject: str
    body: str
    kind: str
    created_at: str
    metadata: dict[str, Any] = field(default_factory=dict)


class EmailOutbox:
    def __init__(self) -> None:
        self._lock = Lock()
        self._items: list[OutboxMessage] = []

    def send(self, to: str, subject: str, body: str, kind: str, **metadata: Any) -> OutboxMessage:
        msg = OutboxMessage(
            id=str(uuid.uuid4()),
            to=to,
            subject=subject,
            body=body,
            kind=kind,
            created_at=datetime.now(timezone.utc).isoformat(),
            metadata=dict(metadata),
        )
        with self._lock:
            self._items.append(msg)
        return msg

    def list(self, to: str | None = None, kind: str | None = None) -> list[OutboxMessage]:
        with self._lock:
            items = list(self._items)
        if to:
            items = [m for m in items if m.to == to]
        if kind:
            items = [m for m in items if m.kind == kind]
        return items

    def get(self, message_id: str) -> OutboxMessage | None:
        with self._lock:
            for m in self._items:
                if m.id == message_id:
                    return m
        return None

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
