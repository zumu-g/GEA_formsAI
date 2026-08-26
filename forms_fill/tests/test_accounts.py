import pytest
from fastapi.testclient import TestClient

from forms_fill import accounts
from forms_fill.api import app

TOKEN = "test-token"
MACHINE = {"Authorization": f"Bearer {TOKEN}"}


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("FORMS_API_TOKEN", TOKEN)
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://testserver")
    monkeypatch.delenv("RESEND_API_KEY", raising=False)


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def _invite(client, email="jane@grantsea.com.au", **kw):
    return client.post(
        "/agents/invite",
        json={"email": email, "name": "Jane Agent", "mobile": "0400000000", **kw},
        headers=MACHINE,
    )


def _accept_token(resp):
    return resp.json()["accept_url"].split("#accept=")[1]


def test_invite_rejects_foreign_domains(client):
    resp = _invite(client, email="jane@gmail.com")
    assert resp.status_code == 422
    assert "@grantsea.com.au" in resp.json()["message"]


def test_invite_requires_admin_auth(client):
    resp = client.post("/agents/invite", json={"email": "jane@grantsea.com.au"})
    assert resp.status_code == 401


def test_full_invite_accept_login_flow(client):
    resp = _invite(client)
    assert resp.status_code == 200
    assert resp.json()["emailed"] is False  # no RESEND_API_KEY in tests

    accept = client.post(
        "/auth/accept", json={"token": _accept_token(resp), "password": "s3cret-pass"}
    )
    assert accept.status_code == 200
    session = accept.json()["token"]

    # Session token works on an existing protected endpoint.
    forms = client.get("/forms", headers={"Authorization": f"Bearer {session}"})
    assert forms.status_code == 200

    # Fresh login issues a working token too.
    login = client.post(
        "/auth/login", json={"email": "Jane@grantsea.com.au", "password": "s3cret-pass"}
    )
    assert login.status_code == 200
    me = client.get(
        "/auth/me", headers={"Authorization": "Bearer " + login.json()["token"]}
    )
    assert me.json()["email"] == "jane@grantsea.com.au"
    assert me.json()["is_admin"] is True  # first agent auto-admin


def test_wrong_password_and_reused_invite_fail(client):
    resp = _invite(client)
    token = _accept_token(resp)
    assert client.post("/auth/accept", json={"token": token, "password": "s3cret-pass"}).status_code == 200
    # Invite is single-use.
    assert client.post("/auth/accept", json={"token": token, "password": "another-pass"}).status_code == 400
    # Wrong password.
    bad = client.post("/auth/login", json={"email": "jane@grantsea.com.au", "password": "nope-nope"})
    assert bad.status_code == 401
    # Short password on a fresh invite.
    assert client.post("/auth/accept", json={"token": "bogus", "password": "short"}).status_code == 400


def test_non_admin_cannot_invite(client):
    first = _invite(client)  # auto-admin
    client.post("/auth/accept", json={"token": _accept_token(first), "password": "s3cret-pass"})
    second = _invite(client, email="bob@grantsea.com.au")
    session = client.post(
        "/auth/accept", json={"token": _accept_token(second), "password": "s3cret-pass"}
    ).json()["token"]
    resp = client.post(
        "/agents/invite",
        json={"email": "carol@grantsea.com.au"},
        headers={"Authorization": f"Bearer {session}"},
    )
    assert resp.status_code == 403


def test_machine_token_still_works_everywhere(client):
    assert client.get("/forms", headers=MACHINE).status_code == 200
    assert client.get("/agents", headers=MACHINE).status_code == 200
    me = client.get("/auth/me", headers=MACHINE).json()
    assert me["machine"] is True


def _session(client, email="jane@grantsea.com.au"):
    resp = _invite(client, email=email)
    return client.post(
        "/auth/accept", json={"token": _accept_token(resp), "password": "s3cret-pass"}
    ).json()["token"]


def _hdr(token):
    return {"Authorization": f"Bearer {token}"}


def test_draft_save_list_get_roundtrip(client):
    sess = _session(client)
    state = '{"caller_fields":{"rent_amount":"700"},"provider":"propertyme"}'
    save = client.post(
        "/drafts",
        json={"form_key": "residential_rental_agreement", "label": "12 Example St", "state": state},
        headers=_hdr(sess),
    )
    assert save.status_code == 200
    draft_id = save.json()["id"]

    listed = client.get("/drafts", headers=_hdr(sess)).json()["drafts"]
    assert [d["id"] for d in listed] == [draft_id]
    assert listed[0]["label"] == "12 Example St"
    assert "state" not in listed[0]  # list is light; blob comes from GET /drafts/{id}

    got = client.get(f"/drafts/{draft_id}", headers=_hdr(sess)).json()["draft"]
    assert got["state"] == state  # verbatim round-trip


