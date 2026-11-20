from forms_fill.forms.residential_rental_agreement.spec import build_context
from forms_fill.models import TenancyBundle


def _ctx(sample_bundle_dict, fields):
    return build_context(TenancyBundle.model_validate(sample_bundle_dict), fields)


def test_emergency_contact_defaults_to_grants_property_maintenance(sample_bundle_dict):
    ctx = _ctx(sample_bundle_dict, {})
    assert ctx["emergency_contact_name"] == "Grants Property Maintenance"
    assert ctx["emergency_phone"] == "0438 100 545"
    assert ctx["emergency_email"] == "propertymanagement@grantsea.com.au"


def test_caller_emergency_phone_wins(sample_bundle_dict):
    ctx = _ctx(sample_bundle_dict, {"emergency_phone": "0399991234"})
    assert ctx["emergency_phone"] == "0399991234"
    assert ctx["emergency_contact_name"] == "Grants Property Maintenance"


def test_payment_methods_and_e_service_email_in_context(sample_bundle_dict):
    ctx = _ctx(sample_bundle_dict, {})
    assert ctx["payment_methods"] == ["bank_transfer", "deft_bpay", "centrepay"]
    assert ctx["provider_e_service_email"] == "propertymanagement@grantsea.com.au"
