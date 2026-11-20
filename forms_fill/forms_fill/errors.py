"""Typed errors. Shells (CLI/API) convert these to stderr / HTTP status."""

from __future__ import annotations


class FormsFillError(Exception):
    """Base for all expected, user-facing failures."""


class UnknownFormError(FormsFillError):
    """Requested form key is not in the registry."""


class ProviderConfigError(FormsFillError):
    """Data provider is misconfigured (e.g. missing API key)."""


class MissingIdentifiersError(FormsFillError):
    """Caller sent no lot_id/tenancy_id for a form that needs a tenancy fetch."""


class TenancyNotFoundError(FormsFillError):
    """No tenancy/property matched the supplied identifiers."""


class RenderError(FormsFillError):
    """Document or PDF rendering failed."""


class UpstreamError(FormsFillError):
    """A data provider's upstream service failed (e.g. 5xx after retries)."""


class ProviderContractError(FormsFillError):
    """A provider response was missing a key the contract guarantees."""


class SearchUnsupportedError(FormsFillError):
    """The selected data provider cannot search lots by address."""


class FetchUnsupportedError(FormsFillError):
    """The selected data provider can find a property but not its contact/
    tenancy details — the caller should fall back to manual field entry
    rather than treat this as an upstream failure."""


class ApplicationAiError(FormsFillError):
    """applicationAI lookup failed. ``code`` is the only thing callers expose."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class UnconfirmedItemsError(FormsFillError):
    """The PM has not confirmed every review item for a lease (R11, KTD7)."""

    def __init__(self, items: list[str]) -> None:
        super().__init__(f"PM has not confirmed: {', '.join(items)}")
        self.items = items
