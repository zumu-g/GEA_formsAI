"""Request / result / data-bundle models (U1).

These pin the shapes that flow through the whole tool:

- ``FillRequest`` — the one internal request that the CLI, ``--json``/stdin, and
  ``POST /fill`` all normalise into. ``fields`` and ``identifiers`` stay in
  separate buckets end-to-end and are never merged (R3).
- ``TenancyBundle`` — the provider contract (mirrors
  ``docs/integrations/crm-data-contract-prompt.md``); PropertyMe and GEA CRM
  both return this shape.
- ``FillResult`` — the machine-readable result printed to stdout / returned by
  the API (R8).
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class _Strict(BaseModel):
    """Reject unknown keys so contract drift is caught early (U1)."""

    model_config = ConfigDict(extra="forbid")


# ── Provider contract (TenancyBundle) ──────────────────────────────────────────


class Premises(_Strict):
    address_line: str = ""
    suburb: str = ""
    state: str = ""
    postcode: str = ""


class Renter(_Strict):
    full_name: str = ""
    address_for_service: str = ""
    service_postcode: str = ""
    phone_business_hours: str = ""
    phone_after_hours: str = ""
    email: str = ""


class RentalProvider(_Strict):
    # Must be the OWNER, never the managing agent (legal constraint on the form).
    full_name: str = ""
    service_address: str = ""
    service_postcode: str = ""
    phone_business_hours: str = ""
    phone_after_hours: str = ""
    email: str = ""


class BundleMeta(_Strict):
    tenancy_id: str = ""
    lot_id: str = ""
    source: str = ""
    as_at: str = ""
    # Optional data-quality flag. GEA CRM may set this (e.g. >1 active lease, or a
    # missing owner link); other providers omit it. Non-null = surface to the PM.
    note: str | None = None


class TenancyBundle(_Strict):
    premises: Premises = Field(default_factory=Premises)
    renters: list[Renter] = Field(default_factory=list)
    rental_provider: RentalProvider = Field(default_factory=RentalProvider)
    meta: BundleMeta = Field(default_factory=BundleMeta)


def apply_service_address_defaults(bundle: TenancyBundle) -> TenancyBundle:
    """Default a blank renter service address/postcode to the premises'.

    Both the GEA CRM provider docstring and several form specs already
    document this as the intended contract ("null address_for_service when
    service address == premises") — this is the one place that actually
    implements it, applied provider-agnostically so PropertyMe, GEA CRM, and
    the fixture provider all benefit without per-provider duplication.
    Renters that already carry a real (different) service address are left
    untouched.
    """

    if not bundle.premises.address_line:
        return bundle

    changed = False
    new_renters = []
    for renter in bundle.renters:
        if renter.address_for_service.strip():
            new_renters.append(renter)
            continue
        changed = True
        new_renters.append(
            renter.model_copy(
                update={
                    "address_for_service": bundle.premises.address_line,
                    "service_postcode": renter.service_postcode
                    or bundle.premises.postcode,
                }
            )
        )

    if not changed:
        return bundle
    return bundle.model_copy(update={"renters": new_renters})


# ── Request / result ───────────────────────────────────────────────────────────


class FillRequest(_Strict):
    form: str
    identifiers: dict[str, Any] = Field(default_factory=dict)
    fields: dict[str, Any] = Field(default_factory=dict)
    out_dir: str = "./out"
    # Optional per-request provider override (fixture/propertyme/gea_crm). None
    # falls back to the FORMS_DATA_PROVIDER env var (select_provider's default).
    provider: str | None = None


class FillFiles(_Strict):
    docx: str | None = None
    pdf: str | None = None


class FillResult(_Strict):
    ok: bool
    form: str
    files: FillFiles = Field(default_factory=FillFiles)
    # Names of the declared fields that were filled (engine contract: a list,
    # so the caller can show the PM exactly what came through).
    filled_fields: list[str] = Field(default_factory=list)
    blank_fields: list[str] = Field(default_factory=list)
    # Non-fatal notes (e.g. "PDF skipped — LibreOffice unavailable").
    warnings: list[str] = Field(default_factory=list)


def build_request(
    *,
    form: str | None = None,
    identifiers: str | dict[str, Any] | None = None,
    fields: str | dict[str, Any] | None = None,
    out_dir: str | None = None,
    json_payload: str | dict[str, Any] | None = None,
) -> FillRequest:
    """Normalise any accepted input style into one ``FillRequest`` (R1).

    Precedence: a whole-payload ``json_payload`` (``--json`` / stdin) is used as
    the base; explicit split flags (``form`` / ``identifiers`` / ``fields`` /
    ``out_dir``) override matching keys when provided. This lets the HTTP body and
    the CLI flags share one builder.
    """

    base: dict[str, Any] = {}
    if json_payload is not None:
        base = _as_obj(json_payload, "json payload")

    if form is not None:
        base["form"] = form
    if identifiers is not None:
        base["identifiers"] = _as_obj(identifiers, "identifiers")
    if fields is not None:
        base["fields"] = _as_obj(fields, "fields")
    if out_dir is not None:
        base["out_dir"] = out_dir

    if "form" not in base or not base["form"]:
        raise ValueError("missing required 'form'")

    return FillRequest(**base)


def _as_obj(value: str | dict[str, Any], label: str) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON for {label}: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{label} must be a JSON object")
    return parsed
