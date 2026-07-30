---
title: "feat: Add PM Exclusive Leasing Authority form"
date: 2026-07-29
type: feat
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
execution: code
product_contract_source: ce-plan-bootstrap
---

# feat: Add PM Exclusive Leasing Authority form

## Summary

Add a new form to `forms_fill` — `pm_exclusive_leasing_authority` — covering the
"exclusive leasing and management authority" GEA's PM team signs owners to
before letting a property. It appears in the form dropdown under the
existing "GEA PM" category, alongside the CAV notices already built. There is
no GEA source template for this authority (unlike `reiv_exclusive_sale_authority`,
which overlays GEA's real REIV pad) — the only reference is a 26-page
iProperty Express-generated contract from a different agency (O'Brien Real
Estate), used here only to identify the sections and fields a leasing
authority needs, never for its wording.

---

## Problem Frame

GEA's PM roadmap ([[project_target_forms]]) names "Exclusive leasing
authority" as the next PM form to build, alongside sales authorities already
shipped. Today `FORM_REGISTRY` (`forms_fill/forms_fill/registry.py`) has no
leasing-authority key, so it can't appear in the web UI dropdown
(`forms_fill/forms_fill/static/index.html`) or be requested via the API.

Unlike every other form in the registry, this one has no authoritative
source document to fill:
- `reiv_exclusive_sale_authority` overlay-stamps GEA's actual REIV Code 002
  pad — REIV owns the legal wording, GEA fills fields.
- `residential_rental_agreement` fills CAV's official Form 1 `.docx` —
  a government-sourced template.
- The only leasing-authority reference on hand is a signed iProperty
  Express contract belonging to a competitor agency, with a different
  client's PII in it and iProperty's own copyrighted clause wording.

This means the software work (registry entry, template engine, caller
fields, dropdown listing) is buildable now, but the legal clause text (the
"AGREEMENT" section's ~11 numbered clauses covering fees, liability,
indemnity, termination, etc.) is **not** — it must come from GEA's own
approved wording (solicitor-drafted, or an REIV/CAV equivalent if one
exists), not be reverse-engineered from a competitor's document. See Open
Questions.

---

## Requirements

- **R1**: `pm_exclusive_leasing_authority` is registered in `FORM_REGISTRY`
  and selectable from the web UI form dropdown, grouped under "GEA PM".
- **R2**: The essential-particulars fields (agent, client/owner, property,
  exclusive leasing period, continuing leasing period, fixed management
  period, rent, bond, urgent repair limit) are caller-supplied per-form
  fields, following the verbatim-caller-input rule (R4 in existing forms).
- **R3**: Agent/agency identity fields reuse `fixtures/gea_agency.json` via
  the existing `agency.py` defaults (same pattern as `sales.py`), not
  re-entered per fill.
- **R4**: Fees (leasing fee, re-leasing fee, managing fee — each as a % or
  flat amount) and commission-sharing/rebate declarations are caller fields,
  matching the "AGENT FEES AND CHARGES" and "Rebate Statement" sections
  identified in the iProperty reference.
- **R5**: The legal boilerplate (AGREEMENT warranties, numbered clauses 1-11+)
  is rendered from GEA-approved wording supplied separately — this plan does
  not author that text.

## Scope Boundaries

**In scope:** registry entry, dropdown listing, caller field set for
essential particulars + fees + rebate statement, a `.docx` template
authored with GEA's own branding and (once supplied) GEA's own legal
wording, `build_context`/agency-default wiring, tests for field population.

**Out of scope / deferred:**
- Drafting or approving the actual legal clause wording — owned by GEA
  outside this tool.
- "Schedule of Agent Fees" itemised marketing/admin fee line items (For
  Lease Board, VCAT prep fee, etc.) — deferred to a follow-up once GEA
  confirms its own fee schedule differs from the reference document's.
- Any REIV/CAV statutory equivalent research — only pursue if Open Question
  1 below resolves to "yes, one exists."

---

## Key Technical Decisions

**KTD1 — `.docx` template engine, not `pdf_overlay`.** This is a fresh
GEA-authored contract, not a pre-printed pad being filled — there is no
scanned form to overlay-stamp. Follows the `residential_rental_agreement`
pattern (python-docx table fill), not `reiv_exclusive_sale_authority`'s
pixel-coordinate overlay.

**KTD2 — Legal clause text is an external input, not generated content.**
The plan defines the *fields* a clause needs to reference (e.g. urgent
repair limit, notice period) but the clause prose itself is inserted from
GEA-supplied text once available (Open Question 1). Building the `.docx`
template with placeholder/TBD clause paragraphs first lets the field-filling
plumbing (R1-R4) ship and be tested independently of the legal content.

**KTD3 — Agent/agency fields via `agency.py`, not duplicated.** Mirrors
`sales.py`'s `build_sales_context` merge-over-defaults pattern (R3) rather
than re-declaring agent fields as caller inputs.

---

## Implementation Units

### U1. Author the `.docx` template with placeholder legal clauses

**Goal:** Produce `forms_fill/forms_fill/forms/pm_exclusive_leasing_authority/template.docx`
with GEA branding, the essential-particulars table, fees/rebate section, and
clause headings 1-11+ present but carrying `[TBD — GEA legal wording]`
placeholder body text per clause, so the document structure exists without
copying iProperty's prose.

**Requirements:** R5 (structurally), sets up R1-R4's tables.

**Dependencies:** none.

**Files:**
- `forms_fill/forms_fill/forms/pm_exclusive_leasing_authority/template.docx` (new)

**Approach:**
- Use the iProperty reference purely for section *names and order*
  (Essential Particulars → Agreement warranties → Signatures → Agent Fees
  and Charges → Rebate Statement → Agent Services → numbered clauses 1-11+)
  — not its sentences.
- Table layout matches the `residential_rental_agreement` convention
  (label cell / value cell) so `TextOp`/`CheckboxOp` addressing works the
  same way.

**Test scenarios:**
- Test expectation: none — template authoring has no behaviour to unit test; U3's field-population tests exercise it.

---

### U2. Add `FormSpec` module

**Goal:** `forms_fill/forms_fill/forms/pm_exclusive_leasing_authority/spec.py`
declaring fields, `TextOp`/`CheckboxOp` table addressing, and `build_context`.

**Requirements:** R2, R3, R4

**Dependencies:** U1 (needs final table indices from the authored template)

**Files:**
- `forms_fill/forms_fill/forms/pm_exclusive_leasing_authority/spec.py` (new)
- `forms_fill/forms_fill/forms/pm_exclusive_leasing_authority/__init__.py` (new)

**Approach:**
1. Declare `AGENCY_DEFAULT_FIELDS` reusing `agency.py`'s shape (agent name,
   mobile, email, office address) per KTD3.
