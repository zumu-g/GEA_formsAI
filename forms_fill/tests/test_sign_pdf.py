"""Stamping tenant signatures into their own renter boxes + audit page."""

import hashlib

import fitz
import pytest

from forms_fill.sign_pdf import SigningError, build_signed_pdf


def _png():
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 60, 20), False)
    pix.set_rect(pix.irect, (20, 20, 20))
    return pix.tobytes("png")


def _lease_pdf(slots=(1, 2)):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 100), "Signature of rental provider 1")
    for i, slot in enumerate(slots):
        page.insert_text((72, 200 + 80 * i), f"Signature of renter {slot}")
    return doc.tobytes()


def _signer(slot, name):
    return {"slot": slot, "name": name, "email": f"{name.split()[0].lower()}@example.com",
            "signed_name": name, "signature_png": _png(), "signed_at": "2026-10-30T02:00:00+00:00",
            "ip": "1.2.3.4", "user_agent": "Mozilla/5.0"}


def test_each_signature_lands_right_of_its_own_renter_label():
    original = _lease_pdf()
    out = fitz.open(stream=build_signed_pdf(original, [_signer(1, "Jane Renter"), _signer(2, "Sam Renter")]))
    page = out[0]
    # one entry per placement (identical PNGs share an xref)
    images = sorted((fitz.Rect(i["bbox"]) for i in page.get_image_info()), key=lambda r: r.y0)
    assert len(images) == 2
    for rect, slot in zip(images, (1, 2)):
        (label,) = page.search_for(f"Signature of renter {slot}")
        assert rect.x0 >= label.x1  # to the right of the label
        assert rect.y0 <= label.y1 and rect.y1 >= label.y0  # on the label's row


def test_audit_page_lists_every_signer_and_the_document_hash():
    original = _lease_pdf()
    out = fitz.open(stream=build_signed_pdf(original, [_signer(1, "Jane Renter"), _signer(2, "Sam Renter")]))
    assert len(out) == 2
    audit = out[-1].get_text()
    assert hashlib.sha256(original).hexdigest() in audit
    for text in ("Jane Renter", "sam@example.com", "1.2.3.4", "30/10/2026 1:00 PM",
                 "Electronic Transactions (Victoria) Act 2000"):
        assert text in audit


def test_a_missing_renter_box_raises_instead_of_dropping_a_signature():
    with pytest.raises(SigningError, match="renter 3"):
        build_signed_pdf(_lease_pdf(), [_signer(3, "Alex Renter")])


def test_missing_boxes_names_each_slot_without_a_box():
    from forms_fill.sign_pdf import missing_boxes

    assert missing_boxes(_lease_pdf(), [1, 2]) == []
    assert missing_boxes(_lease_pdf(), [1, 3]) == [3]
