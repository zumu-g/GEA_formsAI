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
        assert f["category"] in {"GEA Sales", "GEA PM", "Notices", "Bond"}
        assert f["short_title"]
    sales = {f["key"] for f in forms if f["category"] == "GEA Sales"}
    assert sales == {"reiv_exclusive_sale_authority"}
    bond = {f["key"] for f in forms if f["category"] == "Bond"}
    assert bond == {"notice_requesting_additional_bond"}
    notices = {f["key"] for f in forms if f["category"] == "Notices"}
    assert "notice_to_vacate" in notices and "cav_rent_increase_notice" in notices
    rent = next(f for f in forms if f["key"] == "cav_rent_increase_notice")
    assert rent["short_title"] == "Rent increase to renter"
    assert "s 44" not in rent["short_title"]


def test_form_catalogue_helper_matches_endpoint():
    catalogue = form_catalogue()
    assert {c["key"] for c in catalogue} >= {"cav_rent_increase_notice", "notice_to_vacate"}


# ── U7: field kind/section metadata ─────────────────────────────────────────


def test_declaring_form_publishes_kind_and_section(client):
    forms = client.get("/forms", headers=AUTH).json()["forms"]
    agreement = next(f for f in forms if f["key"] == "residential_rental_agreement")
    by_name = {f["name"]: f for f in agreement["caller_fields"]}
    assert by_name["agreement_date"]["kind"] == "date"
    assert by_name["agreement_date"]["section"] == "1. Date of agreement"
    assert by_name["is_renewal"]["kind"] == "checkbox"


def test_non_declaring_form_falls_back_to_current_behaviour(client):
    forms = client.get("/forms", headers=AUTH).json()["forms"]
    ntv = next(f for f in forms if f["key"] == "notice_to_vacate")
    for f in ntv["caller_fields"]:
        assert f["kind"] == "text"
        assert f["section"] == ""


def test_selector_field_with_checkbox_ops_still_publishes_its_options():
    catalogue = form_catalogue()
    agreement = next(c for c in catalogue if c["key"] == "residential_rental_agreement")
    by_name = {f["name"]: f for f in agreement["caller_fields"]}
    assert by_name["term_type"]["kind"] == "select"
    assert sorted(by_name["term_type"]["options"]) == ["fixed", "periodic"]
    assert sorted(by_name["rent_period"]["options"]) == ["calendar month", "fortnight", "week"]


def test_agreement_fields_group_under_form_sections_in_order():
    catalogue = form_catalogue()
    agreement = next(c for c in catalogue if c["key"] == "residential_rental_agreement")
    sections = [f["section"] for f in agreement["caller_fields"]]
    assert "3. Rental provider & agent" in sections
    assert "6. Rent" in sections
    assert "10. Urgent repairs contact" in sections
