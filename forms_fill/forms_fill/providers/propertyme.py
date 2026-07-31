"""PropertyMe provider (U2 — live API, confirmed 2026-07-06).

Targets the confirmed PropertyMe API: base ``https://app.propertyme.com/api``,
Swagger at ``GET /api/openapi``, resources under ``/v1``. Auth is OAuth2
Authorization Code with a long-lived refresh token (verified: refresh tokens
are NOT rotated on use, so env/file storage is stable).

Required env:
    PME_CLIENT_ID / PME_CLIENT_SECRET — OAuth client credentials
    PME_REFRESH_TOKEN or PME_TOKEN_FILE — refresh token (file: JSON with a
        ``refresh_token`` key, e.g. secrets/propertyme-tokens.json)
Optional env:
    PME_TOKEN_URL — default https://login.propertyme.com/connect/token
    PME_API_BASE  — default https://app.propertyme.com/api

Data flow per fill (all read-only GETs):
    /v1/tenancies?LotId=..&IncludeClosed=false  → active tenancy (rent, names)
    /v1/contacts/{Tenancy.ContactId}            → renter persons (names/contacts)
    /v1/lots/{LotId}/detail                     → premises + Ownership.ContactId
    /v1/contacts/{Ownership.ContactId}          → OWNER name + service address

COMPLIANCE: the rental-provider name comes from the lot's *Ownership* contact —
never the managing agency, which does not appear anywhere on this path.
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
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
    LeaseTerms,
    Premises,
    RentalProvider,
    Renter,
    TenancyBundle,
)
from .base import LotMatch, PropertyDataProvider

_DEFAULT_API_BASE = "https://app.propertyme.com/api"
_DEFAULT_TOKEN_URL = "https://login.propertyme.com/connect/token"
# PropertyMe's edge blocks default library user agents (403) — identify honestly.
_USER_AGENT = "gea-forms-fill/0.1"
_MAX_RENTERS = 4
_MAX_SEARCH_RESULTS = 10


class PropertyMeProvider(PropertyDataProvider):
    name = "propertyme"

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        refresh_token: str | None = None,
        token_file: str | None = None,
        api_base: str | None = None,
        token_url: str | None = None,
    ) -> None:
        self.client_id = client_id or os.environ.get("PME_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("PME_CLIENT_SECRET")
        self.token_file = token_file or os.environ.get("PME_TOKEN_FILE")
        self.refresh_token = refresh_token or os.environ.get("PME_REFRESH_TOKEN")
        if not self.refresh_token and self.token_file:
            try:
                self.refresh_token = json.loads(Path(self.token_file).read_text()).get(
                    "refresh_token"
                )
            except (OSError, ValueError) as exc:
                raise ProviderConfigError(f"PME_TOKEN_FILE unreadable: {exc}") from exc
        if not (self.client_id and self.client_secret and self.refresh_token):
            raise ProviderConfigError(
                "propertyme provider needs PME_CLIENT_ID, PME_CLIENT_SECRET and a "
                "refresh token (PME_REFRESH_TOKEN or PME_TOKEN_FILE)"
            )
        self.api_base = (
            api_base or os.environ.get("PME_API_BASE") or _DEFAULT_API_BASE
        ).rstrip("/")
        self.token_url = (
            token_url or os.environ.get("PME_TOKEN_URL") or _DEFAULT_TOKEN_URL
        )
        self._access_token: str | None = None
        self._expires_at: float = 0.0

    # ── OAuth ───────────────────────────────────────────────────────────────────

    def _refresh(self) -> None:
        try:
            resp = httpx.post(
                self.token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"User-Agent": _USER_AGENT},
                timeout=30.0,
            )
        except httpx.HTTPError as exc:
            raise UpstreamError(f"propertyme token refresh failed: {exc}") from exc
        if resp.status_code >= 500:
            raise UpstreamError(
                f"propertyme token endpoint returned {resp.status_code}"
            )
        if resp.status_code >= 400:
            raise ProviderConfigError(
                f"propertyme token refresh rejected ({resp.status_code}) — "
                "check client credentials / refresh token"
            )
        tok = resp.json()
        if not tok.get("access_token"):
            raise ProviderConfigError(
                "propertyme token endpoint returned 200 without an access_token"
            )
        self._access_token = tok["access_token"]
        self._expires_at = time.time() + tok.get("expires_in", 3600) - 60
        # Rotation-safe: PMe doesn't rotate refresh tokens today, but if a new one
        # ever arrives, persist it immediately so it is never lost.
        new_refresh = tok.get("refresh_token")
        if new_refresh and new_refresh != self.refresh_token:
            self.refresh_token = new_refresh
            if self.token_file:
                try:
                    path = Path(self.token_file)
                    data = json.loads(path.read_text()) if path.exists() else {}
                    data["refresh_token"] = new_refresh  # persist the secret only
                    path.write_text(json.dumps(data, indent=2))
                except OSError:
                    # ponytail: best-effort persist; env-supplied tokens can't be written back
                    pass

    def _token(self) -> str:
        if not self._access_token or time.time() >= self._expires_at:
            self._refresh()
        assert self._access_token is not None
        return self._access_token

    # ── network seam ────────────────────────────────────────────────────────────

    def _get(self, path: str, params: dict | None = None) -> Any:
        url = f"{self.api_base}{path}"
        headers = {
            "Authorization": f"Bearer {self._token()}",
            "Accept": "application/json",
            "User-Agent": _USER_AGENT,
        }
        try:
            resp = httpx.get(url, headers=headers, params=params or {}, timeout=60.0)
            if resp.status_code == 401:
                # stale access token — refresh once and retry
                self._refresh()
                headers["Authorization"] = f"Bearer {self._access_token}"
                resp = httpx.get(
                    url, headers=headers, params=params or {}, timeout=60.0
                )
        except httpx.HTTPError as exc:
            raise UpstreamError(f"propertyme request failed: {exc}") from exc
        if resp.status_code == 404:
            raise TenancyNotFoundError(f"propertyme: not found: {path}")
        if resp.status_code == 401:
            raise ProviderConfigError("propertyme: unauthorized after token refresh")
        if resp.status_code >= 400:
            raise UpstreamError(
                f"propertyme returned {resp.status_code} for {path}: {resp.text[:200]}"
            )
        return resp.json()

    # ── bundle assembly ─────────────────────────────────────────────────────────

    def fetch_bundle(self, identifiers: dict) -> TenancyBundle:
        lot_id = _s(identifiers.get("lot_id"))
        tenancy_id = _s(identifiers.get("tenancy_id"))
        if not lot_id and not tenancy_id:
            raise TenancyNotFoundError(
                "propertyme: provide at least one of lot_id, tenancy_id"
            )

        tenancy, note = self._resolve_tenancy(lot_id, tenancy_id)
        tenancy_lot = _s(tenancy.get("LotId"))
        if not tenancy_lot:
            raise ProviderContractError("propertyme: tenancy record missing LotId")
        lot_detail = self._get(f"/v1/lots/{tenancy_lot}/detail")
        renters = self._renters(tenancy)
        provider = self._owner(lot_detail)

        premises = _parse_address(
            _s(lot_detail.get("AddressText")) or _s(tenancy.get("LotAddress"))
        )
        meta = BundleMeta(
            tenancy_id=_s(tenancy.get("Id")),
            lot_id=_s(tenancy.get("LotId")),
            source="propertyme",
            as_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            note=note,
        )
        current_rent = _money(tenancy.get("RentAmount"))
        rent_period = _s(tenancy.get("RentPeriod"))
        return TenancyBundle(
            premises=premises,
            renters=renters,
            rental_provider=provider,
            meta=meta,
            current_rent=current_rent,
            rent_period=rent_period,
            lease=self._lease_terms(tenancy, current_rent, rent_period),
        )

    def _lease_terms(
        self, tenancy: dict[str, Any], current_rent: str, rent_period: str
    ) -> LeaseTerms:
        """Rent/period mirror the existing top-level fields (U2, R2).

        term_type, end date, bond, payment day, and first-due-date have no
        confirmed field name in the /v1/tenancies shape used elsewhere in
        this adapter (only TenancyStart, RentAmount, RentPeriod are verified
        live) — left blank rather than guessed (execution note, R4). Confirm
        against a live tenancy record or the PropertyMe API reference before
        mapping them.
        """

        return LeaseTerms(
            rent_amount=current_rent,
            rent_period=rent_period,
        )

    def _resolve_tenancy(
        self, lot_id: str, tenancy_id: str
    ) -> tuple[dict[str, Any], str | None]:
        params: dict[str, Any] = {"IncludeClosed": "false"}
        if lot_id:
            params["LotId"] = lot_id
        rows = self._get("/v1/tenancies", params)
        if not isinstance(rows, list):
            rows = rows.get("Data") or rows.get("Items") or []
        if tenancy_id:
            # ponytail: /v1/tenancies has no Id filter; at GEA's scale (~300 active)
            # the list is a single page. Always pass lot_id where possible.
            rows = [t for t in rows if _s(t.get("Id")) == tenancy_id]
        # ACTIVE only — a vacated-but-unclosed tenancy must never receive a notice
        pool = [t for t in rows if t.get("IsActive") and not t.get("IsClosed")]
        if not pool:
            raise TenancyNotFoundError(
                f"propertyme: no current tenancy for lot_id={lot_id!r} "
                f"tenancy_id={tenancy_id!r}"
            )
        note = None
        if len(pool) > 1:
            pool = sorted(pool, key=lambda t: _s(t.get("TenancyStart")), reverse=True)
            note = f"{len(pool)} active tenancies matched — most-recent used"
        return pool[0], note

    def search_lots(self, query: str, listing: str = "sale") -> list[LotMatch]:
        """Address search over the active-tenancy list.

        /v1/tenancies rows carry LotAddress, so one GET covers search (same
        single-page assumption as _resolve_tenancy — ~300 active at GEA's
        scale). Filter is a case-insensitive substring on the address.
        """

        q = (query or "").strip().lower()
        if not q:
            raise ValueError("search query must not be empty")
        rows = self._get("/v1/tenancies", {"IncludeClosed": "false"})
        if not isinstance(rows, list):
            rows = rows.get("Data") or rows.get("Items") or []
        matches = []
        for t in rows:
            if not t.get("IsActive") or t.get("IsClosed"):
                continue
            address = _s(t.get("LotAddress"))
            if q in address.lower():
                matches.append(
                    LotMatch(
                        lot_id=_s(t.get("LotId")),
                        address_label=address,
                        tenancy_id=_s(t.get("Id")),
                    )
                )
            if len(matches) >= _MAX_SEARCH_RESULTS:
                break
        return matches

    def _renters(self, tenancy: dict[str, Any]) -> list[Renter]:
        persons: list[dict[str, Any]] = []
        contact_id = _s(tenancy.get("ContactId"))
        if contact_id:
            contact = self._get(f"/v1/contacts/{contact_id}")
            body = contact.get("Contact") or contact
            persons = body.get("ContactPersons") or []
            persons = sorted(
                persons,
                key=lambda p: (not p.get("IsPrimary"), p.get("SortOrder") or 0),
            )
        if not persons:
            # fall back to the tenancy's combined name so the form is never empty
            return [
                Renter(
                    full_name=_s(tenancy.get("Name")),
                    phone_business_hours=_s(tenancy.get("ContactPhone")),
                    email=_s(tenancy.get("ContactEmail")),
                )
            ]
        return [
            Renter(
                full_name=_s(p.get("FullName"))
                or (_s(p.get("FirstName")) + " " + _s(p.get("LastName"))).strip(),
                # address for service defaults to the premises → left blank by design
                phone_business_hours=_s(p.get("WorkPhone")) or _s(p.get("CellPhone")),
                phone_after_hours=_s(p.get("HomePhone")),
                email=_s(p.get("Email")),
            )
            for p in persons[:_MAX_RENTERS]
        ]

    def _owner(self, lot_detail: dict[str, Any]) -> RentalProvider:
        ownership = lot_detail.get("Ownership") or {}
        owner_contact_id = _s(ownership.get("ContactId"))
        if not owner_contact_id:
            raise TenancyNotFoundError(
                "propertyme: lot has no active ownership record — cannot determine "
                "the rental provider (owner)"
            )
        contact = self._get(f"/v1/contacts/{owner_contact_id}")
        body = contact.get("Contact") or contact
        # NameText covers joint owners and companies (e.g. "A Smith & B Smith").
        full_name = _s(body.get("NameText")) or (
            _s(ownership.get("FirstName")) + " " + _s(ownership.get("LastName"))
        ).strip()
        service_address = _s(body.get("PostalAddressText")) or _s(
            body.get("PhysicalAddressText")
        )
        return RentalProvider(
            full_name=full_name,
            service_address=service_address,
            service_postcode=_postcode(service_address),
            phone_business_hours=_s(body.get("WorkPhone"))
            or _s(body.get("CellPhone"))
            or _s(ownership.get("CellPhone")),
            phone_after_hours=_s(body.get("HomePhone")),
            email=_s(body.get("Email")) or _s(ownership.get("Email")),
        )


_ADDR_RE = re.compile(
    r"^(?P<line>.*?),?\s+(?P<suburb>[A-Za-z' -]+?)\s+"
    r"(?P<state>VIC|NSW|QLD|SA|WA|TAS|NT|ACT)\s+(?P<postcode>\d{4})\s*$",
    re.IGNORECASE,
)


def _parse_address(text: str) -> Premises:
    """Best-effort split of "12 Example St, Richmond VIC 3121"; unparsed parts stay blank."""
    m = _ADDR_RE.match(text or "")
    if not m:
        return Premises(address_line=text or "")
    return Premises(
        address_line=(
            f"{m.group('line').rstrip(', ')}, {m.group('suburb')} "
            f"{m.group('state').upper()}"
        ).strip(", "),
        suburb=m.group("suburb"),
        state=m.group("state").upper(),
        postcode=m.group("postcode"),
    )


def _postcode(text: str) -> str:
    m = re.search(r"\b(\d{4})\s*$", text or "")
    return m.group(1) if m else ""


def _s(value: object) -> str:
    return "" if value is None else str(value)


def _money(value: object) -> str:
    """Render a numeric amount as a plain string the PM would have typed —
    "2607", not "2607.0" — without inventing decimal precision PropertyMe
    itself doesn't imply."""

    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)
