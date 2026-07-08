"""CAV "Termination after death of a sole renter" form spec (RTA 1997 (Vic) s 91N).

Source: https://www.consumer.vic.gov.au/library/forms/housing-and-accommodation/
renting/notice-to-vacate-in-the-case-of-death-of-a-sole-renter.docx (downloaded
2026-07-08).

Table/cell indices below were derived by inspecting the template's structure
(python-docx): 17 tables total, indexed label/value cell layout, same style as
`notice_to_vacate`.

Unlike `notice_to_vacate`, section 5 "Reason for notice" is fixed boilerplate
text reciting the statutory death-of-sole-renter fact — there is no free-text
ground field to declare.

Left blank by design (mirrors R7 in the rent-increase spec): section 6
"Delivery of this notice" (tables 9-14, delivery-method checkboxes/tracking
number) and section 7 signature block (tables 15-16) — PM manual-service
steps, never automated.
"""

from __future__ import annotations

from pathlib import Path

from ...formspec import FormSpec, TextOp
from ...models import TenancyBundle

TEMPLATE = Path(__file__).with_name("template.docx")

# Caller-supplied, rendered verbatim (mirrors `termination_date` in the
# shipped notice-to-vacate spec).
CALLER_FIELDS = ("termination_date",)

# Fetched-from-provider text fields.
FETCHED_FIELDS = (
    "premises_address",
    "premises_postcode",
    "renter1_name",
    "provider_name",
    "provider_address",
    "provider_postcode",
    "provider_business_hours",
    "provider_after_hours",
    "provider_email",
)

DECLARED_FIELDS = FETCHED_FIELDS + CALLER_FIELDS

TEXT_OPS = (
    # Section 1 — premises
    TextOp("premises_address", table_index=1, cell_index=0),
    TextOp("premises_postcode", table_index=1, cell_index=2),
    # Section 2 — deceased renter
    TextOp("renter1_name", table_index=2, cell_index=1),
    # Section 3 — rental provider
    TextOp("provider_name", table_index=3, cell_index=0),
    TextOp("provider_address", table_index=4, cell_index=0),
    TextOp("provider_postcode", table_index=4, cell_index=2),
    TextOp("provider_business_hours", table_index=5, cell_index=1),
    TextOp("provider_after_hours", table_index=6, cell_index=1),
    TextOp("provider_email", table_index=7, cell_index=1),
    # Section 4 — termination date (engine/caller-supplied, verbatim)
    TextOp("termination_date", table_index=8, cell_index=1),
)

CHECKBOX_OPS = ()


def _s(value: object) -> str:
    return "" if value is None else str(value)


def build_context(bundle: TenancyBundle, fields: dict) -> dict[str, str]:
    """Merge fetched bundle data with verbatim caller fields into a flat context."""

    renters = list(bundle.renters)
    deceased_renter = renters[0] if renters else None

    ctx: dict[str, str] = {
        "premises_address": _s(bundle.premises.address_line),
        "premises_postcode": _s(bundle.premises.postcode),
        "renter1_name": _s(deceased_renter.full_name) if deceased_renter else "",
        "provider_name": _s(bundle.rental_provider.full_name),
        "provider_address": _s(bundle.rental_provider.service_address),
        "provider_postcode": _s(bundle.rental_provider.service_postcode),
        "provider_business_hours": _s(bundle.rental_provider.phone_business_hours),
        "provider_after_hours": _s(bundle.rental_provider.phone_after_hours),
        "provider_email": _s(bundle.rental_provider.email),
        # Caller field — verbatim, no computation/validation.
        "termination_date": _s(fields.get("termination_date")),
    }

    return ctx


SPEC = FormSpec(
    key="notice_to_vacate_death_sole_renter",
    template=TEMPLATE,
    declared_fields=DECLARED_FIELDS,
    text_ops=TEXT_OPS,
    checkbox_ops=CHECKBOX_OPS,
    build_context=build_context,
    title="Notice to vacate — death of a sole renter",
    group="notice_to_vacate_death_sole_renter",
    caller_field_labels={
        "termination_date": "Requested vacate-by date",
    },
)
