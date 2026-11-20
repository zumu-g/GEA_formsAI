import logging

import httpx
import pytest
from fastapi.testclient import TestClient

from forms_fill import accounts
from forms_fill.api import app
from forms_fill.errors import ApplicationAiError
from forms_fill.providers import applicationai

ADDR = "12 Example Street Berwick"
ROW = {
    "id": "a1", "address": ADDR, "applicantName": "Jo Renter",
    "applicantPhone": "0400111222", "applicantEmail": "jo@example.com",
    "proposedLeaseStart": "2026-12-01", "weeklyRent": 550,
}


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path):
    monkeypatch.setenv("FORMS_API_TOKEN", "machine-token")
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://testserver")
    monkeypatch.setenv("FORMS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("APPLICATIONAI_BASE_URL", "http://ai.test")
    monkeypatch.setenv("APPLICATIONAI_AGENT_TOKEN", "ai-secret")
    monkeypatch.setattr(applicationai.time, "sleep", lambda s: None)


def _mock(monkeypatch, handler):
    real = httpx.Client
    monkeypatch.setattr(
        applicationai.httpx, "Client",
        lambda **kw: real(transport=httpx.MockTransport(handler), **kw),
    )


def test_maps_one_application_and_sends_headers(monkeypatch):
    seen = {}

    def handler(req):
        seen["auth"] = req.headers["authorization"]
        seen["agent"] = req.headers["x-acting-agent"]
        seen["path"] = req.url.path
        seen["q"] = req.url.params["propertyAddress"]
        return httpx.Response(200, json={"applications": [ROW]})

    _mock(monkeypatch, handler)
    out = applicationai.search_by_address(ADDR, "pm@grantsea.com.au")
    assert out == [{
        "id": "a1", "address": ADDR, "renter1_name": "Jo Renter",
        "renter1_phone": "0400111222", "renter1_email": "jo@example.com",
        "proposed_lease_start": "2026-12-01", "weekly_rent": 550,
    }]
    assert seen == {"auth": "Bearer ai-secret", "agent": "pm@grantsea.com.au",
                    "path": "/api/agent/v1/lease-handoff", "q": ADDR}


def test_timeout_then_success_retries_once(monkeypatch):
    calls = []

    def handler(req):
        calls.append(1)
        if len(calls) == 1:
            raise httpx.ReadTimeout("slow", request=req)
        return httpx.Response(200, json={"applications": []})

    _mock(monkeypatch, handler)
    assert applicationai.search_by_address(ADDR, "a@b.c") == []
    assert len(calls) == 2


def test_timeout_twice_raises_upstream_code(monkeypatch):
    calls = []

    def handler(req):
        calls.append(1)
        raise httpx.ConnectError("down", request=req)

    _mock(monkeypatch, handler)
    with pytest.raises(ApplicationAiError) as ei:
        applicationai.search_by_address(ADDR, "a@b.c")
    assert ei.value.code == "applicationai_unavailable"
    assert len(calls) == 2


def test_no_pii_in_logs_on_upstream_failure(monkeypatch, caplog):
    _mock(monkeypatch, lambda req: httpx.Response(500, text="0400111222 jo@example.com"))
    with caplog.at_level(logging.DEBUG):
        with pytest.raises(ApplicationAiError):
            applicationai.search_by_address(ADDR, "pm@grantsea.com.au")
    text = caplog.text + "".join(str(r.args) for r in caplog.records)
    assert "0400111222" not in text and "jo@example.com" not in text
    assert "ai-secret" not in text


def test_unconfigured_raises_not_configured(monkeypatch):
    monkeypatch.delenv("APPLICATIONAI_AGENT_TOKEN")
    with pytest.raises(ApplicationAiError) as ei:
        applicationai.search_by_address(ADDR, "a@b.c")
    assert ei.value.code == "applicationai_not_configured"


# --- route ---

@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def session():
    tok = accounts.create_invite("pm@grantsea.com.au", name="PM")
    return {"Authorization": f"Bearer {accounts.accept_invite(tok, 'longenough1')}"}


def test_route_requires_agent_session(client):
    assert client.get("/applications/search?address=" + ADDR).status_code == 401


def test_route_rejects_machine_token(client):
    r = client.get("/applications/search?address=" + ADDR,
                   headers={"Authorization": "Bearer machine-token"})
    assert r.status_code == 401


def test_route_short_address_400(client, session):
    r = client.get("/applications/search?address=12 Ex", headers=session)
    assert r.status_code == 400 and r.json()["error"] == "invalid_request"


def test_route_returns_mapped_applications(client, session, monkeypatch):
    _mock(monkeypatch, lambda req: httpx.Response(
        200, json={"applications": [{**ROW, "secret": "x"}]}))
    r = client.get("/applications/search?address=" + ADDR, headers=session)
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["applications"][0]["renter1_email"] == "jo@example.com"
    assert "secret" not in body["applications"][0]


def test_route_unconfigured_envelope(client, session, monkeypatch):
    monkeypatch.delenv("APPLICATIONAI_BASE_URL")
    r = client.get("/applications/search?address=" + ADDR, headers=session)
    assert r.status_code == 503
    assert r.json()["error"] == "applicationai_not_configured"


def test_route_upstream_error_carries_code_only(client, session, monkeypatch):
    _mock(monkeypatch, lambda req: httpx.Response(401, text="jo@example.com leaked"))
    r = client.get("/applications/search?address=" + ADDR, headers=session)
    assert r.status_code == 502
    assert r.json()["error"] == "applicationai_rejected"
    assert "jo@example.com" not in r.text
