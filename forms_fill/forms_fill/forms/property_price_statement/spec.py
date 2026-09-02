"""Property Price Statement (PPS) form spec (U1, R1–R8).

Interim template pending CAV-approved form (see KTD1, R8). Renders subject property
key features (building type, beds, baths, cars, floor, land) and three comparable
properties with their feature sets plus address, sale price, and sale date. Fields
are fully editable; warnings flag <3 comparables, missing auction reserve, indicative
price outside comparable range.
"""

from __future__ import annotations

from pathlib import Path

from ...formspec import FormSpec, TextOp
from ...sales import build_sales_context

_DIR = Path(__file__).parent
TEMPLATE = _DIR / "template.docx"

# Caller-supplied, rendered verbatim (R4).
CALLER_FIELDS = (
    "indicative_price",
    "subject_building_type",
    "subject_beds",
    "subject_baths",
    "subject_cars",
    "subject_floor_m2",
    "subject_land_m2",
    "comp1_address",
    "comp1_sale_price",
    "comp1_sale_date",
    "comp1_building_type",
    "comp1_beds",
    "comp1_baths",
    "comp1_cars",
    "comp1_floor_m2",
    "comp1_land_m2",
    "comp2_address",
    "comp2_sale_price",
    "comp2_sale_date",
    "comp2_building_type",
    "comp2_beds",
    "comp2_baths",
    "comp2_cars",
    "comp2_floor_m2",
    "comp2_land_m2",
    "comp3_address",
    "comp3_sale_price",
    "comp3_sale_date",
    "comp3_building_type",
    "comp3_beds",
    "comp3_baths",
    "comp3_cars",
    "comp3_floor_m2",
    "comp3_land_m2",
    "sale_method",
    "auction_date",
    "reserve_price",
)

DECLARED_FIELDS = CALLER_FIELDS

# ponytail: placeholder text ops — template structure TBD; land-loading during U1
# execution (once template is refined for real content).
TEXT_OPS = ()


def build_context(bundle, fields: dict) -> dict[str, str]:
    return build_sales_context(fields)


def _money(value: str) -> float | None:
    try:
        return float(str(value).replace("$", "").replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def validate_warnings(context: dict) -> list[str]:
    warnings = []
    # Count comparables: all three optional, but <3 is a warning (R1).
    comparables = sum(
        1 for i in (1, 2, 3)
        if context.get(f"comp{i}_address", "").strip()
    )
    if comparables < 3:
        warnings.append(
            f"only {comparables} comparable(s) filled; "
            "recommend 3 for statutory compliance when regulations publish (R8)"
        )
    # Auction/fixed-date without reserve is a warning (R5).
    sale_method = (context.get("sale_method", "") or "").strip().lower()
    if sale_method in ("auction", "fixed-date") and not context.get("reserve_price", "").strip():
        warnings.append(
            "auction or fixed-date sale without reserve price; "
            "reserve must be published 7+ days before the event (R5)"
        )
    # Indicative price outside comparable range — warning only (KTD6).
    indicative = _money(context.get("indicative_price", ""))
    comp_prices = [
        _money(context.get(f"comp{i}_sale_price", ""))
        for i in (1, 2, 3)
    ]
    comp_prices = [p for p in comp_prices if p is not None]
    if indicative is not None and comp_prices:
        min_price = min(comp_prices)
        max_price = max(comp_prices)
        if indicative < min_price or indicative > max_price:
            warnings.append(
                f"indicative price ${indicative:,.0f} outside comparable range "
                f"${min_price:,.0f}–${max_price:,.0f}"
            )
    return warnings


SPEC = FormSpec(
    key="property_price_statement",
    template=TEMPLATE,
    declared_fields=DECLARED_FIELDS,
    text_ops=TEXT_OPS,
    checkbox_ops=(),
    build_context=build_context,
    selector_fields=(),
    title="Property Price Statement",
    group="sales_pps",
    caller_field_labels={
        "indicative_price": "Indicative selling price ($)",
        "subject_building_type": "Subject: building type (e.g. House, Unit)",
        "subject_beds": "Subject: bedrooms",
        "subject_baths": "Subject: bathrooms",
        "subject_cars": "Subject: car spaces",
        "subject_floor_m2": "Subject: internal floor area (m²)",
        "subject_land_m2": "Subject: land size (m²)",
        "comp1_address": "Comparable 1: address",
        "comp1_sale_price": "Comparable 1: sale price ($)",
        "comp1_sale_date": "Comparable 1: sale date (YYYY-MM-DD)",
        "comp1_building_type": "Comparable 1: building type",
        "comp1_beds": "Comparable 1: bedrooms",
        "comp1_baths": "Comparable 1: bathrooms",
        "comp1_cars": "Comparable 1: car spaces",
        "comp1_floor_m2": "Comparable 1: floor area (m²)",
        "comp1_land_m2": "Comparable 1: land size (m²)",
        "comp2_address": "Comparable 2: address",
        "comp2_sale_price": "Comparable 2: sale price ($)",
        "comp2_sale_date": "Comparable 2: sale date (YYYY-MM-DD)",
        "comp2_building_type": "Comparable 2: building type",
        "comp2_beds": "Comparable 2: bedrooms",
        "comp2_baths": "Comparable 2: bathrooms",
        "comp2_cars": "Comparable 2: car spaces",
        "comp2_floor_m2": "Comparable 2: floor area (m²)",
        "comp2_land_m2": "Comparable 2: land size (m²)",
        "comp3_address": "Comparable 3: address",
        "comp3_sale_price": "Comparable 3: sale price ($)",
        "comp3_sale_date": "Comparable 3: sale date (YYYY-MM-DD)",
        "comp3_building_type": "Comparable 3: building type",
        "comp3_beds": "Comparable 3: bedrooms",
        "comp3_baths": "Comparable 3: bathrooms",
        "comp3_cars": "Comparable 3: car spaces",
        "comp3_floor_m2": "Comparable 3: floor area (m²)",
        "comp3_land_m2": "Comparable 3: land size (m²)",
        "sale_method": "Sale method (auction | fixed-date | private sale)",
        "auction_date": "Auction/fixed-date date (YYYY-MM-DD)",
        "reserve_price": "Vendor reserve price ($) — required for auction/fixed-date",
    },
    engine="docx",
    requires_bundle=False,
    validate_warnings=validate_warnings,
)
