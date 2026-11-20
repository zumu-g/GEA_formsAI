"""Items the PM must confirm on the review step before a lease PDF is made (R11, KTD7).

Shared contract: the /fill gate (U4) and the review screen (U5) both use this list.
"""

CONFIRM_ITEMS: tuple[str, ...] = (
    # R1-R10 defaults
    "agreement_date",
    "renters",
    "fixed_end_date",
    "rent_amount",
    "first_rent_due_date",
    "bond",
    "payment_methods",
    "provider_e_service",
    "emergency_contact",
    # R11 questions the PM answers every time
    "owners_corp",
    "condition_report",
    "special_conditions",
)
