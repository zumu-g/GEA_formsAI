"""Fixture provider (U3).

Reads a local JSON file matching the data contract. Makes the CAV fill path
end-to-end testable today, before the real PropertyMe integration exists. The
file is chosen by ``FORMS_FIXTURE_PATH`` or defaults to the bundled sample.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from ..errors import TenancyNotFoundError
from ..models import TenancyBundle
from .base import PropertyDataProvider

_DEFAULT_FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "sample_tenancy.json"


class FixtureProvider(PropertyDataProvider):
    name = "fixture"

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path or os.environ.get("FORMS_FIXTURE_PATH") or _DEFAULT_FIXTURE)

    def fetch_bundle(self, identifiers: dict) -> TenancyBundle:
        if not self.path.exists():
            raise TenancyNotFoundError(f"fixture not found: {self.path}")
        data = json.loads(self.path.read_text(encoding="utf-8"))
        # Echo identifiers into meta so callers see what was requested.
        meta = data.setdefault("meta", {})
        meta.setdefault("source", "fixture")
        if "lot_id" in identifiers:
            meta["lot_id"] = str(identifiers["lot_id"])
        if "tenancy_id" in identifiers:
            meta["tenancy_id"] = str(identifiers["tenancy_id"])
        return TenancyBundle.model_validate(data)
