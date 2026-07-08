import json
from pathlib import Path

import pytest

from forms_fill.approval import ApprovalError, approve, verify_approval


@pytest.fixture
def notice(tmp_path) -> Path:
    p = tmp_path / "notice_to_vacate.docx"
    p.write_bytes(b"fake docx content")
    return p


def test_approve_then_verify(notice):
    record = approve(notice, "Jane PM")
    assert record["approver"] == "Jane PM"
    verified = verify_approval(notice)
    assert verified["sha256"] == record["sha256"]


def test_sidecar_written_next_to_file(notice):
    approve(notice, "Jane PM")
    sidecar = notice.with_name(notice.name + ".approval.json")
    assert sidecar.is_file()
    assert json.loads(sidecar.read_text())["file"] == notice.name


def test_tampered_file_fails_verification(notice):
    approve(notice, "Jane PM")
    notice.write_bytes(b"regenerated different content")
    with pytest.raises(ApprovalError, match="changed since approval"):
        verify_approval(notice)


def test_unapproved_file_fails_verification(notice):
    with pytest.raises(ApprovalError, match="not approved"):
        verify_approval(notice)


def test_approve_missing_file_fails(tmp_path):
    with pytest.raises(ApprovalError, match="file not found"):
        approve(tmp_path / "nope.docx", "Jane PM")


def test_approve_blank_approver_fails(notice):
    with pytest.raises(ApprovalError, match="approver name is required"):
        approve(notice, "   ")


def test_approval_record_contains_no_pii_beyond_filename(notice):
    record = approve(notice, "Jane PM")
    assert set(record) <= {"approver", "approved_at", "sha256", "file", "ground", "signature"}


def test_corrupt_sidecar_raises_approval_error(notice):
    approve(notice, "Jane PM")
    sidecar = notice.with_name(notice.name + ".approval.json")
    sidecar.write_text("{truncated", encoding="utf-8")
    with pytest.raises(ApprovalError, match="unreadable"):
        verify_approval(notice)


def test_signed_approval_roundtrip(notice, monkeypatch):
    monkeypatch.setenv("FORMS_APPROVE_TOKEN", "signing-secret")
    record = approve(notice, "Jane PM", ground="91ZM")
    assert record["signature"]
    assert verify_approval(notice, ground="91ZM")["ground"] == "91ZM"


def test_forged_unsigned_sidecar_rejected_when_signing_configured(notice, monkeypatch):
    monkeypatch.setenv("FORMS_APPROVE_TOKEN", "signing-secret")
    # Forge: write a plausible unsigned record directly (attacker has fs access).
    import hashlib
    sidecar = notice.with_name(notice.name + ".approval.json")
    sidecar.write_text(json.dumps({
        "approver": "Forged PM",
        "approved_at": "2026-07-08T00:00:00+00:00",
        "sha256": hashlib.sha256(notice.read_bytes()).hexdigest(),
        "file": notice.name,
        "ground": "91ZM",
    }), encoding="utf-8")
    with pytest.raises(ApprovalError, match="unsigned or has an invalid signature"):
        verify_approval(notice)


def test_tampered_signature_rejected(notice, monkeypatch):
    monkeypatch.setenv("FORMS_APPROVE_TOKEN", "signing-secret")
    approve(notice, "Jane PM")
    sidecar = notice.with_name(notice.name + ".approval.json")
    stored = json.loads(sidecar.read_text())
    stored["approver"] = "Someone Else"  # mutate after signing
    sidecar.write_text(json.dumps(stored), encoding="utf-8")
    with pytest.raises(ApprovalError, match="invalid signature"):
        verify_approval(notice)


def test_ground_mismatch_rejected(notice):
    approve(notice, "Jane PM", ground="86")
    with pytest.raises(ApprovalError, match="approval mismatch"):
        verify_approval(notice, ground="91ZM")


def test_legacy_record_without_ground_still_verifies(notice):
    approve(notice, "Jane PM")  # no ground recorded
    assert verify_approval(notice, ground="91ZM")["approver"] == "Jane PM"
