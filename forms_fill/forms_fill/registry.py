"""Template registry (U2, R11).

A form is registered under a stable key. Adding a future form (VCAT, inspection)
means writing a spec module and registering it here — no change to the core,
renderer, CLI, or API.
"""

from __future__ import annotations

from .errors import UnknownFormError
from .formspec import FormSpec
from .forms.breach_of_duty_notice.spec import SPEC as BREACH_SPEC
from .forms.cav_rent_increase_notice.spec import SPEC as CAV_SPEC
from .forms.notice_to_vacate.spec import SPEC as NTV_SPEC

FORM_REGISTRY: dict[str, FormSpec] = {
    CAV_SPEC.key: CAV_SPEC,
    NTV_SPEC.key: NTV_SPEC,
    BREACH_SPEC.key: BREACH_SPEC,
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


def form_catalogue() -> list[dict]:
    """Registry-driven catalogue for the web UI (U1): key, title, group, and
    the caller-supplied fields the PM needs to enter for each form."""

    return [
        {
            "key": spec.key,
            "title": spec.title or spec.key,
            "group": spec.group or "other",
            "caller_fields": [
                {"name": name, "label": label}
                for name, label in spec.caller_field_labels.items()
            ],
        }
        for key, spec in sorted(FORM_REGISTRY.items())
    ]
