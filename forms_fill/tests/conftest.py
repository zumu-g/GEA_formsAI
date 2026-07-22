import json
from datetime import date, timedelta
from pathlib import Path

import pytest

FIXTURE = (
    Path(__file__).resolve().parents[1] / "fixtures" / "sample_tenancy.json"
)


@pytest.fixture
def sample_bundle_dict() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


VALID_START_DATE = (date.today() + timedelta(days=90)).isoformat()


@pytest.fixture
def caller_fields() -> dict:
    return {
        "current_rent": 615,
        "new_rent": 650,
        "increase": 35,
        "rent_period": "weekly",
        "start_date": VALID_START_DATE,
        "method_basis": "market comparison (rental CMA)",
    }
