"""HTTP shell (U7, R10) — bearer-authenticated, engine-contract responses.

Exposes ``POST /fill`` over the same ``fill_form`` core, plus authenticated file
retrieval. Each request writes to its own output directory keyed by a request id.

Fail-closed startup (production posture — the rent-review engine depends on it):
    FORMS_API_TOKEN  — required; every route 401s without ``Authorization:
                       Bearer <token>``. The app refuses to start unset.
    PUBLIC_BASE_URL  — required; ``files.pdf`` / ``files.docx`` are returned as
                       absolute URLs the caller can fetch. Refuses to start
                       unset (a silent relative-path fallback would make the
                       engine's fail-soft path swallow the misconfig forever).
                       Local dev: set it to http://localhost:8080.
    FORMS_OUTPUT_DIR — optional output root (default ./out).

Error responses use the engine's machine codes:
    unauthorized | invalid_request | no_current_tenancy | fetch_failed | template_error
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from typing import Any

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from . import accounts, leases
from .core import fill_form
from .registry import form_catalogue
from .errors import (
    FormsFillError,
    ProviderConfigError,
    RenderError,
    TenancyNotFoundError,
    UnknownFormError,
    UpstreamError,
)
from .models import apply_service_address_defaults, build_request

app = FastAPI(title="GEA forms-fill", version="0.2.0")

OUTPUT_ROOT = Path(os.environ.get("FORMS_OUTPUT_DIR", "./out"))
STATIC_DIR = Path(__file__).with_name("static")

# PM-facing review UI (U4) -- static, no auth on the page itself; every data
# call it makes (`/forms`, `/fill`, `/files/...`) is bearer-protected as usual.
app.mount("/ui", StaticFiles(directory=str(STATIC_DIR), html=True), name="ui")


@app.middleware("http")
async def _no_cache_ui(request, call_next):
    # Without Cache-Control, browsers heuristically cache /ui/ and keep serving
    # stale pages after a deploy. no-cache forces an ETag revalidation (304).
    response = await call_next(request)
    if request.url.path.startswith("/ui"):
        response.headers["Cache-Control"] = "no-cache"
    return response


@app.get("/", include_in_schema=False)
def _root() -> RedirectResponse:
    return RedirectResponse("/ui/")


@app.on_event("startup")
def _fail_closed() -> None:
    missing = [v for v in ("FORMS_API_TOKEN", "PUBLIC_BASE_URL") if not os.environ.get(v)]
    if missing:
        raise RuntimeError(
            f"refusing to start: {', '.join(missing)} not set (fail-closed; "
            "for local dev set PUBLIC_BASE_URL=http://localhost:8080)"
        )
    host = (urlsplit(os.environ["PUBLIC_BASE_URL"]).hostname or "").lower()
    if host not in ("localhost", "127.0.0.1", "testserver") and not os.environ.get("FORMS_DATA_PROVIDER"):
        # an unset provider silently meant fixture (sample) data for real tenancies
        raise RuntimeError(
            "refusing to start: FORMS_DATA_PROVIDER not set on a shared server "
            "(propertyme, gea_crm, vaultre — or fixture explicitly for a demo)"
        )
    accounts.init_db()
    leases.init()


def _bearer(authorization: str) -> str:
    scheme, _, supplied = authorization.partition(" ")
    return supplied.strip() if scheme == "Bearer" else ""


def _is_machine(supplied: str) -> bool:
    token = os.environ.get("FORMS_API_TOKEN") or ""
    return bool(token) and hmac.compare_digest(supplied.encode(), token.encode())


def _require_auth(authorization: str) -> None:
    # ponytail: local-dev escape hatch only; Railway never sets this
    if os.environ.get("FORMS_DEV_NO_AUTH") == "1":
        return
    supplied = _bearer(authorization)
    # Machine token first (Hermes relay etc., unchanged), then agent session.
    if supplied and (_is_machine(supplied) or accounts.session_agent(supplied)):
        return
    raise HTTPException(
        status_code=401,
        detail={"error": "unauthorized", "message": "missing or invalid bearer token"},
    )


def _require_admin(authorization: str) -> None:
    if os.environ.get("FORMS_DEV_NO_AUTH") == "1":
        return
    supplied = _bearer(authorization)
    if supplied and _is_machine(supplied):
        return  # the machine token is trusted as admin
    agent = accounts.session_agent(supplied) if supplied else None
    if agent and agent["is_admin"]:
        return
    raise HTTPException(
        status_code=403 if agent else 401,
        detail={"error": "forbidden", "message": "admin access required"},
    )


def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status, content={"ok": False, "error": code, "message": message}
    )


@app.exception_handler(HTTPException)
async def _http_exc(request: Any, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return _err(exc.status_code, exc.detail["error"], exc.detail.get("message", ""))
    return _err(exc.status_code, "invalid_request", str(exc.detail))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# ── agent accounts (invite → accept → login) ────────────────────────────────


@app.post("/auth/login")
def auth_login(payload: dict[str, Any]) -> Any:
    token = accounts.login(str(payload.get("email", "")), str(payload.get("password", "")))
    if not token:
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthorized", "message": "wrong email or password"},
        )
    agent = accounts.session_agent(token)
    return {"ok": True, "token": token, "name": agent["name"], "is_admin": bool(agent["is_admin"])}


@app.post("/auth/accept")
def auth_accept(payload: dict[str, Any]) -> Any:
    try:
        token = accounts.accept_invite(
            str(payload.get("token", "")), str(payload.get("password", ""))
        )
    except accounts.AccountError as exc:
        raise HTTPException(
            status_code=400, detail={"error": "invalid_request", "message": str(exc)}
        ) from None
    agent = accounts.session_agent(token)
    return {"ok": True, "token": token, "name": agent["name"], "is_admin": bool(agent["is_admin"])}


@app.post("/auth/logout")
def auth_logout(authorization: str = Header(default="")) -> Any:
    accounts.logout(_bearer(authorization))
    return {"ok": True}


@app.get("/auth/me")
def auth_me(authorization: str = Header(default="")) -> Any:
    _require_auth(authorization)
    supplied = _bearer(authorization)
    if _is_machine(supplied) or os.environ.get("FORMS_DEV_NO_AUTH") == "1":
        return {"ok": True, "machine": True, "is_admin": True}
    agent = accounts.session_agent(supplied)
    return {"ok": True, "machine": False, **{k: agent[k] for k in ("email", "name", "mobile")},
            "is_admin": bool(agent["is_admin"])}


@app.post("/agents/invite")
def agents_invite(payload: dict[str, Any], authorization: str = Header(default="")) -> Any:
    _require_admin(authorization)
    try:
        invite_token = accounts.create_invite(
            str(payload.get("email", "")),
            str(payload.get("name", "")),
            str(payload.get("mobile", "")),
            bool(payload.get("is_admin", False)),
        )
    except accounts.AccountError as exc:
        raise HTTPException(
            status_code=422, detail={"error": "invalid_request", "message": str(exc)}
        ) from None
    base = (os.environ.get("PUBLIC_BASE_URL") or "").rstrip("/")
    accept_url = f"{base}/ui/#accept={invite_token}"
    try:
        emailed = accounts.send_invite_email(str(payload.get("email", "")), accept_url)
    except Exception:
        emailed = False  # email is best-effort; the copyable link below always works
    return {"ok": True, "accept_url": accept_url, "emailed": emailed}


@app.get("/agents")
def agents_list(authorization: str = Header(default="")) -> Any:
    _require_admin(authorization)
    return {"ok": True, "agents": accounts.list_agents()}


# ── e-signature (Annature) ───────────────────────────────────────────────────


@app.post("/esign/send")
def esign_send(payload: dict[str, Any], authorization: str = Header(default="")) -> Any:
    _require_auth(authorization)
    from . import esign

    request_id = str(payload.get("request_id", ""))
    if not request_id.isalnum():
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_request", "message": "invalid request id"},
        )
    if leases.get(request_id) is not None:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "invalid_request",
                "message": "leases go out via POST /lease/{request_id}/approve-send (PM approval)",
            },
        )
    recipients = [
        {"name": str(r.get("name", "")).strip(), "email": str(r.get("email", "")).strip()}
        for r in payload.get("recipients", [])
    ]
    recipients = [r for r in recipients if r["name"] or r["email"]]
    if not recipients or any(not r["name"] or "@" not in r["email"] for r in recipients):
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_request",
                "message": "each signer needs a name and a valid email",
            },
        )
    directory = OUTPUT_ROOT / request_id
    matches = sorted(directory.glob("*.pdf")) if directory.exists() else []
    if not matches:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": "no generated PDF for that request id"},
        )
    try:
        result = esign.send_for_signing(
            matches[0],
            str(payload.get("title", "")) or matches[0].stem,
            recipients,
            str(payload.get("message", "")),
        )
    except esign.EsignConfigError as exc:
        raise HTTPException(
            status_code=503, detail={"error": "not_configured", "message": str(exc)}
        ) from None
    except Exception as exc:  # upstream/network failures — Annature is a black box here
        raise HTTPException(
            status_code=502, detail={"error": "upstream_error", "message": str(exc)}
        ) from None
    return {"ok": True, **result, "signers": len(recipients)}


# ── ingoing lease: PM approval → e-sign → engine notification ───────────────


def _lease_or_404(request_id: str) -> dict:
    row = leases.get(request_id) if request_id.isalnum() else None
    if row is None:
        raise HTTPException(
            status_code=404, detail={"error": "not_found", "message": "no lease for that request id"}
        )
    return row


@app.post("/lease/{request_id}/approve-send")
def lease_approve_send(
    request_id: str, payload: dict[str, Any], authorization: str = Header(default="")
) -> Any:
    """PM approves the drafted lease; only then does it go to every tenant."""

    _require_approve_auth(authorization)
    from . import signing
    from .agency import load_agency_config
    from .approval import ApprovalError, approve

    row = _lease_or_404(request_id)
    if row["status"] != "draft":
        return _err(409, "invalid_request", f"lease already {row['status']}")
    facts = row["facts"]
    try:
        payments = load_agency_config().get("payments") or {}
    except ProviderConfigError as exc:
        return _err(503, "not_configured", str(exc))
    missing = leases.missing_payment_facts(facts, payments)
    signers = leases.tenants(facts)
    if not signers or any(not s["name"] or "@" not in s["email"] for s in signers):
        missing.append("renter names and emails")
    if missing:
        return JSONResponse(
            status_code=422,
            content={
                "ok": False,
                "error": "missing_facts",
                "message": "cannot send until these are filled: " + ", ".join(missing),
                "missing": missing,
            },
        )
    pdfs = sorted((OUTPUT_ROOT / request_id).glob("*.pdf"))
    if len(pdfs) != 1:
        return _err(409, "invalid_request", "lease needs exactly one generated PDF to send")
    from .sign_pdf import missing_boxes

    no_box = missing_boxes(pdfs[0].read_bytes(), [t["slot"] for t in signers])
    if no_box:
        return _err(422, "template_error", "lease PDF has no signature box for "
                    + ", ".join(f"renter {n}" for n in no_box))
    try:
        approve(pdfs[0], str(payload.get("approver", "")))
        signing.send_signing_links(request_id, signers, leases.signing_message(facts, payments))
    except ApprovalError as exc:
        return _err(400, "invalid_request", str(exc))
    except signing.SigningConfigError as exc:
        return _err(503, "not_configured", str(exc))
    except signing.SigningSendError as exc:  # lease stays a draft, PM can retry
        return _err(502, "upstream_error", str(exc))
    leases.update(request_id, status="sent", signers_expected=len(signers))
    return {"ok": True, "signers": len(signers)}


# ── tenant signing pages (public: the link token is the credential) ─────────

_INVALID_LINK = HTMLResponse(
    "<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width'>"
    "<title>Link not valid</title><body style='font-family:system-ui;padding:2rem;max-width:32rem'>"
    "<h1>This signing link is no longer valid</h1>"
    "<p>It may already have been used, or the lease was withdrawn. Contact Grants Estate Agents "
    "if you think this is wrong.</p>",
    status_code=404,
)


def _open_signer_or_none(token: str) -> dict | None:
    s = leases.signer_by_token(token) if 0 < len(token) <= 100 else None
    return s if s and s["status"] == "pending" and s["lease_status"] == "sent" else None


def _signer_or_error(token: str) -> dict:
    s = leases.signer_by_token(token) if 0 < len(token) <= 100 else None
    if s is None:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "unknown signing link"})
    if s["status"] != "pending" or s["lease_status"] != "sent":
        raise HTTPException(status_code=409, detail={"error": "invalid_request", "message": "this link is no longer open for signing"})
    return s


@app.get("/sign/{token}", include_in_schema=False)
def sign_page(token: str) -> Any:
    if _open_signer_or_none(token) is None:
        return _INVALID_LINK
    return FileResponse(STATIC_DIR / "sign.html", media_type="text/html")


@app.get("/sign/{token}/info")
def sign_info(token: str) -> Any:
    from .agency import load_agency_config

    s = _signer_or_error(token)
    row = leases.get(s["request_id"])
    try:
        payments = load_agency_config().get("payments") or {}
    except ProviderConfigError as exc:
        return _err(503, "not_configured", str(exc))
    return {"name": s["name"], "message": leases.signing_message(row["facts"], payments)}


@app.get("/sign/{token}/pdf")
def sign_pdf_view(token: str) -> FileResponse:
    s = _signer_or_error(token)
    (pdf,) = sorted((OUTPUT_ROOT / s["request_id"]).glob("*.pdf"))
    return FileResponse(str(pdf), media_type="application/pdf", filename="lease.pdf")


def _client_ip(request: Request) -> str:
    # Railway terminates TLS at a proxy; the first forwarded hop is the tenant
    forwarded = request.headers.get("x-forwarded-for", "")
    return forwarded.split(",")[0].strip() or (request.client.host if request.client else "")


def _signature_bytes(data_url: Any) -> bytes | None:
    import base64
    import binascii

    prefix = "data:image/png;base64,"
    if not isinstance(data_url, str) or not data_url.startswith(prefix) or len(data_url) > 300_000:
        return None
    try:
        png = base64.b64decode(data_url[len(prefix):], validate=True)
    except (binascii.Error, ValueError):
        return None
    return png if png.startswith(b"\x89PNG\r\n\x1a\n") else None


def _finish_lease(request_id: str) -> None:
    """Last tenant signed: stamp the approved PDF and mark the lease signed."""

    import logging

    from .approval import ApprovalError, verify_approval
    from .sign_pdf import SigningError, build_signed_pdf

    (pdf,) = sorted((OUTPUT_ROOT / request_id).glob("*.pdf"))
    try:
        verify_approval(pdf)  # tenants signed exactly what the PM approved
        signed = build_signed_pdf(pdf.read_bytes(), leases.signers_for(request_id))
    except (ApprovalError, SigningError) as exc:
        logging.getLogger("forms_fill").error("lease %s could not be finalised: %s", request_id, exc)
        leases.update(request_id, status="signing_error")
        return
    signed_dir = OUTPUT_ROOT / request_id / "signed"
    signed_dir.mkdir(parents=True, exist_ok=True)
    (signed_dir / "lease-signed.pdf").write_bytes(signed)
    leases.update(request_id, status="signed", signed_at=datetime.now(timezone.utc).isoformat())


@app.post("/sign/{token}")
async def sign_submit(token: str, request: Request, background: BackgroundTasks) -> Any:
    from . import ingoing

    _signer_or_error(token)
    try:
        body = await request.json()
    except ValueError:
        body = None
    body = body if isinstance(body, dict) else {}
    full_name = str(body.get("full_name") or "").strip()[:200]
    png = _signature_bytes(body.get("signature_png"))
    problems = [msg for ok, msg in (
        (body.get("consent") is True, "tick the box to agree to sign electronically"),
        (bool(full_name), "type your full name"),
        (png is not None, "draw your signature"),
    ) if not ok]
    if problems:
        return _err(422, "invalid_request", "Please " + " and ".join(problems) + ".")
    outcome = leases.record_signature(
        token, full_name, png, _client_ip(request), request.headers.get("user-agent", "")[:300]
    )
    if outcome == "invalid":
        return _err(409, "invalid_request", "this link is no longer open for signing")
    if outcome == "complete":
        request_id = leases.signer_by_token(token)["request_id"]
        _finish_lease(request_id)
        if leases.get(request_id)["status"] == "signed":
            background.add_task(ingoing.notify_lease_signed, request_id)
    return {"ok": True, "signed": True}


@app.post("/sign/{token}/decline")
def sign_decline(token: str, payload: dict[str, Any]) -> Any:
    _signer_or_error(token)
    if leases.record_decline(token, str(payload.get("reason") or "").strip()) == "invalid":
        return _err(409, "invalid_request", "this link is no longer open for signing")
    return {"ok": True, "declined": True}


@app.post("/lease/{request_id}/resend-ingoing", status_code=202)
def lease_resend_ingoing(
    request_id: str, background: BackgroundTasks, authorization: str = Header(default="")
) -> Any:
    """PM's "Resend to Ingoing" — only after the automatic attempts failed."""

    _require_approve_auth(authorization)
    from . import ingoing

    row = _lease_or_404(request_id)
    if row["status"] != "signed" or row["notify_status"] != "ingoing_notify_failed":
        return _err(409, "invalid_request", f"nothing to resend (notify status: {row['notify_status']})")
    background.add_task(ingoing.notify_lease_signed, request_id)
    return {"ok": True, "notify_status": "sending"}


