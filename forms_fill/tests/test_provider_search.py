import time

import httpx
import pytest

from forms_fill.errors import ProviderConfigError, UpstreamError
from forms_fill.providers.base import LotMatch
from forms_fill.providers.fixture import FixtureProvider
from forms_fill.providers.gea_crm import GeaCrmProvider
from forms_fill.providers.propertyme import PropertyMeProvider


# ── fixture provider ─────────────────────────────────────────────────────────


def test_fixture_search_finds_sample_lot():
    matches = FixtureProvider().search_lots("example")
    assert len(matches) == 1
    m = matches[0]
    assert m.lot_id == "L-2002"
    assert m.tenancy_id == "T-1001"
    assert "12 Example Street" in m.address_label


def test_fixture_search_is_case_insensitive():
    assert FixtureProvider().search_lots("EXAMPLE STREET")


def test_fixture_search_no_match_returns_empty():
    assert FixtureProvider().search_lots("zzz nonexistent") == []


def test_fixture_search_empty_query_raises():
    with pytest.raises(ValueError):
        FixtureProvider().search_lots("   ")


# ── gea_crm search (mocked httpx.get, no live call) ─────────────────────────


def _crm(monkeypatch):
    monkeypatch.setenv("GEA_CRM_BASE_URL", "http://localhost:9")
    monkeypatch.setenv("GEA_CRM_SYNC_SECRET", "x")
    return GeaCrmProvider()


class _FakeResponse:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        return self._payload


def test_gea_crm_search_maps_rows(monkeypatch):
    rows = [
        {"lot_id": "L-1", "address_label": "12 Example St, Richmond VIC 3121", "tenancy_id": "T-1"},
        {"lot_id": "L-2", "address_label": "14 Example St, Richmond VIC 3121", "tenancy_id": ""},
    ]
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _FakeResponse(200, rows))
    matches = _crm(monkeypatch).search_lots("example")
    assert matches == [
        LotMatch(lot_id="L-1", address_label="12 Example St, Richmond VIC 3121", tenancy_id="T-1"),
        LotMatch(lot_id="L-2", address_label="14 Example St, Richmond VIC 3121", tenancy_id=""),
    ]


def test_gea_crm_search_caps_results(monkeypatch):
    rows = [
        {"lot_id": f"L-{i}", "address_label": f"{i} Example St", "tenancy_id": ""}
        for i in range(25)
    ]
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _FakeResponse(200, rows))
    assert len(_crm(monkeypatch).search_lots("example")) == 10


def test_gea_crm_search_empty_query_raises(monkeypatch):
    with pytest.raises(ValueError):
        _crm(monkeypatch).search_lots("   ")


def test_gea_crm_search_unauthorised_raises_config_error(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _FakeResponse(401, text="nope"))
    with pytest.raises(ProviderConfigError):
        _crm(monkeypatch).search_lots("example")


def test_gea_crm_search_upstream_5xx_raises_after_retries(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda *_: None)
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _FakeResponse(500, text="boom"))
    with pytest.raises(UpstreamError):
        _crm(monkeypatch).search_lots("example")


def test_gea_crm_search_transport_error_raises_after_retries(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda *_: None)

    def _raise(*a, **k):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx, "get", _raise)
    with pytest.raises(UpstreamError):
        _crm(monkeypatch).search_lots("example")


# ── propertyme mapping (canned response, no live call) ──────────────────────


def _pme(monkeypatch, rows):
    monkeypatch.setenv("PME_CLIENT_ID", "x")
    monkeypatch.setenv("PME_CLIENT_SECRET", "x")
    monkeypatch.setenv("PME_REFRESH_TOKEN", "x")
    provider = PropertyMeProvider()
    provider._get = lambda path, params=None: rows
    return provider


def test_propertyme_search_maps_active_rows(monkeypatch):
    rows = [
        {"Id": "T-1", "LotId": "L-1", "LotAddress": "12 Example Street, Richmond VIC 3121", "IsActive": True, "IsClosed": False},
        {"Id": "T-2", "LotId": "L-2", "LotAddress": "99 Other Road, Kew VIC 3101", "IsActive": True, "IsClosed": False},
        {"Id": "T-3", "LotId": "L-3", "LotAddress": "12 Example Street, Richmond VIC 3121", "IsActive": False, "IsClosed": False},
    ]
    matches = _pme(monkeypatch, rows).search_lots("example street")
    assert matches == [
        LotMatch(lot_id="L-1", address_label="12 Example Street, Richmond VIC 3121", tenancy_id="T-1")
    ]


def test_propertyme_search_caps_results(monkeypatch):
    rows = [
        {"Id": f"T-{i}", "LotId": f"L-{i}", "LotAddress": f"{i} Example Street", "IsActive": True, "IsClosed": False}
        for i in range(25)
    ]
    matches = _pme(monkeypatch, rows).search_lots("example")
    assert len(matches) == 10


def test_propertyme_search_empty_query_raises(monkeypatch):
    with pytest.raises(ValueError):
        _pme(monkeypatch, []).search_lots("")
