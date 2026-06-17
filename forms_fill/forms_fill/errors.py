"""Typed errors. Shells (CLI/API) convert these to stderr / HTTP status."""

from __future__ import annotations


class FormsFillError(Exception):
    """Base for all expected, user-facing failures."""


class UnknownFormError(FormsFillError):
    """Requested form key is not in the registry."""


class ProviderConfigError(FormsFillError):
    """Data provider is misconfigured (e.g. missing API key)."""


class TenancyNotFoundError(FormsFillError):
    """No tenancy/property matched the supplied identifiers."""


class RenderError(FormsFillError):
    """Document or PDF rendering failed."""
