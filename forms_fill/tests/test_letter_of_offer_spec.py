"""Allmain letter of offer spec tests (U13)."""

from __future__ import annotations

import docx

from forms_fill.core import fill_form
from forms_fill.models import FillRequest

FIELDS = {
    "date_of_offer": "11/07/2026",
    "property_address": "43 Bellagio Road, Berwick VIC 3806",
    "vendor_name": "ANZ Banking Group Limited (mortgagee exercising power of sale)",
    "purchaser_name": "Jane Q Buyer",
    "purchaser_solicitor": "Smith & Co Conveyancing",
    "offer_amount": "$560,000",
    "settlement_days": "60",
    "deposit_amount": "$56,000",
    "payment_method": "EFT",
    "finance_days": "14",
    "agent_recommendation": "Strong offer relative to the appraised range; recommend acceptance.",
}


def test_letter_of_offer_fills_cells_verbatim(tmp_path):
    result = fill_form(
        FillRequest(
            form="allmain_letter_of_offer",
            identifiers={},
            fields=FIELDS,
            out_dir=str(tmp_path),
        )
    )
    assert result.ok
    text = "\n".join(
        c.text for t in docx.Document(result.files.docx).tables for r in t.rows for c in r.cells
    )
    assert "$560,000" in text
    assert "Jane Q Buyer" in text
    assert "recommend acceptance" in text
    assert "Grants Estate Agents" in text  # agency defaults in Section 8
    assert "additional_conditions" in result.blank_fields
