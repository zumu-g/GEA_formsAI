"""Form key ``lease`` (GEA_PM_WF plan 2026-07-31-002 U2).

``lease`` is an alias for the shipped CAV Form 1 residential rental agreement
spec, so POST /fill {form: "lease", ...} renders the DRAFT agreement with the
standard result contract.
"""

import json

import docx

from forms_fill.core import fill_form
from forms_fill.models import FillRequest, TenancyBundle
from forms_fill.providers.fixture import FixtureProvider
from forms_fill.registry import get_form_spec


def _lease_fields() -> dict:
    # Dates deliberately dd/mm/yyyy — the renderer must pass them verbatim.
    return {
        # U9: renters seed from the fetched tenancy only on a renewal —
        # machine callers filling for the sitting tenants must send this.
        "is_renewal": "true",
        "agreement_date": "01/08/2026",
        "renter1_current_address": "5 Old St",
        "renter1_current_postcode": "3122",
        "term_type": "fixed",
        "fixed_start_date": "15/08/2026",
        "fixed_end_date": "14/08/2027",
        "rent_amount": "615",
        "rent_period": "week",
        "rent_payment_day": "Thursday",
        "first_rent_due_date": "15/08/2026",
        "bond_amount": "2460",
        "bond_due_date": "15/08/2026",
        "emergency_contact_name": "GEA Maintenance",
        "emergency_phone": "0399991234",
        "emergency_email": "maint@example.com",
    }


def _all_text(path) -> str:
    document = docx.Document(str(path))
    return " ".join(
        cell.text
        for table in document.tables
        for row in table.rows
        for cell in row.cells
    )


def test_lease_resolves_to_rental_agreement_spec():
    spec = get_form_spec("lease")
    assert spec.key == "residential_rental_agreement"
    assert spec.template.exists()


def test_lease_full_payload_fills(tmp_path):
    req = FillRequest(
        form="lease",
        identifiers={"lot_id": "L-2002", "tenancy_id": "T-1001"},
        fields=_lease_fields(),
        out_dir=str(tmp_path),
    )
    result = fill_form(req, provider=FixtureProvider())
    assert result.ok
    assert result.form == "lease"
    assert result.files.docx is not None
    assert "renter1_name" in result.filled_fields
    assert "rent_amount" in result.filled_fields
    # nothing this payload supplies is reported blank
    assert not set(_lease_fields()) & set(result.blank_fields)


def test_lease_missing_renter_name_listed_blank_still_ok(tmp_path):
    class NoRenterNameProvider(FixtureProvider):
        def fetch_bundle(self, identifiers):
            data = json.loads(self.path.read_text())
            data["renters"][0]["full_name"] = ""
            return TenancyBundle.model_validate(data)

    req = FillRequest(
        form="lease",
        identifiers={},
        fields=_lease_fields(),
        out_dir=str(tmp_path),
    )
    result = fill_form(req, provider=NoRenterNameProvider())
    assert result.ok
    assert "renter1_name" in result.blank_fields


def test_lease_dates_pass_through_verbatim(tmp_path):
    req = FillRequest(
        form="lease",
        identifiers={},
        fields=_lease_fields(),
        out_dir=str(tmp_path),
    )
    result = fill_form(req, provider=FixtureProvider())
    text = _all_text(result.files.docx)
    assert "15/08/2026" in text
    assert "14/08/2027" in text
    assert "01/08/2026" in text
