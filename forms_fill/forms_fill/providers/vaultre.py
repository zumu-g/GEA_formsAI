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

**Vendor/owner contact.** Confirmed against the public swagger spec
(``https://docs.api.vaultre.com.au/swagger/vaultre_v1_2.yaml``, checked
2026-07-31) — not embedded on the listing. The property detail response
carries a ``saleLifeId``; owners are a separate sub-resource keyed by it:
``GET /properties/{id}/sale/{lifeid}/owners`` returns the linked contact(s),
then ``GET /contacts/{id}`` gives the full ``ContactExtended`` record
(``displayName``/``firstName``+``lastName``, nested ``address`` ->
``suburb``/``state``, ``phoneNumbers[]`` with a ``type`` of
Home/Work/Mobile/Facsimile/Direct, ``emails[]`` as bare strings).

The owners-endpoint response body is *undocumented* in the spec
(``200: content: {}`` — no schema ref, no example), so ``_get_owners`` below
parses defensively: it accepts either a bare list or ``{"items": [...]}``,
and each entry may already be a full contact or just an id reference (in
which case it's resolved via ``_get_contact``). ponytail: unverified against
a live response — GEA_crmAI's bearer token is still pending issuance
(``__init__`` below), so this has never actually round-tripped. Re-check the
first live response shape once the token lands and loosen/tighten the
parsing then.

No ``phoneNumbers[].type`` value maps cleanly to "after hours" — the enum is
Home/Work/Mobile/Facsimile/Direct — so ``phone_business_hours`` takes
Work/Direct and ``phone_after_hours`` takes Home/Mobile; a contact with only
a mobile number gets it in both fields rather than leaving one blank.
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

from ..errors import (
    ProviderConfigError,
    TenancyNotFoundError,
    UpstreamError,
)
from ..models import BundleMeta, Premises, RentalProvider, TenancyBundle
from .base import LotMatch, PropertyDataProvider

_BUSINESS_PHONE_TYPES = ("Work", "Direct")
_AFTER_HOURS_PHONE_TYPES = ("Home", "Mobile")

# listing mode → (life-id field on the property detail, contacts sub-resource).
# Sale lives link vendors via /owners; lease lives link landlords via
# /landlords (swagger vaultre_v1_2.yaml, both confirmed present).
_LISTING_SHAPE = {
    "sale": ("saleLifeId", "owners"),
    "lease": ("leaseLifeId", "landlords"),
}


def _listing_mode(value: Any) -> str:
    listing = str(value or "sale").strip().lower()
    if listing not in _LISTING_SHAPE:
        raise ValueError(f"vaultre: unknown listing mode '{listing}' (sale|lease)")
    return listing


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
        lot_id = str(identifiers.get("lot_id") or identifiers.get("property_id") or "").strip()
        if not lot_id:
            raise ValueError("vaultre: identifiers must include 'lot_id'")
        listing = _listing_mode(identifiers.get("listing"))
        life_key, contacts_segment = _LISTING_SHAPE[listing]

        item = self._get_property(lot_id, listing)
        life_id = item.get(life_key)
        if not life_id:
            raise TenancyNotFoundError(
                f"vaultre: property {lot_id} has no {life_key} — no "
                "owner/vendor to attach; use 'Add manually'"
            )

        owners = self._get_owners(lot_id, listing, life_id, contacts_segment)
        if not owners:
            raise TenancyNotFoundError(
                f"vaultre: no owner/vendor linked to property {lot_id} — "
                "use 'Add manually' to enter vendor details for this property"
            )

        owner = owners[0]
        if not (owner.get("firstName") or owner.get("displayName") or owner.get("company")):
            contact_id = owner.get("id") or owner.get("contactId")
            if contact_id:
                owner = self._get_contact(contact_id)

        note = None
        if len(owners) > 1:
            note = f"{len(owners)} {contacts_segment} linked — only the first was used"

        return TenancyBundle(
            premises=_premises_from_item(item),
            rental_provider=_rental_provider_from_contact(owner),
            meta=BundleMeta(lot_id=lot_id, source="vaultre", note=note),
        )

    def _get_property(self, lot_id: str, listing: str) -> dict[str, Any]:
        resp = self._request(f"/properties/residential/{listing}/{lot_id}")
        status = resp.status_code
        if status == 200:
            return resp.json()
        if status == 404:
            raise TenancyNotFoundError(f"vaultre: no property with id {lot_id}")
        if status == 401:
            raise ProviderConfigError(
                "vaultre: unauthorised — check VAULTRE_API_KEY / VAULTRE_BEARER_TOKEN"
            )
        raise UpstreamError(f"vaultre property {status}: {_err(resp)}")

    def _get_owners(
        self, lot_id: str, listing: str, life_id: Any, contacts_segment: str
    ) -> list[dict[str, Any]]:
        resp = self._request(f"/properties/{lot_id}/{listing}/{life_id}/{contacts_segment}")
        status = resp.status_code
        if status == 404:
            return []
        if status == 401:
            raise ProviderConfigError(
                "vaultre: unauthorised — check VAULTRE_API_KEY / VAULTRE_BEARER_TOKEN"
            )
        if status != 200:
            raise UpstreamError(f"vaultre owners {status}: {_err(resp)}")
        body = resp.json()
        if isinstance(body, list):
            return body
        return body.get("items") or []

    def _get_contact(self, contact_id: Any) -> dict[str, Any]:
        resp = self._request(f"/contacts/{contact_id}")
        status = resp.status_code
        if status == 200:
            return resp.json()
        if status == 401:
            raise ProviderConfigError(
                "vaultre: unauthorised — check VAULTRE_API_KEY / VAULTRE_BEARER_TOKEN"
            )
        raise UpstreamError(f"vaultre contact {status}: {_err(resp)}")

    def search_lots(self, query: str, listing: str = "sale") -> list[LotMatch]:
        """Address search over active residential listings (sale or lease book).

        VaultRE's confirmed endpoints have no documented address-query
        parameter (GEA_crmAI's client fetches the full active-listing set),
        so matching is done client-side against the returned address fields.
        """

        q = (query or "").strip().lower()
        if not q:
            raise ValueError("search query must not be empty")

        items = self._list_residential(_listing_mode(listing))
        matches: list[LotMatch] = []
        for item in items:
            label = _address_label(item)
            if q in label.lower():
                matches.append(
                    LotMatch(lot_id=str(item.get("id", "")), address_label=label)
                )
        return matches[:_MAX_SEARCH_RESULTS]

    def _list_residential(self, listing: str) -> list[dict[str, Any]]:
        resp = self._request(f"/properties/residential/{listing}")
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


def _premises_from_item(item: dict[str, Any]) -> Premises:
    addr = item.get("address") or {}
    return Premises(
        address_line=_address_label(item),
        suburb=str(addr.get("suburb") or ""),
        state=str(addr.get("state") or ""),
        postcode=str(addr.get("postcode") or ""),
    )


def _rental_provider_from_contact(contact: dict[str, Any]) -> RentalProvider:
    full_name = (
        contact.get("displayName")
        or " ".join(
            p for p in (contact.get("firstName"), contact.get("lastName")) if p
        )
        or contact.get("company")
        or ""
    )

    addr = contact.get("address") or {}
    suburb = addr.get("suburb") or {}
    state = suburb.get("state") or {}
    street_parts = [addr.get("unitNumber"), addr.get("streetNumber"), addr.get("street")]
    street = " ".join(str(p) for p in street_parts if p)
    address_parts = [street, suburb.get("name"), state.get("abbreviation")]
    service_address = ", ".join(str(p) for p in address_parts if p)
    service_postcode = str(suburb.get("postcode") or "")

    phones = contact.get("phoneNumbers") or []
    business_phone = _first_phone(phones, _BUSINESS_PHONE_TYPES)
    after_hours_phone = _first_phone(phones, _AFTER_HOURS_PHONE_TYPES)

    emails = contact.get("emails") or []
    email = str(emails[0]) if emails else ""

    return RentalProvider(
        full_name=str(full_name),
        service_address=service_address,
        service_postcode=service_postcode,
        phone_business_hours=business_phone,
        phone_after_hours=after_hours_phone,
        email=email,
    )


def _first_phone(phones: list[dict[str, Any]], types: tuple[str, ...]) -> str:
    for wanted in types:
        for phone in phones:
            if phone.get("type") == wanted:
                return str(phone.get("number") or "")
    return str(phones[0].get("number") or "") if phones else ""


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
