---
title: "fix: Sales-form UI — hide tenant fields, prefill vendor from GEA CRM"
date: 2026-07-22
type: fix
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
execution: code
product_contract_source: ce-plan-bootstrap
---

# fix: Sales-form UI — hide tenant fields, prefill vendor from GEA CRM

## Summary

When a PM selects a GEA Sales form (Exclusive Sale Authority, Letter of Offer) in the web UI, the page still behaves as a tenancy tool: the "2. Tenancy" section shows renter details, submit is blocked without a Lot/Tenancy ID (which sales forms don't use), and vendor details must be typed by hand even though the GEA CRM bundle already carries the owner's name, address, phone, and email. This plan makes the UI sales-aware and prefills vendor fields from the CRM owner record — UI-only, caller values always win (R4), no backend or CRM changes.

## Problem Frame

- `forms_fill/forms_fill/core.py` correctly skips the bundle fetch for sales forms (`requires_bundle=False`) and builds context from caller fields + agency defaults (`sales.py`).
- The catalogue (`forms_fill/forms_fill/registry.py`, `requires_identifiers` key) already tells the UI whether a form needs a tenancy — the UI ignores it.
- `forms_fill/forms_fill/static/index.html` always renders the tenancy section, shows "Renters", requires lot/tenancy IDs on submit, and has no vendor prefill.
- The GEA CRM tenancy bundle's `rental_provider` is by contract the **owner** (`forms_fill/forms_fill/models.py:48`) — i.e. the vendor for a sale of the same property.

## Requirements

- R1: Selecting a sales-category form relabels the property section (no "Tenancy"/renter framing) and hides the renter row in the preview.
- R2: Sales forms can be submitted without Lot/Tenancy IDs; the lot/tenancy submit guard applies only to forms with `requires_identifiers: true`.
- R3: When a property is searched and previewed with a sales form selected, vendor fields are prefilled from the bundle (field paths per `forms_fill/forms_fill/models.py` `RentalProvider`/`Premises`): `vendor_name` ← `rental_provider.full_name`, `vendor_address` ← `rental_provider.service_address` + `rental_provider.service_postcode`, `vendor_phone` ← `rental_provider.phone_business_hours`, `vendor_email` ← `rental_provider.email`, `property_address` ← `premises.address_line` + `premises.suburb` + `premises.state` + `premises.postcode`. Targets are matched by `data-field` and silently skipped when the selected form doesn't declare that caller field (e.g. Letter of Offer exposes only `vendor_name` and `property_address`).
- R4: Prefill never overwrites a value the PM has already typed; all prefilled fields remain editable (mirrors the existing `RENT_PREFILL_FIELDS` pattern).
- R5: A vacant / owner-occupied lot (CRM returns `no_current_tenancy`) degrades gracefully: a hint that vendor details must be entered manually, not an error banner blocking the flow.

## Key Technical Decisions

- **UI-only change.** The fill core, providers, and registry stay untouched; the sales path in `core.py` already ignores identifiers, so unblocking submit needs no backend work. (Alternative — a new CRM vendor/listing endpoint — deferred; it requires a CRM-repo change and the owner record covers today's need.)
- **Reuse the existing search → preview flow** to fetch the bundle even for sales forms; the bundle is used purely for client-side prefill and is never sent with the `/fill` payload (sales fills carry `fields` only).
- **Detect sales forms via `category === 'GEA Sales'`** from the catalogue (already present), keyed off `requires_identifiers === false` for the submit guard so future non-bundle forms behave the same.

## Implementation Units

### U1. Sales-aware tenancy section and submit guard

**Goal:** UI adapts when the selected form doesn't require a tenancy.
**Requirements:** R1, R2, R5
**Dependencies:** none
**Files:** `forms_fill/forms_fill/static/index.html`
**Approach:** On form select (and initial load), read the selected spec's `requires_identifiers`/`category`. For sales forms: set the section legend to "2. Property / Vendor", hide the "Renter(s)" row in `renderPreview`, and skip the lot/tenancy guard in the submit handler. When a preview fetch returns `no_current_tenancy` while a sales form is selected, show a hint ("No tenancy on this lot — enter vendor details manually") instead of the red error result.
**Test scenarios:**
- Select Exclusive Sale Authority → legend reads "Property / Vendor", no renter row after preview, submit with empty lot/tenancy proceeds to `/fill`.
- Select a PM form (e.g. Notice to vacate) → behaviour unchanged: renters shown, submit without IDs blocked.
- Sales form + preview of a lot with no tenancy → hint shown, form still submittable.

### U2. Vendor prefill from CRM owner record

**Goal:** Picking a property prefills vendor fields for sales forms.
**Requirements:** R3, R4
**Dependencies:** U1
**Files:** `forms_fill/forms_fill/static/index.html`
**Approach:** Extend the existing prefill mechanism (`lastPreviewBundle` + `prefillRentFields`) with a sales map using R3's exact field paths: `vendor_name` ← `rental_provider.full_name`; `vendor_address` ← `rental_provider.service_address` joined with `service_postcode` (space-separated, skip blanks); `vendor_phone` ← `rental_provider.phone_business_hours`; `vendor_email` ← `rental_provider.email`; `property_address` ← `premises.address_line` + `suburb` + `state` + `postcode` (space-separated, skip blanks — same joining style as `buildCmaUrl`/preview rendering). Inputs matched by `data-field`; targets missing from the selected form's caller fields are silently skipped. Apply on preview and on form-select change (so picking the property first, then the form, still prefills). Only fill empty inputs.
**Test scenarios:**
- Preview a tenanted lot via GEA CRM, then select Sales Authority → vendor_name/address/phone/email and property_address populated from `rental_provider`/`premises`.
- Type a vendor name first, then preview → typed value preserved (R4).
- Fixture provider works identically (same bundle shape).
- Blank owner email in bundle → field left empty, no "undefined" text.

**Verification:** run the API locally (`FORMS_DEV_NO_AUTH=1`), load `/ui/`, walk both a sales and a PM form end-to-end against the fixture provider; confirm a sales `/fill` succeeds with no identifiers and the rendered PDF carries the prefilled vendor values.

## Scope Boundaries

### Deferred to Follow-Up Work
- CRM listing/vendor endpoint that returns owner details for lots with **no** tenancy (needs a change in the GEA CRM repo; today those lots fall back to manual entry per R5).
- Prefilling `vendor_abn` / `vendor_capacity` — not present in the bundle.

## Risks

- The bundle's `rental_provider` is the owner by contract, but for a small number of lots CRM data quality may lag (e.g. sold/transferred owners). Prefill is editable, so the PM remains the check.

## Assumptions

- "Client details" = the vendor (property owner) as held in GEA CRM's owner record; confirmed via the vendor-source decision (reuse CRM owner data).
