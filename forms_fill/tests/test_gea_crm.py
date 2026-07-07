import copy
import json
from pathlib import Path

import pytest

from forms_fill.errors import (
    ProviderConfigError,
    ProviderContractError,
    TenancyNotFoundError,
    UpstreamError,
)
from forms_fill.providers import gea_crm as gc
from forms_fill.providers.base import select_provider
from forms_fill.providers.gea_crm import GeaCrmProvider

SAMPLE = json.loads(
    (Path(__file__).resolve().parents[1] / "fixtures" / "gea_crm_sample.json").read_text()
)


class _FakeResp:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setenv("GEA_CRM_BASE_URL", "https://crm.example.com")
    monkeypatch.setenv("GEA_CRM_SYNC_SECRET", "s3cret")
    return GeaCrmProvider()


# ── mapping / contract ─────────────────────────────────────────────────────────


def test_maps_sample_one_to_one():
    bundle = GeaCrmProvider._to_bundle(copy.deepcopy(SAMPLE))
    assert bundle.premises.address_line == "8 Acacia Avenue, Brunswick"
    assert [r.full_name for r in bundle.renters] == ["Maria Garcia", "Tom Nguyen"]
    # owner, never agent
    assert bundle.rental_provider.full_name == "Helen Brooks"
    assert bundle.meta.source == "gea_crm"


def test_null_address_for_service_becomes_blank():
    bundle = GeaCrmProvider._to_bundle(copy.deepcopy(SAMPLE))
    assert bundle.renters[0].address_for_service == ""  # null → ""


def test_after_hours_blank_is_expected():
    bundle = GeaCrmProvider._to_bundle(copy.deepcopy(SAMPLE))
    assert bundle.rental_provider.phone_after_hours == ""
    assert all(r.phone_after_hours == "" for r in bundle.renters)


def test_meta_note_logged_and_preserved(caplog):
    data = copy.deepcopy(SAMPLE)
    data["meta"]["note"] = ">1 active lease — most-recently-started returned"
    with caplog.at_level("WARNING"):
        bundle = GeaCrmProvider._to_bundle(data)
    assert bundle.meta.note.startswith(">1 active lease")
    assert any("data-quality note" in r.message for r in caplog.records)


@pytest.mark.parametrize(
    "drop",
    ["premises", "renters", "rental_provider", "meta"],
)
def test_dropped_top_level_key_fails_loudly(drop):
    data = copy.deepcopy(SAMPLE)
    del data[drop]
    with pytest.raises(ProviderContractError):
        GeaCrmProvider._to_bundle(data)


def test_dropped_nested_key_fails_loudly():
    data = copy.deepcopy(SAMPLE)
    del data["premises"]["postcode"]
    with pytest.raises(ProviderContractError):
        GeaCrmProvider._to_bundle(data)

    data = copy.deepcopy(SAMPLE)
    del data["renters"][1]["email"]
    with pytest.raises(ProviderContractError):
        GeaCrmProvider._to_bundle(data)


def test_optional_note_key_absent_is_fine():
    data = copy.deepcopy(SAMPLE)
    del data["meta"]["note"]
    bundle = GeaCrmProvider._to_bundle(data)
    assert bundle.meta.note is None


# ── config / selection ─────────────────────────────────────────────────────────


def test_requires_base_url(monkeypatch):
    monkeypatch.delenv("GEA_CRM_BASE_URL", raising=False)
    monkeypatch.setenv("GEA_CRM_SYNC_SECRET", "x")
    with pytest.raises(ProviderConfigError):
        GeaCrmProvider()


def test_requires_secret(monkeypatch):
    monkeypatch.setenv("GEA_CRM_BASE_URL", "https://crm.example.com")
    monkeypatch.delenv("GEA_CRM_SYNC_SECRET", raising=False)
    with pytest.raises(ProviderConfigError):
        GeaCrmProvider()


def test_factory_selects_gea_crm(monkeypatch):
    monkeypatch.setenv("GEA_CRM_BASE_URL", "https://crm.example.com")
    monkeypatch.setenv("GEA_CRM_SYNC_SECRET", "s3cret")
    assert isinstance(select_provider("gea_crm"), GeaCrmProvider)


# ── HTTP behaviour ─────────────────────────────────────────────────────────────


def test_requires_an_identifier(provider):
    with pytest.raises(TenancyNotFoundError):
        provider.fetch_bundle({})


def test_sends_secret_header_and_prefers_tenancy_id(provider, monkeypatch):
    seen = {}

    def fake_get(url, headers, params, timeout):
        seen["url"] = url
        seen["headers"] = headers
        seen["params"] = params
        return _FakeResp(200, SAMPLE)

    monkeypatch.setattr(gc.httpx, "get", fake_get)
    provider.fetch_bundle({"tenancy_id": "lease_abc123", "lot_id": "mp_xyz789"})
    assert seen["headers"]["x-sync-secret"] == "s3cret"
    assert seen["params"]["tenancyId"] == "lease_abc123"
    assert seen["url"].endswith("/api/forms/tenancy-bundle")


def test_404_is_no_current_tenancy(provider, monkeypatch):
    monkeypatch.setattr(
        gc.httpx, "get",
        lambda *a, **k: _FakeResp(404, {"error": "no active tenancy"}),
    )
    with pytest.raises(TenancyNotFoundError) as exc:
        provider.fetch_bundle({"lot_id": "mp_x"})
    assert "no active tenancy" in str(exc.value)


def test_401_is_config_error(provider, monkeypatch):
    monkeypatch.setattr(gc.httpx, "get", lambda *a, **k: _FakeResp(401, text="nope"))
    with pytest.raises(ProviderConfigError):
        provider.fetch_bundle({"lot_id": "mp_x"})


def test_500_retries_then_raises_upstream(provider, monkeypatch):
    calls = {"n": 0}

    def fake_get(*a, **k):
        calls["n"] += 1
        return _FakeResp(500, text="boom")

    monkeypatch.setattr(gc.httpx, "get", fake_get)
    monkeypatch.setattr(gc.time, "sleep", lambda *_: None)
    with pytest.raises(UpstreamError):
        provider.fetch_bundle({"lot_id": "mp_x"})
    assert calls["n"] == 3  # initial + 2 retries


def test_500_then_success_recovers(provider, monkeypatch):
    seq = [_FakeResp(500, text="boom"), _FakeResp(200, SAMPLE)]

    def fake_get(*a, **k):
        return seq.pop(0)

    monkeypatch.setattr(gc.httpx, "get", fake_get)
    monkeypatch.setattr(gc.time, "sleep", lambda *_: None)
    bundle = provider.fetch_bundle({"lot_id": "mp_x"})
    assert bundle.premises.suburb == "Brunswick"
