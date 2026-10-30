"""formsAI's own lease e-signing: email each tenant a private signing link.

Links are created and emailed together; if any email is refused, every link
for the lease is withdrawn so nothing goes out half-sent and the PM can retry.
Env: RESEND_API_KEY, MAIL_FROM (same as agent invites), PUBLIC_BASE_URL.
"""

from __future__ import annotations

import html
import os

import httpx

from . import leases

_post = httpx.post  # seam: tests capture emails instead of sending


class SigningConfigError(RuntimeError):
    """Email not configured — api maps to 503."""


class SigningSendError(RuntimeError):
    """Resend refused or failed — api maps to 502."""


def _email_html(name: str, link: str, message: str) -> str:
    body = html.escape(message).replace("\n", "<br>")
    return (
        f"<p>Hi {html.escape(name)},</p>"
        f"<p>{body}</p>"
        f'<p><a href="{html.escape(link)}">Review and sign your lease</a></p>'
        "<p>This link is personal to you; please don't forward it.</p>"
        "<p>Grants Estate Agents</p>"
    )


def send_signing_links(request_id: str, tenants: list[dict], message: str) -> int:
    """Email every tenant their link. Returns the number emailed."""

    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key:
        raise SigningConfigError("email not configured: set RESEND_API_KEY")
    base = (os.environ.get("PUBLIC_BASE_URL") or "").rstrip("/")
    tokens = leases.create_signers(request_id, tenants)
    try:
        for slot, tenant in zip(tokens, tenants):  # dict order = tenants order
            resp = _post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "from": os.environ.get("MAIL_FROM", "forms@grantsea.com.au"),
                    "to": [tenant["email"]],
                    "subject": "Your residential rental agreement is ready to sign",
                    "html": _email_html(tenant["name"], f"{base}/sign/{tokens[slot]}", message),
                },
                timeout=15.0,
            )
            if not resp.is_success:
                raise SigningSendError(f"email to tenant {slot} refused: {resp.status_code}")
    except Exception as exc:
        leases.delete_signers(request_id)  # withdraw every link; PM retries cleanly
        if isinstance(exc, SigningSendError):
            raise
        raise SigningSendError(f"email failed: {type(exc).__name__}") from exc
    return len(tokens)