def test_draft_upsert_updates_not_duplicates(client):
    sess = _session(client)
    body = {"form_key": "notice_to_vacate", "label": "a", "state": "{}"}
    draft_id = client.post("/drafts", json=body, headers=_hdr(sess)).json()["id"]
    again = client.post(
        "/drafts", json={**body, "id": draft_id, "label": "b"}, headers=_hdr(sess)
    ).json()["id"]
    assert again == draft_id
    listed = client.get("/drafts", headers=_hdr(sess)).json()["drafts"]
    assert len(listed) == 1 and listed[0]["label"] == "b"


def test_drafts_are_private_per_agent(client):
    sess_a = _session(client)
    sess_b = _session(client, email="bob@grantsea.com.au")
    draft_id = client.post(
        "/drafts", json={"form_key": "general_notice", "state": "{}"}, headers=_hdr(sess_a)
    ).json()["id"]
    assert client.get(f"/drafts/{draft_id}", headers=_hdr(sess_b)).status_code == 404
    assert client.delete(f"/drafts/{draft_id}", headers=_hdr(sess_b)).status_code == 404
    assert client.get("/drafts", headers=_hdr(sess_b)).json()["drafts"] == []
    # Machine bucket is separate from agent buckets too.
    assert client.get("/drafts", headers=MACHINE).json()["drafts"] == []


def test_draft_delete_removes_from_list(client):
    sess = _session(client)
    draft_id = client.post(
        "/drafts", json={"form_key": "general_notice", "state": "{}"}, headers=_hdr(sess)
    ).json()["id"]
    assert client.delete(f"/drafts/{draft_id}", headers=_hdr(sess)).status_code == 200
    assert client.get("/drafts", headers=_hdr(sess)).json()["drafts"] == []


def test_machine_token_uses_shared_bucket(client):
    draft_id = client.post(
        "/drafts", json={"form_key": "general_notice", "state": "{}"}, headers=MACHINE
    ).json()["id"]
    listed = client.get("/drafts", headers=MACHINE).json()["drafts"]
    assert [d["id"] for d in listed] == [draft_id]


# ── U3 (lease-flow speed-up): per-agent sticky defaults ─────────────────────


def test_defaults_roundtrip_per_agent(client):
    sess = _session(client)
    resp = client.post(
        "/defaults/residential_rental_agreement",
        json={"emergency_contact_name": "Jim Fixit", "emergency_phone": "0400111222",
              "agent_acn": "111 222 333"},
        headers=_hdr(sess),
    )
    assert resp.status_code == 200
    got = client.get("/defaults/residential_rental_agreement", headers=_hdr(sess)).json()
    assert got["values"]["emergency_contact_name"] == "Jim Fixit"
    # Another agent sees nothing.
    sess_b = _session(client, email="bob@grantsea.com.au")
    assert client.get("/defaults/residential_rental_agreement", headers=_hdr(sess_b)).json()["values"] == {}


def test_defaults_allowlist_and_validation(client):
    sess = _session(client)
    client.post(
        "/defaults/residential_rental_agreement",
        json={"emergency_phone": "0400", "rent_amount": "700", "provider_acn": "999",
              "emergency_email": "x" * 600, "agent_acn": 42},
        headers=_hdr(sess),
    )
    values = client.get("/defaults/residential_rental_agreement", headers=_hdr(sess)).json()["values"]
    assert values == {"emergency_phone": "0400"}  # non-allowlisted, oversized, non-string all dropped


def test_defaults_blank_value_clears_key(client):
    sess = _session(client)
    client.post("/defaults/lease", json={"emergency_phone": "0400"}, headers=_hdr(sess))
    client.post("/defaults/lease", json={"emergency_phone": ""}, headers=_hdr(sess))
    assert client.get("/defaults/lease", headers=_hdr(sess)).json()["values"] == {}


def test_defaults_are_signed_in_only(client):
    # Machine token neither saves nor serves defaults (no shared NULL bucket here).
    client.post("/defaults/lease", json={"emergency_phone": "0400"}, headers=MACHINE)
    assert client.get("/defaults/lease", headers=MACHINE).json()["values"] == {}


def test_sessions_persist_in_sqlite(client):
    resp = _invite(client)
    session = client.post(
        "/auth/accept", json={"token": _accept_token(resp), "password": "s3cret-pass"}
    ).json()["token"]
    # Direct module read (fresh connection) — survives app restarts by construction.
    agent = accounts.session_agent(session)
    assert agent["email"] == "jane@grantsea.com.au"
    accounts.logout(session)
    assert accounts.session_agent(session) is None
