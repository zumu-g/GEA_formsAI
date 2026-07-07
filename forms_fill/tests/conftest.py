import json
from pathlib import Path

import pytest

FIXTURE = (
    Path(__file__).resolve().parents[1] / "fixtures" / "sample_tenancy.json"
)


@pytest.fixture
def sample_bundle_dict() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture
def caller_fields() -> dict:
    return {
        "current_rent": 615,
        "new_rent": 650,
        "increase": 35,
        "rent_period": "weekly",
        "start_date": "2026-09-15",
        "method_basis": "market comparison (rental CMA)",
    }
