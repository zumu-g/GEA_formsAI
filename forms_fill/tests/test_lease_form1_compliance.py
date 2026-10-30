"""U1: the rendered lease must carry every prescribed line of Form 1 (RT Regs 2021 v009), in order.

``assert_form1_compliant(pdf_bytes)`` is the reusable gate for U3.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import fitz
import pytest

from forms_fill.forms.residential_rental_agreement.spec import SPEC as FORM1_SPEC
from forms_fill.forms.residential_rental_agreement.spec import build_context
from forms_fill.providers.fixture import FixtureProvider
from forms_fill.render import render

FIXTURE = Path(__file__).parent / "fixtures" / "form1_v009.txt"

_CHAR_MAP = str.maketrans(
    {
        "‘": "'", "’": "'", "“": '"', "”": '"',
        "–": "-", "—": "-", "‑": "-", "−": "-",
        " ": " ", "­": None, "•": " ",
    }
)


def normalise(text: str) -> str:
    """Compare wording, not layout: unify quotes/dashes, join hyphen breaks, collapse whitespace, ignore case."""
    text = text.translate(_CHAR_MAP)
    text = re.sub(r"[-☐-☒]", " ", text)  # tick-box glyphs
    text = re.sub(r"-\s*\n\s*", "-", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r" ?- ?", "-", text)
    text = re.sub(r"\b(\d+[a-z]?)\.(?= |$)", r"\1", text, flags=re.I)  # "7. Bond" == "7 Bond"
    return text.strip().lower()


def form1_lines() -> list[str]:
    return [
        ln for ln in FIXTURE.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.startswith("#")
    ]


def missing_form1_lines(text: str) -> list[str]:
    """Fixture lines not found in ``text`` in order (a miss does not advance the cursor)."""
    hay = normalise(text)
    pos, missing = 0, []
    for line in form1_lines():
        at = hay.find(normalise(line), pos)
        if at < 0:
            missing.append(line)
        else:
            pos = at + len(normalise(line))
    return missing


def pdf_text(pdf_bytes: bytes) -> str:
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        return "\n".join(page.get_text() for page in doc)


def assert_form1_compliant(pdf_bytes: bytes) -> None:
    missing = missing_form1_lines(pdf_text(pdf_bytes))
    assert not missing, (
        f"{len(missing)} Form 1 (v009) line(s) missing or out of order:\n"
        + "\n".join(f"  - {ln}" for ln in missing)
    )


# ── helper self-checks ──────────────────────────────────────────────────────


def test_fixture_passes_against_itself():
    assert missing_form1_lines("\n".join(form1_lines())) == []


def test_normalise_ignores_layout_differences():
    assert normalise("Rental provider’s  pre-\ntermination PART A – General") == normalise(
        "rental provider's pre-termination PART A—GENERAL"
    )
    assert normalise("7\nBond") == normalise("7. Bond")


def test_out_of_order_line_is_reported():
    lines = form1_lines()
    swapped = "\n".join([lines[1], lines[0], *lines[2:]])
    assert missing_form1_lines(swapped) == [lines[1]]


# ── the gate ────────────────────────────────────────────────────────────────


def _render_lease_pdf(tmp_path) -> bytes:
    bundle = FixtureProvider().fetch_bundle({"tenancy_id": "T-1001"})
    fields = {
        "term_type": "fixed",
        "agreement_date": "2026-07-01",
        "agent_name": "GEA Property",
        "agent_address": "1 Agent St",
        "agent_postcode": "3000",
        "agent_phone": "0399990000",
        "agent_email": "gea@example.com",
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
        "emergency_contact_name": "GEA Maintenance",
        "emergency_phone": "0399991234",
        "emergency_email": "maint@example.com",
    }
    _, pdf_path, warnings = render(FORM1_SPEC, build_context(bundle, fields), tmp_path)
    if pdf_path is None:
        pytest.skip(f"no PDF produced: {warnings}")
    return pdf_path.read_bytes()


@pytest.mark.xfail(strict=True, reason="lease template not yet on Form 1 v009 — U3")
@pytest.mark.skipif(
    FORM1_SPEC.engine == "docx" and not shutil.which("soffice"),
    reason="DOCX engine needs LibreOffice (soffice) to make the PDF",
)
def test_rendered_lease_is_form1_v009_compliant(tmp_path):
    assert_form1_compliant(_render_lease_pdf(tmp_path))
