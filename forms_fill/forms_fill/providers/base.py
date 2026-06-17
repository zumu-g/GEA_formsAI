"""Property-data provider interface + selection (U3, R12).

The fill core depends only on this interface. PropertyMe is the first adapter;
GEA CRM is a later additive adapter against the same ``TenancyBundle`` contract
(``docs/integrations/crm-data-contract-prompt.md``). Swapping providers changes
nothing in the core — only which adapter ``select_provider`` returns.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod

from ..errors import ProviderConfigError
from ..models import TenancyBundle


class PropertyDataProvider(ABC):
    name: str = "base"

    @abstractmethod
    def fetch_bundle(self, identifiers: dict) -> TenancyBundle:
        """Return the tenancy bundle for the given identifiers (lot_id/tenancy_id)."""


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

    raise ProviderConfigError(
        f"unknown data provider '{name}'. Valid: fixture, propertyme"
    )
