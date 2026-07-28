"""CAV "Form 2 - Residential rental agreement for a fixed term of more than
five years" spec (RTA 1997 (Vic) s 26).

Source: https://www.consumer.vic.gov.au/library/forms/housing-and-accommodation/
renting/form-2-residential-rental-agreement-for-a-fixed-term-of-more-than-five-years.docx
(downloaded 2026-07-08).

Table/cell indices below were derived by inspecting the template's structure
(python-docx): 90 tables total. Sections 1-4 (agreement date, premises,
rental provider/agent, renters) are identical to `residential_rental_agreement`
(Form 1). Form 2 is fixed-term only — it has no "periodic agreement" option,
so there is no `term_type` selector here and the table indices from the rent
section onward are shifted by -1 relative to Form 1.

Same blank-by-design scope as Form 1 (KTD3): payment-method ticks, electronic-
service consent ticks, owners corporation, condition report ticks, Part E
additional terms, and all signature blocks are left for the PM to complete on
the printed form. This form also adds a fixed 5-year-plus rent-review clause
(annual CPI-linked review) which is boilerplate with no fillable field in the
sections this spec declares.
"""

from __future__ import annotations

from pathlib import Path

from ...formspec import CheckboxOp, FormSpec, TextOp
from ...models import TenancyBundle
from .._rental_agreement_shared import (
    LEASE_FIELDS_COMMON,
    apply_agent_autofill,
    apply_lease_autofill,
    lease_fields_for_mode,
)

TEMPLATE = Path(__file__).with_name("template.docx")

# Form 2 is fixed-term only — no term_type/periodic_start_date (see module
# docstring). Shared lease fields cover everything this form needs.
LEASE_FIELDS = LEASE_FIELDS_COMMON

# "handling_agent" and "is_renewal" are selectors only (U5/U6) — excluded
# from text_ops/printed output; see _rental_agreement_shared.
CALLER_FIELDS = (
    "agreement_date",
    "provider_company_name",
    "provider_acn",
    "handling_agent",
    "is_renewal",
    "agent_name",
    "agent_address",
    "agent_postcode",
    "agent_phone",
    "agent_acn",
    "agent_email",
    "renter1_current_address",
    "renter1_current_postcode",
    "renter2_current_address",
    "renter2_current_postcode",
    "renter3_current_address",
    "renter3_current_postcode",
    "renter4_current_address",
    "renter4_current_postcode",
    "fixed_start_date",
    "fixed_end_date",
    "rent_amount",
    "rent_period",
    "rent_payment_day",
    "first_rent_due_date",
    "bond_amount",
    "bond_due_date",
    "emergency_contact_name",
    "emergency_phone",
    "emergency_email",
)

FETCHED_FIELDS = (
    "premises_address",
    "premises_postcode",
    "provider_name",
    "provider_address",
    "provider_postcode",
    "provider_phone",
    "provider_email",
    "renter1_name",
    "renter1_phone",
    "renter1_email",
    "renter2_name",
    "renter2_phone",
    "renter2_email",
    "renter3_name",
    "renter3_phone",
    "renter3_email",
    "renter4_name",
    "renter4_phone",
    "renter4_email",
)

DECLARED_FIELDS = FETCHED_FIELDS + CALLER_FIELDS

