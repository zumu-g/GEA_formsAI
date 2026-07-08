"""CAV "Notice of breach of duty to renter/s of rented premises" form spec
(RTA 1997 (Vic) s 208(1) and (2), duty-breach grounds ss 60-89).

Source: https://www.consumer.vic.gov.au/library/forms/housing-and-accommodation/
renting/notice-of-breach-of-duty-to-renters-of-rented-premises.docx (downloaded
2026-07-08, current version — confirmed the reference table at table index 27
lists all 14 duty provisions the myVCAT "Giving Notice for Breach of Duty"
catalogue covers: 60(1), 60(2), 61, 63(1), 63A, 64(1A)(a), 64(1A)(b), 64(2),
70(2), 70(3), 89).

Table/cell indices below were derived by inspecting the template's structure
(python-docx): 28 tables total, same label/value single-row layout as
`notice_to_vacate` and `cav_rent_increase_notice`.

One template covers every duty-breach ground (KTD2, mirrors `notice_to_vacate`):
the specific provision + facts are supplied verbatim by the caller in
`breach_details`, never authored or validated by this spec.

Left blank by design (mirrors R7 in the rent-increase spec, R4 in NTV): section
5 "Delivery of this notice" (tables 15-19) and section 6 signature block (tables
25-26) — the PM's manual-service steps, never automated. Table 13 (the
"relevant breach / timeframe" reference table) and table 27 (the full duty-
provision reference list) are static reference content printed on the template
itself, not fillable fields — the rental provider circles/copies from them by
hand, so neither is declared here.
"""

from __future__ import annotations

from pathlib import Path

from ...formspec import FormSpec, TextOp
from ...models import TenancyBundle

TEMPLATE = Path(__file__).with_name("template.docx")

# Caller-supplied, rendered verbatim — never computed or validated here.
CALLER_FIELDS = (
    "breach_details",
    "loss_or_damage",
    "remedy_action",
    "compensation_amount",
)

# Fetched-from-provider text fields (same shape as notice_to_vacate).
FETCHED_FIELDS = (
    "premises_address",
    "premises_postcode",
    "renter1_name",
    "renter2_name",
    "renter3_name",
    "renter4_name",
    "provider_name",
    "provider_address",
    "provider_postcode",
    "provider_business_hours",
    "provider_after_hours",
    "provider_email",
)

DECLARED_FIELDS = FETCHED_FIELDS + CALLER_FIELDS

TEXT_OPS = (
    # Part B, section 1 — premises
    TextOp("premises_address", table_index=1, cell_index=0),
    TextOp("premises_postcode", table_index=1, cell_index=2),
    # Section 2 — renters
    TextOp("renter1_name", table_index=2, cell_index=1),
    TextOp("renter2_name", table_index=3, cell_index=1),
    TextOp("renter3_name", table_index=4, cell_index=1),
    TextOp("renter4_name", table_index=5, cell_index=1),
    # Section 3 — rental provider (never the mortgagee/agent)
    TextOp("provider_name", table_index=6, cell_index=0),
    TextOp("provider_address", table_index=7, cell_index=0),
    TextOp("provider_postcode", table_index=7, cell_index=2),
    TextOp("provider_business_hours", table_index=8, cell_index=1),
    TextOp("provider_after_hours", table_index=9, cell_index=1),
    TextOp("provider_email", table_index=10, cell_index=1),
    # Section 4 — reason for notice (free text; provision + facts supplied
    # verbatim by the caller, never authored by this spec)
    TextOp("breach_details", table_index=11, cell_index=0),
    TextOp("loss_or_damage", table_index=12, cell_index=0),
    TextOp("remedy_action", table_index=14, cell_index=0, row_index=0),
    TextOp("compensation_amount", table_index=14, cell_index=1, row_index=1),
)


def _s(value: object) -> str:
    return "" if value is None else str(value)


def build_context(bundle: TenancyBundle, fields: dict) -> dict[str, str]:
    """Merge fetched bundle data with verbatim caller fields into a flat context."""

    renters = list(bundle.renters)

    def renter(i: int):
        return renters[i] if i < len(renters) else None

    ctx: dict[str, str] = {
        "premises_address": _s(bundle.premises.address_line),
        "premises_postcode": _s(bundle.premises.postcode),
        "renter1_name": _s(renter(0).full_name) if renter(0) else "",
        "renter2_name": _s(renter(1).full_name) if renter(1) else "",
        "renter3_name": _s(renter(2).full_name) if renter(2) else "",
        "renter4_name": _s(renter(3).full_name) if renter(3) else "",
        "provider_name": _s(bundle.rental_provider.full_name),
        "provider_address": _s(bundle.rental_provider.service_address),
        "provider_postcode": _s(bundle.rental_provider.service_postcode),
        "provider_business_hours": _s(bundle.rental_provider.phone_business_hours),
        "provider_after_hours": _s(bundle.rental_provider.phone_after_hours),
        "provider_email": _s(bundle.rental_provider.email),
        # Caller fields — verbatim, no computation/validation.
        "breach_details": _s(fields.get("breach_details")),
        "loss_or_damage": _s(fields.get("loss_or_damage")),
        "remedy_action": _s(fields.get("remedy_action")),
        "compensation_amount": _s(fields.get("compensation_amount")),
    }

    # >4 renters -> overflow note appended to renter 4's slot (mirrors
    # notice_to_vacate's handling).
    if len(renters) > 4:
        extra = ", ".join(_s(r.full_name) for r in renters[4:])
        ctx["renter4_name"] = (
            f"{ctx['renter4_name']} (plus additional renters on extra page: {extra})"
        )

    return ctx


SPEC = FormSpec(
    key="breach_of_duty_notice",
    template=TEMPLATE,
    declared_fields=DECLARED_FIELDS,
    text_ops=TEXT_OPS,
    checkbox_ops=(),
    build_context=build_context,
    title="Notice of breach of duty to renter/s of rented premises",
    group="breach_of_duty",
    caller_field_labels={
        "breach_details": "Breach details (provision + facts, verbatim)",
        "loss_or_damage": "Loss or damage caused (if any)",
        "remedy_action": "Remedy required within the notice period",
        "compensation_amount": "Compensation required ($, if any)",
    },
)
