from forms_fill.forms.residential_rental_agreement.spec import SPEC as FORM1_SPEC
from forms_fill.forms.residential_rental_agreement.spec import (
    build_context as form1_context,
)
from forms_fill.models import TenancyBundle
from forms_fill.render import compute_blank_fields, render


def _bundle(d):
    return TenancyBundle.model_validate(d)


def _base_fields():
    return {
        "agreement_date": "2026-07-01",
        "agent_name": "GEA Property",
        "agent_address": "1 Agent St",
        "agent_postcode": "3000",
        "agent_phone": "0399990000",
        "agent_email": "gea@example.com",
        "renter1_current_address": "5 Old St",
        "renter1_current_postcode": "3122",
        "fixed_start_date": "2026-08-01",
        "fixed_end_date": "2027-08-01",
        "rent_amount": "615",
        "rent_period": "week",
        "rent_payment_day": "Thursday",
        "first_rent_due_date": "2026-08-01",
        "bond_amount": "2460",
        "bond_due_date": "2026-08-01",
        "emergency_contact_name": "GEA Maintenance",
        "emergency_phone": "0399991234",
        "emergency_email": "maint@example.com",
    }


# ── Form 1 (residential_rental_agreement) ───────────────────────────────────


def test_form1_context_has_premises_renter_provider(sample_bundle_dict):
    fields = dict(_base_fields(), term_type="fixed")
    ctx = form1_context(_bundle(sample_bundle_dict), fields)
    assert ctx["premises_address"] == "12 Example Street, Richmond"
    # U9: without is_renewal the fetched renters are the OUTGOING tenants —
    # never seeded. Renewal seeding is covered in the U9 tests below.
    assert ctx["renter1_name"] == ""
    assert ctx["provider_name"] == "Robert James Owner"


def test_form1_fixed_term_fields_render_verbatim(sample_bundle_dict):
    fields = dict(_base_fields(), term_type="fixed")
    ctx = form1_context(_bundle(sample_bundle_dict), fields)
    assert ctx["fixed_start_date"] == "2026-08-01"
    assert ctx["fixed_end_date"] == "2027-08-01"
    assert ctx["term_type"] == "fixed"


def test_form1_periodic_term_supported(sample_bundle_dict):
    fields = dict(_base_fields(), term_type="periodic", periodic_start_date="2026-08-01")
    del fields["fixed_start_date"]
    del fields["fixed_end_date"]
    ctx = form1_context(_bundle(sample_bundle_dict), fields)
    assert ctx["term_type"] == "periodic"
    assert ctx["periodic_start_date"] == "2026-08-01"
    assert ctx["fixed_start_date"] == ""


def test_form1_agent_and_current_address_are_caller_fields(sample_bundle_dict):
    ctx = form1_context(_bundle(sample_bundle_dict), {})
    assert "agent_name" in FORM1_SPEC.declared_fields
    assert "renter1_current_address" in FORM1_SPEC.declared_fields
    # agent_name auto-fills from the configured office agent (U5, R5) when the
    # caller supplies nothing; renter current address has no source (R13) and
    # stays blank.
    assert ctx["agent_name"] == "Stuart Grant"
    assert ctx["renter1_current_address"] == ""


def test_form1_leaves_additional_terms_and_signatures_undeclared():
    joined = " ".join(FORM1_SPEC.declared_fields)
    for forbidden in ("signature", "additional_term"):
        assert forbidden not in joined


def test_form1_end_date_before_start_date_not_validated_by_spec(sample_bundle_dict):
    # The spec renders verbatim; date ordering is the caller's responsibility.
    fields = dict(_base_fields(), term_type="fixed", fixed_start_date="2027-01-01", fixed_end_date="2026-01-01")
    ctx = form1_context(_bundle(sample_bundle_dict), fields)
    assert ctx["fixed_start_date"] == "2027-01-01"
    assert ctx["fixed_end_date"] == "2026-01-01"


