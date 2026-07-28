"""Sales-form context building (U10, KTD8, R16).

Sales authorities have no tenancy: the context is caller ``fields`` rendered
verbatim, merged over agency/agent defaults from ``fixtures/gea_agency.json``
(overridable via ``FORMS_AGENCY_FILE``). Caller values always win.

Agency/agent loading itself lives in ``forms_fill.agency`` (U4, KTD2) so the
rental agreement can read the same config with different field names; this
module is a thin mapper onto sales forms' own output shape, unchanged from
before that split.
"""

from __future__ import annotations

from .agency import default_agent, load_agency_config, office_address


def load_agency_defaults() -> dict[str, str]:
    """Flat default fields derived from the agency config file (sales shape)."""

    cfg = load_agency_config()
    agency = cfg["agency"]
    agent = default_agent(cfg["agents"])
    name = agency.get("name", "")
    if agency.get("office"):
        name = f"{name} ({agency['office']})"
    return {
        "agent_name": name,
        "agent_acn": agency.get("acn") or "",
        "agency_address": office_address(agency),
        "attention": agent.get("full_name", ""),
        "agent_mobile": agent.get("mobile", ""),
        "agent_email": agent.get("email", ""),
    }


def build_sales_context(fields: dict) -> dict[str, str]:
    """Merge caller fields (verbatim, R4) over agency defaults."""

    context = load_agency_defaults()
    context.update({k: "" if v is None else str(v) for k, v in fields.items()})
    return context
