import docx

from forms_fill.core import fill_form
from forms_fill.models import FillRequest
from forms_fill.providers.fixture import FixtureProvider


def _all_text(path) -> str:
    document = docx.Document(str(path))
    return " ".join(
        cell.text
        for table in document.tables
        for row in table.rows
        for cell in row.cells
    )


def test_fill_form_happy_path(tmp_path, caller_fields):
    req = FillRequest(
        form="cav_rent_increase_notice",
        identifiers={"lot_id": "L-2002", "tenancy_id": "T-1001"},
        fields=caller_fields,
        out_dir=str(tmp_path),
    )
    result = fill_form(req, provider=FixtureProvider())
    assert result.ok
    assert result.files.docx is not None
    assert len(result.filled_fields) > 0
    assert isinstance(result.blank_fields, list)


def test_caller_values_verbatim_in_output(tmp_path, caller_fields):
    req = FillRequest(
        form="cav_rent_increase_notice",
        identifiers={},
        fields=caller_fields,
        out_dir=str(tmp_path),
    )
    result = fill_form(req, provider=FixtureProvider())
    text = _all_text(result.files.docx)
    assert "615" in text and "650" in text
    assert "2026-09-15" in text  # start date not reformatted


def test_blank_fields_listed_for_missing_value(tmp_path, caller_fields, monkeypatch):
    # Provider whose primary renter has no email.
    import json

    from forms_fill.models import TenancyBundle

    class NoEmailProvider(FixtureProvider):
        def fetch_bundle(self, identifiers):
            data = json.loads(self.path.read_text())
            data["renters"][0]["email"] = ""
            return TenancyBundle.model_validate(data)

    req = FillRequest(
        form="cav_rent_increase_notice",
        identifiers={},
        fields=caller_fields,
        out_dir=str(tmp_path),
    )
    result = fill_form(req, provider=NoEmailProvider())
    assert "renter_email" in result.blank_fields


def test_request_provider_override_selects_named_provider(tmp_path, caller_fields, monkeypatch):
    # No `provider` arg passed to fill_form -- request.provider must drive
    # select_provider() so the API/UI can let the PM choose per request.
    monkeypatch.setenv("FORMS_DATA_PROVIDER", "gea_crm")  # env says gea_crm...
    req = FillRequest(
        form="cav_rent_increase_notice",
        identifiers={"lot_id": "L-2002", "tenancy_id": "T-1001"},
        fields=caller_fields,
        out_dir=str(tmp_path),
        provider="fixture",  # ...but the request explicitly asks for fixture
    )
    result = fill_form(req)
    assert result.ok


def test_blank_renter_service_address_defaults_to_premises(tmp_path, caller_fields):
    # Real-world regression: a PropertyMe tenancy whose primary renter had no
    # ContactPersons service address rendered a blank field instead of
    # defaulting to the premises address (U1 fix).
    import json

    from forms_fill.models import TenancyBundle

    class NoServiceAddressProvider(FixtureProvider):
        def fetch_bundle(self, identifiers):
            data = json.loads(self.path.read_text())
            data["renters"][0]["address_for_service"] = ""
            data["renters"][0]["service_postcode"] = ""
            return TenancyBundle.model_validate(data)

    req = FillRequest(
        form="cav_rent_increase_notice",
        identifiers={},
        fields=caller_fields,
        out_dir=str(tmp_path),
    )
    result = fill_form(req, provider=NoServiceAddressProvider())
    assert "renter_service_address" not in result.blank_fields
    text = _all_text(result.files.docx)
    assert "12 Example Street, Richmond" in text


def test_unknown_form_raises(tmp_path, caller_fields):
    import pytest

    from forms_fill.errors import UnknownFormError

    req = FillRequest(form="nope", identifiers={}, fields=caller_fields, out_dir=str(tmp_path))
    with pytest.raises(UnknownFormError):
        fill_form(req, provider=FixtureProvider())
