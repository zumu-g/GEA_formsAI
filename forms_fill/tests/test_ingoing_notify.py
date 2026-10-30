"""Ingoing-engine notifier: exact body, once only, retries, no secret in logs.
HTTP and sleep are injected — the live webhook is never called."""

import logging

import httpx
import pytest

from forms_fill import ingoing, leases

URL = "https://example.invalid/webhook/gea-pm-ingoing-engine"
SECRET = "s3cret-value"


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("INGOING_ENGINE_WEBHOOK", URL)
    monkeypatch.setenv("INGOING_WEBHOOK_SECRET", SECRET)
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://forms.example")
    leases.init()


def _signed_lease(request_id="doc1", idem_key="OAK12:ingoing"):
    leases.save(request_id, idem_key, {"renter1_name": "Jane", "bond_amount": "2600"})
    # 14:30 UTC on 30 Oct = 01:30 on 31 Oct in Melbourne (AEDT)
    leases.update(request_id, status="signed", signers=2, signed_at="2026-10-30T14:30:00+00:00")
    return request_id


class Poster:
    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def __call__(self, url, json=None, headers=None, timeout=None):
        self.calls.append({"url": url, "json": json, "headers": headers, "timeout": timeout})
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return httpx.Response(outcome, text="ok", request=httpx.Request("POST", url))


def _notify(request_id, poster, sleeps=None):
    return ingoing.notify_lease_signed(
        request_id, post=poster, sleep=(sleeps.append if sleeps is not None else lambda s: None)
    )


def test_posts_once_with_the_exact_body():
    doc = _signed_lease()
    poster = Poster(200)
    _notify(doc, poster)
    (call,) = poster.calls
    assert call["url"] == URL
    assert call["headers"] == {"X-GEA-Secret": SECRET, "Content-Type": "application/json"}
    assert call["timeout"] == 15
    assert call["json"] == {
        "workflow_type": "ingoing",
        "intake_mode": "step_action",
        "source": "formsai",
        "sender": "formsai",
        "idem_key": "OAK12:ingoing",
        "step": 3,
        "answer": "lease_signed",
        "figures": {
            "lease_signed_date": "2026-10-31",
            "signers": 2,
            "signed_pdf_url": "https://forms.example/files/doc1/signed",
            "formsai_document_id": "doc1",
        },
    }
    row = leases.get(doc)
    assert row["notify_status"] == "sent" and row["notify_sent_at"]
    assert "200" in row["notify_response"]


def test_never_resends_after_success():
    doc = _signed_lease()
    _notify(doc, Poster(200))
    again = Poster(200)
    _notify(doc, again)
    assert again.calls == []


def test_500_then_200_ends_sent_after_a_5s_backoff():
    doc = _signed_lease()
    sleeps = []
    _notify(doc, Poster(500, 200), sleeps)
    assert sleeps == [5]
    row = leases.get(doc)
    assert (row["notify_status"], row["notify_attempts"]) == ("sent", 2)


def test_three_retries_then_failed_and_signing_untouched():
    doc = _signed_lease()
    sleeps = []
    poster = Poster(500, httpx.TimeoutException("slow"), 502, 503)
    _notify(doc, poster, sleeps)
    assert len(poster.calls) == 4  # first try + 3 retries
    assert sleeps == [5, 30, 120]
    row = leases.get(doc)
    assert row["notify_status"] == "ingoing_notify_failed"
    assert row["status"] == "signed"


def test_no_idem_key_flags_for_pm_and_does_not_post():
    doc = _signed_lease(idem_key=None)
    poster = Poster()
    _notify(doc, poster)
    assert poster.calls == []
    assert leases.get(doc)["notify_status"] == "no_idem_key"


def test_unconfigured_webhook_fails_without_posting(monkeypatch):
    monkeypatch.delenv("INGOING_WEBHOOK_SECRET")
    doc = _signed_lease()
    poster = Poster()
    _notify(doc, poster)
    assert poster.calls == []
    assert leases.get(doc)["notify_status"] == "ingoing_notify_failed"


def test_body_carries_no_tenant_or_bank_details():
    doc = _signed_lease()
    poster = Poster(200)
    _notify(doc, poster)
    assert "Jane" not in str(poster.calls[0]["json"])
    assert "2600" not in str(poster.calls[0]["json"])


def test_secret_never_logged(caplog):
    doc = _signed_lease()
    with caplog.at_level(logging.DEBUG):
        _notify(doc, Poster(500, 200))
    assert caplog.records  # it does log the request
    assert SECRET not in caplog.text
