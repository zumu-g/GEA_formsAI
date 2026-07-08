import pytest

from forms_fill.errors import SearchUnsupportedError
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


# ── unsupported providers ────────────────────────────────────────────────────


def test_gea_crm_search_raises_unsupported(monkeypatch):
    monkeypatch.setenv("GEA_CRM_BASE_URL", "http://localhost:9")
    monkeypatch.setenv("GEA_CRM_SYNC_SECRET", "x")
    provider = GeaCrmProvider()
    with pytest.raises(SearchUnsupportedError, match="does not support"):
        provider.search_lots("12 Example St")


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
