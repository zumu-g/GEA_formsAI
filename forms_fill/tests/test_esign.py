import base64
import shutil

import pytest
from fastapi.testclient import TestClient

from forms_fill import esign
from forms_fill.api import OUTPUT_ROOT, app

TOKEN = "test-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}
REQ = "esigntest123"


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("FORMS_API_TOKEN", TOKEN)
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://testserver")
    monkeypatch.setenv("ANNATURE_ID", "pub")
    monkeypatch.setenv("ANNATURE_KEY", "priv")


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def pdf_request():
    directory = OUTPUT_ROOT / REQ
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "notice.pdf").write_bytes(b"%PDF-1.4 fake")
    yield REQ
    shutil.rmtree(directory, ignore_errors=True)


@pytest.fixture()
def sent(monkeypatch):
    calls = []

    def fake_post(payload):
        calls.append(payload)
        return {"id": "env_123", "status": "sent"}

    monkeypatch.setattr(esign, "_post_envelope", fake_post)
    return calls


def _send(client, **overrides):
    body = {
        "request_id": REQ,
        "recipients": [{"name": "Jane Renter", "email": "jane@example.com"}],
    }
    body.update(overrides)
    return client.post("/esign/send", json=body, headers=AUTH)


def test_send_happy_path(client, pdf_request, sent):
    resp = _send(client, title="Rental agreement", message="Please sign")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True, "envelope_id": "env_123", "status": "sent", "signers": 1}
    payload = sent[0]
    assert base64.b64decode(payload["documents"][0]["base"]).startswith(b"%PDF")
    signer = payload["recipients"][0]
    assert signer["type"] == "signer" and signer["email"] == "jane@example.com"
    assert signer["fields"][0]["type"] == "signature"
    assert signer["fields"][0]["anchor"]  # anchor-placed, required
    assert signer["fields"][0]["required"] is True


def test_unknown_request_id_404(client, sent):
    resp = _send(client, request_id="nosuchreq1")
    assert resp.status_code == 404


def test_missing_or_bad_recipients_422(client, pdf_request, sent):
    assert _send(client, recipients=[]).status_code == 422
    assert _send(client, recipients=[{"name": "X", "email": "not-an-email"}]).status_code == 422
    assert _send(client, recipients=[{"name": "", "email": "a@b.co"}]).status_code == 422


def test_unconfigured_keys_503(client, pdf_request, monkeypatch):
    monkeypatch.delenv("ANNATURE_ID")
    resp = _send(client)
    assert resp.status_code == 503
    assert "ANNATURE" in resp.json()["message"]


def test_requires_auth(client, pdf_request):
    resp = client.post("/esign/send", json={"request_id": REQ, "recipients": []})
    assert resp.status_code == 401


def test_upstream_error_502(client, pdf_request, monkeypatch):
    def boom(payload):
        raise esign.EsignUpstreamError("Annature 400: bad anchor")

    monkeypatch.setattr(esign, "_post_envelope", boom)
    resp = _send(client)
    assert resp.status_code == 502
    assert "Annature" in resp.json()["message"]
