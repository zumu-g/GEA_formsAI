"""Property-data client for comparables autofill (U2, R2, KTD3).

Thin client for everyproperty API (env EVERYPROPERTY_API_KEY, EVERYPROPERTY_API_BASE_URL).
Returns PropertyFacts with 6 key features (building type, beds, baths, cars, floor, land)
plus sale price and date for comparables. Manual entry is the zero-config path.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class PropertyFacts:
    """Key property features for PPS form: subject or comparable."""

    building_type: str = ""
    beds: str = ""
    baths: str = ""
    cars: str = ""
    floor_m2: str = ""
    land_m2: str = ""
    # Comparables only:
    sale_price: str = ""
    sale_date: str = ""


class PropertyDataError(Exception):
    """Raised when API call fails or credentials missing."""


def property_facts(address: str) -> PropertyFacts:
    """Fetch subject property key features from everyproperty API.

    Returns PropertyFacts with 6 features. If credentials missing,
    returns empty PropertyFacts (manual entry path).
    """

    api_key = os.environ.get("EVERYPROPERTY_API_KEY", "").strip()
    base_url = os.environ.get("EVERYPROPERTY_API_BASE_URL", "").strip()

    if not api_key or not base_url:
        # No credentials → return empty; UI hides autofill button (R2).
        return PropertyFacts()

    try:
        client = httpx.Client(timeout=10)
        # ponytail: everyproperty API shape TBD; stub returns empty on actual call.
        # Real integration depends on API docs when available.
        response = client.get(
            f"{base_url}/property/search",
            params={"q": address},
            headers={"Authorization": f"Bearer {api_key}"},
        )
        response.raise_for_status()
        data = response.json()
        # Expect { building_type, beds, baths, cars, floor_m2, land_m2 } shape.
        return PropertyFacts(
            building_type=data.get("building_type", ""),
            beds=str(data.get("beds", "")),
            baths=str(data.get("baths", "")),
            cars=str(data.get("cars", "")),
            floor_m2=str(data.get("floor_m2", "")),
            land_m2=str(data.get("land_m2", "")),
        )
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        # API error: return empty PropertyFacts so form remains fillable manually.
        return PropertyFacts()


def comparable_sales(address: str, limit: int = 3) -> list[PropertyFacts]:
    """Fetch comparable sales within default SOI rules (6 months, 2 km, by type).

    Returns list of PropertyFacts (each with all 8 fields including sale_price/date).
    If credentials missing or API error, returns empty list (manual entry works).
    """

    api_key = os.environ.get("EVERYPROPERTY_API_KEY", "").strip()
    base_url = os.environ.get("EVERYPROPERTY_API_BASE_URL", "").strip()

    if not api_key or not base_url:
        # No credentials → return empty.
        return []

    try:
        client = httpx.Client(timeout=10)
        response = client.get(
            f"{base_url}/property/comparables",
            params={
                "address": address,
                "limit": limit,
                "months": 6,
                "radius_km": 2,
            },
            headers={"Authorization": f"Bearer {api_key}"},
        )
        response.raise_for_status()
        data = response.json()
        # Expect { comparables: [ { address, building_type, beds, baths, cars, floor_m2, land_m2, sale_price, sale_date }, ... ] }
        comparables = data.get("comparables", [])
        return [
            PropertyFacts(
                building_type=c.get("building_type", ""),
                beds=str(c.get("beds", "")),
                baths=str(c.get("baths", "")),
                cars=str(c.get("cars", "")),
                floor_m2=str(c.get("floor_m2", "")),
                land_m2=str(c.get("land_m2", "")),
                sale_price=str(c.get("sale_price", "")),
                sale_date=c.get("sale_date", ""),
            )
            for c in comparables[:limit]
        ]
    except (httpx.RequestError, httpx.HTTPStatusError):
        # API error: return empty list.
        return []
