"""CAV "Condition report" form spec (RTA 1997 (Vic) s 30).

Source: https://www.consumer.vic.gov.au/library/forms/housing-and-accommodation/
renting/condition-report-word.docx (downloaded 2026-07-08).

Table/cell indices below were derived by inspecting the template's structure
(python-docx): 37 tables total.

Per KTD3, this spec fills only the identity block (report date, premises,
rental provider/agent names, renter names) and the four safety-check dates.
The move-in room-by-room condition tables (269 and 10 rows) and the
end-of-tenancy duplicate section (254 and 24 rows) are large repeating
structures the PM and renter complete together when walking the property —
declaring them here would mean inventing a repeating-row engine nobody asked
for (KTD3). NBN/internet connection details, all signature blocks, and the
end-of-tenancy report date are blank-by-design for the same reason as every
shipped notice spec's manual-service sections.

Safety-check dates (pool barrier, smoke alarm, electrical, gas) are
caller-supplied — they are property compliance facts, not part of the
`TenancyBundle` provider contract.
"""

from __future__ import annotations

from pathlib import Path

from ...formspec import FormSpec, TextOp
from ...models import TenancyBundle

TEMPLATE = Path(__file__).with_name("template.docx")

CALLER_FIELDS = (
    "report_date",
    "agent_name",
    "agent_company_name",
    "pool_barrier_check_date",
    "smoke_alarm_check_date",
    "electrical_safety_check_date",
    "gas_safety_check_date",
)

FETCHED_FIELDS = (
    "premises_address",
    "premises_postcode",
    "provider_name",
    "renter1_name",
    "renter2_name",
    "renter3_name",
    "renter4_name",
)

DECLARED_FIELDS = FETCHED_FIELDS + CALLER_FIELDS

TEXT_OPS = (
    TextOp("report_date", table_index=2, cell_index=1),
    TextOp("premises_address", table_index=3, cell_index=0),
    TextOp("premises_postcode", table_index=3, cell_index=2),
    TextOp("provider_name", table_index=4, cell_index=1),
    TextOp("agent_name", table_index=5, cell_index=1),
    TextOp("agent_company_name", table_index=6, cell_index=1),
    TextOp("renter1_name", table_index=7, cell_index=1),
    TextOp("renter2_name", table_index=8, cell_index=1),
    TextOp("renter3_name", table_index=9, cell_index=1),
    TextOp("renter4_name", table_index=10, cell_index=1),
    TextOp("pool_barrier_check_date", table_index=18, cell_index=1),
    TextOp("smoke_alarm_check_date", table_index=19, cell_index=1),
    TextOp("electrical_safety_check_date", table_index=20, cell_index=1),
    TextOp("gas_safety_check_date", table_index=21, cell_index=1),
)

CHECKBOX_OPS = ()


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
        "provider_name": _s(bundle.rental_provider.full_name),
        "renter1_name": _s(renter(0).full_name) if renter(0) else "",
        "renter2_name": _s(renter(1).full_name) if renter(1) else "",
        "renter3_name": _s(renter(2).full_name) if renter(2) else "",
        "renter4_name": _s(renter(3).full_name) if renter(3) else "",
    }

    if len(renters) > 4:
        extra = ", ".join(_s(r.full_name) for r in renters[4:])
        ctx["renter4_name"] = (
            f"{ctx['renter4_name']} (plus additional renters on extra page: {extra})"
        )

    for name in CALLER_FIELDS:
        ctx[name] = _s(fields.get(name))

    return ctx


SPEC = FormSpec(
    key="condition_report",
    template=TEMPLATE,
    declared_fields=DECLARED_FIELDS,
    text_ops=TEXT_OPS,
    checkbox_ops=CHECKBOX_OPS,
    build_context=build_context,
    title="Condition report",
    group="condition_report",
    caller_field_labels={
        "report_date": "Date of condition report",
        "agent_name": "Agent full name",
        "agent_company_name": "Agent's company name (if applicable)",
        "pool_barrier_check_date": "Date of last pool barrier compliance check",
        "smoke_alarm_check_date": "Date of last smoke alarm test",
        "electrical_safety_check_date": "Date of last electrical safety check",
        "gas_safety_check_date": "Date of last gas safety check",
    },
)
