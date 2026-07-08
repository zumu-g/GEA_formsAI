"""CAV "Notice to renter of rented premises" form spec
(RTA 1997 (Vic) ss 55, 66, 78, 79, 91M — the "General" notices group).

Source: https://www.consumer.vic.gov.au/library/forms/housing-and-accommodation/
renting/notice-to-renter-of-rented-premises.docx (downloaded 2026-07-08).

CAV publishes ss 55(1), 66(2)/(3), 78(1), 79(1), 79(2), and 91M as ONE shared
template (28 tables, single reason-for-notice free-text field at table 11) —
confirmed by inspection (table 22 is a reference list of all six reasons, for
the rental provider to copy from, mirroring `notice_to_vacate`'s ground
handling). Per KTD2, one spec covers this whole group; the section + facts are
supplied verbatim by the caller in `reason_for_notice`, exactly like
`notice_to_vacate`. 86 (Notice of Entry) is a genuinely separate CAV document
and gets its own spec (`notice_of_entry`).

Table/cell indices derived by inspecting the template's structure (python-docx).

Left blank by design: "Delivery of this notice" (tables 12-19) and "Signature of
rental provider or agent" (tables 20-21) — the PM's manual-service steps, never
automated. Table 22 (reason reference list) is static reference content on the
template itself, not a fillable field.
"""

from __future__ import annotations

from pathlib import Path

from ...formspec import FormSpec, TextOp
from ...models import TenancyBundle

TEMPLATE = Path(__file__).with_name("template.docx")

# Caller-supplied, rendered verbatim — never computed or validated here.
CALLER_FIELDS = ("reason_for_notice",)

# Fetched-from-provider text fields (same shape as notice_to_vacate).
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
    # Address of rented premises
    TextOp("premises_address", table_index=1, cell_index=0),
    TextOp("premises_postcode", table_index=1, cell_index=2),
    # Renters details
    TextOp("renter1_name", table_index=2, cell_index=1),
    TextOp("renter2_name", table_index=3, cell_index=1),
    TextOp("renter3_name", table_index=4, cell_index=1),
    TextOp("renter4_name", table_index=5, cell_index=1),
    # Rental provider details (never the mortgagee/agent)
    TextOp("provider_name", table_index=6, cell_index=0),
    TextOp("provider_address", table_index=7, cell_index=0),
    TextOp("provider_postcode", table_index=7, cell_index=2),
    TextOp("provider_business_hours", table_index=8, cell_index=1),
    TextOp("provider_after_hours", table_index=9, cell_index=1),
    TextOp("provider_email", table_index=10, cell_index=1),
    # Reason for notice (free text; section + facts supplied verbatim by the
    # caller, never authored by this spec)
    TextOp("reason_for_notice", table_index=11, cell_index=0),
)


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
        "reason_for_notice": _s(fields.get("reason_for_notice")),
    }

    if len(renters) > 4:
        extra = ", ".join(_s(r.full_name) for r in renters[4:])
        ctx["renter4_name"] = (
            f"{ctx['renter4_name']} (plus additional renters on extra page: {extra})"
        )

    return ctx


SPEC = FormSpec(
    key="general_notice",
    template=TEMPLATE,
    declared_fields=DECLARED_FIELDS,
    text_ops=TEXT_OPS,
    checkbox_ops=(),
    build_context=build_context,
    title="Notice to renter of rented premises (ss 55, 66, 78, 79, 91M)",
    group="general_notice",
    caller_field_labels={
        "reason_for_notice": "Reason for notice (section + facts, verbatim)",
    },
)
