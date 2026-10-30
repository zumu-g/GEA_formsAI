"""formsAI's own lease e-signing: signer records, links, signing page, stamped
PDF. All outbound HTTP (Resend, ingoing engine) is mocked."""

import hashlib

import pytest

from forms_fill import leases


@pytest.fixture(autouse=True)
def _db():
    leases.init()


TENANTS = [{"name": "Jane Renter", "email": "jane@example.com"},
           {"name": "Sam Renter", "email": "sam@example.com"}]


def _lease(request_id="lease1"):
    leases.save(request_id, "OAK12:ingoing", {})
    tokens = leases.create_signers(request_id, TENANTS)
    leases.update(request_id, status="sent", signers_expected=len(TENANTS))
    return tokens


SIG = dict(signed_name="Jane Renter", signature_png=b"png", ip="1.2.3.4", user_agent="UA")


# ── S1: signer records ───────────────────────────────────────────────────────


def test_tokens_are_long_random_and_stored_hashed():
    tokens = _lease()
    assert set(tokens) == {1, 2} and all(len(t) >= 32 for t in tokens.values())
    with leases._connect() as conn:
        stored = [r[0] for r in conn.execute("SELECT token_hash FROM lease_signers")]
    assert tokens[1] not in stored
    assert hashlib.sha256(tokens[1].encode()).hexdigest() in stored


def test_signer_by_token_finds_its_own_lease_only():
    tokens = _lease("lease1")
    other = _lease("lease2")
    s = leases.signer_by_token(tokens[2])
    assert (s["request_id"], s["slot"], s["email"]) == ("lease1", 2, "sam@example.com")
    assert leases.signer_by_token(other[1])["request_id"] == "lease2"
    assert leases.signer_by_token("not-a-token") is None


def test_only_the_last_signature_completes_the_lease():
    tokens = _lease()
    assert leases.record_signature(tokens[1], **SIG) == "signed"
    assert leases.record_signature(tokens[2], **SIG) == "complete"


def test_a_token_cannot_sign_twice():
    tokens = _lease()
    leases.record_signature(tokens[1], **SIG)
    assert leases.record_signature(tokens[1], **SIG) == "invalid"


def test_decline_stops_further_signing():
    tokens = _lease()
    assert leases.record_decline(tokens[1], "rent is wrong") == "declined"
    assert leases.get("lease1")["status"] == "declined"
    assert leases.record_signature(tokens[2], **SIG) == "invalid"


def test_tenants_keep_their_renter_number_when_an_earlier_slot_is_blank():
    facts = {"renter2_name": "Sam Renter", "renter2_email": "sam@example.com"}
    assert leases.tenants(facts) == [{"slot": 2, "name": "Sam Renter", "email": "sam@example.com"}]
    leases.save("gap", None, facts)
    tokens = leases.create_signers("gap", leases.tenants(facts))
    assert set(tokens) == {2}
    assert leases.signer_by_token(tokens[2])["slot"] == 2