@app.post("/lease/{request_id}/void")
def lease_void(request_id: str, authorization: str = Header(default="")) -> Any:
    """PM withdraws a lease out for signing: every link stops working."""

    _require_approve_auth(authorization)
    if not leases.void(_lease_or_404(request_id)["request_id"]):
        return _err(409, "invalid_request", "only a lease awaiting signatures can be voided")
    return {"ok": True, "status": "voided"}


@app.get("/leases")
def lease_list(authorization: str = Header(default="")) -> Any:
    _require_auth(authorization)
    keep = ("request_id", "idem_key", "status", "signers_expected", "signers", "signed_at",
            "notify_status", "notify_attempts", "notify_sent_at", "created_at", "updated_at")
    return {"leases": [{k: r[k] for k in keep} for r in leases.list_all()]}


# ── per-agent sticky defaults (U3) ───────────────────────────────────────────


@app.get("/defaults/{form_key}")
def defaults_get(form_key: str, authorization: str = Header(default="")) -> Any:
    _require_auth(authorization)
    agent_id = _draft_agent_id(authorization)
    if agent_id is None:  # machine / dev bypass: defaults are signed-in-only
        return {"ok": True, "values": {}}
    return {"ok": True, "values": accounts.get_defaults(agent_id, form_key)}


@app.post("/defaults/{form_key}")
def defaults_save(
    form_key: str, payload: dict[str, Any], authorization: str = Header(default="")
) -> Any:
    _require_auth(authorization)
    agent_id = _draft_agent_id(authorization)
    if agent_id is None:
        return {"ok": True, "stored": False}
    values = accounts.save_defaults(agent_id, form_key, payload)
    return {"ok": True, "stored": True, "values": values}


