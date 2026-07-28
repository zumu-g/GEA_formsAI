import json

import pytest

from forms_fill.agency import (
    default_agent,
    find_agent,
    load_agency_config,
    office_address,
)
from forms_fill.errors import ProviderConfigError


def test_loads_configured_office_and_agents():
    cfg = load_agency_config()
    assert cfg["agency"]["name"] == "Grants Estate Agents"
    assert len(cfg["agents"]) == 1
    assert cfg["agents"][0]["full_name"] == "Stuart Grant"


def test_default_agent_is_first_configured():
    cfg = load_agency_config()
    assert default_agent(cfg["agents"])["full_name"] == "Stuart Grant"


def test_default_agent_empty_list_returns_empty_dict():
    assert default_agent([]) == {}


def test_find_agent_matches_case_insensitively():
    agents = [{"full_name": "Stuart Grant"}, {"full_name": "Alex Lee"}]
    assert find_agent(agents, "alex lee")["full_name"] == "Alex Lee"


def test_find_agent_no_match_returns_none():
    agents = [{"full_name": "Stuart Grant"}]
    assert find_agent(agents, "Nobody") is None


def test_office_address_composes_line_and_suburb_state_postcode():
    addr = office_address(
        {"address_line": "3a Gloucester Avenue", "suburb": "Berwick", "state": "VIC", "postcode": "3806"}
    )
    assert addr == "3a Gloucester Avenue, Berwick VIC 3806"


def test_missing_agency_file_raises_config_error(monkeypatch, tmp_path):
    monkeypatch.setenv("FORMS_AGENCY_FILE", str(tmp_path / "nope.json"))
    with pytest.raises(ProviderConfigError):
        load_agency_config()


def test_legacy_single_agent_object_still_loads(monkeypatch, tmp_path):
    """A config file that hasn't migrated to "agents": [...] must still work."""

    path = tmp_path / "agency.json"
    path.write_text(
        json.dumps(
            {
                "agency": {"name": "Legacy Agency"},
                "agent": {"full_name": "Sole Agent"},
            }
        )
    )
    monkeypatch.setenv("FORMS_AGENCY_FILE", str(path))
    cfg = load_agency_config()
    assert cfg["agents"] == [{"full_name": "Sole Agent"}]


def test_agents_list_shape_normalises_to_list(monkeypatch, tmp_path):
    path = tmp_path / "agency.json"
    path.write_text(
        json.dumps(
            {
                "agency": {"name": "Multi Agent Office"},
                "agents": [{"full_name": "A One"}, {"full_name": "B Two"}],
            }
        )
    )
    monkeypatch.setenv("FORMS_AGENCY_FILE", str(path))
    cfg = load_agency_config()
    assert [a["full_name"] for a in cfg["agents"]] == ["A One", "B Two"]
