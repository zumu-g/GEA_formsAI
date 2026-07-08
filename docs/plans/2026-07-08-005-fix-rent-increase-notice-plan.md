---
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
execution: code
product_contract_source: ce-plan-bootstrap
created: 2026-07-08
---

# fix: Rent increase notice — service-address default, rent prefill, CMA link

**Target dir:** `forms_fill/`

---

## Summary

Four fixes/additions surfaced from a live PropertyMe fill of
`cav_rent_increase_notice`:

1. **Bug fix** — a renter's service address/postcode render blank instead of
   defaulting to the premises address, even though two provider docstrings
   already document that default as the intended contract.
2. **Feature** — prefill `current_rent`/`rent_period` from the tenancy record
   (PropertyMe already returns `RentAmount`/`RentPeriod` on the same row this
   tool already fetches — no new API call), editable by the PM.
3. **Small UX fix** — the "LibreOffice not found" warning gets an install
   hint; this machine genuinely has no LibreOffice installed (confirmed), so
   there is no code bug to fix here, only a friendlier message.
4. **Feature** — a "Request comparables report" button in `/ui` that opens
   GEA St CMA's rent-increase report flow
   (`https://geastcma-production.up.railway.app/reports/new?reportType=rent-increase&address={address}...`)
   for the loaded premises address in a new tab. The CMA tool has no
   PropertyMe/lot-ID integration and requires the PM to already be logged in
   — this is a plain deep link, not an API call.

---

## Requirements

- **R1 — Service-address default:** when a renter's `address_for_service` is
  blank, it defaults to the tenancy's premises address (and `service_postcode`
  to the premises postcode) — matching the documented contract in both
  `notice_to_vacate/spec.py`-style specs' comments and `gea_crm.py`'s
  docstring ("null `address_for_service` when service address == premises").
  Applied once, provider-agnostically, so PropertyMe, GEA CRM, and fixture
  all benefit without per-provider duplication.
- **R2 — Rent prefill:** `TenancyBundle` carries the tenancy's current rent
  amount and period. PropertyMe/GEA CRM/fixture populate it from data already
  fetched (or the fixture file). `cav_rent_increase_notice`'s `current_rent`
  and `rent_period` are prefilled from the bundle when the caller doesn't
  supply them; an explicit caller value always wins (unchanged verbatim
  contract — R4 in that spec). The `/ui` caller-field renderer prefills these
  two inputs once a tenancy preview loads.
- **R3 — Friendlier PDF warning:** the "PDF skipped" warning names the fix
  (`brew install --cask libreoffice` on macOS) instead of just stating the
  fact.