# ── in-progress form drafts ──────────────────────────────────────────────────


def _draft_agent_id(authorization: str) -> int | None:
    """The draft bucket owner: the signed-in agent, or None for the machine
    token / dev bypass (a shared bucket)."""

    supplied = _bearer(authorization)
    if os.environ.get("FORMS_DEV_NO_AUTH") == "1" or _is_machine(supplied):
        return None
    agent = accounts.session_agent(supplied)
    return agent["id"] if agent else None


@app.get("/drafts")
def drafts_list(authorization: str = Header(default="")) -> Any:
    _require_auth(authorization)
    return {"ok": True, "drafts": accounts.list_drafts(_draft_agent_id(authorization))}


@app.get("/drafts/{draft_id}")
def drafts_get(draft_id: int, authorization: str = Header(default="")) -> Any:
    _require_auth(authorization)
    draft = accounts.get_draft(_draft_agent_id(authorization), draft_id)
    if not draft:
        raise HTTPException(
            status_code=404, detail={"error": "not_found", "message": "no such draft"}
        )
    return {"ok": True, "draft": draft}


@app.post("/drafts")
def drafts_save(payload: dict[str, Any], authorization: str = Header(default="")) -> Any:
    _require_auth(authorization)
    form_key = str(payload.get("form_key", ""))
    if not form_key:
        raise HTTPException(
            status_code=422, detail={"error": "invalid_request", "message": "form_key required"}
        )
    draft_id = accounts.save_draft(
        _draft_agent_id(authorization),
        payload.get("id"),
        form_key,
        str(payload.get("label", "")),
        str(payload.get("state", "{}")),
    )
    return {"ok": True, "id": draft_id}