2. Declare `CALLER_FIELDS`: client/owner name(s) + address + contact,
   property address, exclusive_leasing_days, continuing_leasing_days,
   fixed_management_period, rent_per_week, security_bond, urgent_repair_limit,
   leasing_fee_pct, releasing_fee_flat, managing_fee_pct, agreement_date.
3. Declare `SELECTOR_FIELDS`: `commission_sharing` (yes/no), `rebate_entitlement`
   (yes/no) as `CheckboxOp`s, mirroring `cav_rent_increase_notice`'s tick
   pattern.
4. `build_context` merges caller fields over `agency.py` defaults (same
   shape as `build_sales_context`).

**Patterns to follow:** `forms_fill/forms_fill/forms/residential_rental_agreement/spec.py` (docx table engine), `forms_fill/forms_fill/sales.py` (agency-default merge).

**Test scenarios:**
- Caller fields render verbatim into their declared table cells given a minimal fields dict.
- Agency defaults populate agent/agency fields when fields dict omits them; caller-supplied values override agency defaults (per R4/verbatim rule).
- `commission_sharing="no"` and `="yes"` tick the correct checkbox and leave the other blank.
- Missing required caller field (e.g. no property address) surfaces as a blank/declared-but-unfilled field, not a crash — matches existing `blank_fields` accounting.

