"""CAV "Notice of goods left behind" form spec (RTA 1997 (Vic) s 435).

Source: https://www.consumer.vic.gov.au/library/forms/housing-and-accommodation/
renting/notice-of-goods-left-behind.docx (downloaded 2026-07-08).

Table/cell indices below were derived by inspecting the template's structure
(python-docx): 21 tables total, indexed label/value cell layout.

This notice is given by the owner of the premises to a *former* renter after
they have vacated — the single "renter" here maps to `bundle.renters[0]`
(overflow to more than one former renter is out of scope; this notice is
issued per former occupant).

Left blank by design: section 8 "Delivery of this notice" (tables 15-19,
delivery-method checkboxes/tracking number) and section 10 signature (table
20) — PM manual-service steps, never automated.
"""

from __future__ import annotations

from pathlib import Path

from ...formspec import FormSpec, TextOp
from ...models import TenancyBundle

TEMPLATE = Path(__file__).with_name("template.docx")

# Caller-supplied, rendered verbatim — the tool doesn't infer vacate dates,
# goods descriptions, or disposal deadlines.
CALLER_FIELDS = (
    "notice_date",
    "date_vacated",
    "goods_description",
    "dispose_by_date",
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
    # Section 2 — former renter
    TextOp("renter1_name", table_index=2, cell_index=0),
    TextOp("renter_service_address", table_index=3, cell_index=0),
    TextOp("renter_service_postcode", table_index=3, cell_index=2),
    TextOp("renter_business_hours", table_index=4, cell_index=1),
    TextOp("renter_email", table_index=5, cell_index=1),
    # Section 3 — owner of the premises
    TextOp("provider_name", table_index=6, cell_index=0),
    TextOp("provider_address", table_index=7, cell_index=0),
    TextOp("provider_postcode", table_index=7, cell_index=2),
    TextOp("provider_business_hours", table_index=8, cell_index=1),
    TextOp("provider_email", table_index=9, cell_index=1),
    # Section 4 — former rented premises
    TextOp("premises_address", table_index=10, cell_index=0),
    TextOp("premises_postcode", table_index=10, cell_index=2),
    # Section 5 — goods left behind (caller)
    TextOp("date_vacated", table_index=11, cell_index=1),
    TextOp("goods_description", table_index=12, cell_index=0),
    # Section 7 — sale of goods (caller)
    TextOp("dispose_by_date", table_index=13, cell_index=1),
)

CHECKBOX_OPS = ()


def _s(value: object) -> str:
    return "" if value is None else str(value)


def build_context(bundle: TenancyBundle, fields: dict) -> dict[str, str]:
    """Merge fetched bundle data with verbatim caller fields into a flat context."""

    renters = list(bundle.renters)
    former_renter = renters[0] if renters else None

    ctx: dict[str, str] = {
        "premises_address": _s(bundle.premises.address_line),
        "premises_postcode": _s(bundle.premises.postcode),
        "renter1_name": _s(former_renter.full_name) if former_renter else "",
        "renter_service_address": (
            _s(former_renter.address_for_service) if former_renter else ""
        ),
        "renter_service_postcode": (
            _s(former_renter.service_postcode) if former_renter else ""
        ),
        "renter_business_hours": (
            _s(former_renter.phone_business_hours) if former_renter else ""
        ),
        "renter_email": _s(former_renter.email) if former_renter else "",
        "provider_name": _s(bundle.rental_provider.full_name),
        "provider_address": _s(bundle.rental_provider.service_address),
        "provider_postcode": _s(bundle.rental_provider.service_postcode),
        "provider_business_hours": _s(bundle.rental_provider.phone_business_hours),
        "provider_email": _s(bundle.rental_provider.email),
        # Caller fields — verbatim, no computation/validation.
        "notice_date": _s(fields.get("notice_date")),
        "date_vacated": _s(fields.get("date_vacated")),
        "goods_description": _s(fields.get("goods_description")),
        "dispose_by_date": _s(fields.get("dispose_by_date")),
    }

    return ctx


SPEC = FormSpec(
    key="notice_of_goods_left_behind",
    template=TEMPLATE,
    declared_fields=DECLARED_FIELDS,
    text_ops=TEXT_OPS,
    checkbox_ops=CHECKBOX_OPS,
    build_context=build_context,
    title="Notice of goods left behind",
    group="notice_of_goods_left_behind",
    caller_field_labels={
        "notice_date": "Date of notice",
        "date_vacated": "Date the former renter vacated",
        "goods_description": "Description of goods left behind",
        "dispose_by_date": "Date goods will be sold/disposed of if uncollected",
    },
)
