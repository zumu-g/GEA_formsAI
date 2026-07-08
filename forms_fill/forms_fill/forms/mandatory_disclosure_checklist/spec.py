"""CAV "Mandatory Disclosures" checklist form spec (RTA 1997 (Vic) s 30A).

Source: https://www.consumer.vic.gov.au/library/forms/housing-and-accommodation/
renting/mandatory-disclosure-checklist.docx (downloaded 2026-07-08).

Inspected with python-docx: unlike the plan's assumption of "mostly static
text with a small identity block", this template is a ~20-item Yes/No
disclosure checklist (40 legacy checkboxes in one table) with no premises,
renter, or rental-provider identity fields at all — every disclosure answer
(intent to sell, mortgagee action, embedded network, minimum standards,
safety-check dates, heritage listing, asbestos, flooding, building disputes,
etc.) is a property-specific fact the PM must supply from their own
knowledge, not something `TenancyBundle` models or forms-fill can source.

Ponytail call: wiring 20 individual boolean caller fields plus a free-text
elaboration field for a checklist with no data-fetch value would be a lot of
surface for a form the PM completes by reading the actual property file.
Registered with zero declared fields (pass-through, PM completes on the
printed form) — add structured per-item fields later if a workflow needs to
drive answers programmatically from a disclosure data source.
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
    key="mandatory_disclosure_checklist",
    template=TEMPLATE,
    declared_fields=DECLARED_FIELDS,
    text_ops=TEXT_OPS,
    checkbox_ops=CHECKBOX_OPS,
    build_context=build_context,
    title="Mandatory disclosure checklist",
    group="mandatory_disclosure_checklist",
    caller_field_labels={},
)
