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


def _ink_only(png: bytes) -> fitz.Pixmap:
    """Crop the signing pad's transparent canvas to the drawn ink."""

    pix = fitz.Pixmap(png)
    if not pix.alpha:
        return pix
    w, h = pix.width, pix.height
    alpha = pix.samples[pix.n - 1 :: pix.n]
    rows = [y for y in range(h) if alpha[y * w : (y + 1) * w].strip(b"\0")]
    if not rows:
        return pix
    left = min(w - len(alpha[y * w : (y + 1) * w].lstrip(b"\0")) for y in rows)
    right = max(len(alpha[y * w : (y + 1) * w].rstrip(b"\0")) for y in rows)
    ink = fitz.IRect(left, rows[0], right, rows[-1] + 1)
    cropped = fitz.Pixmap(pix.colorspace, ink, True)
    cropped.copy(pix, ink)
    return cropped


def _date_label_below(page, label):
    """The renter's own Date box label: the first "Date" just below."""

    below = [d for d in page.search_for("Date") if label.y1 <= d.y0 <= label.y1 + 70]
    return min(below, key=lambda d: d.y0) if below else None


def missing_boxes(pdf: bytes, slots: list[int]) -> list[int]:
    """Renter slots with no signature box — checked before links go out."""

    doc = fitz.open(stream=pdf, filetype="pdf")
    found = {s for s in slots for page in doc if page.search_for(f"Signature of renter {s}")}
    return [s for s in slots if s not in found]


def build_signed_pdf(original: bytes, signers: list[dict]) -> bytes:
    doc = fitz.open(stream=original, filetype="pdf")
    for s in signers:
        page, label = _label(doc, s["slot"])
        ink = _ink_only(s["signature_png"])
        mid = (label.y0 + label.y1) / 2
        height = 26.0
        width = min(height * ink.width / ink.height, page.rect.width - 36 - (label.x1 + 24))
        page.insert_image(fitz.Rect(label.x1 + 24, mid - height / 2, label.x1 + 24 + width, mid + height / 2),
                          pixmap=ink, keep_proportion=True)
        date_label = _date_label_below(page, label)
        if date_label is not None:
            signed_on = datetime.fromisoformat(s["signed_at"]).astimezone(MELBOURNE)
            page.insert_text((label.x1 + 24, date_label.y1 - 2), f"{signed_on:%d/%m/%Y}", fontsize=10)

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
            f"  Device: {s['user_agent'] or ''}",
            "",
        ]
    lines.append(CONSENT)
    audit.insert_textbox(fitz.Rect(54, 54, audit.rect.width - 54, audit.rect.height - 54),
                         "\n".join(lines), fontsize=9)
    return doc.tobytes(garbage=3, deflate=True)
