"""CAV "Notice of proposed rent increase" form spec (RTA 1997 s44(1)).

Table/cell indices below were derived by inspecting the template's structure:
every fillable field is a single-row label/value table addressed by index, and
the 13 legacy form checkboxes group 3-per-table for current/new/increase rent
rows (document order: week, fortnight, calendar month).

Left blank by design (R7): the "Delivery of this notice" section, the
signature-block date, and the renter's "Rent increase investigation" section —
these fields are simply not declared here, so the renderer never touches them.
"""

from __future__ import annotations

from pathlib import Path

from ...formspec import CheckboxOp, FormSpec, TextOp
from ...models import TenancyBundle

TEMPLATE = Path(__file__).with_name("template.docx")

# Caller-supplied, rendered verbatim (R4). These are the exact `fields` JSON keys
# the rent-review system wires to.
CALLER_FIELDS = (
    "current_rent",
    "new_rent",
    "increase",
    "start_date",
    "method_basis",
)

# Fetched-from-provider text fields.
FETCHED_FIELDS = (
    "premises_address",
    "premises_postcode",
    "renter1_name",
    "renter2_name",
    "renter3_name",
    "renter4_name",
    "renter_service_address",
    "renter_service_postcode",
    "renter_business_hours",
    "renter_after_hours",
    "renter_email",
    "provider_name",
    "provider_address",
    "provider_postcode",
    "provider_business_hours",
    "provider_after_hours",
    "provider_email",
)

DECLARED_FIELDS = FETCHED_FIELDS + CALLER_FIELDS

TEXT_OPS = (
    # Section 1 — premises
    TextOp("premises_address", table_index=1, cell_index=0),
    TextOp("premises_postcode", table_index=1, cell_index=2),
    # Section 2 — renters
    TextOp("renter1_name", table_index=2, cell_index=1),
    TextOp("renter2_name", table_index=3, cell_index=1),
    TextOp("renter3_name", table_index=4, cell_index=1),
    TextOp("renter4_name", table_index=5, cell_index=1),
    TextOp("renter_service_address", table_index=6, cell_index=0),
    TextOp("renter_service_postcode", table_index=6, cell_index=2),
    TextOp("renter_business_hours", table_index=7, cell_index=1),
    TextOp("renter_after_hours", table_index=8, cell_index=1),
    TextOp("renter_email", table_index=9, cell_index=1),
    # Section 3 — rental provider (owner)
    TextOp("provider_name", table_index=10, cell_index=0),
    TextOp("provider_address", table_index=11, cell_index=0),
    TextOp("provider_postcode", table_index=11, cell_index=2),
    TextOp("provider_business_hours", table_index=12, cell_index=1),
    TextOp("provider_after_hours", table_index=13, cell_index=1),
    TextOp("provider_email", table_index=14, cell_index=1),
    # Section 4 — proposed rent increase (values; periods handled by checkboxes)
    TextOp("current_rent", table_index=15, cell_index=1),
    TextOp("new_rent", table_index=16, cell_index=1),
    TextOp("increase", table_index=17, cell_index=1),
    TextOp("start_date", table_index=17, cell_index=1, row_index=1),
    # Section 5 — method
    TextOp("method_basis", table_index=18, cell_index=1),
)

# One rent_period applies to the whole notice; tick it in all three rent rows.
_PERIODS = {"week": 0, "fortnight": 1, "calendar month": 2}
CHECKBOX_OPS = (
    CheckboxOp("rent_period", table_index=15, options=_PERIODS),
    CheckboxOp("rent_period", table_index=16, options=_PERIODS),
    CheckboxOp("rent_period", table_index=17, options=_PERIODS),
)

# Accept common synonyms for the period; normalise to the form's wording.
_PERIOD_SYNONYMS = {
    "week": "week",
    "weekly": "week",
    "fortnight": "fortnight",
    "fortnightly": "fortnight",
    "calendar month": "calendar month",
    "month": "calendar month",
    "monthly": "calendar month",
    "calendar_month": "calendar month",
}


def normalise_period(value: str) -> str:
    return _PERIOD_SYNONYMS.get(str(value).strip().lower(), str(value).strip().lower())


def _s(value: object) -> str:
    return "" if value is None else str(value)


def build_context(bundle: TenancyBundle, fields: dict) -> dict[str, str]:
    """Merge fetched bundle data with verbatim caller fields into a flat context."""

    renters = list(bundle.renters)

    def renter(i: int):
        return renters[i] if i < len(renters) else None

    primary = renter(0)
    ctx: dict[str, str] = {
        "premises_address": _s(bundle.premises.address_line),
        "premises_postcode": _s(bundle.premises.postcode),
        "renter1_name": _s(renter(0).full_name) if renter(0) else "",
        "renter2_name": _s(renter(1).full_name) if renter(1) else "",
        "renter3_name": _s(renter(2).full_name) if renter(2) else "",
        "renter4_name": _s(renter(3).full_name) if renter(3) else "",
        "renter_service_address": _s(primary.address_for_service) if primary else "",
        "renter_service_postcode": _s(primary.service_postcode) if primary else "",
        "renter_business_hours": _s(primary.phone_business_hours) if primary else "",
        "renter_after_hours": _s(primary.phone_after_hours) if primary else "",
        "renter_email": _s(primary.email) if primary else "",
        "provider_name": _s(bundle.rental_provider.full_name),
        "provider_address": _s(bundle.rental_provider.service_address),
        "provider_postcode": _s(bundle.rental_provider.service_postcode),
        "provider_business_hours": _s(bundle.rental_provider.phone_business_hours),
        "provider_after_hours": _s(bundle.rental_provider.phone_after_hours),
        "provider_email": _s(bundle.rental_provider.email),
        # Caller fields — verbatim, no computation/validation (R4). current_rent
        # and rent_period fall back to the tenancy record when the caller
        # doesn't supply them; an explicit caller value always wins (U2).
        "current_rent": _s(fields.get("current_rent")) or _s(bundle.current_rent),
        "new_rent": _s(fields.get("new_rent")),
        "increase": _s(fields.get("increase")),
        "start_date": _s(fields.get("start_date")),
        "method_basis": _s(fields.get("method_basis")),
        # Selector (not a declared text field).
        "rent_period": normalise_period(
            fields.get("rent_period") or bundle.rent_period or ""
        ),
    }

    # >4 renters → overflow note appended to renter 4's slot (R5).
    if len(renters) > 4:
        extra = ", ".join(_s(r.full_name) for r in renters[4:])
        ctx["renter4_name"] = (
            f"{ctx['renter4_name']} (plus additional renters on extra page: {extra})"
        )

    return ctx


SPEC = FormSpec(
    key="cav_rent_increase_notice",
    template=TEMPLATE,
    declared_fields=DECLARED_FIELDS,
    text_ops=TEXT_OPS,
    checkbox_ops=CHECKBOX_OPS,
    build_context=build_context,
    selector_fields=("rent_period",),
    title="Notice of rent increase to renter of rented premises (s 44(1))",
    group="rent_increase",
    caller_field_labels={
        "current_rent": "Current rent ($)",
        "new_rent": "New rent ($)",
        "increase": "Increase amount ($)",
        "rent_period": "Rent period (weekly/fortnightly/calendar month)",
        "start_date": "New rent start date",
        "method_basis": "Basis for the increase (e.g. market comparison)",
    },
)
