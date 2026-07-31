import docx
import pytest
from fastapi.testclient import TestClient

from forms_fill.api import OUTPUT_ROOT, app

TOKEN = "test-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("FORMS_API_TOKEN", TOKEN)
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://testserver")


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def _fill(client, caller_fields, **overrides):
    payload = {
        "form": "cav_rent_increase_notice",
        "identifiers": {"lot_id": "L-2002"},
        "fields": caller_fields,
    }
    payload.update(overrides)
    return client.post("/fill", json=payload, headers=AUTH)


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_startup_fails_closed_without_token(monkeypatch):
    monkeypatch.delenv("FORMS_API_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="FORMS_API_TOKEN"):
        with TestClient(app):
            pass


def test_startup_fails_closed_without_base_url(monkeypatch):
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="PUBLIC_BASE_URL"):
        with TestClient(app):
            pass


def test_fill_requires_bearer_token(client, caller_fields):
    resp = client.post("/fill", json={"form": "cav_rent_increase_notice", "fields": caller_fields})
    assert resp.status_code == 401
    body = resp.json()
    assert body["ok"] is False
    assert body["error"] == "unauthorized"

    wrong = client.post(
        "/fill",
        json={"form": "cav_rent_increase_notice", "fields": caller_fields},
        headers={"Authorization": "Bearer nope"},
    )
    assert wrong.status_code == 401


def test_agency_requires_bearer_token(client):
    assert client.get("/agency").status_code == 401


def test_agency_returns_office_and_agents(client):
    body = client.get("/agency", headers=AUTH).json()
    assert "Grants Estate Agents" in body["office"]["name"]
    assert body["agents"][0]["full_name"] == "Stuart Grant"


def test_files_require_bearer_token(client, caller_fields):
    body = _fill(client, caller_fields).json()
    url = body["files"]["docx"]
    assert client.get(url).status_code == 401
    assert client.get(url, headers=AUTH).status_code == 200


def test_post_fill_returns_contract_shape(client, caller_fields):
    resp = _fill(client, caller_fields)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    # filled_fields is a list of field names (engine contract)
    assert isinstance(body["filled_fields"], list)
    assert len(body["filled_fields"]) > 0
    assert all(isinstance(f, str) for f in body["filled_fields"])
    # files are absolute URLs
    assert body["files"]["docx"].startswith("http://testserver/files/")

    fetched = client.get(body["files"]["docx"], headers=AUTH)
    assert fetched.status_code == 200
    assert len(fetched.content) > 0


def test_post_fill_unknown_form_is_machine_coded_400(client, caller_fields):
    resp = _fill(client, caller_fields, form="bogus")
    assert resp.status_code == 400
    body = resp.json()
    assert body["ok"] is False
    assert body["error"] == "invalid_request"


def test_no_tenancy_maps_to_machine_code(client, caller_fields, monkeypatch):
    from forms_fill import api as api_mod
    from forms_fill.errors import TenancyNotFoundError

    def boom(request, provider=None):
        raise TenancyNotFoundError("no current tenancy")

    monkeypatch.setattr(api_mod, "fill_form", boom)
    resp = _fill(client, caller_fields)
    assert resp.status_code == 404
    assert resp.json()["error"] == "no_current_tenancy"


def test_upstream_maps_to_fetch_failed(client, caller_fields, monkeypatch):
    from forms_fill import api as api_mod
    from forms_fill.errors import UpstreamError

    def boom(request, provider=None):
        raise UpstreamError("propertyme 503")

    monkeypatch.setattr(api_mod, "fill_form", boom)
    resp = _fill(client, caller_fields)
    assert resp.status_code == 502
    assert resp.json()["error"] == "fetch_failed"


def test_cli_and_api_produce_same_text(client, caller_fields, tmp_path):
    body = _fill(client, caller_fields).json()
    api_out = OUTPUT_ROOT / body["request_id"]
    api_file = next(api_out.glob("*.docx"))

    from forms_fill.core import fill_form
    from forms_fill.models import FillRequest
    from forms_fill.providers.fixture import FixtureProvider

    req = FillRequest(
        form="cav_rent_increase_notice",
        identifiers={"lot_id": "L-2002"},
        fields=caller_fields,
        out_dir=str(tmp_path),
    )
    result = fill_form(req, provider=FixtureProvider())

    def text(p):
        d = docx.Document(str(p))
        return " ".join(c.text for t in d.tables for r in t.rows for c in r.cells)

    assert text(api_file) == text(result.files.docx)


# ── /tenancy/search and /tenancy/preview (U2) ────────────────────────────────


def test_tenancy_search_requires_auth(client):
    assert client.get("/tenancy/search?q=example").status_code == 401


def test_tenancy_preview_requires_auth(client):
    assert client.get("/tenancy/preview?lot_id=L-2002").status_code == 401


def test_tenancy_search_fixture_happy_path(client):
    resp = client.get("/tenancy/search?q=example&provider=fixture", headers=AUTH)
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "fixture"
    assert body["matches"][0]["lot_id"] == "L-2002"
    assert "12 Example Street" in body["matches"][0]["address_label"]


def test_tenancy_search_empty_query_rejected(client):
    resp = client.get("/tenancy/search?q=  &provider=fixture", headers=AUTH)
    assert resp.status_code == 400
    assert resp.json()["error"] == "invalid_request"


