import pytest

from forms_fill.forms.notice_to_vacate.spec import SPEC, build_context
from forms_fill.models import TenancyBundle

GROUNDS = (
    "sale_of_premises",
    "owner_or_family_moving_in",
    "repairs_or_renovations",
    "demolition",
    "change_of_use",
)


def _bundle(d):
    return TenancyBundle.model_validate(d)


@pytest.fixture
def ntv_caller_fields():
    return {
        "minimum_notice_days": "90",
        "termination_date": "2026-10-15",
        "reason_for_notice": "The property is being sold (s 263).",
    }


def test_context_has_premises_renter_provider(sample_bundle_dict, ntv_caller_fields):
    ctx = build_context(_bundle(sample_bundle_dict), ntv_caller_fields)
    assert ctx["premises_address"] == "12 Example Street, Richmond"
    assert ctx["renter1_name"] == "Jane Alice Smith"
    assert ctx["provider_name"] == "Robert James Owner"


@pytest.mark.parametrize("ground", GROUNDS)
def test_caller_fields_render_verbatim_for_each_ground(sample_bundle_dict, ground):
    fields = {
        "minimum_notice_days": "90",
        "termination_date": "2026-10-15",
        "reason_for_notice": f"Ground: {ground} (s 263-267).",
    }
    ctx = build_context(_bundle(sample_bundle_dict), fields)
    assert ctx["minimum_notice_days"] == "90"
    assert ctx["termination_date"] == "2026-10-15"
    assert ctx["reason_for_notice"] == f"Ground: {ground} (s 263-267)."


def test_giving_capacity_always_rental_provider(sample_bundle_dict, ntv_caller_fields):
    # GEA never serves as mortgagee; the selector must always resolve to the
    # rental-provider checkbox, regardless of caller input.
    ctx = build_context(_bundle(sample_bundle_dict), ntv_caller_fields)
    assert ctx["giving_capacity"] == "rental_provider"
    assert "giving_capacity" not in SPEC.declared_fields  # selector, not text field


def test_missing_caller_field_renders_blank_not_guessed(sample_bundle_dict):
    ctx = build_context(_bundle(sample_bundle_dict), {})
    assert ctx["minimum_notice_days"] == ""
    assert ctx["termination_date"] == ""
    assert ctx["reason_for_notice"] == ""


def test_leave_delivery_and_signature_fields_not_declared():
    # Mirrors the rent-increase spec's R7: manual-service sections are never
    # declared, so the renderer never touches them.
    joined = " ".join(SPEC.declared_fields)
    for forbidden in ("delivery", "signature", "tracking"):
        assert forbidden not in joined


def test_overflow_note_for_more_than_four_renters(sample_bundle_dict, ntv_caller_fields):
    renters = [{"full_name": f"Renter {i}"} for i in range(1, 6)]
    sample_bundle_dict["renters"] = renters
    ctx = build_context(_bundle(sample_bundle_dict), ntv_caller_fields)
    assert ctx["renter1_name"] == "Renter 1"
    assert "extra page" in ctx["renter4_name"]
    assert "Renter 5" in ctx["renter4_name"]
