"""Allmain Letter of Offer / EOI (U13, R15).

Template supplied by Allmain on appointment (live DOCX, label/value tables).
All values are caller-supplied verbatim over agency defaults (KTD8) — the
completing agent is the appointed selling agent.

ponytail: the finance-status, building & pest, and nature-of-offer tick boxes
are Wingdings glyph characters, not form checkboxes — glyph ticking is not
implemented; the agent ticks those in the output document. Upgrade path: run
replacement of the box glyph in the matching run if this becomes high-volume.
"""

from __future__ import annotations

from pathlib import Path

from ...formspec import FormSpec, TextOp
from ...sales import build_sales_context

TEMPLATE = Path(__file__).with_name("template.docx")

CALLER_FIELDS = (
    "date_of_offer",
    "property_address",
    "vendor_name",
    "purchaser_name",
    "purchaser_solicitor",
    "offer_amount",
    "settlement_days",
    "deposit_amount",
    "payment_method",
    "finance_days",
    "additional_conditions",
    "agent_recommendation",
)

AGENCY_FIELDS = ("agent_full_name", "agency_name", "agency_phone", "agency_email")

DECLARED_FIELDS = CALLER_FIELDS + AGENCY_FIELDS

TEXT_OPS = (
    # Section 1: property & transaction
    TextOp("date_of_offer", table_index=1, row_index=0, cell_index=1),
    TextOp("property_address", table_index=1, row_index=1, cell_index=1),
    TextOp("vendor_name", table_index=1, row_index=2, cell_index=1),
    # Section 2: purchaser
    TextOp("purchaser_name", table_index=2, row_index=0, cell_index=1),
    TextOp("purchaser_solicitor", table_index=2, row_index=1, cell_index=1),
    # Section 3: offer terms
    TextOp("offer_amount", table_index=3, row_index=0, cell_index=1),
    TextOp("settlement_days", table_index=4, row_index=0, cell_index=1),
    TextOp("deposit_amount", table_index=4, row_index=0, cell_index=3),
    TextOp("payment_method", table_index=4, row_index=1, cell_index=1),
    TextOp("finance_days", table_index=4, row_index=1, cell_index=3),
    # Section 4: additional conditions (free-text box)
    TextOp("additional_conditions", table_index=7, row_index=0, cell_index=0),
    # Section 6: agent recommendation (free-text box)
    TextOp("agent_recommendation", table_index=9, row_index=0, cell_index=0),
    # Section 8: agent declaration
    TextOp("agent_full_name", table_index=11, row_index=0, cell_index=1),
    TextOp("agency_name", table_index=11, row_index=1, cell_index=1),
    TextOp("agency_phone", table_index=11, row_index=2, cell_index=1),
    TextOp("agency_email", table_index=11, row_index=3, cell_index=1),
)


def build_context(bundle, fields: dict) -> dict[str, str]:
    defaults = build_sales_context({})
    context = {
        "agent_full_name": defaults.get("attention", ""),
        "agency_name": defaults.get("agent_name", ""),
        "agency_phone": defaults.get("agent_mobile", ""),
        "agency_email": defaults.get("agent_email", ""),
    }
    context.update({k: "" if v is None else str(v) for k, v in fields.items()})
    return context


SPEC = FormSpec(
    key="allmain_letter_of_offer",
    template=TEMPLATE,
    declared_fields=DECLARED_FIELDS,
    text_ops=TEXT_OPS,
    checkbox_ops=(),
    build_context=build_context,
    title="Letter of Offer / EOI (Allmain)",
    group="sales_authority",
    caller_field_labels={
        "date_of_offer": "Date of offer (DD/MM/YYYY)",
        "property_address": "Property address",
        "vendor_name": "Vendor / seller name",
        "purchaser_name": "Purchaser full legal name",
        "purchaser_solicitor": "Purchaser solicitor / conveyancer",
        "offer_amount": "Offer amount ($)",
        "settlement_days": "Settlement (days from contract)",
        "deposit_amount": "Deposit amount ($)",
        "payment_method": "Payment method",
        "finance_days": "Finance days",
        "additional_conditions": "Additional conditions",
        "agent_recommendation": "Agent recommendation to vendor",
    },
    requires_bundle=False,
)
