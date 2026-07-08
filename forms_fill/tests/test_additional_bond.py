from forms_fill.forms.notice_requesting_additional_bond.spec import (
    SPEC,
    build_context,
)
from forms_fill.models import TenancyBundle
from forms_fill.render import compute_blank_fields, render


def _bundle(d):
    return TenancyBundle.model_validate(d)


def _fields():
    return {
        "notice_date": "2026-08-01",
        "existing_bond_amount": "2460",
        "old_weekly_rent": "615",
        "new_weekly_rent": "650",
        "additional_bond_amount": "140",
    }


def test_context_has_premises_renter_provider(sample_bundle_dict):
    ctx = build_context(_bundle(sample_bundle_dict), _fields())
    assert ctx["premises_address"] == "12 Example Street, Richmond"
    assert ctx["renter1_name"] == "Jane Alice Smith"
    assert ctx["provider_name"] == "Robert James Owner"


def test_caller_amounts_render_with_dollar_sign(sample_bundle_dict):
    # The template cells hold a static "$" as their only run; render.py
    # overwrites that run rather than appending, so the sign must be
    # reapplied by build_context or it's silently lost on fill.
    ctx = build_context(_bundle(sample_bundle_dict), _fields())
    assert ctx["existing_bond_amount"] == "$2460"
    assert ctx["old_weekly_rent"] == "$615"
    assert ctx["new_weekly_rent"] == "$650"
    assert ctx["additional_bond_amount"] == "$140"


def test_missing_amount_renders_blank_not_guessed(sample_bundle_dict):
    ctx = build_context(_bundle(sample_bundle_dict), {})
    assert ctx["additional_bond_amount"] == ""
    assert ctx["existing_bond_amount"] == ""


def test_leaves_signature_undeclared():
    joined = " ".join(SPEC.declared_fields)
    assert "signature" not in joined


def test_fill_renders_docx(tmp_path, sample_bundle_dict):
    ctx = build_context(_bundle(sample_bundle_dict), _fields())
    blanks = compute_blank_fields(SPEC, ctx)
    assert blanks == []
    docx_path, _, _ = render(SPEC, ctx, tmp_path)
    assert docx_path.exists()