def test_tenancy_search_gea_crm_happy_path(client, monkeypatch):
    import httpx

    monkeypatch.setenv("GEA_CRM_BASE_URL", "http://localhost:9")
    monkeypatch.setenv("GEA_CRM_SYNC_SECRET", "x")

    class _FakeResponse:
        status_code = 200

        def json(self):
            return [{"lot_id": "L-1", "address_label": "12 Example St", "tenancy_id": "T-1"}]

    monkeypatch.setattr(httpx, "get", lambda *a, **k: _FakeResponse())
    resp = client.get("/tenancy/search?q=example&provider=gea_crm", headers=AUTH)
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "gea_crm"
    assert body["matches"] == [
        {"lot_id": "L-1", "address_label": "12 Example St", "tenancy_id": "T-1"}
    ]


def test_tenancy_search_gea_crm_empty_query_rejected(client, monkeypatch):
    monkeypatch.setenv("GEA_CRM_BASE_URL", "http://localhost:9")
    monkeypatch.setenv("GEA_CRM_SYNC_SECRET", "x")
    resp = client.get("/tenancy/search?q=  &provider=gea_crm", headers=AUTH)
    assert resp.status_code == 400
    assert resp.json()["error"] == "invalid_request"


def test_tenancy_preview_happy_path(client):
    resp = client.get("/tenancy/preview?lot_id=L-2002&provider=fixture", headers=AUTH)
    assert resp.status_code == 200
    bundle = resp.json()["bundle"]
    assert bundle["premises"]["address_line"] == "12 Example Street, Richmond"
    assert bundle["renters"][0]["full_name"] == "Jane Alice Smith"
    assert bundle["rental_provider"]["full_name"] == "Robert James Owner"


def test_tenancy_preview_requires_an_identifier(client):
    resp = client.get("/tenancy/preview?provider=fixture", headers=AUTH)
    assert resp.status_code == 400


def test_tenancy_preview_defaults_blank_service_address_to_premises(client, monkeypatch):
    # U1: /tenancy/preview must show the same defaulted value the eventual
    # fill will render — no preview/fill divergence.
    import json

    from forms_fill.providers import fixture as fixture_module

    original_read = fixture_module.Path.read_text

    def patched_read(self, *a, **kw):
        text = original_read(self, *a, **kw)
        if self.name == "sample_tenancy.json":
            data = json.loads(text)
            data["renters"][0]["address_for_service"] = ""
            data["renters"][0]["service_postcode"] = ""
            return json.dumps(data)
        return text

    monkeypatch.setattr(fixture_module.Path, "read_text", patched_read)
    resp = client.get("/tenancy/preview?lot_id=L-2002&provider=fixture", headers=AUTH)
    assert resp.status_code == 200
    bundle = resp.json()["bundle"]
    assert bundle["renters"][0]["address_for_service"] == bundle["premises"]["address_line"]


# ── listing mode pass-through (U3, plan 2026-07-31 property-autopopulate) ──────


def test_tenancy_search_invalid_listing_rejected(client):
    resp = client.get("/tenancy/search?q=example&provider=fixture&listing=banana", headers=AUTH)
    assert resp.status_code == 400
    assert resp.json()["error"] == "invalid_request"


def test_tenancy_preview_invalid_listing_rejected(client):
    resp = client.get("/tenancy/preview?lot_id=L-2002&provider=fixture&listing=banana", headers=AUTH)
    assert resp.status_code == 400
    assert resp.json()["error"] == "invalid_request"


def test_tenancy_search_listing_reaches_provider(client, monkeypatch):
    from forms_fill.providers import base as base_module
    from forms_fill.providers.base import LotMatch, PropertyDataProvider

    seen = {}

    class _Spy(PropertyDataProvider):
        name = "spy"

        def fetch_bundle(self, identifiers):
            raise AssertionError("not used")

        def search_lots(self, query, listing="sale"):
            seen["listing"] = listing
            return [LotMatch(lot_id="L-9", address_label="9 Spy St")]

    monkeypatch.setattr(base_module, "select_provider", lambda name=None: _Spy())
    monkeypatch.setattr("forms_fill.providers.base.select_provider", lambda name=None: _Spy())
    resp = client.get("/tenancy/search?q=spy&listing=lease", headers=AUTH)
    assert resp.status_code == 200
    assert seen["listing"] == "lease"


def test_tenancy_preview_lease_listing_reaches_identifiers(client, monkeypatch):
    from forms_fill.models import TenancyBundle
    from forms_fill.providers import base as base_module
    from forms_fill.providers.base import PropertyDataProvider

    seen = {}

    class _Spy(PropertyDataProvider):
        name = "spy"

        def fetch_bundle(self, identifiers):
            seen["identifiers"] = identifiers
            return TenancyBundle()

    monkeypatch.setattr("forms_fill.providers.base.select_provider", lambda name=None: _Spy())
    resp = client.get("/tenancy/preview?lot_id=7&listing=lease", headers=AUTH)
    assert resp.status_code == 200
    assert seen["identifiers"]["listing"] == "lease"


def test_tenancy_preview_default_listing_absent_from_identifiers(client, monkeypatch):
    from forms_fill.models import TenancyBundle
    from forms_fill.providers.base import PropertyDataProvider

    seen = {}

    class _Spy(PropertyDataProvider):
        name = "spy"

        def fetch_bundle(self, identifiers):
            seen["identifiers"] = identifiers
            return TenancyBundle()

    monkeypatch.setattr("forms_fill.providers.base.select_provider", lambda name=None: _Spy())
    resp = client.get("/tenancy/preview?lot_id=7", headers=AUTH)
    assert resp.status_code == 200
    assert "listing" not in seen["identifiers"]
