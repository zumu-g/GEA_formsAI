from pathlib import Path

import pytest

from forms_fill.approval import ApprovalError, approve
from forms_fill.vcat import LodgementError, lodge, vcat_application_type


@pytest.fixture
def approved_notice(tmp_path) -> Path:
    p = tmp_path / "notice_to_vacate.docx"
    p.write_bytes(b"fake docx content")
    approve(p, "Jane PM")
    return p


@pytest.fixture
def creds(monkeypatch):
    monkeypatch.setenv("VCAT_USERNAME", "user-secret")
    monkeypatch.setenv("VCAT_PASSWORD", "pass-secret")


def test_mapping_vacate_ground():
    assert vcat_application_type("91ZM") == "possession_order"


def test_mapping_breach_ground():
    assert vcat_application_type("60(1)") == "compliance_order"


def test_mapping_general_ground_refuses():
    with pytest.raises(LodgementError, match="no automated VCAT follow-on"):
        vcat_application_type("86")


def test_unapproved_file_refuses_before_anything(tmp_path, creds):
    p = tmp_path / "draft.docx"
    p.write_bytes(b"x")
    with pytest.raises(ApprovalError, match="not approved"):
        lodge(p, "91ZM")


def test_tampered_file_refuses(approved_notice, creds):
    approved_notice.write_bytes(b"regenerated")
    with pytest.raises(ApprovalError, match="changed since approval"):
        lodge(approved_notice, "91ZM")


def test_missing_credentials_refuses(approved_notice, monkeypatch):
    monkeypatch.delenv("VCAT_USERNAME", raising=False)
    monkeypatch.delenv("VCAT_PASSWORD", raising=False)
    with pytest.raises(LodgementError, match="credentials not configured"):
        lodge(approved_notice, "91ZM")


def test_portal_boundary_reached_with_all_gates_passed(approved_notice, creds):
    # All gates pass; the flow stops at the not-yet-recorded portal boundary.
    with pytest.raises(LodgementError, match="portal flow not yet recorded"):
        lodge(approved_notice, "91ZM", confirm=False)


def test_errors_never_contain_credentials(approved_notice, creds):
    try:
        lodge(approved_notice, "91ZM")
    except LodgementError as exc:
        assert "user-secret" not in str(exc)
        assert "pass-secret" not in str(exc)
