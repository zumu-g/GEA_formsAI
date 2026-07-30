"""PM Exclusive Leasing & Management Authority (U1-U3, plan 2026-07-29-001).

No REIV/CAV pad exists for this authority (unlike ``reiv_exclusive_sale_
authority``, which overlays GEA's real pad) — see the plan's Open Question 1.
``template.docx`` is therefore a freshly authored GEA document, table-per-
field addressed the same way as ``cav_rent_increase_notice``, with the legal
clause body text left as ``[TBD — GEA legal wording pending]`` placeholders
(KTD2). Do not fill those placeholders from the iProperty Express reference
document used to scope this form's sections — that document belongs to a
different agency and its wording is not GEA's approved legal text.

Commission-sharing and rebate-entitlement are plain Yes/No text fields
rather than legacy-checkbox selectors (simplification vs. the plan's KTD2
sketch — a tick mark needs a hand-authored ``w:checkBox`` legacy form field
in the template's OOXML, which python-docx cannot create; a text field does
the same job with far less template-authoring risk. Add real checkboxes
later if the printed form needs them).

Agent/agency fields reuse ``sales.py``'s shape (KTD3) — same merge-over-
defaults pattern as ``reiv_exclusive_sale_authority``.
"""

from __future__ import annotations

from pathlib import Path

from ...formspec import FormSpec, TextOp
from ...sales import build_sales_context

TEMPLATE = Path(__file__).with_name("template.docx")

AGENCY_DEFAULT_FIELDS = (
    "agent_name",
    "agent_acn",
    "agency_address",
    "attention",
    "agent_mobile",
    "agent_email",
)

CALLER_FIELDS = (
    "owner_names",
    "owner_address",
    "owner_phone",
    "owner_email",
    "property_address",
    "exclusive_leasing_days",
    "continuing_leasing_days",
    "fixed_management_period",
    "rent_per_week",
    "security_bond",
    "urgent_repair_limit",
    "leasing_fee",
    "releasing_fee",
    "managing_fee",
    "commission_sharing",
    "rebate_entitlement",
    "agreement_date",
)

DECLARED_FIELDS = AGENCY_DEFAULT_FIELDS + CALLER_FIELDS

# Table order matches the order fields were written in build_template.py —
# one 1-row, 2-cell (label | value) table per field, cell_index=1 is value.
TEXT_OPS = (
    TextOp("agent_name", table_index=0, cell_index=1),
    TextOp("agent_acn", table_index=1, cell_index=1),
    TextOp("agency_address", table_index=2, cell_index=1),
    TextOp("attention", table_index=3, cell_index=1),
    TextOp("agent_mobile", table_index=4, cell_index=1),
    TextOp("agent_email", table_index=5, cell_index=1),
    TextOp("owner_names", table_index=6, cell_index=1),
    TextOp("owner_address", table_index=7, cell_index=1),
    TextOp("owner_phone", table_index=8, cell_index=1),
    TextOp("owner_email", table_index=9, cell_index=1),
    TextOp("property_address", table_index=10, cell_index=1),
    TextOp("exclusive_leasing_days", table_index=11, cell_index=1),
    TextOp("continuing_leasing_days", table_index=12, cell_index=1),
    TextOp("fixed_management_period", table_index=13, cell_index=1),
    TextOp("rent_per_week", table_index=14, cell_index=1),
    TextOp("security_bond", table_index=15, cell_index=1),
    TextOp("urgent_repair_limit", table_index=16, cell_index=1),
    TextOp("leasing_fee", table_index=17, cell_index=1),
    TextOp("releasing_fee", table_index=18, cell_index=1),
    TextOp("managing_fee", table_index=19, cell_index=1),
    TextOp("commission_sharing", table_index=20, cell_index=1),
    TextOp("rebate_entitlement", table_index=21, cell_index=1),
    TextOp("agreement_date", table_index=22, cell_index=1),
)


def build_context(bundle, fields: dict) -> dict[str, str]:
    return build_sales_context(fields)


SPEC = FormSpec(
    key="pm_exclusive_leasing_authority",
    template=TEMPLATE,
    declared_fields=DECLARED_FIELDS,
    text_ops=TEXT_OPS,
    checkbox_ops=(),
    build_context=build_context,
    selector_fields=(),
    title="Exclusive Leasing & Management Authority",
    group="pm_authority",
    caller_field_labels={
        "owner_names": "Owner(s) name(s)",
        "owner_address": "Owner address",
        "property_address": "Property address",
        "exclusive_leasing_days": "Exclusive leasing period (days)",
        "continuing_leasing_days": "Continuing leasing period (days)",
        "fixed_management_period": "Fixed management period (or n/a)",
        "rent_per_week": "Rent (per week)",
        "security_bond": "Security bond",
        "urgent_repair_limit": "Urgent repair limit ($)",
        "leasing_fee": "Leasing fee",
        "releasing_fee": "Re-leasing fee",
        "managing_fee": "Managing fee",
        "commission_sharing": "Commission sharing (Yes/No)",
        "rebate_entitlement": "Rebate entitlement (Yes/No)",
        "agreement_date": "Agreement date",
    },
    engine="docx",
    requires_bundle=False,
)
