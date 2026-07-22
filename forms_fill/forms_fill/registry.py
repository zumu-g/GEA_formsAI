"""Template registry (U2, R11).

A form is registered under a stable key. Adding a future form (VCAT, inspection)
means writing a spec module and registering it here — no change to the core,
renderer, CLI, or API.
"""

from __future__ import annotations

from .errors import UnknownFormError
from .formspec import FormSpec
from .forms.allmain_letter_of_offer.spec import SPEC as LETTER_OF_OFFER_SPEC
from .forms.breach_of_duty_notice.spec import SPEC as BREACH_SPEC
from .forms.cav_rent_increase_notice.spec import SPEC as CAV_SPEC
from .forms.condition_report.spec import SPEC as CONDITION_REPORT_SPEC
from .forms.consent_electronic_service.spec import SPEC as CONSENT_ELECTRONIC_SPEC
from .forms.general_notice.spec import SPEC as GENERAL_SPEC
from .forms.mandatory_disclosure_checklist.spec import (
    SPEC as MANDATORY_DISCLOSURE_SPEC,
)
from .forms.notice_of_entry.spec import SPEC as ENTRY_SPEC
from .forms.notice_of_goods_left_behind.spec import SPEC as GOODS_LEFT_SPEC
from .forms.notice_of_intention_to_sell.spec import SPEC as INTENTION_TO_SELL_SPEC
from .forms.notice_requesting_additional_bond.spec import SPEC as ADDITIONAL_BOND_SPEC
from .forms.notice_to_vacate.spec import SPEC as NTV_SPEC
from .forms.notice_to_vacate_death_sole_renter.spec import (
    SPEC as DEATH_SOLE_RENTER_SPEC,
)
from .forms.reiv_exclusive_sale_authority.spec import SPEC as REIV_EXCLUSIVE_SPEC
from .forms.rental_application.spec import SPEC as RENTAL_APPLICATION_SPEC
from .forms.request_repairs_inspection.spec import SPEC as REPAIRS_INSPECTION_SPEC
from .forms.residential_rental_agreement.spec import SPEC as RENTAL_AGREEMENT_SPEC
from .forms.residential_rental_agreement_5yr.spec import (
    SPEC as RENTAL_AGREEMENT_5YR_SPEC,
)
from .forms.statement_of_information_applicants.spec import (
    SPEC as STATEMENT_OF_INFORMATION_SPEC,
)

FORM_REGISTRY: dict[str, FormSpec] = {
    CAV_SPEC.key: CAV_SPEC,
    NTV_SPEC.key: NTV_SPEC,
    BREACH_SPEC.key: BREACH_SPEC,
    GENERAL_SPEC.key: GENERAL_SPEC,
    ENTRY_SPEC.key: ENTRY_SPEC,
    INTENTION_TO_SELL_SPEC.key: INTENTION_TO_SELL_SPEC,
    GOODS_LEFT_SPEC.key: GOODS_LEFT_SPEC,
    DEATH_SOLE_RENTER_SPEC.key: DEATH_SOLE_RENTER_SPEC,
    ADDITIONAL_BOND_SPEC.key: ADDITIONAL_BOND_SPEC,
    RENTAL_AGREEMENT_SPEC.key: RENTAL_AGREEMENT_SPEC,
    RENTAL_AGREEMENT_5YR_SPEC.key: RENTAL_AGREEMENT_5YR_SPEC,
    RENTAL_APPLICATION_SPEC.key: RENTAL_APPLICATION_SPEC,
    CONDITION_REPORT_SPEC.key: CONDITION_REPORT_SPEC,
    STATEMENT_OF_INFORMATION_SPEC.key: STATEMENT_OF_INFORMATION_SPEC,
    MANDATORY_DISCLOSURE_SPEC.key: MANDATORY_DISCLOSURE_SPEC,
    CONSENT_ELECTRONIC_SPEC.key: CONSENT_ELECTRONIC_SPEC,
    REPAIRS_INSPECTION_SPEC.key: REPAIRS_INSPECTION_SPEC,
    REIV_EXCLUSIVE_SPEC.key: REIV_EXCLUSIVE_SPEC,
    LETTER_OF_OFFER_SPEC.key: LETTER_OF_OFFER_SPEC,
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


# Display metadata for the web UI dropdown — one reviewed place (KTD1).
# ponytail: display map lives here, not on 19 FormSpec declarations; move onto
# FormSpec if a non-UI consumer ever needs it.
_SALES_KEYS = {"allmain_letter_of_offer", "reiv_exclusive_sale_authority"}
_SHORT_TITLES = {
    "allmain_letter_of_offer": "Letter of Offer / EOI (Allmain)",
    "breach_of_duty_notice": "Breach of duty notice",
    "cav_rent_increase_notice": "Rent increase to renter",
    "condition_report": "Condition report",
    "consent_electronic_service": "Consent to electronic service",
    "general_notice": "General notice to renter",
    "mandatory_disclosure_checklist": "Mandatory disclosure checklist",
    "notice_of_entry": "Entry notice (s 86)",
    "notice_of_goods_left_behind": "Goods left behind",
    "notice_of_intention_to_sell": "Intention to sell",
    "notice_requesting_additional_bond": "Additional bond request",
    "notice_to_vacate": "Notice to vacate",
    "notice_to_vacate_death_sole_renter": "Notice to vacate — death of sole renter",
    "reiv_exclusive_sale_authority": "Exclusive Sale Authority (REIV)",
    "rental_application": "Rental application",
    "request_repairs_inspection": "Repairs inspection / rent assessment",
    "residential_rental_agreement": "Rental agreement (Form 1)",
    "residential_rental_agreement_5yr": "Rental agreement, 5yr+ fixed term (Form 2)",
    "statement_of_information_applicants": "Statement of information for applicants",
}


def form_catalogue() -> list[dict]:
    """Registry-driven catalogue for the web UI (U1): key, title, group, and
    the caller-supplied fields the PM needs to enter for each form."""

    return [
        {
            "key": spec.key,
            "title": spec.title or spec.key,
            "group": spec.group or "other",
            "category": "GEA Sales" if key in _SALES_KEYS else "GEA PM",
            "short_title": _SHORT_TITLES.get(key) or spec.title or spec.key,
            "engine": spec.engine,
            "requires_identifiers": spec.requires_bundle,
            "caller_fields": [
                {"name": name, "label": label}
                for name, label in spec.caller_field_labels.items()
            ],
            "fields": [
                {
                    "key": name,
                    "label": spec.caller_field_labels.get(name, name),
                    "kind": "selector" if name in spec.selector_fields else "text",
                    "options": _selector_options(spec, name),
                }
                for name in spec.declared_fields
            ],
        }
        for key, spec in sorted(FORM_REGISTRY.items())
    ]


def _selector_options(spec: FormSpec, name: str) -> list[str] | None:
    """Allowed values for a selector field, from its checkbox/tick/strike ops."""

    if name not in spec.selector_fields:
        return None
    values: set[str] = set()
    for op in spec.checkbox_ops:
        if op.selector_field == name:
            values.update(op.options)
    for op in spec.tick_ops:
        if op.selector_field == name:
            values.update(op.options)
    for op in spec.strike_ops:
        if op.selector_field == name:
            values.add(op.when_value)
    return sorted(values) or None
