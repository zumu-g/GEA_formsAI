"""Property-data provider interface + selection (U3, R12).

The fill core depends only on this interface. PropertyMe is the first adapter;
GEA CRM is a later additive adapter against the same ``TenancyBundle`` contract
(``docs/integrations/crm-data-contract-prompt.md``). Swapping providers changes
nothing in the core — only which adapter ``select_provider`` returns.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod

from dataclasses import dataclass

from ..errors import ProviderConfigError, SearchUnsupportedError
from ..models import TenancyBundle


@dataclass(frozen=True)
class LotMatch:
    """One address-search result: enough to identify and preview a tenancy."""

    lot_id: str
    address_label: str
    tenancy_id: str = ""


class PropertyDataProvider(ABC):
    name: str = "base"

    @abstractmethod
    def fetch_bundle(self, identifiers: dict) -> TenancyBundle:
        """Return the tenancy bundle for the given identifiers (lot_id/tenancy_id)."""

    def search_lots(self, query: str) -> list[LotMatch]:
        """Address search. Providers opt in; the default is a typed refusal so
        the API/UI can degrade to manual ID entry rather than erroring."""

        raise SearchUnsupportedError(
            f"provider '{self.name}' does not support address search — "
            "enter Lot ID / Tenancy ID directly"
        )


def select_provider(name: str | None = None) -> PropertyDataProvider:
    """Pick a provider by explicit name or the ``FORMS_DATA_PROVIDER`` env var.

    Defaults to the fixture provider so the CAV path works end-to-end without a
    live PropertyMe key.
    """

    name = (name or os.environ.get("FORMS_DATA_PROVIDER") or "fixture").strip().lower()

    if name == "fixture":
        from .fixture import FixtureProvider

        return FixtureProvider()
    if name == "propertyme":
        from .propertyme import PropertyMeProvider

        return PropertyMeProvider()
    if name == "gea_crm":
        from .gea_crm import GeaCrmProvider

        return GeaCrmProvider()
    if name == "vaultre":
        from .vaultre import VaultreProvider

        return VaultreProvider()

    raise ProviderConfigError(
        f"unknown data provider '{name}'. Valid: fixture, propertyme, gea_crm, vaultre"
    )
