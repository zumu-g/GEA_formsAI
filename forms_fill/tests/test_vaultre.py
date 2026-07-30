"""VaultRE provider tests (plan 2026-07-30 provider-routing request).

Contract mocked here matches GEA_crmAI's own working client
(src/lib/vaultre/{config,client}.ts) — dual-header auth, GET
/properties/residential/sale, {"items": [...]} envelope — not guessed.
"""

import pytest

from forms_fill.errors import (
    FetchUnsupportedError,
    ProviderConfigError,
    UpstreamError,
)
from forms_fill.providers import vaultre as vr
from forms_fill.providers.base import select_provider
from forms_fill.providers.vaultre import VaultreProvider


class _FakeResp:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


def test_missing_api_key_raises_config_error(monkeypatch):
    monkeypatch.delenv("VAULTRE_API_KEY", raising=False)
    monkeypatch.delenv("VAULTRE_BEARER_TOKEN", raising=False)
    with pytest.raises(ProviderConfigError):
        VaultreProvider()


def test_missing_bearer_token_raises_config_error(monkeypatch):
    monkeypatch.setenv("VAULTRE_API_KEY", "integrator-key")
    monkeypatch.delenv("VAULTRE_BEARER_TOKEN", raising=False)
    with pytest.raises(ProviderConfigError, match="VAULTRE_BEARER_TOKEN"):
        VaultreProvider()


def test_select_provider_routes_to_vaultre(monkeypatch):
    monkeypatch.setenv("VAULTRE_API_KEY", "k")
    monkeypatch.setenv("VAULTRE_BEARER_TOKEN", "t")
    assert select_provider("vaultre").name == "vaultre"


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setenv("VAULTRE_API_KEY", "integrator-key")
    monkeypatch.setenv("VAULTRE_BEARER_TOKEN", "agency-token")
    return VaultreProvider()


def test_search_matches_by_address_substring(provider, monkeypatch):
    payload = {
        "items": [
            {"id": 101, "address": {"streetAddress": "7 Example Ave", "suburb": "Berwick", "state": "VIC", "postcode": "3806"}},
            {"id": 102, "address": {"streetAddress": "9 Other St", "suburb": "Pakenham", "state": "VIC", "postcode": "3810"}},
        ]
    }
    monkeypatch.setattr(vr.httpx, "get", lambda *a, **k: _FakeResp(200, payload))
    matches = provider.search_lots("example ave")
    assert [m.lot_id for m in matches] == ["101"]
    assert "Berwick" in matches[0].address_label


def test_search_sends_dual_header_auth(provider, monkeypatch):
    seen = {}

    def fake_get(url, headers=None, timeout=None):
        seen["headers"] = headers
        return _FakeResp(200, {"items": []})

    monkeypatch.setattr(vr.httpx, "get", fake_get)
    provider.search_lots("anything")
    assert seen["headers"]["X-Api-Key"] == "integrator-key"
    assert seen["headers"]["Authorization"] == "Bearer agency-token"


def test_search_401_raises_config_error(provider, monkeypatch):
    monkeypatch.setattr(vr.httpx, "get", lambda *a, **k: _FakeResp(401, text="nope"))
    with pytest.raises(ProviderConfigError):
        provider.search_lots("x")


def test_search_empty_query_raises_value_error(provider):
    with pytest.raises(ValueError):
        provider.search_lots("  ")


def test_search_5xx_raises_upstream_error(provider, monkeypatch):
    monkeypatch.setattr(vr.httpx, "get", lambda *a, **k: _FakeResp(500, text="boom"))
    with pytest.raises(UpstreamError):
        provider.search_lots("x")


def test_fetch_bundle_raises_fetch_unsupported(provider):
    with pytest.raises(FetchUnsupportedError):
        provider.fetch_bundle({"lot_id": "101"})
