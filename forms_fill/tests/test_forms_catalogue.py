import pytest
from fastapi.testclient import TestClient

from forms_fill.api import app
from forms_fill.registry import form_catalogue

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


def test_forms_requires_bearer_token(client):
    resp = client.get("/forms")
    assert resp.status_code == 401


def test_forms_lists_registered_forms_with_groups(client):
    resp = client.get("/forms", headers=AUTH)
    assert resp.status_code == 200
    forms = resp.json()["forms"]
    keys = {f["key"] for f in forms}
    assert "cav_rent_increase_notice" in keys
    assert "notice_to_vacate" in keys
    ntv = next(f for f in forms if f["key"] == "notice_to_vacate")
    assert ntv["group"] == "notice_to_vacate"
    field_names = {f["name"] for f in ntv["caller_fields"]}
    assert field_names == {"minimum_notice_days", "termination_date", "reason_for_notice"}


def test_forms_carry_display_category_and_short_title(client):
    forms = client.get("/forms", headers=AUTH).json()["forms"]
    for f in forms:
        assert f["category"] in {"GEA Sales", "GEA PM"}
        assert f["short_title"]
    sales = {f["key"] for f in forms if f["category"] == "GEA Sales"}
    assert sales == {"allmain_letter_of_offer", "reiv_exclusive_sale_authority"}
    rent = next(f for f in forms if f["key"] == "cav_rent_increase_notice")
    assert rent["short_title"] == "Rent increase to renter"
    assert "s 44" not in rent["short_title"]


def test_form_catalogue_helper_matches_endpoint():
    catalogue = form_catalogue()
    assert {c["key"] for c in catalogue} >= {"cav_rent_increase_notice", "notice_to_vacate"}
