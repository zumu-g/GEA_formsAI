"""Ingoing lease flow: idem_key at /fill → PM approve-send → Annature webhook →
one `lease_signed` POST to the ingoing engine. All HTTP is mocked."""

import pytest
from fastapi.testclient import TestClient

from forms_fill import leases
from forms_fill.api import app

TOKEN = "test-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}
LEASE = "residential_rental_agreement"


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("FORMS_API_TOKEN", TOKEN)
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://testserver")


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
