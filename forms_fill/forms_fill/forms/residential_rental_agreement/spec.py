"""CAV "Form 1 - Residential rental agreement" spec (RTA 1997 (Vic) s 26).

Source: https://www.consumer.vic.gov.au/library/forms/housing-and-accommodation/
renting/form-1-residential-rental-agreement.docx (downloaded 2026-07-08).

Table/cell indices below were derived by inspecting the template's structure
(python-docx): 61 tables total, indexed label/value cell layout.

This is the largest template in the registry (KTD3). This spec fills the
fixed identity/premises/term/rent/bond/emergency-contact tables (Parts A-B's
factual sections 1-7 and 10) and declares everything else blank-by-design:

- The rental provider's agent details (section 3) and both renters' current
  addresses (section 4) are caller-supplied — they are not part of the
  `TenancyBundle` provider contract (the agent block is GEA's own fixed
  business details; "current address" is the renter's pre-tenancy address,
  a fact this tool has no source for).
- Section 8 payment-method ticks (table 37) and section 9 electronic-service
  consent ticks (tables 38-42) are multi-select PM/renter negotiated choices,
  left for the PM to complete on the printed form.
- Section 12 owners corporation (table 46), section 13 condition report
  (table 47), Part E additional terms (table 48), and all signature blocks
  (tables 49-60) are blank-by-design, same rule as every shipped notice spec.
- Parts C and D (safety-activity clauses, rights and obligations) are fixed
  statutory boilerplate with no fillable fields.

Term type and rent period are ticked via `CheckboxOp`, mirroring the
shipped `cav_rent_increase_notice` pattern.
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

# Term type + periodic start are Form 1-only lease fields (Form 2 is
# fixed-term-only — see residential_rental_agreement_5yr's module docstring).
LEASE_FIELDS = LEASE_FIELDS_COMMON + ("term_type", "periodic_start_date")

# Caller-supplied, rendered verbatim — not part of the TenancyBundle contract.
# "handling_agent" and "is_renewal" are selectors only (U5/U6) — see
# _rental_agreement_shared; both are excluded from text_ops/printed output.
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
    "term_type",
    "fixed_start_date",
    "fixed_end_date",
    "periodic_start_date",
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

# Fetched-from-provider text fields.
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
    # Section 1 — date of agreement (caller)
    TextOp("agreement_date", table_index=1, cell_index=0),
    # Section 2 — premises (fetched)
    TextOp("premises_address", table_index=2, cell_index=0),
    TextOp("premises_postcode", table_index=2, cell_index=2),
    # Section 3 — rental provider (fetched) + agent (caller)
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
    # Section 4 — renters (fetched name/phone/email; caller current address)
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
    # Section 5 — length of agreement (caller)
    TextOp("fixed_start_date", table_index=29, cell_index=2),
    TextOp("fixed_end_date", table_index=30, cell_index=2),
    TextOp("periodic_start_date", table_index=31, cell_index=2),
    # Section 6 — rent (caller)
    TextOp("rent_amount", table_index=32, row_index=0, cell_index=1),
    TextOp("rent_payment_day", table_index=33, cell_index=0),
    TextOp("first_rent_due_date", table_index=34, cell_index=1),
    # Section 7 — bond (caller)
    TextOp("bond_amount", table_index=35, cell_index=1),
    TextOp("bond_due_date", table_index=36, cell_index=1),
    # Section 10 — urgent repairs emergency contact (caller)
    TextOp("emergency_contact_name", table_index=43, cell_index=1),
    TextOp("emergency_phone", table_index=44, cell_index=1),
    TextOp("emergency_email", table_index=45, cell_index=1),
)

_TERM_TYPES = {"fixed": 0}
_PERIODIC = {"periodic": 0}
_RENT_PERIODS = {"week": 0, "fortnight": 1, "calendar month": 2}

CHECKBOX_OPS = (
    CheckboxOp("term_type", table_index=29, options=_TERM_TYPES),
    CheckboxOp("term_type", table_index=31, options=_PERIODIC),
    CheckboxOp("rent_period", table_index=32, options=_RENT_PERIODS),
)


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

    # Renters: on a renewal the fetched tenancy's renters ARE the signatories,
    # so the bundle seeds them. On a new lease the fetched renters are the
    # OUTGOING tenants — never seed those; the caller supplies the new
    # tenants (typed, or client-side from a GEA CRM fetch). A caller-supplied
    # value always wins either way (R7).
    renewal = str(fields.get("is_renewal", "")).strip().lower() in ("true", "1", "yes", "on")
    for i in range(4):
        r = renter(i) if renewal else None
        prefix = f"renter{i + 1}"
        ctx[f"{prefix}_name"] = _s(fields.get(f"{prefix}_name")) or (_s(r.full_name) if r else "")
        ctx[f"{prefix}_phone"] = _s(fields.get(f"{prefix}_phone")) or (_s(r.phone_business_hours) if r else "")
        ctx[f"{prefix}_email"] = _s(fields.get(f"{prefix}_email")) or (_s(r.email) if r else "")

    if renewal and len(renters) > 4:
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
    key="residential_rental_agreement",
    template=TEMPLATE,
    declared_fields=DECLARED_FIELDS,
    text_ops=TEXT_OPS,
    checkbox_ops=CHECKBOX_OPS,
    build_context=build_context,
    selector_fields=("term_type", "rent_period", "is_renewal"),
    title="Residential rental agreement (Form 1)",
    group="residential_rental_agreement",
    caller_field_labels={
        # is_renewal first (U6/U7) — the PM's first decision, shown before
        # any other section, since it changes what several later fields mean.
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
        # New-lease tenants (U9): typed or seeded client-side from a GEA CRM
        # fetch. On a renewal these stay blank and the fetched tenancy's
        # renters fill the form instead (build_context's renewal gate).
        "renter1_name": "Renter 1 full name",
        "renter1_phone": "Renter 1 phone",
        "renter1_email": "Renter 1 email",
        "renter2_name": "Renter 2 full name",
        "renter2_phone": "Renter 2 phone",
        "renter2_email": "Renter 2 email",
        "renter3_name": "Renter 3 full name",
        "renter3_phone": "Renter 3 phone",
        "renter3_email": "Renter 3 email",
        "renter4_name": "Renter 4 full name",
        "renter4_phone": "Renter 4 phone",
        "renter4_email": "Renter 4 email",
        "renter1_current_address": "Renter 1 current address (before this tenancy)",
        "renter1_current_postcode": "Renter 1 current postcode",
        "renter2_current_address": "Renter 2 current address",
        "renter2_current_postcode": "Renter 2 current postcode",
        "renter3_current_address": "Renter 3 current address",
        "renter3_current_postcode": "Renter 3 current postcode",
        "renter4_current_address": "Renter 4 current address",
        "renter4_current_postcode": "Renter 4 current postcode",
        "term_type": "Term type (fixed/periodic)",
        "fixed_start_date": "Fixed-term start date",
        "fixed_end_date": "Fixed-term end date",
        "periodic_start_date": "Periodic agreement start date",
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
    # U7: field kind/section metadata — matches the printed form's own
    # numbering (module docstring), so the review UI groups fields the way a
    # PM already reads the paper form.
    caller_field_kinds={
        # U4 (lease-flow speed-up): the section-2 radio is the one visible
        # lease-type control; this field stays in the API contract but renders
        # as a hidden carrier.
        "is_renewal": "hidden",
        "handling_agent": "select",  # options come live from /agency, not here
        "agreement_date": "date",
        "fixed_start_date": "date",
        "fixed_end_date": "date",
        "periodic_start_date": "date",
        "first_rent_due_date": "date",
        "bond_due_date": "date",
    },
    guided=True,
    # U4 (R7): one-line help with a real Victorian-context example for the
    # always-manual fields — published via the catalogue, never hardcoded in
    # the client (KTD7).
    caller_field_help={
        "agreement_date": "The day the agreement is signed — usually today, e.g. 27/08/2026.",
        "renter1_current_address": "Where the renter lives now, before this tenancy — e.g. 12 High St, Berwick.",
        "renter1_current_postcode": "4-digit Victorian postcode, e.g. 3806.",
        "renter2_current_address": "Where renter 2 lives now — leave blank if there is no second renter.",
        "renter2_current_postcode": "4-digit postcode, e.g. 3806.",
        "renter3_current_address": "Where renter 3 lives now — leave blank if not needed.",
        "renter3_current_postcode": "4-digit postcode, e.g. 3806.",
        "renter4_current_address": "Where renter 4 lives now — leave blank if not needed.",
        "renter4_current_postcode": "4-digit postcode, e.g. 3806.",
        "term_type": "Fixed term (set start and end dates) or periodic (month to month).",
        "fixed_start_date": "First day of the fixed term, e.g. 08/09/2026.",
        "fixed_end_date": "Last day of the fixed term — must be after the start date, e.g. 07/09/2027.",
        "periodic_start_date": "Only for a periodic agreement — leave blank for a fixed term.",
        "rent_amount": "Dollar amount per rent period, numbers only, e.g. 520.",
        "rent_period": "How often rent is payable: week, fortnight or calendar month.",
        "rent_payment_day": "Day rent is due each period, e.g. Monday, or 1st of the month.",
        "first_rent_due_date": "When the first payment is due — usually the start date, e.g. 08/09/2026.",
        "bond_amount": "Usually one calendar month's rent, e.g. 2260 — lodged with the RTBA.",
        "bond_due_date": "When the bond must be paid — on or before the start date, e.g. 08/09/2026.",
        "emergency_contact_name": "Nominee for urgent repairs (RTA s 72) — e.g. the managing agent or after-hours tradesperson.",
        "emergency_phone": "After-hours number for urgent repairs, e.g. 03 9707 5300.",
        "emergency_email": "Email for the urgent-repairs contact — leave blank if phone-only.",
        "provider_acn": "9-digit ACN, e.g. 123 456 789 — leave blank for an individual provider.",
        "agent_acn": "The agency's 9-digit ACN, e.g. 123 456 789 — leave blank if none.",
        "provider_company_name": "Only if the rental provider is a company — otherwise leave blank.",
    },
    # U4 (R10): review-screen blank classification. blocking = the printed
    # agreement is incomplete without it (date, term, rent, bond, first
    # renter); informational = commonly blank on real agreements. Unlisted
    # fields default to informational in the UI.
    caller_field_required={
        "agreement_date": "blocking",
        "term_type": "blocking",
        "fixed_start_date": "blocking",
        "fixed_end_date": "blocking",
        "rent_amount": "blocking",
        "rent_period": "blocking",
        "rent_payment_day": "blocking",
        "first_rent_due_date": "blocking",
        "bond_amount": "blocking",
        "bond_due_date": "blocking",
        "renter1_current_address": "blocking",
        "renter1_current_postcode": "blocking",
        "agent_name": "blocking",
        "agent_address": "blocking",
        "agent_postcode": "blocking",
        "agent_phone": "blocking",
        "agent_email": "blocking",
        "periodic_start_date": "informational",
        "provider_company_name": "informational",
        "provider_acn": "informational",
        "agent_acn": "informational",
        "renter2_current_address": "informational",
        "renter2_current_postcode": "informational",
        "renter3_current_address": "informational",
        "renter3_current_postcode": "informational",
        "renter4_current_address": "informational",
        "renter4_current_postcode": "informational",
        "emergency_contact_name": "informational",
        "emergency_phone": "informational",
        "emergency_email": "informational",
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
        "renter1_name": "4. Renters — details (new lease)",
        "renter1_phone": "4. Renters — details (new lease)",
        "renter1_email": "4. Renters — details (new lease)",
        "renter2_name": "4. Renters — details (new lease)",
        "renter2_phone": "4. Renters — details (new lease)",
        "renter2_email": "4. Renters — details (new lease)",
        "renter3_name": "4. Renters — details (new lease)",
        "renter3_phone": "4. Renters — details (new lease)",
        "renter3_email": "4. Renters — details (new lease)",
        "renter4_name": "4. Renters — details (new lease)",
        "renter4_phone": "4. Renters — details (new lease)",
        "renter4_email": "4. Renters — details (new lease)",
        "renter1_current_address": "4. Renters — current address",
        "renter1_current_postcode": "4. Renters — current address",
        "renter2_current_address": "4. Renters — current address",
        "renter2_current_postcode": "4. Renters — current address",
        "renter3_current_address": "4. Renters — current address",
        "renter3_current_postcode": "4. Renters — current address",
        "renter4_current_address": "4. Renters — current address",
        "renter4_current_postcode": "4. Renters — current address",
        "term_type": "5. Length of agreement",
        "fixed_start_date": "5. Length of agreement",
        "fixed_end_date": "5. Length of agreement",
        "periodic_start_date": "5. Length of agreement",
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
