"""GEA CRM provider (PropertyDataProvider adapter).

GEA CRM exposes a read-only, server-to-server endpoint that returns a tenancy
bundle in exactly our ``TenancyBundle`` shape, so this is a thin adapter: call
the endpoint with the sync-secret header and map the response 1:1.

Endpoint:
    GET {GEA_CRM_BASE_URL}/api/forms/tenancy-bundle?lotId=<id>&tenancyId=<id>
    header: x-sync-secret: {GEA_CRM_SYNC_SECRET}

Provider-specific blanks are expected, not errors (see module-level notes in the
integration request): owner-only contact, always-blank after-hours, null
``address_for_service`` when service address == premises, and an optional
``meta.note`` data-quality flag.

This file is the only thing that changes to add GEA CRM — the forms-rendering
tool (core, registry, renderer, CLI, API) is untouched.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx

from ..errors import (
    ProviderConfigError,
    ProviderContractError,
    TenancyNotFoundError,
    UpstreamError,
)
from ..models import (
    BundleMeta,
    Premises,
    RentalProvider,
    Renter,
    TenancyBundle,
)
from .base import LotMatch, PropertyDataProvider

log = logging.getLogger("forms_fill.providers.gea_crm")

_RETRY_BACKOFFS = (0.5, 1.0)  # 3 attempts total on 5xx / transport errors
_MAX_SEARCH_RESULTS = 10  # matches PropertyMeProvider's cap for consistent UX

# Keys the contract guarantees are always present (blanks allowed, omission not).
_PREMISES_KEYS = ("address_line", "suburb", "state", "postcode")
_RENTER_KEYS = (
    "full_name",
    "address_for_service",
    "service_postcode",
    "phone_business_hours",
    "phone_after_hours",
    "email",
)
_PROVIDER_KEYS = (
    "full_name",
    "service_address",
    "service_postcode",
    "phone_business_hours",
    "phone_after_hours",
    "email",
)
_META_KEYS = ("tenancy_id", "lot_id", "source", "as_at")  # note is optional


class GeaCrmProvider(PropertyDataProvider):
    name = "gea_crm"

    def __init__(self, base_url: str | None = None, sync_secret: str | None = None) -> None:
        self.base_url = (base_url or os.environ.get("GEA_CRM_BASE_URL") or "").rstrip("/")
        self.sync_secret = sync_secret or os.environ.get("GEA_CRM_SYNC_SECRET")
        if not self.base_url:
            raise ProviderConfigError("GEA_CRM_BASE_URL is not set")
        if not self.sync_secret:
            raise ProviderConfigError("GEA_CRM_SYNC_SECRET is not set")

    def fetch_bundle(self, identifiers: dict) -> TenancyBundle:
        raw = self._fetch_raw(identifiers)
        return self._to_bundle(raw)

    def search_lots(self, query: str) -> list[LotMatch]:
        """Address search against the CRM's tenancy-search endpoint (U2).

        Contract: docs/integrations/crm-data-contract-prompt.md
        ("Address search endpoint"). Returns [] rather than raising when the
        upstream simply has no matches — same convention as the other providers.
        """

        q = (query or "").strip()
        if not q:
            raise ValueError("search query must not be empty")

        resp = self._request("/api/forms/tenancy-search", {"q": q})
        status = resp.status_code
        if status == 200:
            rows = resp.json()
        elif status == 400:
            raise ValueError(f"gea_crm: bad search request: {_err(resp)}")
        elif status == 401:
            raise ProviderConfigError(
                "gea_crm: unauthorised — check GEA_CRM_SYNC_SECRET"
            )
        else:
            raise UpstreamError(f"gea_crm search {status}: {_err(resp)}")

        matches = [
            LotMatch(
                lot_id=_s(row.get("lot_id")),
                address_label=_s(row.get("address_label")),
                tenancy_id=_s(row.get("tenancy_id")),
            )
            for row in rows
        ]
        return matches[:_MAX_SEARCH_RESULTS]

    # ── network ────────────────────────────────────────────────────────────────
    def _request(self, path: str, params: dict[str, str]) -> httpx.Response:
        """GET with the shared auth header + retry-on-5xx/transport-error loop."""

        url = f"{self.base_url}{path}"
        headers = {"x-sync-secret": self.sync_secret, "Accept": "application/json"}

        last_exc: Exception | None = None
        for attempt in range(len(_RETRY_BACKOFFS) + 1):
            try:
                resp = httpx.get(url, headers=headers, params=params, timeout=30.0)
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt < len(_RETRY_BACKOFFS):
                    time.sleep(_RETRY_BACKOFFS[attempt])
                    continue
                raise UpstreamError(f"gea_crm request failed: {exc}") from exc

            if resp.status_code >= 500:
                last_exc = UpstreamError(
                    f"gea_crm upstream {resp.status_code}: {_err(resp)}"
                )
                if attempt < len(_RETRY_BACKOFFS):
                    time.sleep(_RETRY_BACKOFFS[attempt])
                    continue
                raise last_exc
            return resp

        # Unreachable, but keep the type-checker happy.
        raise UpstreamError(f"gea_crm request failed: {last_exc}")

    def _fetch_raw(self, identifiers: dict) -> dict[str, Any]:
        tenancy_id = identifiers.get("tenancy_id")
        lot_id = identifiers.get("lot_id")
        if not tenancy_id and not lot_id:
            raise TenancyNotFoundError(
                "gea_crm: provide at least one of tenancy_id, lot_id"
            )

        # Prefer tenancyId when known.
        params: dict[str, str] = {}
        if tenancy_id:
            params["tenancyId"] = str(tenancy_id)
        if lot_id:
            params["lotId"] = str(lot_id)

        resp = self._request("/api/forms/tenancy-bundle", params)
        status = resp.status_code
        if status == 200:
            return resp.json()
        if status == 400:
            raise TenancyNotFoundError(
                f"gea_crm: bad request (no identifier?): {_err(resp)}"
            )
        if status == 401:
            raise ProviderConfigError(
                "gea_crm: unauthorised — check GEA_CRM_SYNC_SECRET"
            )
        if status == 404:
            raise TenancyNotFoundError(f"no current tenancy: {_err(resp)}")
        # Any other status: surface plainly (5xx already retried in _request).
        raise UpstreamError(f"gea_crm unexpected {status}: {_err(resp)}")

    # ── shape ────────────────────────────────────────────────────────────────--
    @staticmethod
    def _to_bundle(raw: dict[str, Any]) -> TenancyBundle:
        _assert_contract(raw)

        premises = Premises(**{k: _s(raw["premises"].get(k)) for k in _PREMISES_KEYS})
        renters = [
            Renter(**{k: _s(r.get(k)) for k in _RENTER_KEYS})
            for r in raw["renters"]
        ]
        provider = RentalProvider(
            **{k: _s(raw["rental_provider"].get(k)) for k in _PROVIDER_KEYS}
        )

        meta_in = raw["meta"]
        note = meta_in.get("note")
        meta = BundleMeta(
            tenancy_id=_s(meta_in.get("tenancy_id")),
            lot_id=_s(meta_in.get("lot_id")),
            source=_s(meta_in.get("source")) or "gea_crm",
            as_at=_s(meta_in.get("as_at")),
            note=note,
        )
        if note:
            log.warning(
                "gea_crm data-quality note for tenancy %s / lot %s: %s",
                meta.tenancy_id,
                meta.lot_id,
                note,
            )

        return TenancyBundle(
            premises=premises,
            renters=renters,
            rental_provider=provider,
            meta=meta,
            # Optional — not (yet) part of the guaranteed contract above.
            # Left blank rather than guessed if the CRM endpoint omits them.
            current_rent=_s(raw.get("current_rent")),
            rent_period=_s(raw.get("rent_period")),
        )


def _assert_contract(raw: dict[str, Any]) -> None:
    """Fail loudly if the response drops a guaranteed key."""

    for top in ("premises", "renters", "rental_provider", "meta"):
        if top not in raw:
            raise ProviderContractError(f"gea_crm response missing '{top}'")
    if not isinstance(raw["renters"], list):
        raise ProviderContractError("gea_crm 'renters' must be a list")

    _require(raw["premises"], _PREMISES_KEYS, "premises")
    _require(raw["rental_provider"], _PROVIDER_KEYS, "rental_provider")
    _require(raw["meta"], _META_KEYS, "meta")
    for i, renter in enumerate(raw["renters"]):
        _require(renter, _RENTER_KEYS, f"renters[{i}]")


def _require(obj: dict[str, Any], keys: tuple[str, ...], where: str) -> None:
    missing = [k for k in keys if k not in obj]
    if missing:
        raise ProviderContractError(
            f"gea_crm response missing key(s) {missing} in {where}"
        )


def _err(resp: httpx.Response) -> str:
    try:
        body = resp.json()
        if isinstance(body, dict) and "error" in body:
            return str(body["error"])
    except ValueError:
        pass
    return resp.text[:200]


def _s(value: object) -> str:
    """Coerce null/None → "" (contract: blanks are "" or null, never dropped)."""

    return "" if value is None else str(value)
