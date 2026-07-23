import pytest
from fastapi.testclient import TestClient

from forms_fill.api import app

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


def test_ui_page_served_without_auth(client):
    # The static page itself needs no bearer token -- only the data calls it
    # makes (/forms, /fill, /files/...) are protected.
    resp = client.get("/ui/")
    assert resp.status_code == 200
    assert "GEA Forms Fill" in resp.text


def test_ui_page_is_not_browser_cached(client):
    # no-cache forces ETag revalidation so a deploy is never masked by a
    # heuristically-cached stale page.
    assert client.get("/ui/").headers["cache-control"] == "no-cache"


def test_ui_fill_round_trip_matches_direct_api_payload_shape(client, caller_fields):
    # Exercises the exact payload shape the UI's fetch() builds: form, provider,
    # identifiers, fields.
    payload = {
        "form": "cav_rent_increase_notice",
        "provider": "fixture",
        "identifiers": {"lot_id": "L-2002", "tenancy_id": "T-1001"},
        "fields": caller_fields,
    }
    resp = client.post("/fill", json=payload, headers=AUTH)
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["files"]["pdf"] or body["files"]["docx"]


def test_ui_fill_malformed_field_surfaces_api_error_not_blank_download(client):
    payload = {"form": "does_not_exist", "identifiers": {}, "fields": {}}
    resp = client.post("/fill", json=payload, headers=AUTH)
    assert resp.status_code == 400
    body = resp.json()
    assert body["ok"] is False
    assert body["error"] == "invalid_request"


def test_ui_page_contains_lookup_flow_elements(client):
    text = client.get("/ui/").text
    assert 'id="address-query"' in text
    assert 'id="search-results"' in text
    assert 'id="preview"' in text
    assert "/tenancy/search" in text
    assert "/tenancy/preview" in text


def test_ui_page_prefills_rent_fields_from_preview(client):
    text = client.get("/ui/").text
    assert "RENT_PREFILL_FIELDS" in text
    assert "lastPreviewBundle" in text
    assert "prefillRentFields" in text


def test_ui_page_contains_cma_button(client):
    text = client.get("/ui/").text
    assert 'id="cma-btn"' in text
    assert "geastcma-production.up.railway.app" in text
    assert "reportType" in text
    assert "rent-increase" in text
