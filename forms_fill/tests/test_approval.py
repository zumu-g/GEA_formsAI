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
    assert set(record) == {"approver", "approved_at", "sha256", "file"}
