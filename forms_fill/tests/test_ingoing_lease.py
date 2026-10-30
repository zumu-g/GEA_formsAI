"""Ingoing lease flow: idem_key at /fill → PM approve-send → Annature webhook →
one `lease_signed` POST to the ingoing engine. All HTTP is mocked."""

import json
import shutil

import pytest
from fastapi.testclient import TestClient

from forms_fill import esign, leases, signing
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
def emails(monkeypatch):
    """Signing-link emails handed to Resend (never really sent)."""

    import httpx

    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    calls = []

    def fake_post(url, json=None, headers=None, timeout=None):
        calls.append(json)
        return httpx.Response(200, json={"id": "em"}, request=httpx.Request("POST", url))

    monkeypatch.setattr(signing, "_post", fake_post)
    return calls


def _link_token(email):
    import re

    return re.search(r"/sign/([\w-]+)", email["html"]).group(1)


def _lease_pdf():
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    for slot in (1, 2, 3, 4):
        page.insert_text((72, 120 + 90 * slot), f"Signature of renter {slot}")
    return doc.tobytes()


@pytest.fixture()
def lease(client):
    """A filled lease with a PDF on disk (render skipped for speed)."""

    request_id = _fill_lease(client, idem_key="OAK12:ingoing")
    leases.update(request_id, facts=json.dumps({**FACTS, **TENANTS}))
    (OUTPUT_ROOT / request_id / "lease.pdf").write_bytes(_lease_pdf())
    yield request_id
    shutil.rmtree(OUTPUT_ROOT / request_id, ignore_errors=True)


def _approve_send(client, request_id, headers=APPROVE):
    return client.post(
        f"/lease/{request_id}/approve-send", json={"approver": "Stuart Grant"}, headers=headers
    )


def test_nothing_sent_before_pm_approval(client, lease, emails, agency_file):
    assert emails == []
    assert leases.get(lease)["status"] == "draft"


def test_approve_send_needs_the_approval_credential(client, lease, emails, agency_file):
    assert _approve_send(client, lease, headers=AUTH).status_code == 401
    assert emails == []


def test_approve_send_reaches_every_tenant_with_the_payment_pack(client, lease, emails, agency_file):
    resp = _approve_send(client, lease)
    assert resp.status_code == 200, resp.text
    assert [e["to"] for e in emails] == [["jane@example.com"], ["sam@example.com"]]
    tokens = [_link_token(e) for e in emails]
    assert tokens[0] != tokens[1]  # each tenant gets their own link
    assert leases.signer_by_token(tokens[1])["email"] == "sam@example.com"
    for e in emails:
        assert "http://testserver/sign/" in e["html"]
        assert "Residential Tenancies Bond Authority" in e["html"]
        assert "$2600" in e["html"]
    row = leases.get(lease)
    assert (row["status"], row["signers_expected"]) == ("sent", 2)


def test_email_failure_leaves_the_lease_a_draft(client, lease, emails, agency_file, monkeypatch):
    import httpx

    def down(url, json=None, headers=None, timeout=None):
        return httpx.Response(500, text="boom", request=httpx.Request("POST", url))

    monkeypatch.setattr(signing, "_post", down)
    resp = _approve_send(client, lease)
    assert resp.status_code == 502
    assert leases.get(lease)["status"] == "draft"
    assert leases.signers_for(lease) == []


def test_unconfigured_email_blocks_the_send(client, lease, emails, agency_file, monkeypatch):
    monkeypatch.delenv("RESEND_API_KEY")
    assert _approve_send(client, lease).status_code == 503
    assert emails == [] and leases.get(lease)["status"] == "draft"


def test_missing_payment_values_block_the_send(client, lease, emails, agency_file):
    leases.update(lease, facts=json.dumps({**FACTS, **TENANTS, "bond_amount": ""}))
    resp = _approve_send(client, lease)
    assert resp.status_code == 422
    assert resp.json()["missing"] == ["bond_amount"]
    assert emails == []
    assert leases.get(lease)["status"] == "draft"


def test_missing_agency_payment_config_blocks_the_send(client, lease, emails):
    resp = _approve_send(client, lease)
    assert resp.status_code == 422
    assert set(resp.json()["missing"]) == set(PAYMENTS)
    assert emails == []


def test_lease_cannot_be_sent_twice(client, lease, emails, agency_file):
    _approve_send(client, lease)
    assert _approve_send(client, lease).status_code == 409
    assert len(emails) == 2  # one per tenant, once


def test_plain_esign_send_refuses_a_lease(client, lease, emails):
    resp = client.post(
        "/esign/send",
        json={"request_id": lease, "recipients": [{"name": "J", "email": "j@x.co"}]},
        headers=AUTH,
    )
    assert resp.status_code == 409
    assert emails == []


# ── S3: tenants sign in formsAI; one notification when ALL have signed ─────

import base64  # noqa: E402
from datetime import datetime  # noqa: E402
from zoneinfo import ZoneInfo  # noqa: E402

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
def sent_lease(client, lease, emails, agency_file):
    assert _approve_send(client, lease).status_code == 200
    return lease, [_link_token(e) for e in emails]


def _png_data_url():
    import fitz

    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 40, 12), False)
    pix.set_rect(pix.irect, (10, 10, 10))
    return "data:image/png;base64," + base64.b64encode(pix.tobytes("png")).decode()


def _sign(client, token, **overrides):
    body = {"consent": True, "full_name": "Jane Renter", "signature_png": _png_data_url(), **overrides}
    return client.post(f"/sign/{token}", json=body)


