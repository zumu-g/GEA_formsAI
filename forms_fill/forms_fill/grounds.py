"""Statutory grounds catalogue (U1, R1).

Machine-readable catalogue of the RTA 1997 (Vic) grounds/notice types a
Residential Rental Provider issues to a renter, transcribed from the CAV/VCAT
groupings supplied by GEA (2026-07-08). Each entry links a statutory section to
the registry form that renders it and the minimum notice period the ground
fixes.

``min_notice_days`` semantics: 0 = notice may specify today or a later date
("immediate" tier); None = no fixed statutory period applies (general notices);
otherwise the "at least N days" tier.

This module is data + lookups only — it never computes termination dates or
validates statutory logic (the caller/workflow owns that, same rule as the
form specs).
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import FormsFillError


class UnknownGroundError(FormsFillError):
    """Raised when a section number is not in the catalogue."""


FAMILIES = ("vacate", "breach_of_duty", "general", "rent_increase")


@dataclass(frozen=True)
class Ground:
    section: str
    description: str
    family: str
    min_notice_days: int | None
    form_key: str


def _v(section: str, description: str, days: int) -> Ground:
    return Ground(section, description, "vacate", days, "notice_to_vacate")


def _b(section: str, description: str) -> Ground:
    # Breach-of-duty notices carry a statutory 14-day remedy period.
    return Ground(section, description, "breach_of_duty", 14, "breach_of_duty_notice")


def _g(section: str, description: str, form_key: str = "general_notice") -> Ground:
    return Ground(section, description, "general", None, form_key)


GROUNDS: tuple[Ground, ...] = (
    # --- Notice to Vacate: today or a later date (immediate tier) ---
    _v("91N(3)", "Death of sole renter", 0),
    _v("91ZI", "Damage", 0),
    _v("91ZJ", "Danger", 0),
    _v("91ZL", "Unsafe premises", 0),
    # --- Notice to Vacate: at least 14 days ---
    _v("91ZK", "Threats and intimidation", 14),
    _v("91ZM", "Non-payment of rent", 14),
    _v("91ZN", "Failure to pay bond", 14),
    _v("91ZO", "Failure to comply with Tribunal order", 14),
    _v("91ZP", "Successive breaches", 14),
    _v("91ZQ", "Use of premises for illegal purpose", 14),
    _v("91ZT", "Child residing on premises", 14),
    _v("91ZU", "False statement to housing authority", 14),
    _v("91ZV", "Assignment or sub-letting without consent", 14),
    _v("91ZW", "Rental provider resuming principal place of residence", 14),
    # --- Notice to Vacate: at least 28 days ---
    _v("91ZZG", "Pet kept without consent", 28),
    # --- Notice to Vacate: at least 90 days ---
    _v("91ZX", "Repair, renovation or reconstruction", 90),
    _v("91ZY", "Demolition", 90),
    _v("91ZZ", "Change of use of premises", 90),
    _v("91ZZA", "Occupation by residential rental provider or family", 90),
    _v("91ZZB", "Premises are being sold", 90),
    _v("91ZZC", "Premises required for public purposes", 90),
    _v("91ZZE", "Renter no longer meets eligibility for public housing", 90),
    # --- Breach of Duty (to renter/s of rented premises) ---
    _b("60(1)", "Nuisance"),
    _b("60(2)", "Interference with peace"),
    _b("61", "Damaged premises or common areas"),
    _b("63(1)", "Renter must keep and leave rented premises reasonably clean"),
    _b("63A", "Interfered with safety-related duties"),
    _b("64(1A)(a)", "Fixtures without consent"),
    _b("64(1A)(b)", "Alterations without consent"),
    _b("64(2)", "Failure to restore premises"),
    _b("70(2)", "Failure to supply key"),
    _b("70(3)", "Change of lock without consent"),
    _b("89", "Refusal to permit entry"),
    # --- General notices (to renter) ---
    _g("55(1)", "Utility charges"),
    _g("78(1)", "Damage by renter"),
    _g("79(1)", "Cost of repairs"),
    _g("79(2)", "Cost of repairs by residential rental provider"),
    _g("86", "Notice of entry", form_key="notice_of_entry"),
    # --- Rent increase ---
    Ground("44(1)", "Rent increase", "rent_increase", 90, "cav_rent_increase_notice"),
)

_BY_SECTION = {g.section: g for g in GROUNDS}


def get_ground(section: str) -> Ground:
    try:
        return _BY_SECTION[section.strip()]
    except KeyError:
        available = ", ".join(g.section for g in GROUNDS)
        raise UnknownGroundError(
            f"unknown ground '{section}'. Available sections: {available}"
        ) from None


def grounds_catalogue(family: str | None = None) -> list[dict]:
    if family is not None and family not in FAMILIES:
        raise UnknownGroundError(
            f"unknown family '{family}'. Available families: {', '.join(FAMILIES)}"
        )
    return [
        {
            "section": g.section,
            "description": g.description,
            "family": g.family,
            "min_notice_days": g.min_notice_days,
            "form_key": g.form_key,
        }
        for g in GROUNDS
        if family is None or g.family == family
    ]