def test_form1_fill_renders_docx(tmp_path, sample_bundle_dict):
    fields = dict(_base_fields(), term_type="fixed")
    ctx = form1_context(_bundle(sample_bundle_dict), fields)
    docx_path, _, _ = render(FORM1_SPEC, ctx, tmp_path)
    assert docx_path.exists()


# ── U5: agent + lease auto-fill ─────────────────────────────────────────────


def _bundle_with_lease(sample_bundle_dict, lease: dict):
    return _bundle({**sample_bundle_dict, "lease": lease})


_FULL_LEASE = {
    "term_type": "fixed",
    "fixed_start_date": "2026-09-01",
    "fixed_end_date": "2027-09-01",
    "rent_amount": "700",
    "rent_period": "fortnight",
    "rent_payment_day": "Monday",
    "first_rent_due_date": "2026-09-01",
    "bond_amount": "2800",
    "bond_due_date": "2026-08-25",
}


def test_form1_fills_term_rent_bond_from_bundle_lease_with_no_caller_fields(sample_bundle_dict):
    bundle = _bundle_with_lease(sample_bundle_dict, _FULL_LEASE)
    ctx = form1_context(bundle, {})
    assert ctx["term_type"] == "fixed"
    assert ctx["fixed_start_date"] == "2026-09-01"
    assert ctx["fixed_end_date"] == "2027-09-01"
    assert ctx["rent_amount"] == "700"
    assert ctx["rent_period"] == "fortnight"
    assert ctx["rent_payment_day"] == "Monday"
    assert ctx["first_rent_due_date"] == "2026-09-01"
    assert ctx["bond_amount"] == "2800"
    assert ctx["bond_due_date"] == "2026-08-25"


def test_caller_supplied_rent_overrides_bundle_lease(sample_bundle_dict):
    bundle = _bundle_with_lease(sample_bundle_dict, _FULL_LEASE)
    ctx = form1_context(bundle, {"rent_amount": "999"})
    assert ctx["rent_amount"] == "999"
    # untouched fields still auto-fill
    assert ctx["bond_amount"] == "2800"


def test_caller_supplied_agent_name_overrides_configured_agent(sample_bundle_dict):
    ctx = form1_context(_bundle(sample_bundle_dict), {"agent_name": "Someone Else"})
    assert ctx["agent_name"] == "Someone Else"


def test_agent_block_fills_from_default_configured_agent(sample_bundle_dict):
    ctx = form1_context(_bundle(sample_bundle_dict), {})
    assert ctx["agent_name"] == "Stuart Grant"
    assert ctx["agent_email"] == "stuart@grantsea.com.au"
    assert "Gloucester" in ctx["agent_address"]
    assert ctx["handling_agent"] == "Stuart Grant"


def test_empty_lease_block_leaves_fields_blank_and_reported(sample_bundle_dict):
    ctx = form1_context(_bundle(sample_bundle_dict), {})  # sample_tenancy.json has no lease block
    blanks = compute_blank_fields(FORM1_SPEC, ctx)
    assert ctx["rent_amount"] == ""
    assert "rent_amount" in blanks
    assert "bond_amount" in blanks


def test_renter_current_address_stays_blank_even_with_known_premises(sample_bundle_dict):
    ctx = form1_context(_bundle(sample_bundle_dict), {})
    assert sample_bundle_dict["premises"]["address_line"]  # premises IS known
    assert ctx["renter1_current_address"] == ""


def test_blank_field_accounting_still_lists_negotiated_and_signature_sections(sample_bundle_dict):
    ctx = form1_context(_bundle(sample_bundle_dict), _base_fields())
    joined = " ".join(FORM1_SPEC.declared_fields)
    for forbidden in ("signature", "additional_term", "payment_method", "electronic_service"):
        assert forbidden not in joined


# ── U6: renewal mode ─────────────────────────────────────────────────────────