- **R4 — Comparables report button:** `/ui` shows a "Request comparables
  report" button once a tenancy is previewed. It opens
  `https://geastcma-production.up.railway.app/reports/new` with
  `reportType=rent-increase` and `address` (the premises address, the only
  required key — GEA St CMA has no PropertyMe/lot-ID integration) in a new
  tab. `suburb`/`state`/`postcode` are included when the bundle has them as
  enrichment (optional per the tool's own contract); `lat`/`lng` are omitted
  (the tool resolves them from the address). No premises loaded yet →
  button stays disabled.

**Out of scope:** any deep-link auth bypass — GEA St CMA's `/reports/*` is
session-gated, so the PM must already be logged in to that tool in the same
browser or the link bounces to its login page (documented limitation, not
fixed here); installing LibreOffice on any specific machine (operational, not
code); changing `TenancyBundle`'s renter/provider after-hours fields — those
are genuinely absent from the PropertyMe contact record for this tenancy, not
a mapping bug, and no code change addresses missing source data.

### Deferred to Follow-Up Work
- A signed one-time link or other auth handoff if a login-free deep link
  into GEA St CMA is wanted later (explicitly out of scope for this plan).
- Consider whether after-hours-blank should fall back to business-hours phone
  as a display default (separate product decision, not assumed here).

---

## Key Technical Decisions

**KTD1 — Service-address default lives in one shared place, not per
provider.** A pure function on `TenancyBundle` (no provider knowledge) applies
the premises fallback to every renter missing `address_for_service`. Called
once in `core.fill_form` right after `fetch_bundle`, and again in the
`/tenancy/preview` endpoint (which calls `fetch_bundle` directly, bypassing
`core.py`) — so the PM's preview shows the same value the fill will render.

**KTD2 — Rent fields join `TenancyBundle` at the top level.** `current_rent:
str` and `rent_period: str` (matching the string-typed money/period
convention already used by every caller field in this codebase). PropertyMe
maps `RentAmount`/`RentPeriod` off the tenancy row it already fetches in
`_resolve_tenancy` — zero new HTTP calls. GEA CRM passes its endpoint's
equivalent fields through (1:1 mapping, per its existing "thin adapter"
design). Fixture reads them from the sample JSON (add the two keys).

**KTD3 — Caller value always wins, matching the existing verbatim contract.**
`build_context` uses `fields.get("current_rent") or bundle.current_rent` (and
same for `rent_period`) — a PM correcting a stale record types over the
prefill exactly as they would today.

**KTD4 — CMA base URL is a constant in the frontend, not a fetched config
value.** GEA St CMA's base URL
(`https://geastcma-production.up.railway.app`) and query-param contract are
fixed and known now — no env var or config endpoint needed. The button's
target URL is built client-side in `/ui` from the tenancy-preview bundle
already loaded (address, and suburb/state/postcode when present).

---

### U1. Service-address default-to-premises (bug fix)

**Goal:** Renters with a blank `address_for_service` show the premises
address instead of blank, provider-agnostically.

**Requirements:** R1, KTD1

**Dependencies:** none

**Files:**
- `forms_fill/forms_fill/models.py` (edit — add the default-applying
  function)
- `forms_fill/forms_fill/core.py` (edit — call it after `fetch_bundle`)
- `forms_fill/forms_fill/api.py` (edit — call it in `/tenancy/preview` too)
- `forms_fill/tests/test_models.py` (edit)
- `forms_fill/tests/test_core_fill.py` (edit)

**Approach:** A function taking a `TenancyBundle` and returning one with each
renter's blank `address_for_service`/`service_postcode` replaced by the
premises' `address_line`/`postcode`. Renters that already have a service
address (a different address for service, e.g. a PO box) are left untouched —
this only fills genuinely blank values, matching what both provider
docstrings already promise.

**Execution note:** Existing tests already exercise a fixture bundle with one
renter carrying a real `address_for_service` — extend that test rather than
duplicating a bundle fixture, to prove the "existing value wins" edge case
alongside the "blank → premises" happy path.

**Test scenarios:**
- Happy path: renter with blank `address_for_service` → gets the bundle's
  premises `address_line`/`postcode`.
- Existing value preserved: renter with a real, different service address is
  not overwritten.
- Multiple renters: only the blank ones get defaulted; others untouched.
- Integration: `fill_form` on `cav_rent_increase_notice` with a
  blank-service-address fixture renter produces a filled (not blank) service
  address field in the rendered context.
- `/tenancy/preview` returns the same defaulted value the subsequent fill
  will use (no divergence between preview and fill).

**Verification:** tests pass; a live PropertyMe fill for the tenancy that
originally showed the bug now renders the premises address in that field.

---

### U2. Rent prefill (current_rent, rent_period)

**Goal:** `current_rent`/`rent_period` prefill from the tenancy record,
PM-editable.

**Requirements:** R2, KTD2, KTD3

**Dependencies:** none (parallel to U1)

**Files:**
- `forms_fill/forms_fill/models.py` (edit — `TenancyBundle.current_rent`,
  `rent_period`)
- `forms_fill/forms_fill/providers/propertyme.py` (edit — map
  `RentAmount`/`RentPeriod` from the already-fetched tenancy row)
- `forms_fill/forms_fill/providers/gea_crm.py` (edit — pass through if the
  CRM endpoint returns it; if not yet present on that endpoint, document the
  gap and leave the bundle field blank rather than guessing)
- `forms_fill/fixtures/sample_tenancy.json` (edit — add `current_rent`,
  `rent_period`)
- `forms_fill/forms_fill/forms/cav_rent_increase_notice/spec.py` (edit —
  `build_context` prefers `fields`, falls back to `bundle`)
- `forms_fill/forms_fill/static/index.html` (edit — prefill the two caller
  inputs from the tenancy preview, editable)
- `forms_fill/tests/test_cav_spec.py` (edit)
- `forms_fill/tests/test_providers.py` (edit)

**Approach:** `RentAmount` is numeric in PropertyMe's response (e.g.
`2607.0`) — render it as a plain string without forcing decimals the PM
didn't type (`"2607"`, not `"2607.0"`), consistent with how every other
money field in this codebase is a caller-typed string. `RentPeriod` values
("monthly") pass through the spec's existing `normalise_period` synonym map
(already handles "monthly" → "calendar month").

**Execution note:** Verify against the live PropertyMe tenancy row already
inspected this session (`RentAmount: 2607.0`, `RentPeriod: "monthly"`) rather
than only a synthetic fixture — the real API's numeric-vs-string shape is the
part most likely to surprise.

**Test scenarios:**
- Happy path: bundle carries `current_rent="2607"`, `rent_period="monthly"`
  → `build_context` output has `current_rent="2607"`,
  `rent_period="calendar month"` (via existing synonym normalisation) when
  the caller supplies neither.
- Override: caller-supplied `current_rent`/`rent_period` wins over the
  bundle's values.
