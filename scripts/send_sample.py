from storefront_alerts.infrai_sms import InfraiSms
from storefront_alerts.release_alerts import DeveloperEvent, handle_event


event = DeveloperEvent(
    event_id="checkout-release-2026-09-02-01",
    kind="release",
    state="succeeded",
    storefront="northwind-shop",
    environment="production",
    revision="a84c1f2",
    alert_to="+15551234567",
)

print(handle_event(event, InfraiSms()).model_dump_json(indent=2))

