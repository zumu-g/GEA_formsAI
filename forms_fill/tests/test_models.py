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
