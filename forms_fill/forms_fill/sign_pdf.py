"""Build the signed lease: each tenant's signature in their own
"Signature of renter N" box, plus an audit page. Pure: bytes in, bytes out."""

from __future__ import annotations

import hashlib
from pathlib import Path
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


_ASSETS = Path(__file__).parent / "forms" / "_assets"
INK, GREY, RULE = (0x1A / 255, 0x1C / 255, 0x1C / 255), (0x5E / 255,) * 3, (0xCF / 255, 0xC4 / 255, 0xC5 / 255)


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


def _audit_page(doc, sha256: str, signers: list[dict]) -> None:
    """Studio Minimalist signing record, matching the lease pages' chrome."""

    page = doc.new_page(width=595, height=842)  # A4
    for name in ("Regular", "SemiBold"):
        page.insert_font(fontname=f"Inter-{name}", fontfile=str(_ASSETS / "fonts" / f"Inter-{name}.ttf"))
    left, right = 54, page.rect.width - 54
    logo = fitz.Pixmap(str(_ASSETS / "grants-logo-bw.png"))
    page.insert_image(fitz.Rect(left, 36, left + 24 * logo.width / logo.height, 60), pixmap=logo)
    page.insert_textbox(fitz.Rect(right - 200, 48, right, 62), "SIGNING RECORD", fontname="Inter-SemiBold",
                        fontsize=7, color=GREY, align=fitz.TEXT_ALIGN_RIGHT)
    page.draw_line((left, 66), (right, 66), color=RULE, width=0.5)
    page.draw_line((left, 800), (right, 800), color=RULE, width=0.5)
    page.insert_text((left, 812), "Signing record", fontname="Inter-Regular", fontsize=7, color=GREY)

    y = 100

    def write(text, size=9, font="Inter-Regular", color=INK, gap=4):
        nonlocal y
        box = fitz.Rect(left, y, right, 790)
        spare = page.insert_textbox(box, text, fontname=font, fontsize=size, color=color)
        if spare < 0:
            raise SigningError("signing record does not fit on one page")
        y = box.y1 - spare + gap

    def rule():
        nonlocal y
        page.draw_line((left, y), (right, y), color=RULE, width=0.5)
        y += 10

    write("Electronic signing record", size=18, font="Inter-SemiBold", gap=12)
    write("Document SHA-256 (unsigned lease)", size=7, color=GREY, gap=1)
    write(sha256, gap=18)
    for s in signers:
        rule()
        write(f"Renter {s['slot']}: {s['name']} <{s['email']}>", size=10, font="Inter-SemiBold", gap=6)
        for label, value in (("Typed name", s["signed_name"]), ("Signed", _local(s["signed_at"])),
                             ("IP address", s["ip"]), ("Device", s["user_agent"] or "")):
            write(label, size=7, color=GREY, gap=1)
            write(str(value), gap=5)
        y += 10
    rule()
    write(CONSENT, size=8, color=GREY)


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

    _audit_page(doc, hashlib.sha256(original).hexdigest(), signers)
    return doc.tobytes(garbage=3, deflate=True)
