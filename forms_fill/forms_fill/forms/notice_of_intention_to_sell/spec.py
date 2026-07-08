"""CAV "Notice of intention to sell" form spec (RTA 1997 (Vic) s 89).

Source: https://www.consumer.vic.gov.au/library/forms/housing-and-accommodation/
renting/notice-of-intention-to-sell.docx (downloaded 2026-07-08).

Table/cell indices below were derived by inspecting the template's structure
(python-docx): 23 tables total, same indexed label/value cell layout as
`notice_to_vacate`.

Section 3 "Residential rental provider details" on this template exposes only
a business-hours contact (no after-hours/email table) — unlike the shipped
notice-to-vacate spec's provider block. This is a template difference, not an
omission.

Section 4 "Intention to sell" optionally names a selling agent (a distinct
role from GEA acting as the rental provider's managing agent) — these are
caller-supplied free-text fields since a selling agent is not part of the
`TenancyBundle` provider contract.

Left blank by design (mirrors R7 in the rent-increase spec): the "Address for
service (if different to address of premises above)" alternate-address table
(table 6, rarely used and not modelled by the provider contract), section 5
"Delivery of this notice" (tables 15-20, delivery-method checkboxes/tracking
number), and section 6 signature block (tables 21-22) — all PM manual-service
steps, never automated.
"""

from __future__ import annotations

from pathlib import Path

from ...formspec import FormSpec, TextOp
from ...models import TenancyBundle

TEMPLATE = Path(__file__).with_name("template.docx")

# Caller-supplied, rendered verbatim — the selling agent is optional and not
# part of the provider data contract.
CALLER_FIELDS = (
    "selling_agent_name",
    "selling_agent_address",
    "selling_agent_postcode",
    "selling_agent_business_hours",
    "selling_agent_after_hours",
    "selling_agent_email",
)

# Fetched-from-provider text fields.
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
)

DECLARED_FIELDS = FETCHED_FIELDS + CALLER_FIELDS

TEXT_OPS = (
    # Section 1 — premises
    TextOp("premises_address", table_index=1, cell_index=0),
    TextOp("premises_postcode", table_index=1, cell_index=2),
    # Section 2 — renters
    TextOp("renter1_name", table_index=2, cell_index=1),
    TextOp("renter2_name", table_index=3, cell_index=1),
    TextOp("renter3_name", table_index=4, cell_index=1),
    TextOp("renter4_name", table_index=5, cell_index=1),
    # Section 3 — rental provider (business hours only, per this template)
    TextOp("provider_name", table_index=7, cell_index=0),
    TextOp("provider_address", table_index=8, cell_index=0),
    TextOp("provider_postcode", table_index=8, cell_index=2),
    TextOp("provider_business_hours", table_index=9, cell_index=1),
    # Section 4 — selling agent (optional, caller-supplied)
    TextOp("selling_agent_name", table_index=10, cell_index=0),
    TextOp("selling_agent_address", table_index=11, cell_index=0),
    TextOp("selling_agent_postcode", table_index=11, cell_index=2),
    TextOp("selling_agent_business_hours", table_index=12, cell_index=1),
    TextOp("selling_agent_after_hours", table_index=13, cell_index=1),
    TextOp("selling_agent_email", table_index=14, cell_index=1),
)

CHECKBOX_OPS = ()


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
        # Caller fields — verbatim, no computation/validation.
        "selling_agent_name": _s(fields.get("selling_agent_name")),
        "selling_agent_address": _s(fields.get("selling_agent_address")),
        "selling_agent_postcode": _s(fields.get("selling_agent_postcode")),
        "selling_agent_business_hours": _s(fields.get("selling_agent_business_hours")),
        "selling_agent_after_hours": _s(fields.get("selling_agent_after_hours")),
        "selling_agent_email": _s(fields.get("selling_agent_email")),
    }

    if len(renters) > 4:
        extra = ", ".join(_s(r.full_name) for r in renters[4:])
        ctx["renter4_name"] = (
            f"{ctx['renter4_name']} (plus additional renters on extra page: {extra})"
        )

    return ctx


SPEC = FormSpec(
    key="notice_of_intention_to_sell",
    template=TEMPLATE,
    declared_fields=DECLARED_FIELDS,
    text_ops=TEXT_OPS,
    checkbox_ops=CHECKBOX_OPS,
    build_context=build_context,
    title="Notice of intention to sell",
    group="notice_of_intention_to_sell",
    caller_field_labels={
        "selling_agent_name": "Selling agent full name (if sold through an agent)",
        "selling_agent_address": "Selling agent postal address",
        "selling_agent_postcode": "Selling agent postcode",
        "selling_agent_business_hours": "Selling agent business-hours phone",
        "selling_agent_after_hours": "Selling agent after-hours phone",
        "selling_agent_email": "Selling agent email",
    },
)
