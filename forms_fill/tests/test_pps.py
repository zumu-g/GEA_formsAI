"""Tests for Property Price Statement form (U1)."""

import pytest

from forms_fill.registry import get_form_spec, form_catalogue


def test_pps_registered():
    """Form is registered and discoverable."""
    spec = get_form_spec("property_price_statement")
    assert spec.key == "property_price_statement"
    assert spec.title == "Property Price Statement"
    assert spec.engine == "docx"
    assert spec.requires_bundle is False


def test_pps_catalogue_entry():
    """Form appears in catalogue under GEA Sales."""
    catalogue = form_catalogue()
    pps_entry = next((f for f in catalogue if f["key"] == "property_price_statement"), None)
    assert pps_entry is not None
    assert pps_entry["category"] == "GEA Sales"
    assert pps_entry["short_title"] == "Property Price Statement (PPS)"


def test_pps_declared_fields():
    """All caller fields are declared."""
    spec = get_form_spec("property_price_statement")
    # Spot-check a few key fields.
    assert "indicative_price" in spec.declared_fields
    assert "subject_beds" in spec.declared_fields
    assert "comp1_address" in spec.declared_fields
    assert "reserve_price" in spec.declared_fields


def test_pps_validate_warnings_fewer_than_3_comparables():
    """Warning fires when <3 comparables filled."""
    spec = get_form_spec("property_price_statement")
    context = {
        "comp1_address": "123 Main St",
        "comp1_sale_price": "500000",
        "comp1_sale_date": "2026-08-01",
    }
    warnings = spec.validate_warnings(context)
    assert any("comparable" in w.lower() for w in warnings)


def test_pps_validate_warnings_auction_without_reserve():
    """Warning fires when auction/fixed-date sale has no reserve."""
    spec = get_form_spec("property_price_statement")
    context = {
        "sale_method": "auction",
        "auction_date": "2026-09-15",
        # no reserve_price
    }
    warnings = spec.validate_warnings(context)
    assert any("reserve" in w.lower() for w in warnings)


def test_pps_validate_warnings_price_outside_range():
    """Warning fires when indicative price is outside comparable range."""
    spec = get_form_spec("property_price_statement")
    context = {
        "indicative_price": "600000",
        "comp1_sale_price": "480000",
        "comp2_sale_price": "520000",
        "comp3_sale_price": "550000",
    }
    warnings = spec.validate_warnings(context)
    assert any("price" in w.lower() and "outside" in w.lower() for w in warnings)


def test_pps_no_warnings_3_comparables():
    """No warning when 3 comparables are filled."""
    spec = get_form_spec("property_price_statement")
    context = {
        "comp1_address": "123 Main St",
        "comp1_sale_price": "500000",
        "comp2_address": "456 Oak Ave",
        "comp2_sale_price": "510000",
        "comp3_address": "789 Elm Rd",
        "comp3_sale_price": "520000",
    }
    warnings = spec.validate_warnings(context)
    # Should have no "comparables" warning, but might have price warnings.
    comp_warnings = [w for w in warnings if "comparable" in w.lower()]
    assert len(comp_warnings) == 0
