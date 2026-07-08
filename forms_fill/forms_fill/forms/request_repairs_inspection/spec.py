"""CAV "Request for repairs inspection or rent assessment" form spec.

Source: https://www.consumer.vic.gov.au/library/forms/housing-and-accommodation/
renting/request-for-repairs-inspection.docx (downloaded 2026-07-08).

Table/cell indices below were derived by inspecting the template's structure
(python-docx): 8 tables total.

This form is lodged by the *renter* with Consumer Affairs Victoria, not
served by the PM — "Your details" (table 2) is the renter's own details, and
this spec fills what `TenancyBundle`'s `Renter` model captures (address,
postcode, business-hours phone, email). Renter's title, surname/given-name
split, and mobile number are not modelled by the contract (`Renter` has one
`full_name` string and no separate mobile field) and are left as caller
fields. "Details of rental provider/agent" (tables 4-5) fills the rental
provider from provider data; the agent block (GEA's own business details) is
caller-supplied, mirroring the rental-agreement specs.

Left blank by design: the "what is the inspection for" and "property type"
manual-X tick tables (1, 3 — plain text cells, not legacy form checkboxes,
so there is nothing to programmatically tick), the signature block (table 6),
and "Office use only" (table 7, reserved for CAV).
"""

from __future__ import annotations

from pathlib import Path

from ...formspec import FormSpec, TextOp
from ...models import TenancyBundle

TEMPLATE = Path(__file__).with_name("template.docx")

CALLER_FIELDS = (
    "renter_title",
    "renter_family_name",
    "renter_given_names",
    "renter_mobile",
    "agent_name",
    "agent_address",
    "agent_suburb",
    "agent_postcode",
    "agent_phone",
    "agent_mobile",
)

FETCHED_FIELDS = (
    "renter_street_address",
    "renter_postcode",
    "renter_phone",
    "renter_email",
    "provider_name",
    "provider_address",
    "provider_postcode",
    "provider_phone",
)

DECLARED_FIELDS = FETCHED_FIELDS + CALLER_FIELDS

TEXT_OPS = (
    # Your details (renter)
    TextOp("renter_title", table_index=2, cell_index=1, row_index=0),
    TextOp("renter_family_name", table_index=2, cell_index=1, row_index=1),
    TextOp("renter_given_names", table_index=2, cell_index=1, row_index=2),
    TextOp("renter_street_address", table_index=2, cell_index=1, row_index=3),
    TextOp("renter_postcode", table_index=2, cell_index=1, row_index=5),
    TextOp("renter_phone", table_index=2, cell_index=1, row_index=6),
    TextOp("renter_mobile", table_index=2, cell_index=1, row_index=7),
    TextOp("renter_email", table_index=2, cell_index=1, row_index=8),
    # Rental provider
    TextOp("provider_name", table_index=4, cell_index=1, row_index=0),
    TextOp("provider_address", table_index=4, cell_index=1, row_index=1),
    TextOp("provider_postcode", table_index=4, cell_index=1, row_index=3),
    TextOp("provider_phone", table_index=4, cell_index=1, row_index=4),
    # Estate agent (caller-supplied — GEA's own business details)
    TextOp("agent_name", table_index=5, cell_index=1, row_index=0),
    TextOp("agent_address", table_index=5, cell_index=1, row_index=1),
    TextOp("agent_suburb", table_index=5, cell_index=1, row_index=2),
    TextOp("agent_postcode", table_index=5, cell_index=1, row_index=3),
    TextOp("agent_phone", table_index=5, cell_index=1, row_index=4),
    TextOp("agent_mobile", table_index=5, cell_index=1, row_index=5),
)

CHECKBOX_OPS = ()


def _s(value: object) -> str:
    return "" if value is None else str(value)


def build_context(bundle: TenancyBundle, fields: dict) -> dict[str, str]:
    """Merge fetched bundle data with verbatim caller fields into a flat context."""

    renters = list(bundle.renters)
    renter = renters[0] if renters else None

    ctx: dict[str, str] = {
        "renter_street_address": _s(renter.address_for_service) if renter else "",
        "renter_postcode": _s(renter.service_postcode) if renter else "",
        "renter_phone": _s(renter.phone_business_hours) if renter else "",
        "renter_email": _s(renter.email) if renter else "",
        "provider_name": _s(bundle.rental_provider.full_name),
        "provider_address": _s(bundle.rental_provider.service_address),
        "provider_postcode": _s(bundle.rental_provider.service_postcode),
        "provider_phone": _s(bundle.rental_provider.phone_business_hours),
    }

    for name in CALLER_FIELDS:
        ctx[name] = _s(fields.get(name))

    return ctx


SPEC = FormSpec(
    key="request_repairs_inspection",
    template=TEMPLATE,
    declared_fields=DECLARED_FIELDS,
    text_ops=TEXT_OPS,
    checkbox_ops=CHECKBOX_OPS,
    build_context=build_context,
    title="Request for repairs inspection or rent assessment",
    group="request_repairs_inspection",
    caller_field_labels={
        "renter_title": "Renter title (Mr, Mrs, etc.)",
        "renter_family_name": "Renter family name (surname)",
        "renter_given_names": "Renter given names",
        "renter_mobile": "Renter mobile phone",
        "agent_name": "Agent/agency name",
        "agent_address": "Agent street address",
        "agent_suburb": "Agent suburb",
        "agent_postcode": "Agent postcode",
        "agent_phone": "Agent daytime phone",
        "agent_mobile": "Agent mobile phone",
    },
)
