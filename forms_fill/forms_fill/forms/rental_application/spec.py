"""CAV "Residential rental application" form spec (RTA 1997 (Vic) s 30AC).

Source: https://www.consumer.vic.gov.au/library/forms/housing-and-accommodation/
renting/residential-rental-application-31-march-2026.docx (downloaded 2026-07-08,
CAV-dated 31 March 2026 — record this template version if CAV re-dates it).

Table/cell indices below were derived by inspecting the template's structure
(python-docx): 17 tables total.

Per KTD2 (prefill, not completion): this form is substantially completed by
the *applicant*, not the PM. Only Part A's "Premises to which the application
applies" (table 2) and "Rental provider or agent's details" (table 3) are
PM-prefilled before the form is given to a prospective renter — exactly what
CAV's own instructions in the template ("Rental providers or their agents
must provide information outlined in Part A before giving this form to a
prospective renter") say. Every applicant-completed field (personal details,
employment, financial/identity document selection, rental history, referees,
tenancy databases, signature) is left blank-by-design and undeclared.

Australian state/territory of the rental provider's residence is a caller
field — not part of the `TenancyBundle` contract.
"""

from __future__ import annotations

from pathlib import Path

from ...formspec import FormSpec, TextOp
from ...models import TenancyBundle

TEMPLATE = Path(__file__).with_name("template.docx")

CALLER_FIELDS = (
    "provider_acn",
    "provider_state",
)

FETCHED_FIELDS = (
    "premises_address",
    "provider_name",
    "provider_address",
    "provider_phone",
    "provider_email",
)

DECLARED_FIELDS = FETCHED_FIELDS + CALLER_FIELDS

TEXT_OPS = (
    # Premises to which the application applies
    TextOp("premises_address", table_index=2, row_index=1, cell_index=1),
    # Rental provider or agent's details
    TextOp("provider_name", table_index=3, row_index=1, cell_index=1),
    TextOp("provider_acn", table_index=3, row_index=3, cell_index=1),
    TextOp("provider_address", table_index=3, row_index=5, cell_index=1),
    TextOp("provider_phone", table_index=3, row_index=7, cell_index=1),
    TextOp("provider_email", table_index=3, row_index=9, cell_index=1),
    TextOp("provider_state", table_index=3, row_index=11, cell_index=1),
)

CHECKBOX_OPS = ()


def _s(value: object) -> str:
    return "" if value is None else str(value)


def build_context(bundle: TenancyBundle, fields: dict) -> dict[str, str]:
    """Merge fetched bundle data with verbatim caller fields into a flat context."""

    premises = bundle.premises

    ctx: dict[str, str] = {
        "premises_address": _s(premises.address_line),
        "provider_name": _s(bundle.rental_provider.full_name),
        "provider_address": _s(bundle.rental_provider.service_address),
        "provider_phone": _s(bundle.rental_provider.phone_business_hours),
        "provider_email": _s(bundle.rental_provider.email),
        # Caller fields — verbatim, no computation/validation.
        "provider_acn": _s(fields.get("provider_acn")),
        "provider_state": _s(fields.get("provider_state")),
    }

    return ctx


SPEC = FormSpec(
    key="rental_application",
    template=TEMPLATE,
    declared_fields=DECLARED_FIELDS,
    text_ops=TEXT_OPS,
    checkbox_ops=CHECKBOX_OPS,
    build_context=build_context,
    title="Residential rental application",
    group="rental_application",
    caller_field_labels={
        "provider_acn": "Rental provider ACN/ABN (if applicable)",
        "provider_state": "Rental provider's Australian state/territory of residence",
    },
)