---

### U3. Register in `FORM_REGISTRY` and dropdown catalogue

**Goal:** Form is selectable end-to-end via API and UI.

**Requirements:** R1

**Dependencies:** U2

**Files:**
- `forms_fill/forms_fill/registry.py`

**Approach:**
1. Import `SPEC as PM_LEASING_AUTHORITY_SPEC` and add to `FORM_REGISTRY`.
2. Add to `_SHORT_TITLES`: `"pm_exclusive_leasing_authority": "Exclusive Leasing Authority"`.
3. Do **not** add to `_SALES_KEYS` — `form_catalogue()`'s existing
   `"GEA Sales" if key in _SALES_KEYS else "GEA PM"` ternary already puts
   it under "GEA PM" once omitted, satisfying R1 with no dropdown-rendering
   code change (`static/index.html` builds the `<select>` from the
   `/forms` catalogue at runtime — see Verification).

**Test scenarios:**
- Covers R1. `available_forms()` includes `"pm_exclusive_leasing_authority"`.
- `form_catalogue()` entry for the key has `category == "GEA PM"` and `short_title == "Exclusive Leasing Authority"`.
- `get_form_spec("pm_exclusive_leasing_authority")` returns the registered spec without raising `UnknownFormError`.

**Verification:** `GET /forms` (or the equivalent test client call) includes the new key; loading `static/index.html` locally shows it in the "Form type" dropdown under GEA PM once the API is running.

---

## Risks & Dependencies

- **Legal content risk (blocking for a production-usable form):** shipping
  U1-U3 produces a functional but legally incomplete document until GEA
  supplies real clause wording — flagged prominently, not silently patched
  from the iProperty text. Do not fill in placeholder clauses from the
  reference PDF without explicit sign-off; that document is a third party's
  copyrighted content and describes different terms than GEA may want.
- **Fee structure may not match GEA's own model** — the reference document's
  fee percentages/flat fees are O'Brien-specific; GEA's actual fee schedule
  needs confirming before caller-field defaults or examples are chosen.

---

## Open Questions

1. **Does an REIV/CAV statutory pad exist for this authority**, the way
   Code 002 covers sale authorities? If yes, prefer overlay-stamping that
   pad (KTD1 changes to `pdf_overlay`, much smaller build, no legal-drafting
   risk) over authoring a fresh contract. **Recommend resolving this before
   starting U1** — it changes the engine choice.
2. **What is GEA's actual legal clause wording** for the AGREEMENT section
   (warranties, fees clause, indemnity, termination, etc.)? Needed to
   replace U1's placeholders before the form is used for a real signing.
3. **What are GEA's real fee percentages/schedule** for leasing, re-leasing,
   and managing fees, to seed sensible caller-field defaults/examples?

---

## Verification Contract

- `pm_exclusive_leasing_authority` appears in `FORM_REGISTRY` and `available_forms()`.
- `form_catalogue()` lists it under `"GEA PM"` with the short title "Exclusive Leasing Authority".
- A test fill with representative caller fields produces a rendered `.docx`/PDF with essential-particulars and fee fields populated and no unhandled exceptions.
- Existing form tests (`forms_fill/tests/test_render.py`) continue to pass unmodified.

## Definition of Done

- U1-U3 implemented and registered.
- New unit tests for `pm_exclusive_leasing_authority` pass.
- Open Question 1 explicitly answered (even if the answer is "no REIV pad exists, proceeding with fresh contract") before U1's placeholder clauses are treated as final.
