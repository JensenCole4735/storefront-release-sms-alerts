from storefront_alerts.release_alerts import DeveloperEvent, handle_event


class RecordingSms:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def send(self, *, to: str, body: str, idempotency_key: str) -> dict[str, object]:
        self.calls.append(
            {"to": to, "body": body, "idempotency_key": idempotency_key}
        )
        return {"message_id": "msg_storefront_42"}


def event(*, kind: str, state: str) -> DeveloperEvent:
    return DeveloperEvent(
        event_id="evt-checkout-42",
        kind=kind,
        state=state,
        storefront="northwind-shop",
        environment="production",
        revision="a84c1f2",
        diagnostic="Checkout asset compilation stopped",
        alert_to="+15551234567",
    )


def test_failed_build_sends_diagnostic_with_stable_event_key() -> None:
    sms = RecordingSms()

    result = handle_event(event(kind="build", state="failed"), sms)

    assert result.model_dump() == {
        "event_id": "evt-checkout-42",
        "decision": "sent",
        "message_id": "msg_storefront_42",
    }
    assert sms.calls == [
        {
            "to": "+15551234567",
            "body": (
                "[northwind-shop] Build failed in production at a84c1f2: "
                "Checkout asset compilation stopped"
            ),
            "idempotency_key": "evt-checkout-42",
        }
    ]


def test_started_build_is_skipped() -> None:
    sms = RecordingSms()

    result = handle_event(event(kind="build", state="started"), sms)

    assert result.decision == "skipped"
    assert sms.calls == []

