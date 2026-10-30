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
