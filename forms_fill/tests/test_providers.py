import pytest

from forms_fill.errors import ProviderConfigError
from forms_fill.providers.base import select_provider
from forms_fill.providers.fixture import FixtureProvider
from forms_fill.providers.propertyme import PropertyMeProvider


def test_fixture_provider_returns_full_bundle():
    bundle = FixtureProvider().fetch_bundle({"lot_id": "L-2002"})
    assert bundle.premises.address_line == "12 Example Street, Richmond"
    assert bundle.rental_provider.full_name == "Robert James Owner"
    assert bundle.meta.lot_id == "L-2002"  # echoed from identifiers


def test_fixture_preserves_blank_keys():
    bundle = FixtureProvider().fetch_bundle({})
    second = bundle.renters[1]
    assert second.email == ""  # blank, not missing
    assert hasattr(second, "phone_after_hours")


def test_select_provider_defaults_to_fixture(monkeypatch):
    monkeypatch.delenv("FORMS_DATA_PROVIDER", raising=False)
    assert isinstance(select_provider(), FixtureProvider)


def test_propertyme_requires_api_key(monkeypatch):
    monkeypatch.delenv("PROPERTYME_API_KEY", raising=False)
    with pytest.raises(ProviderConfigError):
        PropertyMeProvider()


def test_propertyme_maps_owner_not_agent():
    raw = {
        "property": {"address": "1 Test St", "postcode": "3000"},
        "tenants": [{"name": "Renter One", "email": ""}],
        "owner": {"name": "Owner Person", "address": "Agency Address"},
        "as_at": "2026-06-17",
    }
    bundle = PropertyMeProvider._to_bundle(raw, {"tenancy_id": "T1"})
    assert bundle.rental_provider.full_name == "Owner Person"
    assert bundle.premises.address_line == "1 Test St"
    assert bundle.meta.tenancy_id == "T1"
