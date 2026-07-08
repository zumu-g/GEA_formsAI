"""CAV "Notice requesting additional bond" form spec (RTA 1997 (Vic) s 34A).

Source: https://www.consumer.vic.gov.au/library/forms/housing-and-accommodation/
renting/notice-requesting-additional-bond.docx (downloaded 2026-07-08).

Table/cell indices below were derived by inspecting the template's structure
(python-docx): 16 tables total, indexed label/value cell layout.

Bond and rent amounts are caller-supplied — they are not part of the
`TenancyBundle` provider contract (bond/rent figures live in the PM's own
calculation, not fetched property data).

Left blank by design: section 8 signature (table 15) — PM manual-service step,
never automated.
"""

from __future__ import annotations

from pathlib import Path

from ...formspec import FormSpec, TextOp
from ...models import TenancyBundle

TEMPLATE = Path(__file__).with_name("template.docx")

# Caller-supplied, rendered verbatim.
CALLER_FIELDS = (
    "notice_date",
    "existing_bond_amount",
    "old_weekly_rent",
    "new_weekly_rent",
    "additional_bond_amount",
)

# Fetched-from-provider text fields.
FETCHED_FIELDS = (
    "premises_address",
    "premises_postcode",
    "renter1_name",
    "renter_service_address",
    "renter_service_postcode",
    "renter_business_hours",
    "renter_email",
    "provider_name",
    "provider_address",
    "provider_postcode",
    "provider_business_hours",
    "provider_email",
)

DECLARED_FIELDS = FETCHED_FIELDS + CALLER_FIELDS

TEXT_OPS = (
    # Section 1 — date of notice (caller)
    TextOp("notice_date", table_index=1, cell_index=0),
    # Section 2 — renter
    TextOp("renter1_name", table_index=2, cell_index=0),
    TextOp("renter_service_address", table_index=3, cell_index=0),
    TextOp("renter_service_postcode", table_index=3, cell_index=2),
    TextOp("renter_business_hours", table_index=4, cell_index=1),
    TextOp("renter_email", table_index=5, cell_index=1),
    # Section 3 — rental provider
    TextOp("provider_name", table_index=6, cell_index=0),
    TextOp("provider_address", table_index=7, cell_index=0),
    TextOp("provider_postcode", table_index=7, cell_index=2),
    TextOp("provider_business_hours", table_index=8, cell_index=1),
    TextOp("provider_email", table_index=9, cell_index=1),
    # Section 4 — premises
    TextOp("premises_address", table_index=10, cell_index=0),
    TextOp("premises_postcode", table_index=10, cell_index=2),
    # Section 5 — existing bond (caller)
    TextOp("existing_bond_amount", table_index=11, cell_index=0),
    TextOp("old_weekly_rent", table_index=12, cell_index=1),
    TextOp("new_weekly_rent", table_index=13, cell_index=1),
    # Section 6 — additional bond (caller)
    TextOp("additional_bond_amount", table_index=14, cell_index=0),
)

CHECKBOX_OPS = ()


def _s(value: object) -> str:
    return "" if value is None else str(value)


def _money(value: object) -> str:
    # Each of these template cells already contains a static "$" as its only
    # run; _set_cell_text overwrites that run rather than appending, so the
    # sign must be reapplied here or it's silently destroyed on fill.
    s = _s(value)
    return f"${s}" if s else ""


def build_context(bundle: TenancyBundle, fields: dict) -> dict[str, str]:
    """Merge fetched bundle data with verbatim caller fields into a flat context."""

    renters = list(bundle.renters)
    renter = renters[0] if renters else None

    ctx: dict[str, str] = {
        "premises_address": _s(bundle.premises.address_line),
        "premises_postcode": _s(bundle.premises.postcode),
        "renter1_name": _s(renter.full_name) if renter else "",
        "renter_service_address": _s(renter.address_for_service) if renter else "",
        "renter_service_postcode": _s(renter.service_postcode) if renter else "",
        "renter_business_hours": _s(renter.phone_business_hours) if renter else "",
        "renter_email": _s(renter.email) if renter else "",
        "provider_name": _s(bundle.rental_provider.full_name),
        "provider_address": _s(bundle.rental_provider.service_address),
        "provider_postcode": _s(bundle.rental_provider.service_postcode),
        "provider_business_hours": _s(bundle.rental_provider.phone_business_hours),
        "provider_email": _s(bundle.rental_provider.email),
        # Caller fields — verbatim, no computation/validation.
        "notice_date": _s(fields.get("notice_date")),
        "existing_bond_amount": _money(fields.get("existing_bond_amount")),
        "old_weekly_rent": _money(fields.get("old_weekly_rent")),
        "new_weekly_rent": _money(fields.get("new_weekly_rent")),
        "additional_bond_amount": _money(fields.get("additional_bond_amount")),
    }

    return ctx


SPEC = FormSpec(
    key="notice_requesting_additional_bond",
    template=TEMPLATE,
    declared_fields=DECLARED_FIELDS,
    text_ops=TEXT_OPS,
    checkbox_ops=CHECKBOX_OPS,
    build_context=build_context,
    title="Notice requesting additional bond",
    group="notice_requesting_additional_bond",
    caller_field_labels={
        "notice_date": "Date of notice",
        "existing_bond_amount": "Existing bond amount ($)",
        "old_weekly_rent": "Weekly rent the existing bond was calculated on ($)",
        "new_weekly_rent": "New weekly rent ($)",
        "additional_bond_amount": "Additional bond amount requested ($)",
    },
)
