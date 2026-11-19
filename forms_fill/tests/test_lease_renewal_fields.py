"""Renewal term from request fields (incident 19/11/2026, goal step 4).

The gea-mcp connector sends the new term as start_date / end_date / rent /
rent_period. Those must land on the lease over PropertyMe's current-term
values, and a term that ends on or before it starts must be refused.
"""

import pytest

from forms_fill.forms.residential_rental_agreement.spec import build_context
from forms_fill.models import TenancyBundle

# Real tenancy the connector renews (read-only fixture of its identifiers).
LOT = "a9100166-043a-4958-8fe8-b7315d4a9193"
TENANCY = "b38d046b-5df0-fef1-990a-d04df01c6c61"


def _pm_bundle() -> TenancyBundle:
    # What PropertyMe returns for the CURRENT term — must not reach the PDF.
    return TenancyBundle.model_validate(
        {
            "premises": {"address_line": "1 Test St", "postcode": "3806"},
            "lease": {"rent_amount": "3500", "rent_period": "week",
                      "fixed_start_date": "2026-11-28", "fixed_end_date": "2027-11-27"},
            "meta": {"lot_id": LOT, "tenancy_id": TENANCY, "source": "propertyme"},
        }
    )


def _renewal(**over) -> dict:
    fields = {"is_renewal": "true", "term_type": "fixed", "start_date": "2027-11-28",
              "end_date": "2028-11-27", "rent": "3867", "rent_period": "monthly"}
    fields.update(over)
    return fields


def test_renewal_fields_win_over_propertyme_current_term():
    ctx = build_context(_pm_bundle(), _renewal())
    assert ctx["fixed_start_date"] == "2027-11-28"
    assert ctx["fixed_end_date"] == "2028-11-27"
    assert ctx["rent_amount"] == "3867"
    assert ctx["rent_period"] == "calendar month"


@pytest.mark.parametrize("end", ["2027-11-28", "2027-11-01"])
def test_end_on_or_before_start_is_rejected(end):
    with pytest.raises(ValueError, match="end_date .* after start_date"):
        build_context(_pm_bundle(), _renewal(end_date=end))


def test_alias_dates_must_be_iso():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        build_context(_pm_bundle(), _renewal(start_date="28/11/2027"))


def test_alias_and_canonical_name_disagreeing_is_rejected():
    with pytest.raises(ValueError, match="start_date"):
        build_context(_pm_bundle(), _renewal(fixed_start_date="2027-12-01"))
