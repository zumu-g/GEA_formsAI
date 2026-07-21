---
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
product_contract_source: ce-plan-bootstrap
execution: code
type: feat
created: 2026-07-21
---

# feat: Group form dropdown as GEA Sales / GEA PM with short display titles

## Summary

The form picker currently renders one `<optgroup>` per form, labelled with raw registry slugs (`breach_of_duty`, `notice_to_vacate`, …), because each `FormSpec.group` is near-unique. Replace this with two display categories — **GEA Sales** and **GEA PM** — and give every form a short display title (e.g. "Rent increase to renter"). The full legal title (Act sections etc.) moves out of the dropdown into small grey text shown under the select once a form is chosen.

## Problem Frame

- **R1** — Dropdown groups forms under exactly two headings: GEA Sales (Letter of Offer, Exclusive Sale Authority) and GEA PM (everything else).
- **R2** — Each option shows a short, human title without slugs or statutory clutter.
- **R3** — The full legal title (with section references) remains visible: rendered in de-emphasised text below the select for the chosen form. Compliance detail is not lost.
- Out of scope: custom (non-native) dropdown component; reordering forms within groups beyond alphabetical; any change to form keys, fill behaviour, or API auth.

## Key Technical Decisions

- **KTD1 — Category and short title live in the registry, not the UI.** Add `category` ("GEA Sales" | "GEA PM") and `short_title` fields to `FormSpec` defaults in `forms_fill/forms_fill/formspec.py`, set per-form where specs are declared, and expose both in the `/forms` catalogue payload (`forms_fill/forms_fill/registry.py`). Keeps the UI dumb and the mapping in one reviewed place. `group` stays untouched (other code may key on it).
- **KTD2 — Native `<select>` retained.** Options can't mix font weights, so the short title is the option text and the legal `title` renders below the select on selection. Chosen explicitly over a custom dropdown.
- **KTD3 — Fallbacks.** `category` defaults to "GEA PM"; `short_title` defaults to `title`, so an unmapped future form still renders sanely.

---

## Implementation Units

### U1. Registry: category + short_title in FormSpec and catalogue

**Goal:** Every form in `/forms` carries `category` and `short_title`.
**Requirements:** R1, R2.
**Files:** `forms_fill/forms_fill/formspec.py`, `forms_fill/forms_fill/registry.py`, form spec declarations (wherever each `FormSpec` is constructed — the `forms/` package), `forms_fill/tests/` (existing registry/API test file).
**Approach:** Add the two optional fields to `FormSpec` with KTD3 defaults; include them in `form_catalogue()` dicts. Set `category="GEA Sales"` on `allmain_letter_of_offer` and `reiv_exclusive_sale_authority`; all others inherit "GEA PM". Author a short title per form, e.g. "Rent increase to renter", "Breach of duty notice", "Notice to vacate", "Entry notice (s 86)" — drop leading "Notice of/to" boilerplate where it reads naturally.
**Test scenarios:**
- `/forms` payload: every form has non-empty `category` in {"GEA Sales", "GEA PM"} and non-empty `short_title`.
- The two sales forms are `category == "GEA Sales"`; `cav_rent_increase_notice.short_title` has no "(s 44(1))" suffix.
- A `FormSpec` constructed without the new fields yields `category == "GEA PM"` and `short_title == title`.
**Verification:** registry tests pass; `curl /forms` shows the new fields.

### U2. UI: group by category, show short titles, legal title below select

**Goal:** Dropdown shows two optgroups with short titles; full legal title appears under the select for the chosen form.
**Requirements:** R1, R2, R3. **Dependencies:** U1.
**Files:** `forms_fill/forms_fill/static/index.html`.
**Approach:** In `loadForms()`, bucket by `f.category` (GEA Sales first), option text = `f.short_title`, options alphabetical within group. Add a small muted `<div>` under the select, populated with the selected form's full `title` on change and on initial load. Reuse the existing muted/hint styling already in the page.
**Test scenarios:** UI-only; no JS test harness exists. `Test expectation: none — static page, covered by manual verification below.`
**Verification:** Load `/ui/`, open the dropdown: exactly two group headings, no slugs; select "Rent increase to renter" → grey text below reads "Notice of rent increase to renter of rented premises (s 44(1))".

---

## Definition of Done

- Dropdown shows only "GEA Sales" and "GEA PM" group labels; no slug text anywhere in the picker.
- Every form selectable, short-titled; selecting one reveals its full legal title beneath the select.
- Registry tests pass; `/fill` behaviour unchanged (keys untouched).
