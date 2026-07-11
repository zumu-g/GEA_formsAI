"""Sales-form context building (U10, KTD8, R16).

Sales authorities have no tenancy: the context is caller ``fields`` rendered
verbatim, merged over agency/agent defaults from ``fixtures/gea_agency.json``
(overridable via ``FORMS_AGENCY_FILE``). Caller values always win.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .errors import ProviderConfigError

DEFAULT_AGENCY_FILE = Path(__file__).resolve().parent.parent / "fixtures" / "gea_agency.json"


def load_agency_defaults() -> dict[str, str]:
    """Flat default fields derived from the agency config file."""

    path = Path(os.environ.get("FORMS_AGENCY_FILE", str(DEFAULT_AGENCY_FILE)))
    if not path.exists():
        raise ProviderConfigError(
            f"agency defaults file not found: {path} (set FORMS_AGENCY_FILE)"
        )
    data = json.loads(path.read_text())
    agency = data.get("agency", {})
    agent = data.get("agent", {})
    address = ", ".join(
        p
        for p in (
            agency.get("address_line"),
            f"{agency.get('suburb', '')} {agency.get('state', '')} {agency.get('postcode', '')}".strip(),
        )
        if p
    )
    name = agency.get("name", "")
    if agency.get("office"):
        name = f"{name} ({agency['office']})"
    return {
        "agent_name": name,
        "agent_acn": agency.get("acn") or "",
        "agency_address": address,
        "attention": agent.get("full_name", ""),
        "agent_mobile": agent.get("mobile", ""),
        "agent_email": agent.get("email", ""),
    }


def build_sales_context(fields: dict) -> dict[str, str]:
    """Merge caller fields (verbatim, R4) over agency defaults."""

    context = load_agency_defaults()
    context.update({k: "" if v is None else str(v) for k, v in fields.items()})
    return context
