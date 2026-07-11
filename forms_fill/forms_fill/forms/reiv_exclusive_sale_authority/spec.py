"""REIV Code 002 Exclusive Sale Authority (U11, R15).

Scanned 5-page template (GEA's REIV pad, 2019 print); page 1 carries the
Particulars of Appointment, pages 2-5 are pre-printed terms appended untouched.
Coordinates are pixels on a 1240px-wide render of page 1 (150dpi A4), proven by
the manual 43 Bellagio Rd fill (2026-07-11). The scan carries a ``/Rotate``
flag — the overlay engine's derotation handling is load-bearing here.

All values are caller-supplied verbatim (R4) over agency defaults (KTD8).
The estimate-range spread check (s47A: range ≤ 10% of lower amount) emits a
warning only — this tool owns no statutory logic.
"""

from __future__ import annotations

from pathlib import Path

from ...formspec import FormSpec, OverlayTickOp, StampOp, StrikeOp
from ...sales import build_sales_context

_DIR = Path(__file__).parent
TEMPLATE = _DIR / "template.pdf"
EXTRA_PAGES = tuple(_DIR / f"page{i}.pdf" for i in (2, 3, 4, 5))

AGENCY_DEFAULT_FIELDS = (
    "agent_name",
    "agent_acn",
    "agency_address",
    "attention",
    "agent_mobile",
    "agent_email",
)

CALLER_FIELDS = (
    "agent_phone",
    "vendor_name",
    "vendor_capacity",
    "vendor_abn",
    "vendor_address",
    "vendor_phone",
    "vendor_email",
    "property_address",
    "goods",
    "exclusive_days",
    "continuing_days",
    "vendors_price",
    "payable_in_days",
    "estimate_single",
    "estimate_low",
    "estimate_high",
    "fixed_commission",
    "commission_pct",
    "commission_estimate",
    "commission_gst",
    "sold_at_price",
    "advertising",
    "other_expenses",
    "total_expenses",
    "date_day",
    "date_month",
    "date_year",
)

SELECTOR_FIELDS = ("possession", "payment", "marketing_payable")

DECLARED_FIELDS = AGENCY_DEFAULT_FIELDS + CALLER_FIELDS + SELECTOR_FIELDS

STAMP_OPS = (
    StampOp("agent_name", 160, 248),
    StampOp("agent_acn", 965, 248),
    StampOp("agency_address", 165, 311),
    StampOp("attention", 200, 371),
    StampOp("agent_phone", 130, 426),
    StampOp("agent_mobile", 485, 426),
    StampOp("agent_email", 830, 426),
    StampOp("vendor_name", 150, 474, size=8),
    StampOp("vendor_capacity", 150, 486, size=6.5),
    StampOp("vendor_abn", 970, 491),
    StampOp("vendor_address", 165, 551, size=8.5),
    StampOp("vendor_phone", 145, 608),
    StampOp("vendor_email", 795, 608, size=8.5),
    StampOp("property_address", 180, 671, size=8.5),
    StampOp("goods", 255, 731),
    StampOp("exclusive_days", 365, 788),
    StampOp("continuing_days", 905, 788),
    StampOp("vendors_price", 210, 921, size=8.5),
    StampOp("payable_in_days", 800, 921),
    StampOp("estimate_single", 200, 1074),
    StampOp("estimate_low", 535, 1074),
    StampOp("estimate_high", 835, 1074),
    StampOp("fixed_commission", 440, 1158),
    StampOp("commission_pct", 700, 1200, size=9.5),
    StampOp("commission_estimate", 100, 1308, size=8.5),
    StampOp("commission_gst", 800, 1308),
    StampOp("sold_at_price", 715, 1353, size=8),
    StampOp("advertising", 195, 1501),
    StampOp("other_expenses", 630, 1501),
    StampOp("total_expenses", 950, 1501),
    StampOp("date_day", 935, 1566),
    StampOp("date_month", 995, 1566),
    StampOp("date_year", 1078, 1566),
)

TICK_OPS = (
    OverlayTickOp(
        "possession",
        {"vacant_possession": (190, 843), "subject_to_tenancy": (465, 843)},
    ),
    OverlayTickOp("payment", {"full_purchase_price": (815, 843)}),
)

# "The Marketing Expenses are payable on *the signing of this Authority /
# *written request (*delete the one that does NOT apply)"
STRIKE_OPS = (
    StrikeOp("marketing_payable", "written_request", 58, 1568, 330, 1568),
    StrikeOp("marketing_payable", "on_signing", 340, 1568, 480, 1568),
)


def build_context(bundle, fields: dict) -> dict[str, str]:
    return build_sales_context(fields)


def _money(value: str) -> float | None:
    try:
        return float(str(value).replace("$", "").replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def validate_warnings(context: dict) -> list[str]:
    low = _money(context.get("estimate_low", ""))
    high = _money(context.get("estimate_high", ""))
    if low and high and high > low * 1.10:
        return [
            "estimate range exceeds 10% of the lower amount "
            "(s47A Estate Agents Act 1980) — check estimate_low/estimate_high"
        ]
    return []


SPEC = FormSpec(
    key="reiv_exclusive_sale_authority",
    template=TEMPLATE,
    declared_fields=DECLARED_FIELDS,
    text_ops=(),
    checkbox_ops=(),
    build_context=build_context,
    selector_fields=SELECTOR_FIELDS,
    title="Exclusive Sale Authority (REIV Code 002)",
    group="sales_authority",
    caller_field_labels={
        "vendor_name": "Vendor legal name",
        "vendor_capacity": "Vendor capacity line (e.g. mortgagee exercising power of sale)",
        "vendor_abn": "Vendor ABN",
        "vendor_address": "Vendor address (or C/- legal representative)",
        "property_address": "Property address",
        "goods": "Goods sold with the property",
        "exclusive_days": "Exclusive authority period (days)",
        "commission_pct": "Commission (% of sale price, incl GST)",
        "advertising": "Advertising budget ($ incl GST)",
        "marketing_payable": "Marketing payable on (on_signing | written_request)",
    },
    engine="pdf_overlay",
    stamp_ops=STAMP_OPS,
    tick_ops=TICK_OPS,
    strike_ops=STRIKE_OPS,
    extra_pages=EXTRA_PAGES,
    requires_bundle=False,
    validate_warnings=validate_warnings,
)