def test_renewal_carries_rent_period_payment_day_bond_and_term_type(sample_bundle_dict):
    bundle = _bundle_with_lease(sample_bundle_dict, _FULL_LEASE)
    ctx = form1_context(bundle, {"is_renewal": "true"})
    assert ctx["rent_amount"] == "700"
    assert ctx["rent_period"] == "fortnight"
    assert ctx["rent_payment_day"] == "Monday"
    assert ctx["bond_amount"] == "2800"
    assert ctx["bond_due_date"] == "2026-08-25"
    assert ctx["term_type"] == "fixed"


def test_renewal_leaves_new_term_dates_and_agreement_date_blank(sample_bundle_dict):
    bundle = _bundle_with_lease(sample_bundle_dict, _FULL_LEASE)
    ctx = form1_context(bundle, {"is_renewal": "true"})
    assert ctx["fixed_start_date"] == ""
    assert ctx["fixed_end_date"] == ""
    assert ctx["agreement_date"] == ""


def test_renewal_unset_behaves_identically_to_u5(sample_bundle_dict):
    bundle = _bundle_with_lease(sample_bundle_dict, _FULL_LEASE)
    without_flag = form1_context(bundle, {})
    with_flag_false = form1_context(bundle, {"is_renewal": "false"})
    # "is_renewal" itself is a caller field rendered verbatim (verbatim-caller
    # rule, R4/KTD4) — its own literal echo differs ("" vs "false"), but every
    # field its presence *affects* must be identical.
    without_flag.pop("is_renewal")
    with_flag_false.pop("is_renewal")
    assert without_flag == with_flag_false


def test_renewal_caller_rent_still_overrides_carried_across_value(sample_bundle_dict):
    bundle = _bundle_with_lease(sample_bundle_dict, _FULL_LEASE)
    ctx = form1_context(bundle, {"is_renewal": "true", "rent_amount": "850"})
    assert ctx["rent_amount"] == "850"


def test_renewal_against_empty_lease_block_behaves_as_fresh_agreement(sample_bundle_dict):
    ctx = form1_context(_bundle(sample_bundle_dict), {"is_renewal": "true"})  # no lease block
    assert ctx["rent_amount"] == ""
    assert ctx["bond_amount"] == ""
    assert ctx["fixed_start_date"] == ""


# ── U9: new-lease renters never come from the fetched (outgoing) tenancy ────


def test_new_lease_never_seeds_renters_from_bundle(sample_bundle_dict):
    ctx = form1_context(_bundle(sample_bundle_dict), {})
    assert ctx["renter1_name"] == ""  # bundle holds Jane Smith — the OUTGOING tenant
    assert ctx["renter1_phone"] == ""
    assert ctx["renter1_email"] == ""


def test_new_lease_uses_caller_supplied_renters(sample_bundle_dict):
    ctx = form1_context(
        _bundle(sample_bundle_dict),
        {"renter1_name": "New Tenant", "renter1_email": "new@x.com"},
    )
    assert ctx["renter1_name"] == "New Tenant"
    assert ctx["renter1_email"] == "new@x.com"


def test_renewal_seeds_renters_from_bundle(sample_bundle_dict):
    ctx = form1_context(_bundle(sample_bundle_dict), {"is_renewal": "true"})
    assert ctx["renter1_name"] == "Jane Alice Smith"
    assert ctx["renter2_name"] == "John Peter Smith"


def test_renewal_caller_renter_still_overrides_bundle(sample_bundle_dict):
    ctx = form1_context(
        _bundle(sample_bundle_dict), {"is_renewal": "true", "renter1_name": "Corrected Name"}
    )
    assert ctx["renter1_name"] == "Corrected Name"


def test_is_renewal_never_appears_as_a_blank_field(sample_bundle_dict):
    ctx = form1_context(_bundle(sample_bundle_dict), {})
    blanks = compute_blank_fields(FORM1_SPEC, ctx)
    assert "is_renewal" not in blanks
