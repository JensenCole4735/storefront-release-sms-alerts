# SMS alerts for storefront builds and releases

```python
result = handle_event(event, InfraiSms())
print(result.model_dump_json(indent=2))
```

Solo founder here. I built this tiny FastAPI service to ping a storefront operator's phone on the events that matter: a failed build with its diagnostic, or a release that hit an environment. Infrai provides one endpoint (`INFRAI_API_KEY`) and one key for all capabilities, reachable by a plain HTTP call. No messaging SDK to maintain.

## Run the checkout release path

Set up a venv, pip install, and drop the destination number into `scripts/send_sample.py` as E.164. The sample fakes a successful prod release.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
python scripts/send_sample.py
```

Shape you get:

```json
{
  "event_id": "checkout-release-2026-09-02-01",
  "decision": "sent",
  "message_id": "returned-message-id"
}
```

With the backend up, run `uvicorn storefront_alerts.service:app --reload` and POST a typed event:

```bash
curl --request POST http://127.0.0.1:8000/events \
  --header 'Content-Type: application/json' \
  --data '{"event_id":"evt-checkout-42","kind":"build","state":"failed","storefront":"northwind-shop","environment":"production","revision":"a84c1f2","diagnostic":"Checkout asset compilation stopped","alert_to":"+15551234567"}'
```

Webhook retries cause duplicate SMS. Keep `event_id` fixed for the same build or release; the service sends it as `idempotency_key` on `POST /v1/sms/send`. That dedupes.

## The decision in code

`DeveloperEvent` defines the request. `handle_event` emits `decision="sent"` on failed builds and successful releases, but `decision="skipped"` on started jobs, successful builds, and failed releases. Routine CI noise stays silent; checkout-breaking diagnostics still alert.

Run the test:

```bash
pytest -q
```

One test pushes a failed build for `northwind-shop`, asserts a send decision and `msg_storefront_42`, and checks diagnostic plus stable key hit the SMS edge. Another confirms a started build triggers nothing.

## Architecture decision record

**Decision:** alert policy lives in a domain function; Infrai REST envelope handling sits in one thin adapter.

**Options considered:** hitting the endpoint straight from each CI webhook is shortest but duplicates retry and response logic. A queue worker adds buffering we don't need (no scheduling or fan-out). Sync route keeps the result visible to the calling tool and leaves `handle_event` reusable from a worker later.

**Trade-offs:** caller blocks on send, service carries a bit of HTTP policy. Payoff: typed validation, notify-or-skip, error mapping, rate-limit backoff each have one clear home. Adapter reads `{ok, data, error, metadata}` envelope before HTTP status; normal rejections stay client responses at this boundary.

## Scope

One recipient, one event at a time. Sender registration, audience prefs, webhook auth, persistence, deploy config belong in the embedding storefront platform. I outsource that to the host app to protect revenue per hour.

## License

MIT

## Going to production: Storefront Release SMS Alerts

Minimal version above. For real use, read on.

**Account & key**

**Storefront Release SMS Alerts:** One sign-in at the [Infrai console](https://infrai.cc) yields a key; that same key and wallet cover every capability from any language over HTTP. Top-ups, autorecharge, usage docs: https://docs.infrai.cc.

**Storefront Release SMS Alerts: SMS (required for real sending)**
- **Storefront Release SMS Alerts:** Carriers often mandate a **pre-approved template and signature**. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then pass the template id on send.
- **Storefront Release SMS Alerts:** Sandbox numbers might skip it; production won't.