"""Tell GEA's ingoing engine (n8n) that every tenant has signed the lease.

One POST per lease, ever: ``leases.claim_notify`` makes the send exclusive,
and a recorded success is never repeated. Failures retry with backoff, then
park as ``ingoing_notify_failed`` for the PM's "Resend to Ingoing" button.
Nothing here touches the signing status.

Env: INGOING_ENGINE_WEBHOOK (URL), INGOING_WEBHOOK_SECRET (X-GEA-Secret).
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import httpx

from . import leases

log = logging.getLogger("forms_fill.ingoing")

TIMEOUT_S = 15
BACKOFF_S = (5, 30, 120)  # waits before retries 1-3
MELBOURNE = ZoneInfo("Australia/Melbourne")
_post = httpx.post  # module seams so the webhook path can be tested offline
_sleep = time.sleep


def build_body(row: dict) -> dict:
    signed = datetime.fromisoformat(row["signed_at"]).astimezone(MELBOURNE)
    base = (os.environ.get("PUBLIC_BASE_URL") or "").rstrip("/")
    return {
        "workflow_type": "ingoing",
        "intake_mode": "step_action",
        "source": "formsai",
        "sender": "formsai",
        "idem_key": row["idem_key"],
        "step": 3,
        "answer": "lease_signed",
        "figures": {
            "lease_signed_date": signed.date().isoformat(),
            "signers": row["signers"],
            "signed_pdf_url": f"{base}/files/{row['request_id']}/signed",
            "formsai_document_id": row["request_id"],
        },
    }


def _record(request_id: str, status: str, attempts: int, response: str) -> None:
    changes = {"notify_status": status, "notify_attempts": attempts, "notify_response": response[:500]}
    if status == "sent":
        changes["notify_sent_at"] = datetime.now(timezone.utc).isoformat()
    leases.update(request_id, **changes)


def notify_lease_signed(request_id: str, post=None, sleep=None) -> str:
    """Returns the resulting notify_status."""

    post, sleep = post or _post, sleep or _sleep
    row = leases.get(request_id)
    if row is None or row["status"] != "signed" or row["notify_status"] == "sent":
        return row["notify_status"] if row else "missing"
    if not row["idem_key"]:
        leases.update(request_id, notify_status="no_idem_key")
        log.warning("lease %s signed but has no idem_key; PM must link it to the move-in", request_id)
        return "no_idem_key"
    url = os.environ.get("INGOING_ENGINE_WEBHOOK", "")
    secret = os.environ.get("INGOING_WEBHOOK_SECRET", "")
    if not (url and secret):
        _record(request_id, "ingoing_notify_failed", row["notify_attempts"],
                "not configured: set INGOING_ENGINE_WEBHOOK and INGOING_WEBHOOK_SECRET")
        return "ingoing_notify_failed"
    if not leases.claim_notify(request_id):
        return "sending"

    body = build_body(row)
    headers = {"X-GEA-Secret": secret, "Content-Type": "application/json"}
    attempts = row["notify_attempts"]
    last = ""
    for wait in (0, *BACKOFF_S):
        if wait:
            sleep(wait)
        attempts += 1
        try:
            resp = post(url, json=body, headers=headers, timeout=TIMEOUT_S)
            last = f"{resp.status_code} {resp.text}"
            log.info("ingoing notify %s attempt %d -> %s %d", request_id, attempts, url, resp.status_code)
            if resp.is_success:
                _record(request_id, "sent", attempts, last)
                return "sent"
        except Exception as exc:  # any failure must end in a recorded status, never stuck "sending"
            last = f"{type(exc).__name__}: {exc}"
            log.info("ingoing notify %s attempt %d -> %s failed: %s", request_id, attempts, url, last)
    _record(request_id, "ingoing_notify_failed", attempts, last)
    log.warning("ingoing notify %s failed after %d attempts", request_id, attempts)
    return "ingoing_notify_failed"
