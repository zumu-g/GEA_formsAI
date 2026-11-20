"""applicationAI client: owner-approved applications for a property address.

GET {APPLICATIONAI_BASE_URL}/api/agent/v1/lease-handoff?propertyAddress=<addr>
Auth: Bearer APPLICATIONAI_AGENT_TOKEN + X-Acting-Agent: <agent email>.
Never log the token, the upstream body, or any applicant phone/email.
"""

from __future__ import annotations

import logging
import os
import time

import httpx

from ..errors import ApplicationAiError

log = logging.getLogger("forms_fill.providers.applicationai")

_PATH = "/api/agent/v1/lease-handoff"
_TIMEOUT = 10.0
_RETRY_DELAY = 0.5


def search_by_address(address: str, agent_email: str) -> list[dict]:
    base = (os.environ.get("APPLICATIONAI_BASE_URL") or "").rstrip("/")
    token = os.environ.get("APPLICATIONAI_AGENT_TOKEN") or ""
    if not base or not token:
        raise ApplicationAiError("applicationai_not_configured")

    headers = {"Authorization": f"Bearer {token}", "X-Acting-Agent": agent_email}
    resp = None
    with httpx.Client(timeout=_TIMEOUT) as client:
        for attempt in (1, 2):
            try:
                resp = client.get(
                    base + _PATH, params={"propertyAddress": address}, headers=headers
                )
                break
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                log.warning("applicationai attempt %d failed: %s", attempt, type(exc).__name__)
                if attempt == 2:
                    raise ApplicationAiError("applicationai_unavailable") from None
                time.sleep(_RETRY_DELAY)
            except httpx.HTTPError as exc:
                log.warning("applicationai request failed: %s", type(exc).__name__)
                raise ApplicationAiError("applicationai_unavailable") from None

    if resp.status_code in (401, 403):
        log.warning("applicationai rejected the token (HTTP %d)", resp.status_code)
        raise ApplicationAiError("applicationai_rejected")
    try:
        if resp.status_code != 200:
            raise ValueError
        rows = resp.json()["applications"]
        return [
            {
                "id": r["id"],
                "address": r["address"],
                "renter1_name": r["applicantName"],
                "renter1_phone": r["applicantPhone"],
                "renter1_email": r["applicantEmail"],
                "proposed_lease_start": r["proposedLeaseStart"],
                "weekly_rent": r["weeklyRent"],
            }
            for r in rows
        ]
    except (ValueError, KeyError, TypeError):
        log.warning("applicationai bad response (HTTP %d)", resp.status_code)
        raise ApplicationAiError("applicationai_unavailable") from None
