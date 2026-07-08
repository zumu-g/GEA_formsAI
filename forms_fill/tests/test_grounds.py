import json
import subprocess
import sys
from pathlib import Path

import pytest

from forms_fill.grounds import (
    FAMILIES,
    GROUNDS,
    UnknownGroundError,
    get_ground,
    grounds_catalogue,
)
from forms_fill.registry import FORM_REGISTRY

PKG_ROOT = Path(__file__).resolve().parents[1]


def test_family_counts():
    counts = {f: sum(1 for g in GROUNDS if g.family == f) for f in FAMILIES}
    assert counts == {
        "vacate": 22,
        "breach_of_duty": 11,
        "general": 5,
        "rent_increase": 1,
    }


def test_no_duplicate_sections():
    sections = [g.section for g in GROUNDS]
    assert len(sections) == len(set(sections))


def test_lookup_vacate_ground():
    g = get_ground("91ZM")
    assert g.family == "vacate"
    assert g.min_notice_days == 14
    assert g.form_key == "notice_to_vacate"


def test_lookup_breach_ground():
    g = get_ground("60(1)")
    assert g.family == "breach_of_duty"
    assert g.form_key == "breach_of_duty_notice"


def test_notice_of_entry_maps_to_its_own_form():
    assert get_ground("86").form_key == "notice_of_entry"


def test_vacate_tiers():
    assert get_ground("91N(3)").min_notice_days == 0
    assert get_ground("91ZZG").min_notice_days == 28
    assert get_ground("91ZZB").min_notice_days == 90


def test_unknown_section_raises():
    with pytest.raises(UnknownGroundError):
        get_ground("99Z")


def test_every_form_key_exists_in_registry():
    for g in GROUNDS:
        assert g.form_key in FORM_REGISTRY, f"{g.section} -> {g.form_key} not registered"


def test_catalogue_family_filter():
    vacate = grounds_catalogue("vacate")
    assert len(vacate) == 22
    assert all(e["family"] == "vacate" for e in vacate)


def test_catalogue_unknown_family_raises():
    with pytest.raises(UnknownGroundError):
        grounds_catalogue("bogus")


def test_cli_grounds_subcommand():
    proc = subprocess.run(
        [sys.executable, "-m", "forms_fill.cli", "grounds", "--family", "breach_of_duty"],
        cwd=PKG_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert len(data["grounds"]) == 11
