import httpx
import pytest

from forms_fill.errors import (
    ProviderConfigError,
    TenancyNotFoundError,
    UpstreamError,
)
from forms_fill.providers.base import select_provider
from forms_fill.providers.fixture import FixtureProvider
from forms_fill.providers.propertyme import PropertyMeProvider, _parse_address


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


# ── PropertyMe (live-API shape, network mocked at the _get seam) ────────────────


def _provider() -> PropertyMeProvider:
    return PropertyMeProvider(
        client_id="cid", client_secret="cs", refresh_token="rt"
    )


TENANCY = {
    "Id": "T1",
    "LotId": "L1",
    "ContactId": "C-TEN",
    "Name": "Jane Smith & John Smith",
    "ContactPhone": "0400 000 000",
    "ContactEmail": "jane@example.com",
    "IsActive": True,
    "IsClosed": False,
    "TenancyStart": "2025-01-01",
    "LotAddress": "1 Test St, Berwick VIC 3806",
}


def _routes(persons, owner_body=None, tenancies=None):
    owner_body = owner_body or {
        "Contact": {
            "NameText": "Robert Owner & Mary Owner",
            "PostalAddressText": "PO Box 9, Berwick VIC 3806",
            "WorkPhone": "03 9000 1111",
            "Email": "owners@example.com",
        }
    }
    return {
        "/v1/tenancies": tenancies if tenancies is not None else [TENANCY],
        "/v1/lots/L1/detail": {
            "AddressText": "1 Test St, Berwick VIC 3806",
            "Ownership": {"ContactId": "C-OWN", "FirstName": "Robert", "LastName": "Owner"},
        },
        "/v1/contacts/C-TEN": {"Contact": {"ContactPersons": persons}},
        "/v1/contacts/C-OWN": owner_body,
    }


def _patch_get(monkeypatch, routes):
    def fake_get(self, path, params=None):
        return routes[path]

    monkeypatch.setattr(PropertyMeProvider, "_get", fake_get)


