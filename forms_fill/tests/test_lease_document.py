"""U3: the GEA lease document (cover + Form 1 Parts A-E) rendered by the html engine."""

from __future__ import annotations

import fitz
import pytest

from forms_fill.forms.residential_rental_agreement.spec import SPEC as FORM1_SPEC
from forms_fill.forms.residential_rental_agreement.spec import build_context
from forms_fill.providers.fixture import FixtureProvider
from forms_fill.render import render
from forms_fill.sign_pdf import missing_boxes

FIELDS = {
    "term_type": "fixed",
    "agreement_date": "2026-07-01",
    "renter1_name": "Alice Renter",
    "renter2_name": "Bob Renter",
    "renter1_current_address": "5 Old St",
    "renter1_current_postcode": "3122",
    "fixed_start_date": "2026-08-01",
    "fixed_end_date": "2027-08-01",
    "rent_amount": "615",
    "rent_period": "week",
    "rent_payment_day": "Thursday",
    "first_rent_due_date": "2026-08-01",
    "bond_amount": "2460",
    "bond_due_date": "2026-08-01",
}


def _pdf(tmp_path, **overrides) -> bytes:
    bundle = FixtureProvider().fetch_bundle({"tenancy_id": "T-1001"})
    ctx = build_context(bundle, {**FIELDS, **overrides})
    docx, pdf, _ = render(FORM1_SPEC, ctx, tmp_path)
    assert docx is None
    return pdf.read_bytes()


def _pages(pdf: bytes) -> list[str]:
    with fitz.open(stream=pdf, filetype="pdf") as doc:
        return [p.get_text() for p in doc]


def _flat(s: str) -> str:
    return " ".join(s.split())


def test_lease_uses_html_engine():
    assert FORM1_SPEC.engine == "html" and FORM1_SPEC.build_html is not None


def test_cover_shows_premises_agency_pm_and_renters(tmp_path):
    cover = _flat(_pages(_pdf(tmp_path))[0])
    for text in (
        "Residential Rental Agreement",
        "12 Example Street, Richmond 3121",
        "Grants Estate Agents",
        "Stuart Grant",
        "mobile: 0438 554 522",
        "email: stuart@grantsea.com.au",
        "Alice Renter",
        "Bob Renter",
    ):
        assert text in cover, text


def test_fixed_term_ticks_fixed_and_prints_dates(tmp_path):
    body = _flat("\n".join(_pages(_pdf(tmp_path))[1:]))
    assert "■ Fixed term agreement" in body
    assert "□ Periodic agreement (monthly)" in body
    assert "01/08/2027" in body


def test_periodic_ticks_periodic_and_omits_fixed_dates(tmp_path):
    pdf = _pdf(
        tmp_path, term_type="periodic", periodic_start_date="2026-09-09",
        fixed_start_date="", fixed_end_date="",
    )
    body = _flat("\n".join(_pages(pdf)[1:]))
    assert "□ Fixed term agreement" in body
    assert "■ Periodic agreement (monthly)" in body
    assert "09/09/2026" in body and "01/08/2027" not in body


def test_empty_bond_due_date_prints_label_only(tmp_path):
    body = "\n".join(_pages(_pdf(tmp_path, bond_due_date=""))[1:])
    line_after = body.split("Date bond payment due", 1)[1].lstrip("\n").splitlines()[0]
    assert line_after.startswith("PART B") or line_after == "", line_after
    for junk in ("N/A", "n/a", "TBC", "Sample", "example"):
        assert junk not in body.split("PART B")[0].split("7. Bond")[1]


def test_signing_boxes_present_with_date_below(tmp_path):
    pdf = _pdf(tmp_path)
    assert missing_boxes(pdf, [1, 2, 3, 4]) == []
    with fitz.open(stream=pdf, filetype="pdf") as doc:
        for n in (1, 2, 3, 4):
            hits = [(p, r) for p in doc for r in p.search_for(f"Signature of renter {n}")]
            assert len(hits) == 1
            page, label = hits[0]
            dates = [d for d in page.search_for("Date") if label.y1 <= d.y0 <= label.y1 + 70]
            assert dates, n
            # clear space right of the label for the stamped signature image
            right = fitz.Rect(label.x1 + 2, label.y0 - 12, label.x1 + 300, label.y1 + 12)
            assert not page.get_text(clip=right).strip(), n


def test_html_escapes_values():
    ctx = {k: "" for k in FORM1_SPEC.declared_fields}
    ctx["renter1_name"] = "<b>Eve</b> & Co"
    html = FORM1_SPEC.build_html(ctx).html
    assert "&lt;b&gt;Eve&lt;/b&gt; &amp; Co" in html and "<b>Eve" not in html


def test_postcode_not_repeated_when_address_already_ends_with_it():
    ctx = {k: "" for k in FORM1_SPEC.declared_fields}
    ctx.update(provider_address="1 Agency Rd, Melbourne VIC 3000", provider_postcode="3000")
    html = FORM1_SPEC.build_html(ctx).html
    assert "Melbourne VIC 3000<" in html and "3000 3000" not in html


def test_iso_dates_print_in_australian_format(tmp_path):
    # GEA LLM sends ISO dates; the lease must read DD/MM/YYYY (30 Oct 2026 review).
    text = _flat("".join(_pages(_pdf(tmp_path, agreement_date="2026-07-01", bond_due_date="2026-07-15"))))
    assert "01/07/2026" in text and "15/07/2026" in text
    assert "2026-07-01" not in text


def test_non_iso_dates_print_exactly_as_given(tmp_path):
    text = _flat("".join(_pages(_pdf(tmp_path, agreement_date="1 July 2026"))))
    assert "1 July 2026" in text
