from forms_fill.forms.residential_rental_agreement.spec import SPEC as FORM1_SPEC
from forms_fill.forms.residential_rental_agreement.spec import (
    build_context as form1_context,
)
from forms_fill.forms.residential_rental_agreement_5yr.spec import (
    SPEC as FORM2_SPEC,
)
from forms_fill.forms.residential_rental_agreement_5yr.spec import (
    build_context as form2_context,
)
from forms_fill.models import TenancyBundle
from forms_fill.render import compute_blank_fields, render


def _bundle(d):
    return TenancyBundle.model_validate(d)


def _base_fields():
    return {
        "agreement_date": "2026-07-01",
        "agent_name": "GEA Property",
        "agent_address": "1 Agent St",
        "agent_postcode": "3000",
        "agent_phone": "0399990000",
        "agent_email": "gea@example.com",
        "renter1_current_address": "5 Old St",
        "renter1_current_postcode": "3122",
        "fixed_start_date": "2026-08-01",
        "fixed_end_date": "2027-08-01",
        "rent_amount": "615",
        "rent_period": "week",
        "rent_payment_day": "Thursday",
        "first_rent_due_date": "2026-08-01",
        "bond_amount": "2460",
        "bond_due_date": "2026-08-01",
        "emergency_contact_name": "GEA Maintenance",
        "emergency_phone": "0399991234",
        "emergency_email": "maint@example.com",
    }


# ── Form 1 (residential_rental_agreement) ───────────────────────────────────


def test_form1_context_has_premises_renter_provider(sample_bundle_dict):
    fields = dict(_base_fields(), term_type="fixed")
    ctx = form1_context(_bundle(sample_bundle_dict), fields)
    assert ctx["premises_address"] == "12 Example Street, Richmond"
    assert ctx["renter1_name"] == "Jane Alice Smith"
    assert ctx["provider_name"] == "Robert James Owner"


def test_form1_fixed_term_fields_render_verbatim(sample_bundle_dict):
    fields = dict(_base_fields(), term_type="fixed")
    ctx = form1_context(_bundle(sample_bundle_dict), fields)
    assert ctx["fixed_start_date"] == "2026-08-01"
    assert ctx["fixed_end_date"] == "2027-08-01"
    assert ctx["term_type"] == "fixed"


def test_form1_periodic_term_supported(sample_bundle_dict):
    fields = dict(_base_fields(), term_type="periodic", periodic_start_date="2026-08-01")
    del fields["fixed_start_date"]
    del fields["fixed_end_date"]
    ctx = form1_context(_bundle(sample_bundle_dict), fields)
    assert ctx["term_type"] == "periodic"
    assert ctx["periodic_start_date"] == "2026-08-01"
    assert ctx["fixed_start_date"] == ""


def test_form1_agent_and_current_address_are_caller_fields(sample_bundle_dict):
    ctx = form1_context(_bundle(sample_bundle_dict), {})
    assert "agent_name" in FORM1_SPEC.declared_fields
    assert "renter1_current_address" in FORM1_SPEC.declared_fields
    assert ctx["agent_name"] == ""


def test_form1_leaves_additional_terms_and_signatures_undeclared():
    joined = " ".join(FORM1_SPEC.declared_fields)
    for forbidden in ("signature", "additional_term"):
        assert forbidden not in joined


def test_form1_end_date_before_start_date_not_validated_by_spec(sample_bundle_dict):
    # The spec renders verbatim; date ordering is the caller's responsibility.
    fields = dict(_base_fields(), term_type="fixed", fixed_start_date="2027-01-01", fixed_end_date="2026-01-01")
    ctx = form1_context(_bundle(sample_bundle_dict), fields)
    assert ctx["fixed_start_date"] == "2027-01-01"
    assert ctx["fixed_end_date"] == "2026-01-01"


def test_form1_fill_renders_docx(tmp_path, sample_bundle_dict):
    fields = dict(_base_fields(), term_type="fixed")
    ctx = form1_context(_bundle(sample_bundle_dict), fields)
    docx_path, _, _ = render(FORM1_SPEC, ctx, tmp_path)
    assert docx_path.exists()


# ── Form 2 (residential_rental_agreement_5yr) ───────────────────────────────


def test_form2_context_has_premises_renter_provider(sample_bundle_dict):
    ctx = form2_context(_bundle(sample_bundle_dict), _base_fields())
    assert ctx["premises_address"] == "12 Example Street, Richmond"
    assert ctx["renter1_name"] == "Jane Alice Smith"


def test_form2_has_no_term_type_selector():
    # Form 2 is fixed-term-only; unlike Form 1 it has no periodic option.
    assert "term_type" not in FORM2_SPEC.declared_fields
    assert "term_type" not in FORM2_SPEC.selector_fields


def test_form2_fixed_term_fields_render_verbatim(sample_bundle_dict):
    ctx = form2_context(_bundle(sample_bundle_dict), _base_fields())
    assert ctx["fixed_start_date"] == "2026-08-01"
    assert ctx["fixed_end_date"] == "2027-08-01"


def test_form2_leaves_additional_terms_and_signatures_undeclared():
    joined = " ".join(FORM2_SPEC.declared_fields)
    for forbidden in ("signature", "additional_term"):
        assert forbidden not in joined


def test_form2_fill_renders_docx(tmp_path, sample_bundle_dict):
    ctx = form2_context(_bundle(sample_bundle_dict), _base_fields())
    blanks = compute_blank_fields(FORM2_SPEC, ctx)
    assert "renter1_name" not in blanks
    docx_path, _, _ = render(FORM2_SPEC, ctx, tmp_path)
    assert docx_path.exists()