@app.delete("/drafts/{draft_id}")
def drafts_delete(draft_id: int, authorization: str = Header(default="")) -> Any:
    _require_auth(authorization)
    if not accounts.delete_draft(_draft_agent_id(authorization), draft_id):
        raise HTTPException(
            status_code=404, detail={"error": "not_found", "message": "no such draft"}
        )
    return {"ok": True}


@app.get("/forms")
def forms(authorization: str = Header(default="")) -> Any:
    _require_auth(authorization)
    return {"forms": form_catalogue()}


@app.get("/grounds")
def grounds(
    family: str | None = None, authorization: str = Header(default="")
) -> Any:
    _require_auth(authorization)
    from .grounds import UnknownGroundError, grounds_catalogue

    try:
        return {"grounds": grounds_catalogue(family)}
    except UnknownGroundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None


@app.get("/agency")
def agency(authorization: str = Header(default="")) -> Any:
    """Office details + the configured handling-agent list (U4, R5) — lets the
    UI offer an agent picker instead of the office defaulting silently."""

    _require_auth(authorization)
    from .agency import load_agency_config, office_address
    from .errors import ProviderConfigError

    try:
        cfg = load_agency_config()
    except ProviderConfigError as exc:
        return _err(500, "fetch_failed", f"agency config: {exc}")
    agency_data = cfg["agency"]
    agents = [
        {
            "full_name": a.get("full_name", ""),
            "mobile": a.get("mobile", ""),
            "email": a.get("email", ""),
            "acn": a.get("acn") or agency_data.get("acn") or "",
        }
        for a in cfg["agents"]
    ]
    # U1 (lease-flow speed-up): the signed-in agent is the handling-agent
    # default. Email match (case-insensitive, trimmed), then name; machine
    # token / dev bypass have no session agent → no "me", old default stands.
    me = None
    session = accounts.session_agent(_bearer(authorization))
    if session:
        email = (session.get("email") or "").strip().lower()
        name = (session.get("name") or "").strip().lower()
        me = next((a for a in agents if a["email"].strip().lower() == email), None) or (
            next((a for a in agents if name and a["full_name"].strip().lower() == name), None)
        )
        if me is None:
            import logging

            logging.getLogger("forms_fill").info(
                "agency: session agent %s matched no configured agent", session.get("email")
            )
    return {
        "office": {
            "name": agency_data.get("name", ""),
            "address": office_address(agency_data),
            "postcode": agency_data.get("postcode", ""),
        },
        "agents": agents,
        "me": me,
    }


