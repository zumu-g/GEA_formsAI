"""VaultRE provider (PropertyDataProvider adapter) — sales forms (KTD, plan
2026-07-30 provider-routing request).

Contract confirmed against GEA_crmAI's own working VaultRE integration
(``src/lib/vaultre/{config,client}.ts``), not guessed: dual-header auth
(integrator ``X-Api-Key`` + a *separate*, per-agency ``Authorization: Bearer``
token), base URL ``https://ap-southeast-2.api.vaultre.com.au/api/v1.3``, and
``GET /properties/residential/sale`` returning either a bare array or
``{"items": [...]}`` of listings shaped ``{id, address: {streetAddress,
suburb, state, postcode}, ...}``.

As of this file's authoring, GEA only has the ``X-Api-Key`` half — the
agency ``Authorization: Bearer`` token is still pending issuance from VaultRE
(same "PENDING" state GEA_crmAI's own client documents). ``__init__`` raises
``ProviderConfigError`` until *both* ``VAULTRE_API_KEY`` and
``VAULTRE_BEARER_TOKEN`` are set — the same graceful-until-configured shape
``gea_crm.py`` and GEA_crmAI's own client already use, so this file activates
the moment the second credential lands with no further code change.

**No vendor/owner-contact endpoint is confirmed.** GEA_crmAI's own VaultRE
types (``src/lib/vaultre/types.ts``) only model listing/address/price fields
— "the API returns much more" per that file's comment, but nothing there
maps an owner's name, phone, or email. Inventing that shape here would be
guessing at a real third-party contract with no source to check it against
(the same discipline as the PM leasing-authority form's placeholder clauses).
``fetch_bundle`` therefore raises ``FetchUnsupportedError`` rather than
fabricate vendor contact data — the API layer maps that to the same
``no_current_tenancy`` response sales forms already use to prompt the "Add
manually" flow (``forms_fill/static/index.html``), so the UI degrades
correctly with no extra plumbing.
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

from ..errors import (
    FetchUnsupportedError,
    ProviderConfigError,
    UpstreamError,
)
from ..models import TenancyBundle
from .base import LotMatch, PropertyDataProvider

_RETRY_BACKOFFS = (0.5, 1.0)
_MAX_SEARCH_RESULTS = 10
_DEFAULT_BASE_URL = "https://ap-southeast-2.api.vaultre.com.au/api/v1.3"


class VaultreProvider(PropertyDataProvider):
    name = "vaultre"

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        bearer_token: str | None = None,
    ) -> None:
        self.base_url = (
            base_url or os.environ.get("VAULTRE_BASE_URL") or _DEFAULT_BASE_URL
        ).rstrip("/")
        self.api_key = api_key or os.environ.get("VAULTRE_API_KEY")
        self.bearer_token = bearer_token or os.environ.get("VAULTRE_BEARER_TOKEN")
        if not self.api_key:
            raise ProviderConfigError("VAULTRE_API_KEY is not set")
        if not self.bearer_token:
            raise ProviderConfigError(
                "VAULTRE_BEARER_TOKEN is not set — VaultRE issues this "
                "per-agency; the API key alone is not enough (see GEA_crmAI's "
                "own vaultre client, same pending state)"
            )

    def fetch_bundle(self, identifiers: dict) -> TenancyBundle:
        raise FetchUnsupportedError(
            "vaultre: no confirmed endpoint for vendor/owner contact details — "
            "use 'Add manually' to enter vendor details for this property"
        )

    def search_lots(self, query: str) -> list[LotMatch]:
        """Address search over active residential-for-sale listings.

        VaultRE's confirmed endpoint has no documented address-query
        parameter (GEA_crmAI's client fetches the full active-listing set),
        so matching is done client-side against the returned address fields.
        """

        q = (query or "").strip().lower()
        if not q:
            raise ValueError("search query must not be empty")

        items = self._list_residential_sale()
        matches: list[LotMatch] = []
        for item in items:
            label = _address_label(item)
            if q in label.lower():
                matches.append(
                    LotMatch(lot_id=str(item.get("id", "")), address_label=label)
                )
        return matches[:_MAX_SEARCH_RESULTS]

    def _list_residential_sale(self) -> list[dict[str, Any]]:
        resp = self._request("/properties/residential/sale")
        status = resp.status_code
        if status == 200:
            body = resp.json()
            return body if isinstance(body, list) else (body.get("items") or [])
        if status == 401:
            raise ProviderConfigError(
                "vaultre: unauthorised — check VAULTRE_API_KEY / VAULTRE_BEARER_TOKEN"
            )
        raise UpstreamError(f"vaultre listings {status}: {_err(resp)}")

    def _request(self, path: str) -> httpx.Response:
        url = f"{self.base_url}{path}"
        headers = {
            "X-Api-Key": self.api_key,
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
        }
        last_exc: Exception | None = None
        for attempt in range(len(_RETRY_BACKOFFS) + 1):
            try:
                resp = httpx.get(url, headers=headers, timeout=30.0)
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt < len(_RETRY_BACKOFFS):
                    time.sleep(_RETRY_BACKOFFS[attempt])
                    continue
                raise UpstreamError(f"vaultre request failed: {exc}") from exc
            if resp.status_code >= 500:
                last_exc = UpstreamError(f"vaultre upstream {resp.status_code}: {_err(resp)}")
                if attempt < len(_RETRY_BACKOFFS):
                    time.sleep(_RETRY_BACKOFFS[attempt])
                    continue
                raise last_exc
            return resp
        raise UpstreamError(f"vaultre request failed: {last_exc}")


def _address_label(item: dict[str, Any]) -> str:
    addr = item.get("address") or {}
    parts = [
        addr.get("streetAddress"),
        addr.get("suburb"),
        addr.get("state"),
        addr.get("postcode"),
    ]
    return " ".join(str(p) for p in parts if p)


def _err(resp: httpx.Response) -> str:
    try:
        body = resp.json()
        if isinstance(body, dict) and "message" in body:
            return str(body["message"])
    except ValueError:
        pass
    return resp.text[:200]