TEXT_OPS = (
    TextOp("agreement_date", table_index=1, cell_index=0),
    TextOp("premises_address", table_index=2, cell_index=0),
    TextOp("premises_postcode", table_index=2, cell_index=2),
    TextOp("provider_name", table_index=3, row_index=0, cell_index=1),
    TextOp("provider_company_name", table_index=3, row_index=1, cell_index=1),
    TextOp("provider_acn", table_index=4, cell_index=0),
    TextOp("provider_address", table_index=5, cell_index=1),
    TextOp("provider_postcode", table_index=5, cell_index=3),
    TextOp("provider_phone", table_index=6, cell_index=1),
    TextOp("provider_email", table_index=7, cell_index=1),
    TextOp("agent_name", table_index=8, cell_index=1),
    TextOp("agent_address", table_index=9, cell_index=1),
    TextOp("agent_postcode", table_index=9, cell_index=3),
    TextOp("agent_phone", table_index=10, cell_index=1),
    TextOp("agent_acn", table_index=11, cell_index=1),
    TextOp("agent_email", table_index=12, cell_index=1),
    TextOp("renter1_name", table_index=13, cell_index=1),
    TextOp("renter1_current_address", table_index=14, cell_index=1),
    TextOp("renter1_current_postcode", table_index=14, cell_index=3),
    TextOp("renter1_phone", table_index=15, cell_index=1),
    TextOp("renter1_email", table_index=16, cell_index=1),
    TextOp("renter2_name", table_index=17, cell_index=1),
    TextOp("renter2_current_address", table_index=18, cell_index=1),
    TextOp("renter2_current_postcode", table_index=18, cell_index=3),
    TextOp("renter2_phone", table_index=19, cell_index=1),
    TextOp("renter2_email", table_index=20, cell_index=1),
    TextOp("renter3_name", table_index=21, cell_index=1),
    TextOp("renter3_current_address", table_index=22, cell_index=1),
    TextOp("renter3_current_postcode", table_index=22, cell_index=3),
    TextOp("renter3_phone", table_index=23, cell_index=1),
    TextOp("renter3_email", table_index=24, cell_index=1),
    TextOp("renter4_name", table_index=25, cell_index=1),
    TextOp("renter4_current_address", table_index=26, cell_index=1),
    TextOp("renter4_current_postcode", table_index=26, cell_index=3),
    TextOp("renter4_phone", table_index=27, cell_index=1),
    TextOp("renter4_email", table_index=28, cell_index=1),
    # Section 5 — fixed term only, no periodic option in this template
    TextOp("fixed_start_date", table_index=29, cell_index=2),
    TextOp("fixed_end_date", table_index=30, cell_index=2),
    # Section 6 — rent (index shifted -1 vs Form 1: no periodic table here)
    TextOp("rent_amount", table_index=31, row_index=0, cell_index=1),
    TextOp("rent_payment_day", table_index=32, cell_index=0),
    TextOp("first_rent_due_date", table_index=33, cell_index=1),
    # Section 7 — bond
    TextOp("bond_amount", table_index=34, cell_index=1),
    TextOp("bond_due_date", table_index=35, cell_index=1),
    # Section 10 — urgent repairs emergency contact
    TextOp("emergency_contact_name", table_index=44, cell_index=1),
    TextOp("emergency_phone", table_index=45, cell_index=1),
    TextOp("emergency_email", table_index=46, cell_index=1),
)

_RENT_PERIODS = {"week": 0, "fortnight": 1, "calendar month": 2}

CHECKBOX_OPS = (CheckboxOp("rent_period", table_index=31, options=_RENT_PERIODS),)


def _s(value: object) -> str:
    return "" if value is None else str(value)


def normalise_period(value: str) -> str:
    return str(value or "").strip().lower()


def build_context(bundle: TenancyBundle, fields: dict) -> dict[str, str]:
    """Merge fetched bundle data with verbatim caller fields into a flat context."""

    renters = list(bundle.renters)

    def renter(i: int):
        return renters[i] if i < len(renters) else None

    ctx: dict[str, str] = {
        "premises_address": _s(bundle.premises.address_line),
        "premises_postcode": _s(bundle.premises.postcode),
        "provider_name": _s(bundle.rental_provider.full_name),
        "provider_address": _s(bundle.rental_provider.service_address),
        "provider_postcode": _s(bundle.rental_provider.service_postcode),
        "provider_phone": _s(bundle.rental_provider.phone_business_hours),
        "provider_email": _s(bundle.rental_provider.email),
    }

    for i in range(4):
        r = renter(i)
        prefix = f"renter{i + 1}"
        ctx[f"{prefix}_name"] = _s(r.full_name) if r else ""
        ctx[f"{prefix}_phone"] = _s(r.phone_business_hours) if r else ""
        ctx[f"{prefix}_email"] = _s(r.email) if r else ""

    if len(renters) > 4:
        extra = ", ".join(_s(r.full_name) for r in renters[4:])
        ctx["renter4_name"] = (
            f"{ctx['renter4_name']} (plus additional renters on extra page: {extra})"
        )

    for name in CALLER_FIELDS:
        ctx[name] = _s(fields.get(name))

    apply_agent_autofill(ctx, fields)
    apply_lease_autofill(
        ctx, fields, bundle, lease_fields=lease_fields_for_mode(LEASE_FIELDS, fields)
    )

    ctx["rent_period"] = normalise_period(ctx.get("rent_period", ""))

    return ctx


