"""PM approval sidecar (U4, R5 / KTD4).

A generated notice is a draft. Approval writes ``<file>.approval.json``
(approver, UTC timestamp, SHA-256 of the approved file). Lodgement (U5)
verifies the hash still matches — a regenerated or edited notice invalidates
its approval. No database, no queue: the calling workflow owns orchestration.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .errors import FormsFillError


class ApprovalError(FormsFillError):
    """Missing, invalid, or stale approval."""


def _sidecar(path: Path) -> Path:
    return path.with_name(path.name + ".approval.json")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def approve(path: str | Path, approver: str) -> dict:
    """Record PM approval of the notice file. Returns the approval record."""

    path = Path(path)
    if not path.is_file():
        raise ApprovalError(f"cannot approve: file not found: {path}")
    approver = approver.strip()
    if not approver:
        raise ApprovalError("cannot approve: approver name is required")

    record = {
        "approver": approver,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "sha256": _sha256(path),
        "file": path.name,
    }
    _sidecar(path).write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def verify_approval(path: str | Path) -> dict:
    """Return the approval record iff the file is approved and unchanged."""

    path = Path(path)
    sidecar = _sidecar(path)
    if not sidecar.is_file():
        raise ApprovalError(
            f"not approved: no approval record for {path.name} — a PM must "
            "approve the draft before lodgement"
        )
    record = json.loads(sidecar.read_text(encoding="utf-8"))
    if not path.is_file():
        raise ApprovalError(f"approved file is missing: {path}")
    if _sha256(path) != record.get("sha256"):
        raise ApprovalError(
            f"notice changed since approval: {path.name} no longer matches the "
            "approved version — re-review and re-approve"
        )
    return record