@app.get("/tenancy/search")
def tenancy_search(
    q: str = "",
    provider: str | None = None,
    listing: str = "sale",
    authorization: str = Header(default=""),
) -> Any:
    """Address search across the selected data provider's lots (U2, R2/R4)."""

    _require_auth(authorization)
    if not q.strip():
        return _err(400, "invalid_request", "missing search query 'q'")
    if listing not in ("sale", "lease"):
        return _err(400, "invalid_request", f"invalid listing '{listing}' (sale|lease)")
    from dataclasses import asdict

    from .errors import SearchUnsupportedError
    from .providers.base import select_provider

    try:
        p = select_provider(provider)
        matches = p.search_lots(q, listing=listing)
    except SearchUnsupportedError as exc:
        return _err(400, "search_unsupported", str(exc))
    except ValueError as exc:
        return _err(400, "invalid_request", str(exc))
    except ProviderConfigError as exc:
        return _err(500, "fetch_failed", f"provider config: {exc}")
    except UpstreamError as exc:
        return _err(502, "fetch_failed", str(exc))
    except FormsFillError as exc:
        return _err(502, "fetch_failed", str(exc))
    return {"matches": [asdict(m) for m in matches], "provider": p.name}


@app.get("/tenancy/preview")
def tenancy_preview(
    lot_id: str = "",
    tenancy_id: str = "",
    provider: str | None = None,
    listing: str = "sale",
    authorization: str = Header(default=""),
) -> Any:
    """Fetch and return the tenancy bundle for PM verification before filling
    (U2, R3). Reuses fetch_bundle verbatim — read-only."""

    _require_auth(authorization)
    if not lot_id.strip() and not tenancy_id.strip():
        return _err(400, "invalid_request", "provide at least one of lot_id, tenancy_id")
    if listing not in ("sale", "lease"):
        return _err(400, "invalid_request", f"invalid listing '{listing}' (sale|lease)")
    from .providers.base import select_provider

    identifiers = {}
    if lot_id.strip():
        identifiers["lot_id"] = lot_id.strip()
    if tenancy_id.strip():
        identifiers["tenancy_id"] = tenancy_id.strip()
    if listing != "sale":
        identifiers["listing"] = listing
    from .errors import FetchUnsupportedError

    try:
        p = select_provider(provider)
        bundle = p.fetch_bundle(identifiers)
    except ValueError as exc:
        # e.g. vaultre needs a lot_id and can't use tenancy_id alone — same
        # 400 shape /tenancy/search already returns for provider ValueErrors.
        return _err(400, "invalid_request", str(exc))
    except (TenancyNotFoundError, FetchUnsupportedError) as exc:
        # Same UI path either way (R5): no match, or this provider simply
        # can't supply contact details — both mean "enter manually".
        return _err(404, "no_current_tenancy", str(exc))
    except ProviderConfigError as exc:
        return _err(500, "fetch_failed", f"provider config: {exc}")
    except UpstreamError as exc:
        return _err(502, "fetch_failed", str(exc))
    except FormsFillError as exc:
        return _err(502, "fetch_failed", str(exc))
    bundle = apply_service_address_defaults(bundle)
    return {"bundle": bundle.model_dump(), "provider": p.name}


