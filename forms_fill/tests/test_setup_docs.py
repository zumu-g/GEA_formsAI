from forms_fill.forms.condition_report.spec import SPEC as CONDITION_SPEC
from forms_fill.forms.condition_report.spec import build_context as condition_context
from forms_fill.forms.consent_electronic_service.spec import SPEC as CONSENT_SPEC
from forms_fill.forms.consent_electronic_service.spec import (
    build_context as consent_context,
)
from forms_fill.forms.mandatory_disclosure_checklist.spec import (
    SPEC as MANDATORY_SPEC,
)
from forms_fill.forms.rental_application.spec import SPEC as APPLICATION_SPEC
from forms_fill.forms.rental_application.spec import (
    build_context as application_context,
)
from forms_fill.forms.request_repairs_inspection.spec import SPEC as REPAIRS_SPEC
from forms_fill.forms.request_repairs_inspection.spec import (
    build_context as repairs_context,
)
from forms_fill.forms.statement_of_information_applicants.spec import (
    SPEC as STATEMENT_SPEC,
)
from forms_fill.models import TenancyBundle
from forms_fill.render import compute_blank_fields, render


def _bundle(d):
    return TenancyBundle.model_validate(d)


# ── rental_application ──────────────────────────────────────────────────────


def test_application_prefills_premises_and_provider(sample_bundle_dict):
    ctx = application_context(_bundle(sample_bundle_dict), {"provider_acn": "123", "provider_state": "Victoria"})
    assert ctx["premises_address"] == "12 Example Street, Richmond"
    assert ctx["provider_name"] == "Robert James Owner"
    assert ctx["provider_acn"] == "123"


def test_application_leaves_applicant_sections_undeclared():
    joined = " ".join(APPLICATION_SPEC.declared_fields)
    for forbidden in ("employer", "referee", "signature", "tenancy_database"):
        assert forbidden not in joined


def test_application_fill_renders_docx(tmp_path, sample_bundle_dict):
    ctx = application_context(_bundle(sample_bundle_dict), {})
    docx_path, _, _ = render(APPLICATION_SPEC, ctx, tmp_path)
    assert docx_path.exists()


# ── condition_report ─────────────────────────────────────────────────────────


def test_condition_report_prefills_identity_block(sample_bundle_dict):
    fields = {"report_date": "2026-08-01"}
    ctx = condition_context(_bundle(sample_bundle_dict), fields)
    assert ctx["premises_address"] == "12 Example Street, Richmond"
    assert ctx["renter1_name"] == "Jane Alice Smith"
    assert ctx["report_date"] == "2026-08-01"


def test_condition_report_renter_sections_blank_by_design(sample_bundle_dict):
    ctx = condition_context(_bundle(sample_bundle_dict), {})
    blanks = compute_blank_fields(CONDITION_SPEC, ctx)
    assert "renter3_name" in blanks
    assert "renter4_name" in blanks


def test_condition_report_leaves_room_items_and_signatures_undeclared():
    joined = " ".join(CONDITION_SPEC.declared_fields)
    for forbidden in ("signature", "picture_hook", "floor_covering"):
        assert forbidden not in joined


def test_condition_report_fill_renders_docx(tmp_path, sample_bundle_dict):
    ctx = condition_context(_bundle(sample_bundle_dict), {"report_date": "2026-08-01"})
    docx_path, _, _ = render(CONDITION_SPEC, ctx, tmp_path)
    assert docx_path.exists()


# ── statement_of_information_applicants / mandatory_disclosure_checklist ───


def test_statement_of_information_has_no_declared_fields():
    assert STATEMENT_SPEC.declared_fields == ()


def test_mandatory_disclosure_has_no_declared_fields():
    assert MANDATORY_SPEC.declared_fields == ()


def test_statement_of_information_fill_copies_template(tmp_path, sample_bundle_dict):
    ctx = STATEMENT_SPEC.build_context(_bundle(sample_bundle_dict), {})
    assert ctx == {}
    docx_path, _, _ = render(STATEMENT_SPEC, ctx, tmp_path)
    assert docx_path.exists()


def test_mandatory_disclosure_fill_copies_template(tmp_path, sample_bundle_dict):
    ctx = MANDATORY_SPEC.build_context(_bundle(sample_bundle_dict), {})
    assert ctx == {}
    docx_path, _, _ = render(MANDATORY_SPEC, ctx, tmp_path)
    assert docx_path.exists()


# ── consent_electronic_service ──────────────────────────────────────────────


def test_consent_all_fields_are_caller_supplied(sample_bundle_dict):
    ctx = consent_context(_bundle(sample_bundle_dict), {"provider_contact": "pm@agency.com"})
    assert ctx["provider_contact"] == "pm@agency.com"
    assert ctx["renter1_contact"] == ""
    assert set(CONSENT_SPEC.declared_fields) == {
        "provider_contact",
        "renter1_contact",
        "renter2_contact",
        "renter3_contact",
    }


def test_consent_leaves_signatures_undeclared():
    joined = " ".join(CONSENT_SPEC.declared_fields)
    assert "signature" not in joined


def test_consent_fill_renders_docx(tmp_path, sample_bundle_dict):
    ctx = consent_context(_bundle(sample_bundle_dict), {"provider_contact": "pm@agency.com"})
    docx_path, _, _ = render(CONSENT_SPEC, ctx, tmp_path)
    assert docx_path.exists()


# ── request_repairs_inspection ───────────────────────────────────────────────


def test_repairs_inspection_prefills_renter_and_provider(sample_bundle_dict):
    ctx = repairs_context(_bundle(sample_bundle_dict), {"renter_family_name": "Smith"})
    assert ctx["renter_street_address"] == "PO Box 5, Richmond VIC 3121"
    assert ctx["provider_name"] == "Robert James Owner"
    assert ctx["renter_family_name"] == "Smith"


def test_repairs_inspection_agent_fields_are_caller_supplied(sample_bundle_dict):
    ctx = repairs_context(_bundle(sample_bundle_dict), {})
    assert ctx["agent_name"] == ""
    assert "agent_name" in REPAIRS_SPEC.declared_fields


def test_repairs_inspection_leaves_signature_undeclared():
    joined = " ".join(REPAIRS_SPEC.declared_fields)
    assert "signature" not in joined


def test_repairs_inspection_fill_renders_docx(tmp_path, sample_bundle_dict):
    ctx = repairs_context(_bundle(sample_bundle_dict), {"renter_family_name": "Smith"})
    docx_path, _, _ = render(REPAIRS_SPEC, ctx, tmp_path)
    assert docx_path.exists()
