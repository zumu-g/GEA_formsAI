import pytest

from forms_fill.forms.notice_of_goods_left_behind.spec import (
    SPEC as GOODS_LEFT_SPEC,
    build_context as goods_left_context,
)
from forms_fill.forms.notice_of_intention_to_sell.spec import (
    SPEC as SELL_SPEC,
    build_context as sell_context,
)
from forms_fill.forms.notice_to_vacate_death_sole_renter.spec import (
    SPEC as DEATH_SPEC,
    build_context as death_context,
)
from forms_fill.models import TenancyBundle
from forms_fill.render import compute_blank_fields, render


def _bundle(d):
    return TenancyBundle.model_validate(d)


# ── notice_of_intention_to_sell ────────────────────────────────────────────


def test_sell_context_has_premises_renter_provider(sample_bundle_dict):
    ctx = sell_context(_bundle(sample_bundle_dict), {})
    assert ctx["premises_address"] == "12 Example Street, Richmond"
    assert ctx["renter1_name"] == "Jane Alice Smith"
    assert ctx["provider_name"] == "Robert James Owner"


def test_sell_selling_agent_fields_render_verbatim(sample_bundle_dict):
    fields = {
        "selling_agent_name": "Jane Agent",
        "selling_agent_address": "1 Main St",
        "selling_agent_postcode": "3000",
        "selling_agent_business_hours": "0399991111",
        "selling_agent_after_hours": "0499991111",
        "selling_agent_email": "agent@example.com",
    }
    ctx = sell_context(_bundle(sample_bundle_dict), fields)
    for key, value in fields.items():
        assert ctx[key] == value


def test_sell_selling_agent_fields_blank_when_sold_without_agent(sample_bundle_dict):
    ctx = sell_context(_bundle(sample_bundle_dict), {})
    assert ctx["selling_agent_name"] == ""


def test_sell_leaves_delivery_and_signature_undeclared():
    joined = " ".join(SELL_SPEC.declared_fields)
    for forbidden in ("delivery", "signature", "tracking"):
        assert forbidden not in joined


def test_sell_fill_renders_docx(tmp_path, sample_bundle_dict):
    ctx = sell_context(_bundle(sample_bundle_dict), {})
    blanks = compute_blank_fields(SELL_SPEC, ctx)
    assert "renter3_name" in blanks
    docx_path, _, warnings = render(SELL_SPEC, ctx, tmp_path)
    assert docx_path.exists()


# ── notice_of_goods_left_behind ─────────────────────────────────────────────


def test_goods_left_context_uses_first_renter_as_former_renter(sample_bundle_dict):
    ctx = goods_left_context(_bundle(sample_bundle_dict), {})
    assert ctx["renter1_name"] == "Jane Alice Smith"
    assert ctx["renter_email"] == "jane@example.com"
    assert ctx["provider_name"] == "Robert James Owner"


def test_goods_left_caller_fields_render_verbatim(sample_bundle_dict):
    fields = {
        "notice_date": "2026-08-01",
        "date_vacated": "2026-07-25",
        "goods_description": "A blue couch and a lamp",
        "dispose_by_date": "2026-08-15",
    }
    ctx = goods_left_context(_bundle(sample_bundle_dict), fields)
    for key, value in fields.items():
        assert ctx[key] == value


def test_goods_left_missing_caller_fields_render_blank(sample_bundle_dict):
    ctx = goods_left_context(_bundle(sample_bundle_dict), {})
    assert ctx["goods_description"] == ""
    assert ctx["dispose_by_date"] == ""


def test_goods_left_leaves_delivery_and_signature_undeclared():
    joined = " ".join(GOODS_LEFT_SPEC.declared_fields)
    for forbidden in ("delivery", "signature", "tracking"):
        assert forbidden not in joined


def test_goods_left_fill_renders_docx(tmp_path, sample_bundle_dict):
    fields = {
        "notice_date": "2026-08-01",
        "date_vacated": "2026-07-25",
        "goods_description": "A blue couch and a lamp",
        "dispose_by_date": "2026-08-15",
    }
    ctx = goods_left_context(_bundle(sample_bundle_dict), fields)
    blanks = compute_blank_fields(GOODS_LEFT_SPEC, ctx)
    assert blanks == []
    docx_path, _, _ = render(GOODS_LEFT_SPEC, ctx, tmp_path)
    assert docx_path.exists()


# ── notice_to_vacate_death_sole_renter ──────────────────────────────────────


def test_death_context_uses_first_renter_as_deceased(sample_bundle_dict):
    ctx = death_context(_bundle(sample_bundle_dict), {"termination_date": "2026-09-30"})
    assert ctx["renter1_name"] == "Jane Alice Smith"
    assert ctx["termination_date"] == "2026-09-30"


def test_death_no_free_text_reason_field_declared():
    # Unlike notice_to_vacate, this template's reason section is fixed
    # boilerplate — there is no `reason_for_notice` field to declare.
    assert "reason_for_notice" not in DEATH_SPEC.declared_fields


def test_death_missing_termination_date_renders_blank(sample_bundle_dict):
    ctx = death_context(_bundle(sample_bundle_dict), {})
    assert ctx["termination_date"] == ""


def test_death_leaves_delivery_and_signature_undeclared():
    joined = " ".join(DEATH_SPEC.declared_fields)
    for forbidden in ("delivery", "signature", "tracking"):
        assert forbidden not in joined


def test_death_fill_renders_docx(tmp_path, sample_bundle_dict):
    ctx = death_context(_bundle(sample_bundle_dict), {"termination_date": "2026-09-30"})
    docx_path, _, _ = render(DEATH_SPEC, ctx, tmp_path)
    assert docx_path.exists()
