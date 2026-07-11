"""Tests for the pdf_overlay engine (U9), sales context (U10), and the REIV
exclusive sale authority spec (U11) + GET /forms metadata (U14)."""

from __future__ import annotations

import json

import fitz
import pytest

from forms_fill.core import fill_form
from forms_fill.errors import ProviderConfigError, RenderError
from forms_fill.formspec import FormSpec, OverlayTickOp, StampOp
from forms_fill.forms.reiv_exclusive_sale_authority.spec import SPEC as REIV_SPEC
from forms_fill.models import FillRequest
from forms_fill.registry import form_catalogue
from forms_fill.render_overlay import render_overlay
from forms_fill.sales import build_sales_context, load_agency_defaults

BELLAGIO_FIELDS = {
    "vendor_name": "Australia and New Zealand Banking Group Limited,",
    "vendor_capacity": "in the capacity only as mortgagee exercising power of sale",
    "vendor_abn": "11 005 357 522",
    "vendor_address": "C/- Gadens Melbourne (David Castellino), GPO Box 48, Melbourne VIC 3001",
    "vendor_phone": "(03) 9252 7762",
    "vendor_email": "david.castellino@gadens.com",
    "property_address": "43 Bellagio Road, Berwick VIC 3806 (Lot 2522 on PS816058 - vacant land)",
    "goods": "Nil - vacant land",
    "exclusive_days": "90",
    "possession": "vacant_possession",
    "payment": "full_purchase_price",
    "vendors_price": "To be advised by the Vendor in writing",
    "estimate_low": "540,000",
    "estimate_high": "594,000",
    "commission_pct": "4.125% inclusive of GST",
    "commission_estimate": "22,275.00  (based on estimate of $540,000)",
    "commission_gst": "2,025.00",
    "advertising": "3,380.00",
    "other_expenses": "Nil",
    "total_expenses": "3,380.00",
    "marketing_payable": "written_request",
    "date_day": "11",
    "date_month": "07",
    "date_year": "26",
}


def _fill(tmp_path, fields=BELLAGIO_FIELDS):
    request = FillRequest(
        form="reiv_exclusive_sale_authority",
        identifiers={},
        fields=fields,
        out_dir=str(tmp_path),
    )
    return fill_form(request)


# --- U10: sales context ------------------------------------------------------

def test_agency_defaults_fill_agent_block():
    context = build_sales_context({})
    assert "Grants Estate Agents" in context["agent_name"]
    assert "Gloucester" in context["agency_address"]
    assert context["agent_mobile"] == "0438 554 522"


def test_caller_fields_override_defaults_verbatim():
    context = build_sales_context({"agent_name": "Someone Else Pty Ltd"})
    assert context["agent_name"] == "Someone Else Pty Ltd"


def test_missing_defaults_file_raises_config_error(monkeypatch, tmp_path):
    monkeypatch.setenv("FORMS_AGENCY_FILE", str(tmp_path / "nope.json"))
    with pytest.raises(ProviderConfigError):
        load_agency_defaults()


# --- U9 + U11: overlay render end-to-end -------------------------------------

def test_reiv_fill_produces_five_page_pdf_no_docx(tmp_path):
    result = _fill(tmp_path)
    assert result.ok
    assert result.files.docx is None
    doc = fitz.open(result.files.pdf)
    assert doc.page_count == 5


def test_stamped_text_is_upright_and_searchable(tmp_path):
    # The scanned template carries a /Rotate flag; text must land extractable
    # on page 1 (derotation handling, R14).
    result = _fill(tmp_path)
    page = fitz.open(result.files.pdf)[0]
    assert page.search_for("11 005 357 522")
    assert page.search_for("43 Bellagio Road")
    assert page.search_for("Grants Estate Agents")  # from agency defaults


def test_blank_fields_reported_for_omitted_values(tmp_path):
    result = _fill(tmp_path)
    assert "continuing_days" in result.blank_fields
    assert "agent_acn" in result.blank_fields  # null in agency defaults
    assert "vendor_abn" in result.filled_fields


def test_estimate_spread_over_10_percent_warns_but_renders(tmp_path):
    fields = dict(BELLAGIO_FIELDS, estimate_high="700,000")
    result = _fill(tmp_path, fields)
    assert result.ok
    assert any("10%" in w for w in result.warnings)


def test_unknown_tick_value_raises_typed_error(tmp_path):
    fields = dict(BELLAGIO_FIELDS, possession="upside_down")
    with pytest.raises(RenderError, match="vacant_possession"):
        _fill(tmp_path, fields)


def test_missing_template_raises_render_error(tmp_path):
    spec = FormSpec(
        key="ghost",
        template=tmp_path / "missing.pdf",
        declared_fields=("a",),
        text_ops=(),
        checkbox_ops=(),
        build_context=lambda bundle, fields: dict(fields),
        engine="pdf_overlay",
        stamp_ops=(StampOp("a", 10, 10),),
        requires_bundle=False,
    )
    with pytest.raises(RenderError, match="template not found"):
        render_overlay(spec, {"a": "x"}, tmp_path)


# --- U14: GET /forms metadata -------------------------------------------------

def test_catalogue_reiv_entry_declares_engine_and_fields():
    entry = next(
        e for e in form_catalogue() if e["key"] == "reiv_exclusive_sale_authority"
    )
    assert entry["engine"] == "pdf_overlay"
    assert entry["requires_identifiers"] is False
    possession = next(f for f in entry["fields"] if f["key"] == "possession")
    assert possession["kind"] == "selector"
    assert "vacant_possession" in possession["options"]


def test_catalogue_serialises_every_form():
    payload = json.dumps(form_catalogue())
    assert "cav_rent_increase_notice" in payload
