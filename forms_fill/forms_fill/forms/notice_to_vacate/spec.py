"""CAV "Notice to vacate to renter of rented premises" form spec
(RTA 1997 (Vic) ss 263-267, provider-ground notices).

Source: https://www.consumer.vic.gov.au/library/forms/housing-and-accommodation/
renting/notice-to-vacate-to-renter-of-rented-premises.docx (downloaded 2026-07-07,
current post-25-Nov-2025 amendment version — confirmed the ground list at
paragraph 22-27 matches the five prescribed provider grounds).

Table/cell indices below were derived by inspecting the template's structure
(python-docx): 28 tables total, every fillable field is a single-row label/value
table addressed by index, same layout style as `cav_rent_increase_notice`. Table 6
is the only real checkbox table in the fields this spec declares (2 checkboxes:
"the rental provider" / "the mortgagee") — GEA always serves as agent for the
rental provider, never the mortgagee, so that selector is a fixed constant, not a
caller/fetched field.

Left blank by design (mirrors R7 in the rent-increase spec): Part B section 6
"Delivery of this notice" (tables 15-19, all delivery-method checkboxes/tracking
number) and section 7 signature block — these are the PM's manual-service steps
(RTA s 266B ground/retaliation checks and proof of service), never automated.
"""

from __future__ import annotations

from pathlib import Path

from ...formspec import CheckboxOp, FormSpec, TextOp
from ...models import TenancyBundle

TEMPLATE = Path(__file__).with_name("template.docx")

# Caller-supplied, rendered verbatim (mirrors R4 in the rent-increase spec). The
# vacating engine computes these — this spec never computes or infers a date or
# a day count.
CALLER_FIELDS = (
    "minimum_notice_days",
    "termination_date",
    "reason_for_notice",
)

# Fetched-from-provider text fields (PropertyMe today; GEA CRM is a future
# additive adapter behind the same PropertyDataProvider interface).
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
    TextOp("provider_name", table_index=7, cell_index=0),
    TextOp("provider_address", table_index=8, cell_index=0),
    TextOp("provider_postcode", table_index=8, cell_index=2),
    TextOp("provider_business_hours", table_index=9, cell_index=1),
    TextOp("provider_after_hours", table_index=10, cell_index=1),
    TextOp("provider_email", table_index=11, cell_index=1),
    # Section 4 — termination date + minimum notice (engine-computed, verbatim)
    TextOp("minimum_notice_days", table_index=12, cell_index=1),
    TextOp("termination_date", table_index=13, cell_index=1),
    # Section 5 — reason for notice (free text; ground description supplied
    # verbatim by the caller, never authored by this spec)
    TextOp("reason_for_notice", table_index=14, cell_index=0),
)

# GEA is always the rental provider's agent, never a mortgagee — fixed, not a
# caller/fetched field.
_GIVING_CAPACITY = "rental_provider"
_GIVING_CAPACITY_OPTIONS = {"rental_provider": 0, "mortgagee": 1}

CHECKBOX_OPS = (CheckboxOp("giving_capacity", table_index=6, options=_GIVING_CAPACITY_OPTIONS),)


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
        "minimum_notice_days": _s(fields.get("minimum_notice_days")),
        "termination_date": _s(fields.get("termination_date")),
        "reason_for_notice": _s(fields.get("reason_for_notice")),
        # Selector (not a declared text field) — always the rental provider.
        "giving_capacity": _GIVING_CAPACITY,
    }

    # >4 renters -> overflow note appended to renter 4's slot (mirrors the
    # rent-increase spec's R5 handling).
    if len(renters) > 4:
        extra = ", ".join(_s(r.full_name) for r in renters[4:])
        ctx["renter4_name"] = (
            f"{ctx['renter4_name']} (plus additional renters on extra page: {extra})"
        )

    return ctx


SPEC = FormSpec(
    key="notice_to_vacate",
    template=TEMPLATE,
    declared_fields=DECLARED_FIELDS,
    text_ops=TEXT_OPS,
    checkbox_ops=CHECKBOX_OPS,
    build_context=build_context,
    selector_fields=("giving_capacity",),
)
