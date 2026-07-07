from forms_fill.forms.cav_rent_increase_notice.spec import (
    SPEC,
    build_context,
    normalise_period,
)
from forms_fill.models import TenancyBundle


def _bundle(d):
    return TenancyBundle.model_validate(d)


def test_context_has_premises_renter_provider(sample_bundle_dict, caller_fields):
    ctx = build_context(_bundle(sample_bundle_dict), caller_fields)
    assert ctx["premises_address"] == "12 Example Street, Richmond"
    assert ctx["renter1_name"] == "Jane Alice Smith"
    assert ctx["renter2_name"] == "John Peter Smith"
    assert ctx["provider_name"] == "Robert James Owner"


def test_caller_fields_render_verbatim(sample_bundle_dict, caller_fields):
    ctx = build_context(_bundle(sample_bundle_dict), caller_fields)
    assert ctx["current_rent"] == "615"
    assert ctx["new_rent"] == "650"
    assert ctx["start_date"] == "2026-09-15"
    assert ctx["method_basis"] == "market comparison (rental CMA)"


def test_period_normalisation():
    assert normalise_period("weekly") == "week"
    assert normalise_period("monthly") == "calendar month"
    assert normalise_period("fortnightly") == "fortnight"


def test_leave_blank_fields_not_declared():
    # R7: delivery/signature-date/investigation are never declared.
    joined = " ".join(SPEC.declared_fields)
    for forbidden in ("delivery", "signature", "investigation", "tracking"):
        assert forbidden not in joined


def test_overflow_note_for_more_than_four_renters(sample_bundle_dict, caller_fields):
    renters = [
        {"full_name": f"Renter {i}"} for i in range(1, 6)
    ]
    sample_bundle_dict["renters"] = renters
    ctx = build_context(_bundle(sample_bundle_dict), caller_fields)
    assert ctx["renter1_name"] == "Renter 1"
    assert "extra page" in ctx["renter4_name"]
    assert "Renter 5" in ctx["renter4_name"]
