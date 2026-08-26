"""Auto-fill for the rental agreement spec (U5, KTD4).

The rule: a fetched/configured value seeds a field only when the caller
supplied nothing for it (R7) — never overrides a caller value.

``handling_agent`` is a caller-suppliable *selector* field, not a printed one
(no TextOp references it in either spec) — it exists so the UI can offer an
agent picker (R5, wired to dropdown options in U7 via the ``/agency``
endpoint). Once resolved it is echoed back into the context as the chosen
agent's name, so it never shows as a stray blank field in the fill report
even when the caller left it unset and the default agent was used.
"""

from __future__ import annotations

from ..agency import default_agent, find_agent, load_agency_config, office_address
from ..errors import ProviderConfigError
from ..models import TenancyBundle

AGENT_FIELDS = ("agent_name", "agent_address", "agent_postcode", "agent_phone", "agent_email")

# Lease fields common to both forms. Form 1 additionally has "term_type" and
# "periodic_start_date" (it supports a periodic agreement; Form 2 is
# fixed-term only) — each spec passes its own extra set via `lease_fields`.
LEASE_FIELDS_COMMON = (
    "fixed_start_date",
    "fixed_end_date",
    "rent_amount",
    "rent_period",
    "rent_payment_day",
    "first_rent_due_date",
    "bond_amount",
    "bond_due_date",
)

# Renewal mode (U6, KTD5) never carries these across — the new term's own
# dates must be entered deliberately, not inherited from the expiring lease.
RENEWAL_EXCLUDED_DATE_FIELDS = frozenset(
    {"fixed_start_date", "fixed_end_date", "periodic_start_date"}
)


def is_renewal(fields: dict) -> bool:
    return str(fields.get("is_renewal") or "").strip().lower() in ("1", "true", "yes")


def lease_fields_for_mode(lease_fields: tuple, fields: dict) -> tuple:
    """Which lease fields to seed, given renewal mode (U6, R8)."""

    if not is_renewal(fields):
        return lease_fields
    return tuple(f for f in lease_fields if f not in RENEWAL_EXCLUDED_DATE_FIELDS)


def _seed(ctx: dict[str, str], fields: dict, name: str, value: str) -> None:
    """Seed ``name`` from ``value`` only when the caller supplied nothing (KTD4)."""

    if not str(fields.get(name) or "").strip() and value:
        ctx[name] = value


def apply_agent_autofill(ctx: dict[str, str], fields: dict) -> None:
    """Seed the agent block from the configured office + chosen handling agent."""

    try:
        cfg = load_agency_config()
    except ProviderConfigError:
        # No agency config available — leave the agent block for manual entry,
        # same as any other blank-by-design field, rather than failing the fill.
        return

    agency_data = cfg["agency"]
    agents = cfg["agents"]
    requested = str(fields.get("handling_agent") or "").strip()
    agent = (find_agent(agents, requested) if requested else None) or default_agent(agents)

    _seed(ctx, fields, "agent_name", agent.get("full_name", ""))
    _seed(ctx, fields, "agent_address", office_address(agency_data))
    _seed(ctx, fields, "agent_postcode", agency_data.get("postcode", ""))
    _seed(ctx, fields, "agent_phone", agent.get("mobile", ""))
    _seed(ctx, fields, "agent_email", agent.get("email", ""))

    # Echo the resolved choice back (R5) — never blank once an agent exists,
    # whether the caller picked one explicitly or the default was used.
    ctx["handling_agent"] = requested or agent.get("full_name", "")


def apply_lease_autofill(
    ctx: dict[str, str], fields: dict, bundle: TenancyBundle | None, *, lease_fields: tuple
) -> None:
    """Seed lease/rent/bond fields from the tenancy bundle's lease block."""

    if bundle is None:
        return
    lease = bundle.lease
    for name in lease_fields:
        _seed(ctx, fields, name, str(getattr(lease, name, "") or ""))
