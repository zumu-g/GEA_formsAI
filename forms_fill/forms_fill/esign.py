"""E-signature sending via Annature (create envelope → Annature emails signers).

One module, env-driven, mirroring accounts.py. Annature dispatches the signing
emails itself for non-draft envelopes, so this only creates the envelope.

Env: ANNATURE_ID (public key), ANNATURE_KEY (private key), optional
ANNATURE_ACCOUNT_ID. Keys live in Railway.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

import httpx

ANNATURE_URL = "https://api.annature.com.au/v1/envelopes"


class EsignConfigError(RuntimeError):
    """Annature keys missing — api.py maps this to 503."""


class EsignUpstreamError(RuntimeError):
    """Annature rejected the request — api.py maps this to 502."""


def _post_envelope(payload: dict) -> dict:
    """The single network call, factored out so tests can record it."""

    resp = httpx.post(
        ANNATURE_URL,
        headers={
            "X-Annature-Id": os.environ["ANNATURE_ID"],
            "X-Annature-Key": os.environ["ANNATURE_KEY"],
        },
        json=payload,
        timeout=30.0,
    )
    if resp.status_code >= 400:
        raise EsignUpstreamError(f"Annature {resp.status_code}: {resp.text[:300]}")
    return resp.json()


def send_for_signing(
    pdf_path: Path, title: str, recipients: list[dict], message: str = ""
) -> dict:
    """Create a non-draft envelope; every recipient becomes a signer with one
    required signature field anchored to the document's "Signature" labels."""

    if not (os.environ.get("ANNATURE_ID") and os.environ.get("ANNATURE_KEY")):
        raise EsignConfigError(
            "e-signature not configured: set ANNATURE_ID and ANNATURE_KEY"
        )
    payload: dict = {
        "name": title,
        "message": message or f"Please review and sign: {title}",
        "documents": [
            {
                "name": pdf_path.name,
                "base": base64.b64encode(pdf_path.read_bytes()).decode(),
                "type": "application/pdf",
            }
        ],
        "recipients": [
            {
                "name": r["name"],
                "email": r["email"],
                "type": "signer",
                "fields": [
                    {
                        "type": "signature",
                        "required": True,
                        # Anchor on the templates' signature labels; nudge the
                        # field below the label text. ponytail: one shared
                        # anchor for all forms — add per-form placement only
                        # if a live smoke test shows a form that needs it.
                        "anchor": "Signature",
                        "y_offset": -40,
                    }
                ],
            }
            for r in recipients
        ],
    }
    account_id = os.environ.get("ANNATURE_ACCOUNT_ID")
    if account_id:
        payload["account_id"] = account_id
    body = _post_envelope(payload)
    return {"envelope_id": body.get("id", ""), "status": body.get("status", "sent")}
