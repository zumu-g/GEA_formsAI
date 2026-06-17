"""HTTP shell (U7, R10).

Exposes ``POST /fill`` over the same ``fill_form`` core, plus file retrieval so a
caller (local or on Railway) can fetch the generated PDF/DOCX. Each request
writes to its own output directory keyed by a request id.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from .core import fill_form
from .errors import (
    FormsFillError,
    ProviderConfigError,
    RenderError,
    TenancyNotFoundError,
    UnknownFormError,
)
from .models import build_request

app = FastAPI(title="GEA forms-fill", version="0.1.0")

# Base directory for per-request outputs (overridable via env in deployment).
OUTPUT_ROOT = Path("./out")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/fill")
def fill(payload: dict[str, Any]) -> dict[str, Any]:
    request_id = uuid.uuid4().hex
    out_dir = OUTPUT_ROOT / request_id
    try:
        request = build_request(json_payload=payload, out_dir=str(out_dir))
        result = fill_form(request)
    except (UnknownFormError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except TenancyNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except (ProviderConfigError, RenderError, FormsFillError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    body = result.model_dump()
    body["request_id"] = request_id
    body["fetch"] = {
        "pdf": f"/files/{request_id}/pdf" if result.files.pdf else None,
        "docx": f"/files/{request_id}/docx" if result.files.docx else None,
    }
    return body


@app.get("/files/{request_id}/{kind}")
def get_file(request_id: str, kind: str) -> FileResponse:
    if kind not in ("pdf", "docx"):
        raise HTTPException(status_code=400, detail="kind must be 'pdf' or 'docx'")
    # request_id is a hex uuid; reject anything else to avoid path traversal.
    if not request_id.isalnum():
        raise HTTPException(status_code=400, detail="invalid request id")
    directory = OUTPUT_ROOT / request_id
    matches = list(directory.glob(f"*.{kind}")) if directory.exists() else []
    if not matches:
        raise HTTPException(status_code=404, detail=f"no {kind} for request {request_id}")
    media = "application/pdf" if kind == "pdf" else (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    return FileResponse(str(matches[0]), media_type=media, filename=matches[0].name)
