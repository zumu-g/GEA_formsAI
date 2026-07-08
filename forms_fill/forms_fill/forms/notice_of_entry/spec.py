"""CAV "Notice to renter(s) of entry to rented premises" form spec
(RTA 1997 (Vic) s 86 — the myVCAT "Notice of Entry" general notice).

Source: https://www.consumer.vic.gov.au/library/forms/housing-and-accommodation/
renting/notice-to-renter-of-entry-to-rented-premises.docx (downloaded 2026-07-08).

Table/cell indices derived by inspecting the template's structure (python-docx):
23 tables total. Table 23 is a static reference list of all nine s 86 entry
reasons with their minimum-notice periods (rental provider copies from it by
hand into `entry_reason`, mirroring `notice_to_vacate`'s ground handling) — not
a fillable field.

Left blank by design: "Delivery of this notice" (tables 13-20) and "Signature of
rental provider or agent" (tables 21-22) — the PM's manual-service steps, never
automated. The multi-date variant (table 11, "Use if multiple dates sought")
is left unsupported in this spec's v1 — single entry date/time only.
"""

from __future__ import annotations

from pathlib import Path

from ...formspec import FormSpec, TextOp
from ...models import TenancyBundle

TEMPLATE = Path(__file__).with_name("template.docx")

# Caller-supplied, rendered verbatim — the minimum notice period for the chosen
# s 86 ground is the PM's own legal-timing decision, never computed here.
CALLER_FIELDS = ("entry_date", "entry_window", "entry_reason")

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
)

DECLARED_FIELDS = FETCHED_FIELDS + CALLER_FIELDS

TEXT_OPS = (
    # 1 — Address of rented premises
    TextOp("premises_address", table_index=1, cell_index=0),
    TextOp("premises_postcode", table_index=1, cell_index=2),
    # 2 — Residential rental provider details (never the mortgagee/agent)
    TextOp("provider_name", table_index=2, cell_index=1),
    TextOp("provider_address", table_index=3, cell_index=0),
    TextOp("provider_postcode", table_index=3, cell_index=2),
    TextOp("provider_business_hours", table_index=4, cell_index=1),
    # 3 — Renter details
    TextOp("renter1_name", table_index=5, cell_index=1),
    TextOp("renter2_name", table_index=6, cell_index=1),
    TextOp("renter3_name", table_index=7, cell_index=1),
    TextOp("renter4_name", table_index=8, cell_index=1),
    # 4 — Date entry is required (single date/time; table 10 has 2 rows)
    TextOp("entry_date", table_index=10, cell_index=1, row_index=0),
    TextOp("entry_window", table_index=10, cell_index=1, row_index=1),
    # 5 — Reason for notice of entry (free text; section + facts supplied
    # verbatim by the caller, never authored by this spec)
    TextOp("entry_reason", table_index=12, cell_index=0),
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
        "entry_date": _s(fields.get("entry_date")),
        "entry_window": _s(fields.get("entry_window")),
        "entry_reason": _s(fields.get("entry_reason")),
    }

    if len(renters) > 4:
        extra = ", ".join(_s(r.full_name) for r in renters[4:])
        ctx["renter4_name"] = (
            f"{ctx['renter4_name']} (plus additional renters on extra page: {extra})"
        )

    return ctx


SPEC = FormSpec(
    key="notice_of_entry",
    template=TEMPLATE,
    declared_fields=DECLARED_FIELDS,
    text_ops=TEXT_OPS,
    checkbox_ops=(),
    build_context=build_context,
    title="Notice to renter(s) of entry to rented premises (s 86)",
    group="general_notice",
    caller_field_labels={
        "entry_date": "Entry date",
        "entry_window": "Entry time window (e.g. 9am to 5pm)",
        "entry_reason": "Reason for entry (section + facts, verbatim)",
    },
)
