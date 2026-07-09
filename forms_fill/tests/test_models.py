import json

import pytest

from forms_fill.models import build_request


def test_split_flags_and_json_produce_identical_request(caller_fields):
    identifiers = {"lot_id": "L-2002", "tenancy_id": "T-1001"}
    from_flags = build_request(
        form="cav_rent_increase_notice",
        identifiers=json.dumps(identifiers),
        fields=json.dumps(caller_fields),
        out_dir="./out",
    )
    from_json = build_request(
        json_payload=json.dumps(
            {
                "form": "cav_rent_increase_notice",
                "identifiers": identifiers,
                "fields": caller_fields,
                "out_dir": "./out",
            }
        )
    )
    assert from_flags == from_json


def test_fields_and_identifiers_stay_separate():
    req = build_request(
        form="f",
        identifiers={"name": "id-value"},
        fields={"name": "field-value"},
    )
    assert req.identifiers["name"] == "id-value"
    assert req.fields["name"] == "field-value"


def test_malformed_json_raises():
    with pytest.raises(ValueError):
        build_request(form="f", identifiers="{not json")


def test_unknown_top_level_key_rejected():
    with pytest.raises(ValueError):
        build_request(json_payload={"form": "f", "bogus": 1})


def test_missing_form_raises():
    with pytest.raises(ValueError):
        build_request(json_payload={"identifiers": {}})


# ── apply_service_address_defaults (U1) ─────────────────────────────────────


def _bundle(sample_bundle_dict, renters_override=None):
    from forms_fill.models import TenancyBundle

    data = dict(sample_bundle_dict)
    if renters_override is not None:
        data = {**data, "renters": renters_override}
    return TenancyBundle.model_validate(data)


def test_blank_service_address_defaults_to_premises(sample_bundle_dict):
    from forms_fill.models import apply_service_address_defaults

    renters = [{"full_name": "Jane Smith"}]  # no address_for_service supplied
    bundle = _bundle(sample_bundle_dict, renters)
    result = apply_service_address_defaults(bundle)
    assert result.renters[0].address_for_service == bundle.premises.address_line
    assert result.renters[0].service_postcode == bundle.premises.postcode


def test_existing_service_address_is_preserved(sample_bundle_dict):
    from forms_fill.models import apply_service_address_defaults

    renters = [
        {
            "full_name": "Jane Smith",
            "address_for_service": "PO Box 5, Richmond VIC 3121",
            "service_postcode": "3121",
        }
    ]
    bundle = _bundle(sample_bundle_dict, renters)
    result = apply_service_address_defaults(bundle)
    assert result.renters[0].address_for_service == "PO Box 5, Richmond VIC 3121"
    assert result.renters[0].service_postcode == "3121"


def test_only_blank_renters_are_defaulted(sample_bundle_dict):
    from forms_fill.models import apply_service_address_defaults

    renters = [
        {"full_name": "Jane Smith"},  # blank -> defaulted
        {"full_name": "John Smith", "address_for_service": "Elsewhere"},  # untouched
    ]
    bundle = _bundle(sample_bundle_dict, renters)
    result = apply_service_address_defaults(bundle)
    assert result.renters[0].address_for_service == bundle.premises.address_line
    assert result.renters[1].address_for_service == "Elsewhere"


def test_no_premises_address_leaves_bundle_unchanged(sample_bundle_dict):
    from forms_fill.models import TenancyBundle, apply_service_address_defaults

    data = dict(sample_bundle_dict)
    data["premises"] = {**data["premises"], "address_line": ""}
    data["renters"] = [{"full_name": "Jane Smith"}]
    bundle = TenancyBundle.model_validate(data)
    result = apply_service_address_defaults(bundle)
    assert result.renters[0].address_for_service == ""


def test_no_change_returns_equivalent_bundle(sample_bundle_dict):
    # All renters already have a service address -> no-op, but still equal.
    from forms_fill.models import apply_service_address_defaults

    renters = [
        {"full_name": "Jane Smith", "address_for_service": "PO Box 5", "service_postcode": "3121"},
        {"full_name": "John Smith", "address_for_service": "PO Box 6", "service_postcode": "3121"},
    ]
    bundle = _bundle(sample_bundle_dict, renters)
    result = apply_service_address_defaults(bundle)
    assert result == bundle
