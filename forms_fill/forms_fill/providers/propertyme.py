"""PropertyMe provider (U3).

Targets PropertyMe API v2. The real endpoint paths / response JSON are an
execution-time unknown (the CRM-side integration is currently a stub), so the
network calls live behind ``_fetch_raw`` and the shape-mapping behind
``_to_bundle`` — only those two seams change once the live API is confirmed.
Everything above this file (core, CLI, API) is already final.

Required env:
    PROPERTYME_API_KEY    — bearer token
    PROPERTYME_BASE_URL   — defaults to https://app.propertyme.com/api/v2
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from ..errors import ProviderConfigError, TenancyNotFoundError
from ..models import (
    BundleMeta,
    Premises,
    RentalProvider,
    Renter,
    TenancyBundle,
)
from .base import PropertyDataProvider

_DEFAULT_BASE_URL = "https://app.propertyme.com/api/v2"


class PropertyMeProvider(PropertyDataProvider):
    name = "propertyme"

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("PROPERTYME_API_KEY")
        if not self.api_key:
            raise ProviderConfigError(
                "PROPERTYME_API_KEY is not set — required for the propertyme provider"
            )
        self.base_url = (
            base_url or os.environ.get("PROPERTYME_BASE_URL") or _DEFAULT_BASE_URL
        ).rstrip("/")

    def fetch_bundle(self, identifiers: dict) -> TenancyBundle:
        raw = self._fetch_raw(identifiers)
        return self._to_bundle(raw, identifiers)

    # ── network seam (isolated; finalise once live API is confirmed) ───────────
    def _fetch_raw(self, identifiers: dict) -> dict[str, Any]:
        lot_id = identifiers.get("lot_id")
        tenancy_id = identifiers.get("tenancy_id")
        if not lot_id and not tenancy_id:
            raise TenancyNotFoundError(
                "propertyme: provide at least one of lot_id, tenancy_id"
            )
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }
        # NOTE: exact path is provisional pending PropertyMe v2 docs.
        params = {k: v for k, v in identifiers.items() if v}
        try:
            resp = httpx.get(
                f"{self.base_url}/tenancies",
                headers=headers,
                params=params,
                timeout=30.0,
            )
        except httpx.HTTPError as exc:
            raise TenancyNotFoundError(f"propertyme request failed: {exc}") from exc
        if resp.status_code == 404:
            raise TenancyNotFoundError(
                f"propertyme: no tenancy for {params}"
            )
        if resp.status_code >= 400:
            raise TenancyNotFoundError(
                f"propertyme returned {resp.status_code}: {resp.text[:200]}"
            )
        return resp.json()

    # ── shape seam (isolated; finalise once live API is confirmed) ─────────────
    @staticmethod
    def _to_bundle(raw: dict[str, Any], identifiers: dict) -> TenancyBundle:
        """Normalise PropertyMe JSON → TenancyBundle.

        Defensive ``.get`` mapping; unknown fields collapse to "" rather than
        being dropped, honouring the contract's stable-key rule. Field names are
        best-effort against PropertyMe conventions and may be adjusted when the
        live schema is confirmed.
        """

        prem = raw.get("property") or raw.get("premises") or {}
        premises = Premises(
            address_line=_s(prem.get("address") or prem.get("address_line")),
            suburb=_s(prem.get("suburb")),
            state=_s(prem.get("state")),
            postcode=_s(prem.get("postcode")),
        )

        renters = [
            Renter(
                full_name=_s(t.get("name") or t.get("full_name")),
                address_for_service=_s(t.get("address_for_service")),
                service_postcode=_s(t.get("service_postcode")),
                phone_business_hours=_s(t.get("phone_business") or t.get("phone")),
                phone_after_hours=_s(t.get("phone_after_hours")),
                email=_s(t.get("email")),
            )
            for t in (raw.get("tenants") or raw.get("renters") or [])
        ]

        owner = raw.get("owner") or raw.get("rental_provider") or {}
        provider = RentalProvider(
            full_name=_s(owner.get("name") or owner.get("full_name")),
            service_address=_s(owner.get("service_address") or owner.get("address")),
            service_postcode=_s(owner.get("service_postcode") or owner.get("postcode")),
            phone_business_hours=_s(owner.get("phone_business") or owner.get("phone")),
            phone_after_hours=_s(owner.get("phone_after_hours")),
            email=_s(owner.get("email")),
        )

        meta = BundleMeta(
            tenancy_id=_s(identifiers.get("tenancy_id")),
            lot_id=_s(identifiers.get("lot_id")),
            source="propertyme",
            as_at=_s(raw.get("as_at")),
        )
        return TenancyBundle(
            premises=premises,
            renters=renters,
            rental_provider=provider,
            meta=meta,
        )


def _s(value: object) -> str:
    return "" if value is None else str(value)
