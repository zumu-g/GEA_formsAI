"""Shared agency/agent config loader (U4, KTD2).

Sales forms and the rental agreement both need GEA's own office/agent
details, but they read the same fields with opposite meaning: sales treats
"agent" as the agency's trading name and "attention" as the person, while the
agreement's agent block IS the person. Rather than reinterpret sales_keys for
a new reader, this module loads the raw office and agent records once and
lets each caller map them to its own field names — ``forms_fill.sales``
keeps its current output shape, built on top of this loader (KTD2).

``fixtures/gea_agency.json``'s "agent" key may be a single object (legacy
shape) or a list of objects; both are normalised to a list here so config
that hasn't been migrated keeps working (R5).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .errors import ProviderConfigError

DEFAULT_AGENCY_FILE = Path(__file__).resolve().parent.parent / "fixtures" / "gea_agency.json"


def _agency_file() -> Path:
    return Path(os.environ.get("FORMS_AGENCY_FILE", str(DEFAULT_AGENCY_FILE)))


def load_agency_config() -> dict:
    """Raw ``{"agency": {...}, "agents": [{...}, ...], "meta": {...}}``.

    ``agents`` is always a list, even when the config file still declares a
    single legacy ``"agent"`` object — the first (only) entry becomes the
    list's one member and stays the default agent.
    """

    path = _agency_file()
    if not path.exists():
        raise ProviderConfigError(
            f"agency defaults file not found: {path} (set FORMS_AGENCY_FILE)"
        )
    data = json.loads(path.read_text())
    agency = data.get("agency", {})
    raw_agent = data.get("agents") or data.get("agent") or {}
    agents = raw_agent if isinstance(raw_agent, list) else [raw_agent]
    return {"agency": agency, "agents": [a for a in agents if a], "meta": data.get("meta", {})}


def office_address(agency: dict) -> str:
    """Compose the office's postal address the way sales forms already do."""

    return ", ".join(
        p
        for p in (
            agency.get("address_line"),
            f"{agency.get('suburb', '')} {agency.get('state', '')} {agency.get('postcode', '')}".strip(),
        )
        if p
    )


def default_agent(agents: list[dict]) -> dict:
    """The agent used when the caller has not chosen one — the first configured."""

    return agents[0] if agents else {}


def find_agent(agents: list[dict], full_name: str) -> dict | None:
    """Look up a configured agent by name for the handling-agent picker (R5)."""

    name = (full_name or "").strip().lower()
    if not name:
        return None
    for a in agents:
        if (a.get("full_name") or "").strip().lower() == name:
            return a
    return None
