"""Stamping tenant signatures into their own renter boxes + audit page."""

import hashlib

import fitz
import pytest

from forms_fill.sign_pdf import SigningError, build_signed_pdf


def _png():
    """A wide transparent canvas with a small ink stroke near its middle, like
    the signing pad produces."""

    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 600, 200), True)
    pix.set_rect(pix.irect, (20, 20, 20, 255))
    alpha = bytearray(600 * 200)  # transparent except the stroke
    for y in range(90, 110):
        alpha[y * 600 + 250 : y * 600 + 350] = b"\xff" * 100
    pix.set_alpha(bytes(alpha))
    return pix.tobytes("png")


def _lease_pdf(slots=(1, 2)):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 100), "Signature of rental provider 1")
    for i, slot in enumerate(slots):
        page.insert_text((72, 200 + 80 * i), f"Signature of renter {slot}")
        page.insert_text((72, 230 + 80 * i), "Date")
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


def test_signature_is_cropped_to_the_ink_and_starts_at_the_box():
    out = fitz.open(stream=build_signed_pdf(_lease_pdf(), [_signer(1, "Jane Renter")]))
    page = out[0]
    (label,) = page.search_for("Signature of renter 1")
    (info,) = page.get_image_info()
    rect = fitz.Rect(info["bbox"])
    assert rect.x0 - label.x1 < 30  # starts at the box, not floating right
    assert rect.width / rect.height == pytest.approx(100 / 20, rel=0.1)  # ink only


def test_each_renter_date_box_gets_the_melbourne_signing_date():
    out = fitz.open(stream=build_signed_pdf(_lease_pdf(), [_signer(1, "Jane Renter"), _signer(2, "Sam Renter")]))
    page = out[0]
    dates = page.search_for("30/10/2026")
    labels = page.search_for("Date")
    assert len(dates) == 2
    for d in dates:
        assert any(abs(d.y0 - l.y0) < 4 and d.x0 > l.x1 for l in labels)


def test_audit_page_keeps_the_whole_device_string():
    s = _signer(1, "Jane Renter")
    s["user_agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/140.0 Safari/537.36"
    out = fitz.open(stream=build_signed_pdf(_lease_pdf(), [s]))
    assert "Safari/537.36" in out[-1].get_text().replace("\n", " ")


def test_audit_page_is_studio_minimalist_with_inter_and_logo():
    signers = [_signer(1, "Jane Renter"), _signer(2, "Sam Tenant")]
    original = _lease_pdf()
    audit = fitz.open(stream=build_signed_pdf(original, signers))[-1]
    assert any("Inter" in f[3] for f in audit.get_fonts())
    assert audit.get_images()
    text = audit.get_text()
    for t in ("SIGNING RECORD", "Signing record", "Electronic signing record",
              hashlib.sha256(original).hexdigest(), "Jane Renter", "sam@example.com", "1.2.3.4", "Mozilla/5.0"):
        assert t in text
