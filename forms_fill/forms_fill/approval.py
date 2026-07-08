"""PM approval sidecar (U4, R5 / KTD4).

A generated notice is a draft. Approval writes ``<file>.approval.json``
(approver, UTC timestamp, SHA-256 of the approved file, ground section, and —
when ``FORMS_APPROVE_TOKEN`` is set — an HMAC signature over the record so a
process with mere filesystem access cannot forge an approval). Lodgement (U5)
verifies hash, signature, and ground — a regenerated or edited notice, a
forged sidecar, or a different application ground all invalidate approval.

``FORMS_APPROVE_TOKEN`` is a *separate* secret from the generation API token:
the workflow that generates drafts must not be able to approve its own output
(review finding). Unset = dev mode: records are unsigned and verification
accepts unsigned records.

No database, no queue: the calling workflow owns orchestration.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .errors import FormsFillError

_SIGNING_ENV = "FORMS_APPROVE_TOKEN"


class ApprovalError(FormsFillError):
    """Missing, invalid, forged, or stale approval."""


def _sidecar(path: Path) -> Path:
    return path.with_name(path.name + ".approval.json")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _sign(record: dict) -> str | None:
    key = os.environ.get(_SIGNING_ENV)
    if not key:
        return None
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":"))
    return hmac.new(key.encode(), canonical.encode(), hashlib.sha256).hexdigest()


def approve(path: str | Path, approver: str, ground: str | None = None) -> dict:
    """Record PM approval of the notice file. Returns the approval record.

    ``ground`` binds the approval to the statutory section the PM reviewed, so
    lodgement can refuse a different application type against the same file.
    """

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
        "ground": ground.strip() if ground else None,
    }
    signature = _sign(record)
    stored = {**record, "signature": signature} if signature else record
    _sidecar(path).write_text(json.dumps(stored, indent=2), encoding="utf-8")
    return stored


def verify_approval(path: str | Path, ground: str | None = None) -> dict:
    """Return the approval record iff the file is approved, unchanged, signed
    (when signing is configured), and — if ``ground`` is given — approved for
    that same statutory ground."""

    path = Path(path)
    sidecar = _sidecar(path)
    if not sidecar.is_file():
        raise ApprovalError(
            f"not approved: no approval record for {path.name} — a PM must "
            "approve the draft before lodgement"
        )
    try:
        stored = json.loads(sidecar.read_text(encoding="utf-8"))
        if not isinstance(stored, dict):
            raise ValueError("not an object")
    except (ValueError, OSError):
        raise ApprovalError(
            f"approval record unreadable for {path.name} — re-approve"
        ) from None

    if os.environ.get(_SIGNING_ENV):
        signature = stored.get("signature")
        record = {k: v for k, v in stored.items() if k != "signature"}
        expected = _sign(record)
        if not signature or not hmac.compare_digest(signature, expected or ""):
            raise ApprovalError(
                f"approval record for {path.name} is unsigned or has an invalid "
                "signature — re-approve through the authorised approval step"
            )

    if not path.is_file():
        raise ApprovalError(f"approved file is missing: {path}")
    if _sha256(path) != stored.get("sha256"):
        raise ApprovalError(
            f"notice changed since approval: {path.name} no longer matches the "
            "approved version — re-review and re-approve"
        )
    approved_ground = stored.get("ground")
    if ground is not None and approved_ground is not None and ground.strip() != approved_ground:
        raise ApprovalError(
            f"approval mismatch: {path.name} was approved for ground "
            f"{approved_ground}, not {ground.strip()} — re-approve for the "
            "intended application"
        )
    return stored