@app.get("/property/facts")
def property_facts(
    address: str = "",
    authorization: str = Header(default=""),
) -> Any:
    """Fetch property key features for PPS autofill (U2, R2, KTD3).

    Returns PropertyFacts with 6 features (building type, beds, baths, cars, floor, land).
    If credentials missing, returns {"configured": False} and UI hides autofill button.
    """

    _require_auth(authorization)
    if not address.strip():
        return _err(400, "invalid_request", "missing address query parameter")
    from .providers.property_data import property_facts as fetch_facts

    facts = fetch_facts(address.strip())
    # If facts are all empty, provider is not configured.
    is_configured = any((facts.building_type, facts.beds, facts.baths, facts.cars, facts.floor_m2, facts.land_m2))
    return {
        "configured": is_configured,
        "facts": {
            "building_type": facts.building_type,
            "beds": facts.beds,
            "baths": facts.baths,
            "cars": facts.cars,
            "floor_m2": facts.floor_m2,
            "land_m2": facts.land_m2,
        },
    }


@app.post("/fill")
def fill(payload: dict[str, Any], authorization: str = Header(default="")) -> Any:
    _require_auth(authorization)
    request_id = uuid.uuid4().hex
    out_dir = OUTPUT_ROOT / request_id
    # The ingoing engine's move-in reference — not a form input, so it never
    # reaches FillRequest (extra="forbid").
    idem_key = payload.pop("idem_key", None)
    if idem_key is not None and (not isinstance(idem_key, str) or not 0 < len(idem_key) <= 200):
        return _err(400, "invalid_request", "idem_key must be a non-empty string (max 200)")
    try:
        request = build_request(json_payload=payload, out_dir=str(out_dir))
        result = fill_form(request)
    except (UnknownFormError, ValueError) as exc:
        return _err(400, "invalid_request", str(exc))
    except TenancyNotFoundError as exc:
        return _err(404, "no_current_tenancy", str(exc))
    except UpstreamError as exc:
        return _err(502, "fetch_failed", str(exc))
    except ProviderConfigError as exc:
        return _err(500, "fetch_failed", f"provider config: {exc}")
    except RenderError as exc:
        return _err(500, "template_error", str(exc))
    except FormsFillError as exc:
        return _err(500, "template_error", str(exc))

    base = (os.environ.get("PUBLIC_BASE_URL") or "").rstrip("/")
    if result.form == leases.LEASE_FORM:
        leases.save(request_id, idem_key, result._context)
    body = result.model_dump()
    body["request_id"] = request_id
    # engine contract: files.* are absolute, token-protected URLs
    body["files"] = {
        "pdf": f"{base}/files/{request_id}/pdf" if result.files.pdf else None,
        "docx": f"{base}/files/{request_id}/docx" if result.files.docx else None,
    }
    # files.* need the machine token; a person clicking a link from GEA LLM needs this one
    kind = "pdf" if result.files.pdf else "docx"
    body["review_url"] = f"{base}{_review_path(request_id, kind)}"
    return body


@app.get("/pps")
def pps_list(authorization: str = Header(default="")) -> Any:
    """List PPS records for the signed-in agent (U5, R7)."""

    _require_auth(authorization)
    agent_id = _draft_agent_id(authorization)
    records = accounts.list_pps_records(agent_id)
    return {"ok": True, "records": records}


@app.post("/pps")
def pps_save(payload: dict[str, Any], authorization: str = Header(default="")) -> Any:
    """Create or update a PPS record (U3, R3–R5)."""

    _require_auth(authorization)
    agent_id = _draft_agent_id(authorization)
    record_id = payload.get("id")
    address = str(payload.get("address", ""))
    sale_method = str(payload.get("sale_method", ""))
    reserve_price = str(payload.get("reserve_price", ""))
    auction_date = payload.get("auction_date")
    unconditional_at = payload.get("unconditional_at")
    sale_price = payload.get("sale_price")
    document_request_id = payload.get("document_request_id")

    if not address.strip():
        raise HTTPException(
            status_code=422, detail={"error": "invalid_request", "message": "address required"}
        )

    rid = accounts.save_pps_record(
        agent_id=agent_id,
        record_id=record_id,
        address=address,
        sale_method=sale_method,
        reserve_price=reserve_price,
        auction_date=auction_date,
        unconditional_at=unconditional_at,
        sale_price=sale_price,
        document_request_id=document_request_id,
    )
    record = accounts.get_pps_record(rid, agent_id=agent_id)
    return {"ok": True, "record": record}


@app.patch("/pps/{record_id}")
def pps_update(
    record_id: int, payload: dict[str, Any], authorization: str = Header(default="")
) -> Any:
    """Update PPS record (sale price, unconditional date) (U3, R4)."""

    _require_auth(authorization)
    agent_id = _draft_agent_id(authorization)
    unconditional_at = payload.get("unconditional_at")
    sale_price = payload.get("sale_price")
    document_request_id = payload.get("document_request_id")

    success = accounts.update_pps_record(
        record_id,
        agent_id=agent_id,
        unconditional_at=unconditional_at,
        sale_price=sale_price,
        document_request_id=document_request_id,
    )
    if not success:
        raise HTTPException(
            status_code=404, detail={"error": "not_found", "message": "PPS record not found"}
        )
    record = accounts.get_pps_record(record_id, agent_id=agent_id)
    return {"ok": True, "record": record}


@app.get("/pps/{public_id}")
def get_pps_public(public_id: str) -> FileResponse:
    """Serve a PPS document publicly (unauthenticated, free access). U4, R6.

    public_id is an unguessable UUID; 404s unknown IDs. Serves PDF inline.
    """

    # Isalnum guard: public_id is token_urlsafe(16) → alphanumeric + hyphen/underscore
    if not all(c.isalnum() or c in "-_" for c in public_id):
        raise HTTPException(status_code=404, detail={"error": "not_found"})

    from . import accounts

    record = accounts.get_pps_record_by_public_id(public_id)
    if not record:
        raise HTTPException(status_code=404, detail={"error": "not_found"})

    doc_request_id = record.get("document_request_id")
    if not doc_request_id or not doc_request_id.isalnum():
        raise HTTPException(
            status_code=404, detail={"error": "not_found", "message": "no PDF generated"}
        )

    directory = OUTPUT_ROOT / doc_request_id
    matches = sorted(directory.glob("*.pdf")) if directory.exists() else []
    if not matches:
        raise HTTPException(
            status_code=404, detail={"error": "not_found", "message": "PDF not found"}
        )

    return FileResponse(str(matches[0]), media_type="application/pdf")


REVIEW_LINK_DAYS = 7


def _review_sig(request_id: str, kind: str, exp: int) -> str:
    # key derived from the API token: no new secret; rotating the token kills every link
    key = hmac.new(os.environ.get("FORMS_API_TOKEN", "").encode(), b"review-link-v1", hashlib.sha256).digest()
    return hmac.new(key, f"{request_id}/{kind}:{exp}".encode(), hashlib.sha256).hexdigest()


def _review_path(request_id: str, kind: str) -> str:
    exp = int(time.time()) + REVIEW_LINK_DAYS * 86400
    return f"/files/{request_id}/{kind}?exp={exp}&sig={_review_sig(request_id, kind, exp)}"


def _valid_review_link(request_id: str, kind: str, exp: str, sig: str) -> bool:
    if not (exp.isdigit() and sig) or int(exp) < time.time():
        return False
    return hmac.compare_digest(sig, _review_sig(request_id, kind, int(exp)))


@app.get("/files/{request_id}/{kind}")
def get_file(
    request_id: str,
    kind: str,
    authorization: str = Header(default=""),
    exp: str = "",
    sig: str = "",
) -> FileResponse:
    review_link = _valid_review_link(request_id, kind, exp, sig)
    if not review_link:
        _require_auth(authorization)
    if kind not in ("pdf", "docx", "signed"):
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_request", "message": "kind must be 'pdf', 'docx' or 'signed'"},
        )
    # request_id is a hex uuid; reject anything else to avoid path traversal.
    if not request_id.isalnum():
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_request", "message": "invalid request id"},
        )
    directory = OUTPUT_ROOT / request_id
    if kind == "signed":  # fully signed lease (formsAI signing)
        matches = sorted((directory / "signed").glob("*.pdf")) if directory.exists() else []
    else:
        matches = sorted(directory.glob(f"*.{kind}")) if directory.exists() else []
    if not matches:
        raise HTTPException(
            status_code=404,
            detail={"error": "invalid_request", "message": f"no {kind} for request {request_id}"},
        )
    media = "application/pdf" if kind in ("pdf", "signed") else (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    # A person's review link opens in the browser's viewer: Chrome holds http:// downloads
    # as "Unconfirmed …crdownload". Machine (bearer) callers keep the attachment download.
    return FileResponse(
        str(matches[0]), media_type=media, filename=matches[0].name,
        content_disposition_type="inline" if review_link else "attachment",
    )


def _require_approve_auth(authorization: str) -> None:
    """Approval uses a SEPARATE secret from the generation token, so the
    workflow that generates drafts cannot self-approve them (review P1)."""

    token = os.environ.get("FORMS_APPROVE_TOKEN", "")
    if not token:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "unauthorized",
                "message": "approval disabled: FORMS_APPROVE_TOKEN not configured",
            },
        )
    scheme, _, supplied = authorization.partition(" ")
    if scheme.lower() != "bearer" or not hmac.compare_digest(supplied.strip(), token):
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthorized", "message": "invalid approval token"},
        )


@app.post("/approve/{request_id}/{kind}")
def approve_file(
    request_id: str,
    kind: str,
    payload: dict[str, Any],
    authorization: str = Header(default=""),
) -> Any:
    """Record PM approval of a generated notice (U4).

    Body: {"approver": "<name>", "ground": "<section, e.g. 91ZM>"}.
    Requires the FORMS_APPROVE_TOKEN bearer (distinct from the generation token).
    """

    _require_approve_auth(authorization)
    from .approval import ApprovalError, approve

    if kind not in ("pdf", "docx") or not request_id.isalnum():
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_request", "message": "bad request id or kind"},
        )
    directory = OUTPUT_ROOT / request_id
    matches = sorted(directory.glob(f"*.{kind}")) if directory.exists() else []
    if not matches:
        raise HTTPException(
            status_code=404,
            detail={"error": "invalid_request", "message": f"no {kind} for request {request_id}"},
        )
    if len(matches) > 1:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "invalid_request",
                "message": f"multiple {kind} files for request {request_id} — cannot approve ambiguously",
            },
        )
    try:
        return approve(matches[0], str(payload.get("approver", "")), payload.get("ground"))
    except ApprovalError as exc:
        raise HTTPException(
            status_code=400, detail={"error": "invalid_request", "message": str(exc)}
        ) from None
