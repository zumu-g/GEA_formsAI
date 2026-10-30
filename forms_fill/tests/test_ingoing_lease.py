"""Ingoing lease flow: idem_key at /fill → PM approve-send → Annature webhook →
one `lease_signed` POST to the ingoing engine. All HTTP is mocked."""

import json
import shutil

import pytest
from fastapi.testclient import TestClient

from forms_fill import esign, leases
from forms_fill.api import OUTPUT_ROOT, app

TOKEN = "test-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}
APPROVE = {"Authorization": "Bearer approve-secret"}
LEASE = "residential_rental_agreement"


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("FORMS_API_TOKEN", TOKEN)
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://testserver")
    monkeypatch.setenv("FORMS_APPROVE_TOKEN", "approve-secret")
    monkeypatch.setenv("ANNATURE_API_ID", "pub")
    monkeypatch.setenv("ANNATURE_API_KEY", "priv")
    monkeypatch.setenv("ANNATURE_ACCOUNT_ID", "acct_1")


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def _fill_lease(client, **extra):
    payload = {
        "form": LEASE,
        "identifiers": {"lot_id": "L-2002"},
        "fields": {"rent_amount": "650", "bond_amount": "2600"},
        "pdf": False,
        **extra,
    }
    resp = client.post("/fill", json=payload, headers=AUTH)
    assert resp.status_code == 200, resp.text
    return resp.json()["request_id"]


# ── U1: idem_key carried through /fill ───────────────────────────────────────


def test_fill_with_idem_key_stores_it(client):
    request_id = _fill_lease(client, idem_key="OAK12:ingoing")
    row = leases.get(request_id)
    assert row["idem_key"] == "OAK12:ingoing"
    assert row["status"] == "draft"
    assert row["facts"]["rent_amount"] == "650"


def test_fill_without_idem_key_still_fills(client):
    request_id = _fill_lease(client)
    assert leases.get(request_id)["idem_key"] is None


def test_non_lease_form_rejects_nothing_and_stores_nothing(client, caller_fields):
    resp = client.post(
        "/fill",
        json={"form": "cav_rent_increase_notice", "identifiers": {"lot_id": "L-2002"},
              "fields": caller_fields, "pdf": False, "idem_key": "X:1"},
        headers=AUTH,
    )
    assert resp.status_code == 200, resp.text
    assert leases.get(resp.json()["request_id"]) is None


# ── U2: rent-in-advance and bond facts gate the send ─────────────────────────

FACTS = {
    "rent_amount": "650", "rent_period": "weekly", "first_rent_due_date": "2026-11-07",
    "bond_amount": "2600",
}
PAYMENTS = {
    "rent_payment_details": "EFT to GEA Trust, BSB 063-000 Acc 1234 5678, ref OAK12",
    "bond_payment_instructions": "Pay via the RTBA bond lodgement link emailed to you",
}


def test_complete_facts_have_nothing_missing():
    assert leases.missing_payment_facts(FACTS, PAYMENTS) == []


@pytest.mark.parametrize(
    "gone", ["rent_amount", "first_rent_due_date", "bond_amount"],
)
def test_missing_lease_fact_blocks(gone):
    facts = {**FACTS, gone: "  "}
    assert gone in leases.missing_payment_facts(facts, PAYMENTS)


@pytest.mark.parametrize("gone", list(PAYMENTS))
def test_missing_agency_payment_detail_blocks(gone):
    payments = {k: v for k, v in PAYMENTS.items() if k != gone}
    assert gone in leases.missing_payment_facts(FACTS, payments)


def test_signing_message_carries_rent_bond_and_rtba_note():
    msg = leases.signing_message(FACTS, PAYMENTS)
    for text in ("$650", "07/11/2026", PAYMENTS["rent_payment_details"], "$2600",
                 PAYMENTS["bond_payment_instructions"], "Residential Tenancies Bond Authority"):
        assert text in msg


# ── U3: PM approval gate → send to every tenant ──────────────────────────────

