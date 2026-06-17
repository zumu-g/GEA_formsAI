"""Template registry (U2, R11).

A form is registered under a stable key. Adding a future form (VCAT, inspection)
means writing a spec module and registering it here — no change to the core,
renderer, CLI, or API.
"""

from __future__ import annotations

from .errors import UnknownFormError
from .formspec import FormSpec
from .forms.cav_rent_increase_notice.spec import SPEC as CAV_SPEC

FORM_REGISTRY: dict[str, FormSpec] = {
    CAV_SPEC.key: CAV_SPEC,
}


def get_form_spec(key: str) -> FormSpec:
    try:
        return FORM_REGISTRY[key]
    except KeyError:
        available = ", ".join(sorted(FORM_REGISTRY)) or "(none)"
        raise UnknownFormError(
            f"unknown form '{key}'. Available forms: {available}"
        ) from None


def available_forms() -> list[str]:
    return sorted(FORM_REGISTRY)
