"""CAV "Consent to electronic service of notices and other documents" spec
(Electronic Transactions (Victoria) Act 2000).

Source: https://www.consumer.vic.gov.au/library/forms/housing-and-accommodation/
renting/consent-to-electronic-service-of-notices-and-other-documents.docx
(downloaded 2026-07-08).

Table/cell indices below were derived by inspecting the template's structure
(python-docx): 9 tables total.

This is a personal consent statement each party gives in their own words —
there is no premises/renter/provider identity block to prefill from
`TenancyBundle`; the only fillable fields are each party's nominated
electronic contact detail, which is what *they* are consenting to use, not a
fact this tool fetches. All fields are therefore caller-supplied.

Left blank by design: all four signature/date blocks (tables 2, 4, 6, 8) —
manual-execution steps, never automated.
"""

from __future__ import annotations

from pathlib import Path

from ...formspec import FormSpec, TextOp
from ...models import TenancyBundle

TEMPLATE = Path(__file__).with_name("template.docx")

CALLER_FIELDS = (
    "provider_contact",
    "renter1_contact",
    "renter2_contact",
    "renter3_contact",
)

FETCHED_FIELDS: tuple[str, ...] = ()

DECLARED_FIELDS = FETCHED_FIELDS + CALLER_FIELDS

TEXT_OPS = (
    TextOp("provider_contact", table_index=1, cell_index=0),
    TextOp("renter1_contact", table_index=3, cell_index=0),
    TextOp("renter2_contact", table_index=5, cell_index=0),
    TextOp("renter3_contact", table_index=7, cell_index=0),
)

CHECKBOX_OPS = ()


def _s(value: object) -> str:
    return "" if value is None else str(value)


def build_context(bundle: TenancyBundle, fields: dict) -> dict[str, str]:
    """Every field is caller-supplied — there is nothing to fetch for this form."""

    return {name: _s(fields.get(name)) for name in CALLER_FIELDS}


SPEC = FormSpec(
    key="consent_electronic_service",
    template=TEMPLATE,
    declared_fields=DECLARED_FIELDS,
    text_ops=TEXT_OPS,
    checkbox_ops=CHECKBOX_OPS,
    build_context=build_context,
    title="Consent to electronic service of notices and other documents",
    group="consent_electronic_service",
    caller_field_labels={
        "provider_contact": "Rental provider's nominated electronic contact",
        "renter1_contact": "Renter 1's nominated electronic contact",
        "renter2_contact": "Renter 2's nominated electronic contact",
        "renter3_contact": "Renter 3's nominated electronic contact",
    },
)