TENANTS = {
    "renter1_name": "Jane Renter", "renter1_email": "jane@example.com",
    "renter2_name": "Sam Renter", "renter2_email": "sam@example.com",
}


@pytest.fixture()
def agency_file(tmp_path, monkeypatch):
    from forms_fill.agency import DEFAULT_AGENCY_FILE

    cfg = json.loads(DEFAULT_AGENCY_FILE.read_text())
    cfg["payments"] = PAYMENTS
    path = tmp_path / "agency.json"
    path.write_text(json.dumps(cfg))
    monkeypatch.setenv("FORMS_AGENCY_FILE", str(path))
    return path


@pytest.fixture()
def envelopes(monkeypatch):
    calls = []

    def fake_post(payload):
        calls.append(payload)
        return {"id": f"env_{len(calls)}", "status": "sent"}

    monkeypatch.setattr(esign, "_post_envelope", fake_post)
    return calls


@pytest.fixture()
def lease(client):
    """A filled lease with a PDF on disk (render skipped for speed)."""

    request_id = _fill_lease(client, idem_key="OAK12:ingoing")
    leases.update(request_id, facts=json.dumps({**FACTS, **TENANTS}))
    (OUTPUT_ROOT / request_id / "lease.pdf").write_bytes(b"%PDF-1.4 fake")
    yield request_id
    shutil.rmtree(OUTPUT_ROOT / request_id, ignore_errors=True)


def _approve_send(client, request_id, headers=APPROVE):
    return client.post(
        f"/lease/{request_id}/approve-send", json={"approver": "Stuart Grant"}, headers=headers
    )


def test_nothing_sent_before_pm_approval(client, lease, envelopes, agency_file):
    assert envelopes == []
    assert leases.get(lease)["status"] == "draft"


def test_approve_send_needs_the_approval_credential(client, lease, envelopes, agency_file):
    assert _approve_send(client, lease, headers=AUTH).status_code == 401
    assert envelopes == []


def test_approve_send_reaches_every_tenant_with_the_payment_pack(client, lease, envelopes, agency_file):
    resp = _approve_send(client, lease)
    assert resp.status_code == 200, resp.text
    (payload,) = envelopes
    assert [r["email"] for r in payload["recipients"]] == ["jane@example.com", "sam@example.com"]
    assert "Residential Tenancies Bond Authority" in payload["message"]
    row = leases.get(lease)
    assert (row["status"], row["envelope_id"], row["signers_expected"]) == ("sent", "env_1", 2)


def test_missing_payment_values_block_the_send(client, lease, envelopes, agency_file):
    leases.update(lease, facts=json.dumps({**FACTS, **TENANTS, "bond_amount": ""}))
    resp = _approve_send(client, lease)
    assert resp.status_code == 422
    assert resp.json()["missing"] == ["bond_amount"]
    assert envelopes == []
    assert leases.get(lease)["status"] == "draft"


def test_missing_agency_payment_config_blocks_the_send(client, lease, envelopes):
    resp = _approve_send(client, lease)
    assert resp.status_code == 422
    assert set(resp.json()["missing"]) == set(PAYMENTS)
    assert envelopes == []


def test_lease_cannot_be_sent_twice(client, lease, envelopes, agency_file):
    _approve_send(client, lease)
    assert _approve_send(client, lease).status_code == 409
    assert len(envelopes) == 1


def test_plain_esign_send_refuses_a_lease(client, lease, envelopes):
    resp = client.post(
        "/esign/send",
        json={"request_id": lease, "recipients": [{"name": "J", "email": "j@x.co"}]},
        headers=AUTH,
    )
    assert resp.status_code == 409
    assert envelopes == []


# ── U4: Annature webhook → one notification when ALL tenants have signed ─────

from forms_fill import ingoing  # noqa: E402


