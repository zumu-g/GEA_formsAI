"""Tests for property-data client (U2)."""

import os
import pytest

from forms_fill.providers.property_data import PropertyFacts, property_facts, comparable_sales


def test_property_facts_no_credentials():
    """Returns empty PropertyFacts when credentials missing."""
    # Ensure no env vars set
    os.environ.pop("EVERYPROPERTY_API_KEY", None)
    os.environ.pop("EVERYPROPERTY_API_BASE_URL", None)

    facts = property_facts("123 Main St, VIC 3000")
    assert facts.building_type == ""
    assert facts.beds == ""
    assert facts.baths == ""


def test_comparable_sales_no_credentials():
    """Returns empty list when credentials missing."""
    os.environ.pop("EVERYPROPERTY_API_KEY", None)
    os.environ.pop("EVERYPROPERTY_API_BASE_URL", None)

    comparables = comparable_sales("123 Main St, VIC 3000", limit=3)
    assert comparables == []


def test_property_facts_dataclass():
    """PropertyFacts dataclass behaves correctly."""
    facts = PropertyFacts(
        building_type="House",
        beds="3",
        baths="2",
        cars="1",
        floor_m2="150",
        land_m2="600",
    )
    assert facts.building_type == "House"
    assert facts.beds == "3"
    # Dataclass is frozen; mutation raises error
    with pytest.raises(Exception):
        facts.beds = "4"


def test_property_facts_comparable_dataclass():
    """PropertyFacts with sale price/date for comparables."""
    facts = PropertyFacts(
        building_type="Unit",
        beds="2",
        sale_price="500000",
        sale_date="2026-08-15",
    )
    assert facts.sale_price == "500000"
    assert facts.sale_date == "2026-08-15"
