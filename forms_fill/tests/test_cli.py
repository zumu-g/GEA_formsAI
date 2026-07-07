import json
import subprocess
import sys
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[1]


def _run(args, stdin=None):
    return subprocess.run(
        [sys.executable, "-m", "forms_fill.cli", "fill", *args],
        cwd=PKG_ROOT,
        input=stdin,
        capture_output=True,
        text=True,
    )


def test_cli_split_flags(tmp_path, caller_fields):
    proc = _run(
        [
            "--form",
            "cav_rent_increase_notice",
            "--identifiers",
            json.dumps({"lot_id": "L-2002"}),
            "--fields",
            json.dumps(caller_fields),
            "--out",
            str(tmp_path),
        ]
    )
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert result["ok"] is True
    assert result["form"] == "cav_rent_increase_notice"
    assert Path(result["files"]["docx"]).exists()


def test_cli_json_stdin(tmp_path, caller_fields):
    payload = json.dumps(
        {
            "form": "cav_rent_increase_notice",
            "identifiers": {"lot_id": "L-2002"},
            "fields": caller_fields,
            "out_dir": str(tmp_path),
        }
    )
    proc = _run(["--json", "-"], stdin=payload)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["ok"] is True


def test_cli_unknown_form_nonzero(tmp_path, caller_fields):
    proc = _run(
        ["--form", "bogus", "--fields", json.dumps(caller_fields), "--out", str(tmp_path)]
    )
    assert proc.returncode != 0
    assert proc.stdout.strip() == ""
    assert "error" in proc.stderr.lower()


def test_cli_malformed_identifiers_nonzero(tmp_path):
    proc = _run(
        ["--form", "cav_rent_increase_notice", "--identifiers", "{bad", "--out", str(tmp_path)]
    )
    assert proc.returncode != 0
    assert "json" in proc.stderr.lower()


def test_cli_reports_blank_fields(tmp_path):
    # Minimal fields → many blanks reported.
    proc = _run(
        [
            "--form",
            "cav_rent_increase_notice",
            "--fields",
            json.dumps({"current_rent": 615}),
            "--out",
            str(tmp_path),
        ]
    )
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert "blank_fields" in result
    assert "method_basis" in result["blank_fields"]