@pytest.fixture()
def engine(monkeypatch):
    """Records posts to the ingoing engine; never touches the network."""

    import httpx

    monkeypatch.setenv("INGOING_ENGINE_WEBHOOK", "https://example.invalid/hook")
    monkeypatch.setenv("INGOING_WEBHOOK_SECRET", "s")
    calls = []

    def fake_post(url, json=None, headers=None, timeout=None):
        calls.append(json)
        return httpx.Response(200, text="ok", request=httpx.Request("POST", url))

    monkeypatch.setattr(ingoing, "_post", fake_post)
    monkeypatch.setattr(ingoing, "_sleep", lambda s: None)
    return calls


@pytest.fixture()
def annature(monkeypatch):
    """The envelope state Annature will report when we re-fetch it."""

    state = {"status": "sent", "recipients": []}
    monkeypatch.setattr(esign, "get_envelope", lambda envelope_id: {"id": envelope_id, **state})
    monkeypatch.setattr(esign, "download", lambda url: b"%PDF-1.4 signed")
    return state


def _signer(status):
    return {"type": "signer", "status": status}


@pytest.fixture()
def sent_lease(client, lease, envelopes, agency_file):
    assert _approve_send(client, lease).status_code == 200
    return lease


def _hook(client, event, envelope_id="env_1"):
    return client.post("/esign/annature-webhook", json={"event": event, "envelope_id": envelope_id})


def test_first_of_two_signatures_does_not_post(client, sent_lease, annature, engine):
    annature["recipients"] = [_signer("completed"), _signer("sent")]
    assert _hook(client, "recipient_completed").status_code == 200
    assert engine == []
    assert leases.get(sent_lease)["status"] == "sent"


def test_second_signature_posts_once(client, sent_lease, annature, engine):
    annature["recipients"] = [_signer("completed"), _signer("sent")]
    _hook(client, "recipient_completed")
    annature.update(status="completed", combined="https://annature.invalid/c.pdf",
                    completed="2026-10-30T02:00:00Z",
                    recipients=[_signer("completed"), _signer("completed")])
    _hook(client, "recipient_completed")
    _hook(client, "envelope_completed")  # Annature fires both — still one post
    assert len(engine) == 1
    assert engine[0]["idem_key"] == "OAK12:ingoing"
    assert engine[0]["figures"]["signers"] == 2
    assert engine[0]["figures"]["lease_signed_date"] == "2026-10-30"
    row = leases.get(sent_lease)
    assert (row["status"], row["notify_status"]) == ("signed", "sent")
    signed = client.get(f"/files/{sent_lease}/signed", headers=AUTH)
    assert signed.status_code == 200 and signed.content == b"%PDF-1.4 signed"


def test_reprocessing_a_completed_envelope_does_not_post_again(client, sent_lease, annature, engine):
    annature.update(status="completed", combined="https://annature.invalid/c.pdf",
                    completed="2026-10-30T02:00:00Z",
                    recipients=[_signer("completed"), _signer("completed")])
    _hook(client, "envelope_completed")
    _hook(client, "envelope_completed")
    assert len(engine) == 1


def test_declined_does_not_post(client, sent_lease, annature, engine):
    annature["recipients"] = [_signer("completed"), _signer("declined")]
    _hook(client, "recipient_declined")
    assert engine == []
    assert leases.get(sent_lease)["status"] == "declined"


def test_voided_does_not_post(client, sent_lease, annature, engine):
    annature["status"] = "voided"
    _hook(client, "envelope_voided")
    assert engine == []
    assert leases.get(sent_lease)["status"] == "voided"


def test_webhook_trusts_annature_not_the_body(client, sent_lease, annature, engine):
    # A forged "completed" event changes nothing: the re-fetched envelope says sent.
    _hook(client, "envelope_completed")
    assert engine == []
    assert leases.get(sent_lease)["status"] == "sent"


def test_unknown_envelope_is_acknowledged_and_ignored(client, annature, engine):
    assert _hook(client, "envelope_completed", envelope_id="someone_else").status_code == 200
    assert engine == []
