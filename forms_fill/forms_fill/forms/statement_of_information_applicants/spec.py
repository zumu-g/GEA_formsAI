"""CAV "Statement of Information for Rental Applicants" form spec.

Source: https://www.consumer.vic.gov.au/library/forms/housing-and-accommodation/
renting/statement-of-information-for-rental-applicants.docx (downloaded
2026-07-08).

Inspected with python-docx: this document is entirely static statutory
disclosure text about unlawful discrimination in the rental application
process — there is no fillable table cell anywhere in the template (the one
table is the title block). It must be attached to a rental application
unchanged; there is nothing for forms-fill to fill.

Registered with zero declared fields so it appears in the catalogue and can
be produced via the normal fill pipeline (which simply copies the template
through unmodified) — this keeps it discoverable alongside every other form
in the registry without inventing a separate "static document" code path.
"""

from __future__ import annotations

from pathlib import Path

from ...formspec import FormSpec
from ...models import TenancyBundle

TEMPLATE = Path(__file__).with_name("template.docx")

DECLARED_FIELDS: tuple[str, ...] = ()
TEXT_OPS: tuple = ()
CHECKBOX_OPS: tuple = ()


def build_context(bundle: TenancyBundle, fields: dict) -> dict[str, str]:
    return {}


SPEC = FormSpec(
    key="statement_of_information_applicants",
    template=TEMPLATE,
    declared_fields=DECLARED_FIELDS,
    text_ops=TEXT_OPS,
    checkbox_ops=CHECKBOX_OPS,
    build_context=build_context,
    title="Statement of information for rental applicants",
    group="statement_of_information_applicants",
    caller_field_labels={},
)
