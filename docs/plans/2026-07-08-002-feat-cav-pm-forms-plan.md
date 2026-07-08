---
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
execution: code
product_contract_source: ce-plan-bootstrap
created: 2026-07-08
origin: https://www.consumer.vic.gov.au/resources-and-tools/forms-and-publications
---

# feat: Remaining CAV property-management forms (core PM set + tenancy setup docs)

**Target dir:** `forms_fill/`

---

## Summary

Add the twelve remaining Consumer Affairs Victoria residential-renting forms a
property manager issues or prepares, sourced from the CAV forms-and-publications
page. Every form follows the shipped spec pattern (`notice_to_vacate`,
`breach_of_duty_notice`, etc.): a downloaded CAV DOCX template, a `spec.py`
with table/cell ops derived from the real template, provider-fetched
premises/renter/rental-provider data, caller fields for the rest, registered in
`registry.py` with zero core changes.

Already shipped and out of scope to rebuild: `cav_rent_increase_notice`,
`notice_to_vacate`, `breach_of_duty_notice`, `general_notice`,
`notice_of_entry`, plus the approval/VCAT pipeline from the 2026-07-08-001 plan.

---

## Requirements

- **R1 — Core PM set** (RRP→renter, confirmed by user):
  Form 1 Residential rental agreement; Form 2 Residential rental agreement
  (fixed term > 5 years); Notice of intention to sell; Notice of goods left
  behind; Notice requesting additional bond; Notice to vacate in the case of
  death of a sole renter.
- **R2 — Tenancy setup docs** (confirmed by user):
  Residential Rental Application form; Condition report; Statement of
  information for rental applicants; Mandatory disclosure checklist; Consent
  to electronic service of notices and other documents; Request for repairs
  inspection.
- **R3 — Data fetch parity:** all specs resolve premises, renters, and rental
  provider via the existing `PropertyDataProvider` interface (PropertyMe and
  GEA CRM both work, no per-form provider code).
- **R4 — Real templates:** each spec is written against the actual downloaded
  CAV DOCX (source URL + download date in the spec docstring), same discipline
  as every shipped form. Template URLs are recorded in Sources below.
- **R5 — Registry/API/UI surface for free:** each form appears in
  `available_forms()`, `form_catalogue()`, CLI fill, and `POST /fill` with no
  changes beyond registration.

**Out of scope:** rooming house, caravan park, Part 4A, and SDA form families
(GEA does not manage these premises types — revisit if that changes);
renter→rental-provider forms (issued by the renter, not the PM); CAV
publications/guides; the approval/VCAT pipeline (already planned separately).

### Deferred to Follow-Up Work
- Grounds-catalogue linkage for "notice to vacate — death of sole renter"
  (91ZY) if the existing catalogue lacks it — verify at implementation and add
  the entry if missing.

---

## Key Technical Decisions

**KTD1 — Same pattern, no new machinery.** Every form is a spec module +
template + registry entry. No changes to core, renderer, CLI, or API — that is
the registry's design contract.

**KTD2 — Setup docs are prefill, not completion.** The rental application and
condition report are substantially completed by the renter. forms-fill's job is
to prefill the agent/premises/rental-provider sections from provider data and
leave renter sections blank by design (declared in each spec's blank-by-design
list, same rule as delivery/signature sections on the notices).

**KTD3 — Big documents may need op-count pragmatism.** Form 1 (rental
agreement) and the condition report are long multi-table documents. If the real
template proves to have large repeating sections (per-room condition entries,
additional-term schedules), the spec fills the fixed identity/premises/term
tables and declares the repeating sections blank-by-design rather than
inventing a repeating-row engine. Extend the renderer only if a fixed-shape
fill is genuinely impossible — decided at implementation with the template in
hand.

**KTD4 — Checklist-style docs still ship as fills.** The mandatory disclosure
checklist and statement of information are mostly static text with a small
identity block; the spec fills that block. Low value per form, but they
complete the PM pack cheaply since the machinery already exists.

---

### U1. Sale / end-of-tenancy notices

**Goal:** `notice_of_intention_to_sell`, `notice_of_goods_left_behind`,
`notice_to_vacate_death_sole_renter` registered and filling.

**Requirements:** R1, R3, R4, R5

**Dependencies:** none

**Files:**
- `forms_fill/forms_fill/forms/notice_of_intention_to_sell/{spec.py,template.docx}` (new)
- `forms_fill/forms_fill/forms/notice_of_goods_left_behind/{spec.py,template.docx}` (new)
- `forms_fill/forms_fill/forms/notice_to_vacate_death_sole_renter/{spec.py,template.docx}` (new)
- `forms_fill/forms_fill/registry.py` (edit — register)
- `forms_fill/tests/test_sale_end_notices.py` (new)

**Approach:** Mirror `notice_to_vacate/spec.py`. Caller fields per form:
intention-to-sell needs sale method/agent details; goods-left-behind needs the
goods description and collection deadline; death-of-sole-renter needs the
termination date and (likely) next-of-kin/representative details — confirmed
against the real template.

**Execution note:** Download and inspect each CAV template before writing any
ops — no guessed indices.

**Test scenarios:**
- Happy path per form: fixture tenancy fill → ok:true, key values land in the
  expected cells (assert via python-docx read-back).
- Blank fields: absent renter3/4 → `blank_fields`, not errors.
- Error path: missing required caller field → clear validation error before
  render.
- Integration: one CLI fill per form against the fixture provider.

**Verification:** tests pass; manual open of each filled DOCX.

---

### U2. Bond notice

**Goal:** `notice_requesting_additional_bond` registered and filling.

**Requirements:** R1, R3, R4, R5

**Dependencies:** none

