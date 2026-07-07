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