def test_signing_page_opens_for_a_valid_link(client, sent_lease):
    _, tokens = sent_lease
    page = client.get(f"/sign/{tokens[0]}")
    assert page.status_code == 200 and "sign" in page.text.lower()
    info = client.get(f"/sign/{tokens[0]}/info").json()
    assert info["name"] == "Jane Renter" and "Residential Tenancies Bond Authority" in info["message"]
    pdf = client.get(f"/sign/{tokens[0]}/pdf")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")


def test_unknown_link_is_refused(client):
    assert client.get("/sign/not-a-real-token").status_code == 404
    assert _sign(client, "not-a-real-token").status_code == 404


def test_first_of_two_signatures_does_not_post(client, sent_lease, engine):
    request_id, tokens = sent_lease
    assert _sign(client, tokens[0]).status_code == 200
    assert engine == []
    row = leases.get(request_id)
    assert (row["status"], row["signers"]) == ("sent", 1)


def test_second_signature_posts_once_with_the_spec_body(client, sent_lease, engine):
    request_id, tokens = sent_lease
    _sign(client, tokens[0])
    assert _sign(client, tokens[1], full_name="Sam Renter").status_code == 200
    today = datetime.now(ZoneInfo("Australia/Melbourne")).date().isoformat()
    assert engine == [{
        "workflow_type": "ingoing", "intake_mode": "step_action", "source": "formsai",
        "sender": "formsai", "idem_key": "OAK12:ingoing", "step": 3, "answer": "lease_signed",
        "figures": {"lease_signed_date": today, "signers": 2,
                    "signed_pdf_url": f"http://testserver/files/{request_id}/signed",
                    "formsai_document_id": request_id},
    }]
    row = leases.get(request_id)
    assert (row["status"], row["notify_status"]) == ("signed", "sent")
    signed = client.get(f"/files/{request_id}/signed", headers=AUTH)
    assert signed.status_code == 200 and signed.content.startswith(b"%PDF")


def test_a_used_link_cannot_sign_again_or_repost(client, sent_lease, engine):
    _, tokens = sent_lease
    _sign(client, tokens[0])
    _sign(client, tokens[1])
    assert _sign(client, tokens[1]).status_code == 409
    assert len(engine) == 1


def test_declined_does_not_post(client, sent_lease, engine):
    request_id, tokens = sent_lease
    _sign(client, tokens[0])
    resp = client.post(f"/sign/{tokens[1]}/decline", json={"reason": "Rent is wrong"})
    assert resp.status_code == 200
    assert _sign(client, tokens[1]).status_code == 409
    assert engine == []
    assert leases.get(request_id)["status"] == "declined"


@pytest.mark.parametrize("bad", [
    {"consent": False}, {"full_name": "  "}, {"signature_png": "data:image/jpeg;base64,AAAA"},
    {"signature_png": "data:image/png;base64,bm90IGEgcG5n"},
])
def test_incomplete_signatures_are_rejected(client, sent_lease, engine, bad):
    _, tokens = sent_lease
    assert _sign(client, tokens[0], **bad).status_code == 422
    assert leases.signer_by_token(tokens[0])["status"] == "pending"


# ── U6: PM sees status and can "Resend to Ingoing" ───────────────────────────


def _complete(client, tokens):
    for t in tokens:
        _sign(client, t)


def test_resend_after_failure_posts_once(client, sent_lease, engine, monkeypatch):
    request_id, tokens = sent_lease
    monkeypatch.delenv("INGOING_WEBHOOK_SECRET")
    _complete(client, tokens)
    assert leases.get(request_id)["notify_status"] == "ingoing_notify_failed"
    monkeypatch.setenv("INGOING_WEBHOOK_SECRET", "s")
    resp = client.post(f"/lease/{request_id}/resend-ingoing", headers=APPROVE)
    assert resp.status_code == 202, resp.text  # retries can take minutes: runs in background
    assert leases.get(request_id)["notify_status"] == "sent"
    assert len(engine) == 1


def test_resend_after_success_is_refused(client, sent_lease, engine):
    request_id, tokens = sent_lease
    _complete(client, tokens)
    assert client.post(f"/lease/{request_id}/resend-ingoing", headers=APPROVE).status_code == 409
    assert len(engine) == 1


def test_resend_needs_the_approval_credential(client, sent_lease):
    request_id, _ = sent_lease
    assert client.post(f"/lease/{request_id}/resend-ingoing", headers=AUTH).status_code == 401


def test_lease_list_shows_signing_and_notify_status(client, sent_lease, engine):
    request_id, tokens = sent_lease
    _sign(client, tokens[0])
    (row,) = [r for r in client.get("/leases", headers=AUTH).json()["leases"]
              if r["request_id"] == request_id]
    assert (row["status"], row["signers"], row["signers_expected"]) == ("sent", 1, 2)
    assert row["idem_key"] == "OAK12:ingoing"
    assert "facts" not in row  # tenant details stay out of the list


def test_lease_without_renter_signature_boxes_is_not_sent(client, lease, emails, agency_file):
    import fitz

    doc = fitz.open()
    doc.new_page().insert_text((72, 100), "no signature boxes here")
    (OUTPUT_ROOT / lease / "lease.pdf").write_bytes(doc.tobytes())
    resp = _approve_send(client, lease)
    assert resp.status_code == 422
    assert "renter 1" in resp.json()["message"]
    assert emails == []