**Files:**
- `forms_fill/forms_fill/forms/notice_requesting_additional_bond/{spec.py,template.docx}` (new)
- `forms_fill/forms_fill/registry.py` (edit)
- `forms_fill/tests/test_additional_bond.py` (new)

**Approach:** Small single-notice spec; caller fields for current bond, new
bond amount, and current rent (the >5-year-agreement / rent-threshold
conditions are the PM's judgment, not validated by the tool — same stance as
notice periods elsewhere).

**Test scenarios:** happy path, blank-field reporting, missing-amount
validation error, one CLI integration fill.

**Verification:** as U1.

---

### U3. Rental agreements (Form 1 and Form 2)

**Goal:** `residential_rental_agreement` (Form 1) and
`residential_rental_agreement_5yr` (Form 2) registered and filling their fixed
sections.

**Requirements:** R1, R3, R4, R5, KTD3

**Dependencies:** none

**Files:**
- `forms_fill/forms_fill/forms/residential_rental_agreement/{spec.py,template.docx}` (new)
- `forms_fill/forms_fill/forms/residential_rental_agreement_5yr/{spec.py,template.docx}` (new)
- `forms_fill/forms_fill/registry.py` (edit)
- `forms_fill/tests/test_rental_agreement.py` (new)

**Approach:** Fill parties, premises, term (start/end/periodic), rent amount
and payment details, bond, condition-report and disclosure acknowledgment
blocks from provider data + caller fields. Additional terms / schedules and all
signature blocks are blank-by-design (KTD3). Form 2 likely shares most of Form
1's structure — write Form 1 first, then diff the Form 2 template and reuse
field definitions where the tables match.

**Execution note:** This is the largest template in the repo so far; inspect
fully with python-docx and enumerate every table before choosing what to fill.

**Test scenarios:**
- Happy path: fixture fill → parties/premises/rent/term values in correct
  cells for both forms.
- Periodic vs fixed term: both variants render correctly.
- Blank-by-design: additional-terms schedule reported blank, not error.
- Error path: end date before start date → validation error.
- Integration: CLI fill of Form 1 end-to-end.

**Verification:** tests pass; filled Form 1 manually reviewed against a real
GEA lease for field placement.

---

### U4. Tenancy setup docs

**Goal:** `rental_application`, `condition_report`,
`statement_of_information_applicants`, `mandatory_disclosure_checklist`,
`consent_electronic_service`, `request_repairs_inspection` registered and
filling their PM-side sections.

**Requirements:** R2, R3, R4, R5, KTD2, KTD4

**Dependencies:** none (U3 first is sensible — condition report references the
agreement — but not required)

**Files:**
- `forms_fill/forms_fill/forms/<form_key>/{spec.py,template.docx}` (new, ×6)
- `forms_fill/forms_fill/registry.py` (edit)
- `forms_fill/tests/test_setup_docs.py` (new)

**Approach:** Prefill-only per KTD2: agent, rental provider, premises, and
where applicable rent/bond details from provider data; renter-completed
sections declared blank-by-design. Condition report: fill the header/identity
block; per-room condition rows blank-by-design unless the template's structure
makes a fixed fill trivial (KTD3 judgment at implementation). Note the rental
application template is dated 31 March 2026 — record that version in the
docstring.

**Test scenarios:**
- Happy path per form: identity/premises block filled from fixture.
- Blank-by-design: renter sections reported blank across all six.
- Integration: one CLI fill (condition report) against fixture provider.

**Verification:** tests pass; each filled DOCX opened once to confirm no
renter-section spillover.

---

## Risks & Dependencies

- **Template shape unknowns (all units):** specs cannot be written until each
  DOCX is downloaded and inspected; a template with an unfillable structure
  (content controls, no tables) may need renderer work — surface it rather
  than hacking around it.
- **Form 1 size (U3):** the rental agreement is long; KTD3 caps scope at fixed
  sections to avoid building a repeating-row engine nobody asked for.
- **CAV version churn:** CAV re-dates templates (e.g. application form
  "31 March 2026"). Docstring URL+date discipline is the mitigation, as on
  shipped forms.

---

## Sources & Research

CAV forms-and-publications page (fetched 2026-07-08). Template URLs, all under
`https://www.consumer.vic.gov.au/library/forms/housing-and-accommodation/renting/`:

| Form key | CAV file |
|---|---|
| residential_rental_agreement | `form-1-residential-rental-agreement.docx` |
| residential_rental_agreement_5yr | `form-2-residential-rental-agreement-for-a-fixed-term-of-more-than-five-years.docx` |
| notice_of_intention_to_sell | `notice-of-intention-to-sell.docx` |
| notice_of_goods_left_behind | `notice-of-goods-left-behind.docx` |
| notice_requesting_additional_bond | `notice-requesting-additional-bond.docx` |
| notice_to_vacate_death_sole_renter | `notice-to-vacate-in-the-case-of-death-of-a-sole-renter.docx` |
| rental_application | `residential-rental-application-31-march-2026.docx` |
| condition_report | `condition-report-word.docx` |
| statement_of_information_applicants | `statement-of-information-for-rental-applicants.docx` |
| mandatory_disclosure_checklist | `mandatory-disclosure-checklist.docx` |
| consent_electronic_service | `consent-to-electronic-service-of-notices-and-other-documents.docx` |
| request_repairs_inspection | `request-for-repairs-inspection.docx` |

---

## Definition of Done

- All twelve forms registered; `available_forms()` lists them; `form_catalogue()`
  exposes their caller fields; CLI and `POST /fill` fill each from fixture data
  and a live provider without per-form provider code.
- Every spec docstring records template source URL and download date.
- All new tests pass; the existing test suite still passes (`pytest` in
  `forms_fill/`).
- Filled Form 1 manually reviewed against a real GEA lease.