def test_propertyme_requires_credentials(monkeypatch):
    for var in ("PME_CLIENT_ID", "PME_CLIENT_SECRET", "PME_REFRESH_TOKEN", "PME_TOKEN_FILE"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(ProviderConfigError):
        PropertyMeProvider()


def test_propertyme_maps_owner_not_agent(monkeypatch):
    persons = [
        {"FullName": "Jane Smith", "IsPrimary": True, "Email": "jane@example.com",
         "WorkPhone": "03 9000 0000", "HomePhone": "03 9000 0001"},
        {"FullName": "John Smith", "IsPrimary": False, "SortOrder": 1},
    ]
    _patch_get(monkeypatch, _routes(persons))
    bundle = _provider().fetch_bundle({"lot_id": "L1"})
    # owner name comes from the Ownership contact, never the agency
    assert bundle.rental_provider.full_name == "Robert Owner & Mary Owner"
    assert bundle.rental_provider.service_postcode == "3806"
    assert bundle.renters[0].full_name == "Jane Smith"
    assert bundle.renters[1].full_name == "John Smith"
    assert bundle.premises.postcode == "3806"
    assert bundle.premises.state == "VIC"
    assert bundle.meta.tenancy_id == "T1"
    assert bundle.meta.note is None


def test_propertyme_missing_ownership_fails_loud(monkeypatch):
    routes = _routes([])
    routes["/v1/lots/L1/detail"] = {"AddressText": "1 Test St", "Ownership": {}}
    _patch_get(monkeypatch, routes)
    with pytest.raises(TenancyNotFoundError, match="ownership"):
        _provider().fetch_bundle({"lot_id": "L1"})


def test_propertyme_caps_renters_at_four(monkeypatch):
    persons = [{"FullName": f"Renter {i}", "SortOrder": i} for i in range(6)]
    _patch_get(monkeypatch, _routes(persons))
    bundle = _provider().fetch_bundle({"lot_id": "L1"})
    assert len(bundle.renters) == 4


def test_propertyme_multiple_active_tenancies_warns(monkeypatch):
    t2 = {**TENANCY, "Id": "T2", "TenancyStart": "2026-01-01"}
    _patch_get(monkeypatch, _routes([], tenancies=[TENANCY, t2]))
    bundle = _provider().fetch_bundle({"lot_id": "L1"})
    assert bundle.meta.tenancy_id == "T2"  # most recent wins
    assert "most-recent" in (bundle.meta.note or "")


def test_propertyme_no_tenancy_raises(monkeypatch):
    _patch_get(monkeypatch, _routes([], tenancies=[]))
    with pytest.raises(TenancyNotFoundError):
        _provider().fetch_bundle({"lot_id": "L1"})


def test_propertyme_tenancy_id_filter(monkeypatch):
    other = {**TENANCY, "Id": "T9"}
    _patch_get(monkeypatch, _routes([], tenancies=[TENANCY, other]))
    bundle = _provider().fetch_bundle({"tenancy_id": "T9"})
    assert bundle.meta.tenancy_id == "T9"


def test_propertyme_network_error_is_upstream(monkeypatch):
    def boom(url, **kwargs):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(httpx, "get", boom)
    p = _provider()
    p._access_token, p._expires_at = "tok", 9e12  # skip refresh
    with pytest.raises(UpstreamError):
        p.fetch_bundle({"lot_id": "L1"})


def test_propertyme_rotated_refresh_token_persists(monkeypatch, tmp_path):
    tok_file = tmp_path / "tokens.json"
    tok_file.write_text('{"refresh_token": "old-rt"}')

    def fake_post(url, data=None, **kwargs):
        return httpx.Response(
            200,
            json={"access_token": "at", "expires_in": 3600, "refresh_token": "new-rt"},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    p = PropertyMeProvider(client_id="cid", client_secret="cs", token_file=str(tok_file))
    p._refresh()
    assert p.refresh_token == "new-rt"
    assert '"new-rt"' in tok_file.read_text()
    # second refresh uses the rotated token without error
    p._refresh()
    assert p.refresh_token == "new-rt"


def test_parse_address_splits_state_postcode():
    prem = _parse_address("Unit 2/10 High St, Narre Warren VIC 3805")
    assert prem.suburb == "Narre Warren"
    assert prem.state == "VIC"
    assert prem.postcode == "3805"
    unparsed = _parse_address("weird address")
    assert unparsed.address_line == "weird address"
    assert unparsed.postcode == ""


def test_propertyme_inactive_only_tenancy_is_not_found(monkeypatch):
    vacated = {**TENANCY, "IsActive": False}
    _patch_get(monkeypatch, _routes([], tenancies=[vacated]))
    with pytest.raises(TenancyNotFoundError):
        _provider().fetch_bundle({"lot_id": "L1"})


# ── rent prefill mapping (U2) ────────────────────────────────────────────────


def test_propertyme_maps_rent_amount_and_period(monkeypatch):
    tenancy = {**TENANCY, "RentAmount": 2607.0, "RentPeriod": "monthly"}
    _patch_get(monkeypatch, _routes([], tenancies=[tenancy]))
    bundle = _provider().fetch_bundle({"lot_id": "L1"})
    assert bundle.current_rent == "2607"  # not "2607.0"
    assert bundle.rent_period == "monthly"


def test_propertyme_missing_rent_amount_is_blank(monkeypatch):
    _patch_get(monkeypatch, _routes([], tenancies=[TENANCY]))  # no RentAmount key
    bundle = _provider().fetch_bundle({"lot_id": "L1"})
    assert bundle.current_rent == ""
    assert bundle.rent_period == ""


def test_propertyme_non_integer_rent_amount_preserved(monkeypatch):
    tenancy = {**TENANCY, "RentAmount": 615.5, "RentPeriod": "weekly"}
    _patch_get(monkeypatch, _routes([], tenancies=[tenancy]))
    bundle = _provider().fetch_bundle({"lot_id": "L1"})
    assert bundle.current_rent == "615.5"


def test_fixture_provider_returns_current_rent():
    bundle = FixtureProvider().fetch_bundle({"lot_id": "L-2002"})
    assert bundle.current_rent == "615"
    assert bundle.rent_period == "week"
