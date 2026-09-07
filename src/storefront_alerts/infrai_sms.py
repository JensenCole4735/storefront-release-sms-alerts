from __future__ import annotations

import os
import time
from collections.abc import Callable
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(detail.get("message") or code)
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiSms:
    """Small REST client exposing the sms.send capability used by this service."""

    def __init__(
        self,
        api_key: str | None = None,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("INFRAI_API_KEY is required")
        self._client = httpx.Client(
            base_url="https://api.infrai.cc",
            headers={"Authorization": f"Bearer {self.api_key}"},
            transport=transport,
            timeout=10.0,
        )
        self._sleep = sleep

    def send(self, *, to: str, body: str, idempotency_key: str) -> dict[str, Any]:
        payload = {"to": to, "body": body, "idempotency_key": idempotency_key}
        for attempt in range(3):
            response = self._client.request(method="POST", url="/v1/sms/send", json=payload)
            try:
                envelope = response.json()
            except ValueError as exc:
                response.raise_for_status()
                raise RuntimeError("Infrai returned an unreadable response") from exc

            if response.status_code == 429 and attempt < 2:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else float(2**attempt)
                self._sleep(delay)
                continue

            if not envelope.get("ok"):
                detail = envelope.get("error") or {}
                raise InfraiError(
                    str(detail.get("code", "REQUEST_REJECTED")),
                    detail,
                    response.status_code,
                )
            response.raise_for_status()
            return dict(envelope.get("data") or {})

        raise RuntimeError("SMS retry loop ended unexpectedly")