- Blank bundle rent (fixture/provider has none) → falls through to blank,
  same as today (no regression, no guessed value).
- PropertyMe mapping: numeric `RentAmount` (e.g. `2607.0`) maps to the string
  `"2607"`, not `"2607.0"`.
- UI: selecting a form/tenancy prefills the two inputs; user edits are
  preserved on submit (not silently overwritten by a stale prefill).

**Verification:** tests pass; live PropertyMe fill on the tenancy from this
session shows `current_rent` prefilled without the PM typing it.

---

### U3. Friendlier PDF-skip warning

**Goal:** Name the fix in the LibreOffice-missing warning (R3).

**Requirements:** R3

**Dependencies:** none

**Files:**
- `forms_fill/forms_fill/render.py` (edit — one warning string)
- `forms_fill/tests/test_render.py` (edit — assert the new message text)

**Approach:** Extend the existing warning string with a one-line install
hint gated on `sys.platform` (`brew install --cask libreoffice` on macOS;
generic "install LibreOffice and ensure `soffice` is on PATH" otherwise). No
behavioral change — `_find_soffice`'s detection paths are already correct
(confirmed this session); this is a message-text fix, not a bug fix in
functionality.

**Test scenarios:** Test expectation: message-text only — assert the
warning string contains the install hint when `_find_soffice` returns
`None`.

**Verification:** test passes; warning text reads sensibly on this machine
(LibreOffice confirmed absent).

---

### U4. Comparables report button

**Goal:** `/ui` button opens GEA St CMA's rent-increase report flow for the
loaded premises address (R4).

**Requirements:** R4, KTD4

**Dependencies:** none

**Files:**
- `forms_fill/forms_fill/static/index.html` (edit — button + URL-building +
  `window.open` wiring; no backend change needed per KTD4)
- `forms_fill/tests/test_ui_routes.py` (edit)

**Approach:** Base URL
`https://geastcma-production.up.railway.app/reports/new`, query params
`reportType=rent-increase` and `address` (from the tenancy-preview bundle's
premises address, URL-encoded) always included; `suburb`/`state`/`postcode`
appended when the bundle has non-empty values for them (GEA St CMA treats
these as optional enrichment per its own contract — omitting them is fine,
not an error). `lat`/`lng` are not sent — the tool resolves them from the
address. Button lives in the tenancy-preview area (alongside the existing
preview card from the address-search work), disabled until a preview has
loaded (no address yet → nothing to link to). Since `/reports/*` is
session-gated on GEA St CMA's side, add a short caption near the button
noting the PM needs to already be logged in there, or the tab will land on
its login page.

**Execution note:** This is mostly wiring; prefer a runtime smoke check
(button present/disabled correctly, exact URL built from a loaded preview)
over deep unit coverage.

**Test scenarios:**
- No premises loaded yet: button renders disabled.
- Preview loaded with full address data: clicking builds
  `.../reports/new?reportType=rent-increase&address=<encoded>&suburb=<encoded>&state=<encoded>&postcode=<encoded>`
  correctly URL-encoded (spaces, commas in the address).
- Preview loaded with only a premises address line (no separate
  suburb/state/postcode fields populated): URL includes only `reportType`
  and `address` — no empty query params for the missing enrichment fields.
- Route test: `/ui/` page contains the button element and the GEA St CMA
  base URL string.

**Verification:** browser check with `CMA_TOOL_URL_TEMPLATE` set to a dummy
value confirms the button opens the expected constructed URL in a new tab.

---

## Risks & Dependencies

- **PropertyMe RentPeriod vocabulary drift:** if PropertyMe returns a period
  string outside today's known set ("weekly", "monthly", "fortnightly"),
  `normalise_period` falls through to lowercasing the raw value rather than
  guessing — same existing behavior for caller-typed input, so no new risk
  class, just worth a defensive test case (U2).
- **CMA URL unknown:** R4 ships the mechanism, not the destination. The
  button is genuinely inert until someone supplies the real URL — documented
  plainly, not hidden.
- **GEA CRM rent field may not exist yet:** if the CRM endpoint doesn't
  return rent data, U2's GEA CRM path stays blank rather than fabricating a
  value — flagged in the unit's Approach, not treated as a blocker for
  PropertyMe/fixture.

---

## Definition of Done

- A live PropertyMe fill of `cav_rent_increase_notice` shows the renter's
  service address defaulted to the premises address (was blank) and
  `current_rent` prefilled from the tenancy record (was manual-only).
- `/tenancy/preview` and the eventual fill show the same service-address
  value — no preview/fill divergence.
- The PDF-skip warning names the install fix.
- `/ui` shows a comparables-report button that stays disabled until a
  tenancy is previewed, then opens GEA St CMA's rent-increase report flow
  for the right address in a new tab.
- Full `pytest` suite passes; no regression in existing rent-increase or
  provider tests.
