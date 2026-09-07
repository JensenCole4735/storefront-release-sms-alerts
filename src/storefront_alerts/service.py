from fastapi import FastAPI, HTTPException

from .infrai_sms import InfraiError, InfraiSms
from .release_alerts import AlertResult, DeveloperEvent, handle_event

app = FastAPI(title="Storefront release SMS alerts")


@app.post("/events", response_model=AlertResult)
def receive_event(event: DeveloperEvent) -> AlertResult:
    try:
        return handle_event(event, InfraiSms())
    except InfraiError as exc:
        caller_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=caller_status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc

