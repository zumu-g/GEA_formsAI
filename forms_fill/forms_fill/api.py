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

import hmac
import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

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


def _require_auth(authorization: str) -> None:
    # ponytail: local-dev escape hatch only; Railway never sets this
    if os.environ.get("FORMS_DEV_NO_AUTH") == "1":
        return
    token = os.environ.get("FORMS_API_TOKEN") or ""
    scheme, _, supplied = authorization.partition(" ")
    supplied = supplied.strip()
    if (
        scheme != "Bearer"
        or not token
        or not hmac.compare_digest(supplied.encode(), token.encode())
    ):
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthorized", "message": "missing or invalid bearer token"},
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
    return {
        "office": {
            "name": agency_data.get("name", ""),
            "address": office_address(agency_data),
            "postcode": agency_data.get("postcode", ""),
        },
        "agents": [
            {
                "full_name": a.get("full_name", ""),
                "mobile": a.get("mobile", ""),
                "email": a.get("email", ""),
            }
            for a in cfg["agents"]
        ],
    }


@app.get("/tenancy/search")
def tenancy_search(
    q: str = "", provider: str | None = None, authorization: str = Header(default="")
) -> Any:
    """Address search across the selected data provider's lots (U2, R2/R4)."""

    _require_auth(authorization)
    if not q.strip():
        return _err(400, "invalid_request", "missing search query 'q'")
    from dataclasses import asdict

    from .errors import SearchUnsupportedError
    from .providers.base import select_provider

    try:
        p = select_provider(provider)
        matches = p.search_lots(q)
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
    authorization: str = Header(default=""),
) -> Any:
    """Fetch and return the tenancy bundle for PM verification before filling
    (U2, R3). Reuses fetch_bundle verbatim — read-only."""

    _require_auth(authorization)
    if not lot_id.strip() and not tenancy_id.strip():
        return _err(400, "invalid_request", "provide at least one of lot_id, tenancy_id")
    from .providers.base import select_provider

    identifiers = {}
    if lot_id.strip():
        identifiers["lot_id"] = lot_id.strip()
    if tenancy_id.strip():
        identifiers["tenancy_id"] = tenancy_id.strip()
    from .errors import FetchUnsupportedError

    try:
        p = select_provider(provider)
        bundle = p.fetch_bundle(identifiers)
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


@app.post("/fill")
def fill(payload: dict[str, Any], authorization: str = Header(default="")) -> Any:
    _require_auth(authorization)
    request_id = uuid.uuid4().hex
    out_dir = OUTPUT_ROOT / request_id
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
    body = result.model_dump()
    body["request_id"] = request_id
    # engine contract: files.* are absolute, token-protected URLs
    body["files"] = {
        "pdf": f"{base}/files/{request_id}/pdf" if result.files.pdf else None,
        "docx": f"{base}/files/{request_id}/docx" if result.files.docx else None,
    }
    return body


@app.get("/files/{request_id}/{kind}")
def get_file(
    request_id: str, kind: str, authorization: str = Header(default="")
) -> FileResponse:
    _require_auth(authorization)
    if kind not in ("pdf", "docx"):
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_request", "message": "kind must be 'pdf' or 'docx'"},
        )
    # request_id is a hex uuid; reject anything else to avoid path traversal.
    if not request_id.isalnum():
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_request", "message": "invalid request id"},
        )
    directory = OUTPUT_ROOT / request_id
    matches = sorted(directory.glob(f"*.{kind}")) if directory.exists() else []
    if not matches:
        raise HTTPException(
            status_code=404,
            detail={"error": "invalid_request", "message": f"no {kind} for request {request_id}"},
        )
    media = "application/pdf" if kind == "pdf" else (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    return FileResponse(str(matches[0]), media_type=media, filename=matches[0].name)


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