SPEC = FormSpec(
    key="residential_rental_agreement_5yr",
    template=TEMPLATE,
    declared_fields=DECLARED_FIELDS,
    text_ops=TEXT_OPS,
    checkbox_ops=CHECKBOX_OPS,
    build_context=build_context,
    selector_fields=("rent_period", "is_renewal"),
    title="Residential rental agreement, fixed term over 5 years (Form 2)",
    group="residential_rental_agreement_5yr",
    caller_field_labels={
        "is_renewal": "This is a lease renewal (carry across the current lease's rent, bond and term type)",
        "agreement_date": "Date of agreement",
        "provider_company_name": "Rental provider company name (if applicable)",
        "provider_acn": "Rental provider ACN (if applicable)",
        "handling_agent": "Handling agent (choose from GEA Berwick)",
        "agent_name": "Agent full name",
        "agent_address": "Agent address",
        "agent_postcode": "Agent postcode",
        "agent_phone": "Agent phone number",
        "agent_acn": "Agent ACN (if applicable)",
        "agent_email": "Agent email",
        "renter1_current_address": "Renter 1 current address (before this tenancy)",
        "renter1_current_postcode": "Renter 1 current postcode",
        "renter2_current_address": "Renter 2 current address",
        "renter2_current_postcode": "Renter 2 current postcode",
        "renter3_current_address": "Renter 3 current address",
        "renter3_current_postcode": "Renter 3 current postcode",
        "renter4_current_address": "Renter 4 current address",
        "renter4_current_postcode": "Renter 4 current postcode",
        "fixed_start_date": "Fixed-term start date",
        "fixed_end_date": "Fixed-term end date",
        "rent_amount": "Rent amount ($)",
        "rent_period": "Rent period (week/fortnight/calendar month)",
        "rent_payment_day": "Day rent is paid",
        "first_rent_due_date": "Date first rent payment due",
        "bond_amount": "Bond amount ($)",
        "bond_due_date": "Date bond payment due",
        "emergency_contact_name": "Urgent-repairs emergency contact name",
        "emergency_phone": "Urgent-repairs emergency phone",
        "emergency_email": "Urgent-repairs emergency email",
    },
    # U7: same field-kind/section scheme as Form 1, minus term_type/
    # periodic_start_date (Form 2 is fixed-term only).
    caller_field_kinds={
        "is_renewal": "checkbox",
        "handling_agent": "select",
        "agreement_date": "date",
        "fixed_start_date": "date",
        "fixed_end_date": "date",
        "first_rent_due_date": "date",
        "bond_due_date": "date",
    },
    caller_field_sections={
        "is_renewal": "Renewal",
        "agreement_date": "1. Date of agreement",
        "provider_company_name": "3. Rental provider & agent",
        "provider_acn": "3. Rental provider & agent",
        "handling_agent": "3. Rental provider & agent",
        "agent_name": "3. Rental provider & agent",
        "agent_address": "3. Rental provider & agent",
        "agent_postcode": "3. Rental provider & agent",
        "agent_phone": "3. Rental provider & agent",
        "agent_acn": "3. Rental provider & agent",
        "agent_email": "3. Rental provider & agent",
        "renter1_current_address": "4. Renters — current address",
        "renter1_current_postcode": "4. Renters — current address",
        "renter2_current_address": "4. Renters — current address",
        "renter2_current_postcode": "4. Renters — current address",
        "renter3_current_address": "4. Renters — current address",
        "renter3_current_postcode": "4. Renters — current address",
        "renter4_current_address": "4. Renters — current address",
        "renter4_current_postcode": "4. Renters — current address",
        "fixed_start_date": "5. Length of agreement",
        "fixed_end_date": "5. Length of agreement",
        "rent_amount": "6. Rent",
        "rent_period": "6. Rent",
        "rent_payment_day": "6. Rent",
        "first_rent_due_date": "6. Rent",
        "bond_amount": "7. Bond",
        "bond_due_date": "7. Bond",
        "emergency_contact_name": "10. Urgent repairs contact",
        "emergency_phone": "10. Urgent repairs contact",
        "emergency_email": "10. Urgent repairs contact",
    },
)
