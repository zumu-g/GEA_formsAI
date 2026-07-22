"""s44 60-day minimum notice validation on the CAV rent increase spec."""
from datetime import date, timedelta

import pytest

from forms_fill.forms.cav_rent_increase_notice.spec import _validate_start_date


def test_rejects_start_date_under_60_days():
    too_soon = (date.today() + timedelta(days=30)).isoformat()
    with pytest.raises(ValueError, match="60 days"):
        _validate_start_date(too_soon)


def test_accepts_start_date_at_least_60_days_out():
    ok = (date.today() + timedelta(days=61)).isoformat()
    _validate_start_date(ok)  # no raise
    au = (date.today() + timedelta(days=61)).strftime("%d/%m/%Y")
    _validate_start_date(au)


def test_rejects_garbage_date():
    with pytest.raises(ValueError, match="not a date"):
        _validate_start_date("next tuesday")
