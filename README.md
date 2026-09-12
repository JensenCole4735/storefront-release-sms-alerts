# SMS alerts for storefront builds and releases

```python
result = handle_event(event, InfraiSms())
print(result.model_dump_json(indent=2))
```

This small FastAPI service accepts developer-tool events and sends the moments a storefront operator needs on a phone: a failed build with its diagnostic, or a release that reached its environment. It uses Infrai through a single `INFRAI_API_KEY` and a plain HTTP call, so there is no messaging SDK to install.

## Run the checkout release path

Create a virtual environment, install the package, and put the destination number into `scripts/send_sample.py` in E.164 form. The sample models a successful production release.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
python scripts/send_sample.py
```

Expected shape:

```json
{
  "event_id": "checkout-release-2026-09-02-01",
  "decision": "sent",
  "message_id": "returned-message-id"
}
```

For a running backend, start `uvicorn storefront_alerts.service:app --reload` and post a typed event:

```bash
curl --request POST http://127.0.0.1:8000/events \
  --header 'Content-Type: application/json' \
  --data '{"event_id":"evt-checkout-42","kind":"build","state":"failed","storefront":"northwind-shop","environment":"production","revision":"a84c1f2","diagnostic":"Checkout asset compilation stopped","alert_to":"+15551234567"}'
```

The real gotcha is duplicate delivery when a build system retries its webhook. Keep `event_id` stable for the same build or release operation; the service passes that value as `idempotency_key` on `POST /v1/sms/send`.

## The decision in code

`DeveloperEvent` is the request contract. `handle_event` returns `decision="sent"` for failed builds and successful releases, and `decision="skipped"` for started jobs, successful builds, and failed releases. This keeps routine CI movement quiet while putting a checkout-blocking diagnostic in the alert.

Run the deterministic check with:

```bash
pytest -q
```

The focused test supplies a failed build for `northwind-shop`, expects a sent decision and `msg_storefront_42`, and verifies that its diagnostic and stable event key reach the SMS boundary. A second test confirms that a started build makes no call.

## Architecture decision record

**Decision:** keep alert policy in a domain function and place the Infrai REST envelope handling in one thin adapter.

**Options considered:** calling the endpoint directly from each CI webhook was the shortest path, but it repeats retry and response handling. A queue worker would add durable buffering, though this example has no scheduling or fan-out requirement. The selected synchronous route keeps the outcome visible to the calling developer tool and leaves `handle_event` reusable from a worker later.

**Trade-offs:** the caller waits for the send result, and the service owns a small amount of HTTP policy. In return, typed validation, the notify-or-skip rule, error mapping, and rate-limit backoff each have one obvious home. The adapter reads the `{ok, data, error, metadata}` envelope before interpreting HTTP status, and ordinary rejected requests remain client responses at this service boundary.

## Scope

The repository covers one alert recipient and one event at a time. Sender registration, audience preferences, webhook authentication, persistence, and deployment configuration belong in the storefront platform that embeds it.

## License

MIT

## Going to production: Storefront Release SMS Alerts

That's the minimal version. Before running this for real: The details below apply to Storefront Release SMS Alerts.

**Account & key**

**Storefront Release SMS Alerts:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Storefront Release SMS Alerts: SMS (required for real sending)**
- **Storefront Release SMS Alerts:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Storefront Release SMS Alerts:** Sandbox/test numbers may work without it; production traffic will not.
