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
    assert "GEA — Forms Fill" in resp.text  # <title> — hero shows just "Forms Fill"


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


# ── U7: field kinds + sections ───────────────────────────────────────────────


def test_ui_page_renders_per_field_fetch_button(client):
    text = client.get("/ui/").text
    assert "fetch-btn" in text
    assert "forceFetchField" in text
    assert "FETCHABLE_FIELD_NAMES" in text


def test_ui_page_renders_date_and_select_kinds(client):
    text = client.get("/ui/").text
    assert "kind === 'date'" in text
    assert "kind === 'select'" in text
    assert "kind === 'checkbox'" in text
    assert "field-section-title" in text


# ── U8: review screen ─────────────────────────────────────────────────────────


def test_ui_page_contains_review_screen_elements(client):
    text = client.get("/ui/").text
    assert 'id="review-screen"' in text
    assert 'id="review-rows"' in text
    assert 'id="review-confirm-check"' in text
    assert 'id="review-confirm-btn"' in text


def test_ui_submit_shows_review_before_posting_fill(client):
    # The submit handler must call showReviewScreen(), not POST /fill directly
    # — the actual POST only fires from the review-confirm button (R11).
    text = client.get("/ui/").text
    submit_handler = text.split("form.addEventListener('submit'")[1].split("});")[0]
    assert "showReviewScreen" in submit_handler
    assert "/fill" not in submit_handler
    assert "reviewConfirmBtn.addEventListener('click'" in text


def test_ui_review_confirm_disabled_until_checkbox_ticked(client):
    text = client.get("/ui/").text
    assert "reviewConfirmBtn.disabled = !reviewConfirmCheck.checked" in text


# ── U9: approval ──────────────────────────────────────────────────────────────


def test_ui_page_contains_approval_elements(client):
    text = client.get("/ui/").text
    assert 'id="approve-box"' in text
    assert 'id="approve-name"' in text
    assert 'id="approve-token"' in text
    assert 'id="approve-btn"' in text
    assert "/approve/" in text


def test_ui_approval_uses_separate_credential_not_generation_token(client):
    text = client.get("/ui/").text
    approve_handler = text.split("document.getElementById('approve-btn').addEventListener")[1].split("});")[0]
    # The actual fetch() call must build its Authorization header from the
    # approval-credential input, never from authHeaders() (the stored
    # generation token) — KTD6. Scope to the fetch(...) call itself so the
    # explanatory comment mentioning authHeaders() doesn't trip this.
    fetch_call = approve_handler.split("fetch(")[1].split(");")[0]
    assert "authHeaders()" not in fetch_call
    assert "approveToken" in fetch_call
    assert "approve-token" in approve_handler
