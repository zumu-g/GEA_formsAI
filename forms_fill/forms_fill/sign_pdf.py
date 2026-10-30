"""Build the signed lease: each tenant's signature in their own
"Signature of renter N" box, plus an audit page. Pure: bytes in, bytes out."""

from __future__ import annotations

import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

import fitz  # PyMuPDF

from .errors import FormsFillError

MELBOURNE = ZoneInfo("Australia/Melbourne")
CONSENT = (
    "Each signer consented to sign this agreement electronically under the "
    "Electronic Transactions (Victoria) Act 2000, typed their full name and "
    "drew their signature on formsAI."
)


class SigningError(FormsFillError):
    """The signed PDF can't be built correctly — never ship it half-signed."""


def _local(iso: str) -> str:
    t = datetime.fromisoformat(iso).astimezone(MELBOURNE)
    hour = t.hour % 12 or 12
    return f"{t:%d/%m/%Y} {hour}:{t:%M} {'AM' if t.hour < 12 else 'PM'} ({t.tzname()})"


def _label(doc, slot: int):
    for page in doc:
        hits = page.search_for(f"Signature of renter {slot}")
        if hits:
            return page, hits[0]
    raise SigningError(f"no 'Signature of renter {slot}' box in the lease PDF")


def build_signed_pdf(original: bytes, signers: list[dict]) -> bytes:
    doc = fitz.open(stream=original, filetype="pdf")
    for s in signers:
        page, label = _label(doc, s["slot"])
        mid = (label.y0 + label.y1) / 2
        box = fitz.Rect(label.x1 + 8, mid - 14, page.rect.width - 36, mid + 14)
        page.insert_image(box, stream=s["signature_png"], keep_proportion=True)

    audit = doc.new_page()
    lines = [
        "Electronic signing record",
        "",
        f"Document SHA-256 (unsigned lease): {hashlib.sha256(original).hexdigest()}",
        "",
    ]
    for s in signers:
        lines += [
            f"Renter {s['slot']}: {s['name']} <{s['email']}>",
            f"  Typed name: {s['signed_name']}",
            f"  Signed: {_local(s['signed_at'])}",
            f"  IP address: {s['ip']}",
            f"  Device: {(s['user_agent'] or '')[:90]}",
            "",
        ]
    lines.append(CONSENT)
    audit.insert_textbox(fitz.Rect(54, 54, audit.rect.width - 54, audit.rect.height - 54),
                         "\n".join(lines), fontsize=9)
    return doc.tobytes(garbage=3, deflate=True)
