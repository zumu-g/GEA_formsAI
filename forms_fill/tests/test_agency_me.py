"""U1: /agency `me` resolution + agent_acn seeding (lease-flow speed-up plan)."""

import json

import pytest
from fastapi.testclient import TestClient

from forms_fill.api import app

TOKEN = "test-token"
MACHINE = {"Authorization": f"Bearer {TOKEN}"}


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path):
    monkeypatch.setenv("FORMS_API_TOKEN", TOKEN)
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://testserver")
    agency = {
        "agency": {"name": "GEA", "office": "Berwick", "address_line": "3a Gloucester Ave",
                   "suburb": "Berwick", "state": "VIC", "postcode": "3806", "acn": "123 456 789"},
        "agents": [
            {"full_name": "First Agent", "mobile": "0400000001", "email": "first@grantsea.com.au"},
            {"full_name": "Second Agent", "mobile": "0400000002", "email": "second@grantsea.com.au"},
        ],
    }
    path = tmp_path / "agency.json"
    path.write_text(json.dumps(agency))
    monkeypatch.setenv("FORMS_AGENCY_FILE", str(path))


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def _session_for(client, email):
    invite = client.post(
        "/agents/invite", json={"email": email, "name": "X"}, headers=MACHINE
    ).json()
    accept_token = invite["accept_url"].split("#accept=")[1]
    return client.post(
        "/auth/accept", json={"token": accept_token, "password": "s3cret-pass"}
    ).json()["token"]


def test_me_resolves_session_agent_by_email_case_insensitive(client):
    sess = _session_for(client, "Second@grantsea.com.au")  # mixed case on purpose
    body = client.get("/agency", headers={"Authorization": f"Bearer {sess}"}).json()
    assert body["me"]["full_name"] == "Second Agent"


def test_machine_token_has_no_me(client):
    body = client.get("/agency", headers=MACHINE).json()
    assert body.get("me") is None
    assert body["agents"][0]["full_name"] == "First Agent"  # existing default intact


def test_unmatched_session_agent_has_no_me(client):
    sess = _session_for(client, "nobody@grantsea.com.au")
    body = client.get("/agency", headers={"Authorization": f"Bearer {sess}"}).json()
    assert body.get("me") is None


def test_agent_acn_seeds_from_config_and_caller_wins(sample_bundle_dict):
    from forms_fill.forms.residential_rental_agreement.spec import build_context
    from forms_fill.models import TenancyBundle

    bundle = TenancyBundle.model_validate(sample_bundle_dict)
    ctx = build_context(bundle, {})
    assert ctx["agent_acn"] == "123 456 789"  # agency-level fallback (no per-agent acn)
    ctx2 = build_context(bundle, {"agent_acn": "999"})
    assert ctx2["agent_acn"] == "999"
