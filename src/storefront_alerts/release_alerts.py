from __future__ import annotations

from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, Field


class EventKind(StrEnum):
    BUILD = "build"
    RELEASE = "release"


class EventState(StrEnum):
    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class DeveloperEvent(BaseModel):
    event_id: str = Field(min_length=1, max_length=100)
    kind: EventKind
    state: EventState
    storefront: str = Field(min_length=1, max_length=80)
    environment: str = Field(min_length=1, max_length=40)
    revision: str = Field(min_length=1, max_length=40)
    diagnostic: str | None = Field(default=None, max_length=180)
    alert_to: str = Field(pattern=r"^\+[1-9]\d{7,14}$")


class AlertResult(BaseModel):
    event_id: str
    decision: str
    message_id: str | None = None


class SmsSender(Protocol):
    def send(self, *, to: str, body: str, idempotency_key: str) -> dict[str, object]: ...


def alert_text(event: DeveloperEvent) -> str | None:
    if event.kind == EventKind.BUILD and event.state == EventState.FAILED:
        detail = event.diagnostic or "Check the build log."
        return (
            f"[{event.storefront}] Build failed in {event.environment} at "
            f"{event.revision}: {detail}"
        )
    if event.kind == EventKind.RELEASE and event.state == EventState.SUCCEEDED:
        return (
            f"[{event.storefront}] Release {event.revision} is live in "
            f"{event.environment}."
        )
    return None


def handle_event(event: DeveloperEvent, sms: SmsSender) -> AlertResult:
    body = alert_text(event)
    if body is None:
        return AlertResult(event_id=event.event_id, decision="skipped")

    sent = sms.send(to=event.alert_to, body=body, idempotency_key=event.event_id)
    return AlertResult(
        event_id=event.event_id,
        decision="sent",
        message_id=str(sent["message_id"]),
    )

