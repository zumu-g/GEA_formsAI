---
title: "feat: forms-lv buzz skill — full form catalogue, registry-driven"
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
execution: code
product_contract_source: ce-plan-bootstrap
depth: standard
created: 2026-07-31
---

# feat: forms-lv buzz skill — full form catalogue, registry-driven

**Target host:** `lvpm` (SSH alias, `root@100.89.84.95`), not a git repo — the
Hermes skill lives at `/root/.hermes/skills/forms-lv/` on that VPS as plain
files (auto-backed up daily to `/root/hermes-backups/`). All paths below are
absolute VPS paths for that reason. This plan does not touch the
`GEA_formsAI` repo itself.

**Product Contract preservation:** N/A — no upstream requirements doc; scope
was settled directly with the user (see Assumptions).

---

## Summary

GEA already runs a per-portfolio Hermes agent (LVPM) wired into the `buzz`
chat relay, with a `forms-lv` skill that lets a PM request a CAV notice by
chatting with the assistant, which shells out to `forms_lv.py` → the
`GEA_formsAI` Railway API → a PDF. That skill only knows two forms
(`cav_rent_increase_notice`, `breach_of_duty_notice`), hardcoded as two CLI
subcommands. The `GEA_formsAI` API has since grown to 20 registered forms (exact count
per `forms_fill/forms_fill/registry.py` as of this writing — re-check at
implementation time since the registry grows)
(`forms_fill/forms_fill/registry.py`) exposed generically via `GET /forms`
(full catalogue with per-form caller-field metadata) and `POST /fill`. This
plan makes the buzz skill registry-driven so every current and future form in
the catalogue is requestable from buzz without further skill edits.

## Problem Frame

- PMs can already ask the LVPM assistant in buzz for a rent-increase or
  breach notice; anything else ("give me an Exclusive Leasing Authority", "fill
  out a condition report") isn't wired up, so the assistant either can't help
  or would have to hand-author a legal document — explicitly forbidden by the
  skill's own instructions.
- The API-side catalogue (`GET /forms`) already carries everything a client
  needs to drive any form generically: `key`, `title`, `requires_identifiers`,
  and `caller_fields` (name, label, input kind, options, section). The buzz
  skill just isn't using it.

## Requirements

- **R1** — `forms-lv` can list every form currently in the `GEA_formsAI`
  catalogue (`GET /forms`), with enough metadata (title, required caller
  fields) for the agent to know what to ask the PM for.
- **R2** — `forms-lv` can fill any catalogue form generically (`POST /fill`)
  given a form key, identifiers (when the form needs a PropertyMe/VaultRE
  lookup), and caller fields — no per-form Python subcommand required.
- **R3** — Property/tenancy lookup (`search`) keeps working for forms that
  need identifiers; forms that don't (`requires_identifiers: false`, e.g. the
  leasing/sale authorities) skip the lookup step.
- **R4** — The skill's safety instructions (never hand-author a statutory
  document, never send anything to the renter/buyer, always human review
  before service) are preserved and generalised beyond the two current forms.
- **R5** — Existing behaviour for the two currently-wired forms (notice
  period check, `increase` auto-computation, output filenames under
  `~/rent-notices/` and `~/breach-notices/`) keeps working after the rewrite —
  this is a superset, not a rewrite-and-hope.

## Key Technical Decisions

**KTD1 — Generic `fill` subcommand replaces per-form subcommands.**
`forms_lv.py` gets one `fill` subcommand instead of one Python function per
form. Its argparse contract is `fill <form_key> [--lot-id ID] [--fields
'<json>'] [--new-rent N] [--current-rent N] [--period P] [--start-date D]
[--basis B] [--increase N]` — the typed rent-notice flags stay first-class
(so KTD2's 60-day check and auto-compute can run before the request is
built) and get merged into the request's `fields`/`identifiers` alongside
whatever `--fields` JSON supplies; every other form is driven entirely
through `--lot-id` (when `requires_identifiers: true`) plus `--fields`.
Rationale: the API already accepts an arbitrary form key + fields payload
(`forms_fill/forms_fill/api.py:248` `POST /fill`); hardcoding a Python
function and argparse subcommand per form means every new form in the
registry requires a matching skill deploy, which is exactly the drift that
caused this plan. `notice`/`breach` are dropped as dedicated subcommands —
their special-case logic (60-day notice check, `increase` auto-compute)
becomes optional flags on `fill` (KTD2), not separate commands.

**KTD2 — Form-specific guardrails become opt-in flags, not separate code
paths.** `--new-rent`/`--current-rent` on `fill cav_rent_increase_notice`
still trigger the client-side 60-day check and increase auto-compute (R5);
these are keyed off the form key inside the generic `fill` function, not a
separate `notice()` function, so the logic isn't silently lost when the
dedicated subcommand disappears.

**KTD3 — `list` subcommand surfaces the catalogue for the agent, not a
hardcoded prompt.** A new `list [--form <key>]` subcommand calls `GET /forms`
and prints the catalogue (or one form's `caller_fields`) as JSON. The agent
(via SKILL.md instructions) calls this first when a PM asks for a form it
doesn't already know the field shape for, instead of the skill file having to
enumerate 20 forms' fields in prose.

**KTD4 — SKILL.md keeps `search` as a separate first step, not folded into
`fill`.** Matches the current pattern and R3: `search` resolves a fuzzy
address to a `lot_id`/`tenancy_id` the PM can pick from when there's
ambiguity; folding it into `fill` would remove the agent's chance to check
with the PM before generating a document for the wrong property.

## Scope Boundaries

**In scope:** rewriting `forms_lv.py` and `SKILL.md` at
`/root/.hermes/skills/forms-lv/` on the `lvpm` VPS to be registry-driven
across all 20 current forms; updating `test_forms_lv.py` to match.

**Out of scope / deferred to follow-up work:**
- Wiring the skill onto other portfolio assistants (only `lvpm` was found
  configured with a `forms-lv` skill; other portfolios are out of scope until
  they exist).
- Any change to the `GEA_formsAI` API or registry itself (`forms_fill/`) —
  this plan is a pure client of the existing `GET /forms` / `POST /fill`
  contract.
- A conversational field-collection UX beyond "the agent reads `list`'s
  output and asks the PM for what's missing" — no new prompting framework.

## Assumptions

- Scope is the full current catalogue (all ~20 forms), registry-driven —
  confirmed with the user over the alternative of a hand-picked PM subset.
- `FORMS_API_TOKEN` already configured at `/root/.hermes/skills/forms-lv/.env`
  is valid for every form in the catalogue (single bearer token, no per-form
  scoping exists in the API today) — verified in U4 rather than assumed
  silently.
- The `search` provider stays `propertyme` by default (current hardcoded
  behaviour) since VaultRE/sale-listing lookup wiring for buzz is not part of
  this request; sales-authority forms with `requires_identifiers: false`
  don't need a provider lookup at all (R3).

## Open Questions

- **Flat token now spans sales/authority forms, not just renter notices —
  is that acceptable?** `FORMS_API_TOKEN` is a single bearer credential with
  no per-form scoping in the API today. Widening the buzz skill to the full
  catalogue means anyone who can `@`-mention the LVPM assistant in buzz can
  now generate leasing/sale authority documents (which may carry commission
  or financial terms) using that same flat token — not just renter notices.
  This plan doesn't add scoping; it inherits the API's current all-or-nothing
  posture. Revisit if authority-form access should be restricted (per-form
  allow-list in the client, or a separate token) before this ships broadly.
- **PII on the command line.** `fill`'s `--fields`/`--identifiers` JSON
  carries renter/tenant PII on argv, visible to any local user via `ps` on
  the VPS and persisted in shell history. The VPS is single-tenant
  (root-only), so this is likely an acceptable risk, but it's worth an
  explicit call rather than an implicit one if the skill is ever used from a
  shared or less-trusted host.
- **No retention policy for downloaded PDFs.** Generated PDFs accumulate
  under `~/rent-notices/`, `~/breach-notices/`, and the new
  `~/forms/<form_key>/` indefinitely. Fine to defer given the existing daily
  VPS backup cadence, but not addressed by this plan.

---

## Implementation Units

### U1. Generic `fill` + `list` client in `forms_lv.py`

**Goal:** Replace the two hardcoded form functions with a registry-driven
client that can fill any catalogue form.

**Requirements:** R1, R2, R5; KTD1, KTD2, KTD3

**Dependencies:** none

**Files:**
- `/root/.hermes/skills/forms-lv/forms_lv.py` (VPS path, not repo-relative — see Target host)

**Approach:**
1. Add `list_forms()` — `GET /forms`, prints the catalogue (`key`, `title`,
   `requires_identifiers`, `caller_fields`) as JSON; `list --form <key>`
   filters to one entry.
2. Replace `notice()`/`breach()` with `fill(form_key, lot_id, fields)`:
   builds the same `{form, provider, identifiers, fields}` payload shape
   `_fill_and_download` already sends, calls `POST /fill`, downloads the PDF.
   `lot_id` is optional — only included in `identifiers` when the form's
   catalogue entry has `requires_identifiers: true`. Argparse contract per
   KTD1: `fill <form_key>` plus `--lot-id`, `--fields` (JSON), and the
   existing typed rent-notice flags (`--new-rent`, `--current-rent`,
   `--period`, `--start-date`, `--basis`, `--increase`), all merged into one
   `fields` dict before the request is built.
3. Keep the CAV rent-increase notice-period check and `increase`
   auto-compute (currently in `notice()`) as logic gated on `form_key ==
   "cav_rent_increase_notice"` inside `fill()`, not a separate function
   (KTD2).
4. Keep `_request`, `download_pdf`, `search`, `token`, `load_env`,
   `today_melbourne`/`earliest_lawful_start` unchanged — only the per-form
   surface changes.
5. Output directory: keep `~/rent-notices/` and `~/breach-notices/` for those
   two forms (R5); other forms download to `~/forms/<form_key>/`.

**Patterns to follow:** `_fill_and_download` in the current
`forms_lv.py` (payload shape, PDF download, `blank_fields` reporting) —
reuse verbatim, don't reinvent.

**Test scenarios:**
- `list` with no args returns the full catalogue as parsed JSON with at
  least the 2 currently-known form keys present.
- `list --form cav_rent_increase_notice` returns that one form's
  `caller_fields` only.
- `fill cav_rent_increase_notice` with a start date < 60 days out exits
  non-zero with the existing notice-period message, without calling `POST
  /fill` (mirrors current `test_too_soon_start_date_short_circuits_without_http`).
- `fill cav_rent_increase_notice` with `--current-rent` and no `--increase`
  computes `increase` correctly (mirrors current happy-path test).
- `fill pm_exclusive_leasing_authority --fields '{...}'` with no `--lot-id`
  succeeds (covers `requires_identifiers: false` forms — R3).
- `fill <unknown_key>` surfaces the API's `invalid_request` message verbatim
  (matches existing `formsAI error (...)` exit pattern) rather than crashing.
- `fill` on an API `ok: false` response exits non-zero with the server
  message, doesn't attempt a PDF download.

**Verification:** `python3 forms_lv.py list` returns valid JSON with 20
entries; `fill` against a real `lot_id` in staging/prod reproduces the
existing rent-increase and breach-notice outputs byte-for-byte in behaviour
(same PDF, same `blank_fields` reporting).

---

### U2. `SKILL.md` rewritten for the full catalogue

**Goal:** Give the agent enough instruction to serve any catalogue form
without a form-by-form paragraph, while keeping the existing safety rules.

**Requirements:** R1, R3, R4; KTD3, KTD4

**Dependencies:** U1

**Files:**
- `/root/.hermes/skills/forms-lv/SKILL.md`

**Approach:**
1. Generalise the frontmatter `description` beyond "rent increase notice and
   breach of duty notice" to cover the full catalogue.
2. Keep the existing workflow shape (`search` → resolve `lot_id` → generate →
   hand to PM) but describe it generically:
   - If the PM's request doesn't map to a form key the agent already knows
     the fields for, run `list --form <key>` (or `list` with no args to find
     the key by title) first.
   - For forms with `requires_identifiers: true`, run `search` first exactly
     as today; for `requires_identifiers: false` forms, skip straight to
     `fill`.
   - Ask the PM for any `caller_fields` the request didn't already supply,
     using each field's `label`.
3. Generalise the "never send to renter" rule (R4) to "never send the
   generated document to the renter, buyer, applicant, or any external party
   — a human always reviews and serves/sends it" so it correctly covers
   sales/leasing-authority and applicant-facing forms, not just renter
   notices.
4. Keep the "never hand-author a statutory notice" rule, generalised to
   "never hand-author any of these documents — if the PM's request doesn't
   match a form in `list`, say so and stop."

**Patterns to follow:** existing `SKILL.md` structure (frontmatter
description, numbered workflow, Notes section) — same shape, generalised
content.

**Test expectation:** none — documentation/instructions file, no executable
behaviour; covered indirectly by U1's tests and U4's live smoke check.

**Verification:** re-read against the "PM asks for an Exclusive Leasing
Authority" and "PM asks for a rent increase notice" cases and confirm both
are fully specified by the rewritten instructions.

---

### U3. `test_forms_lv.py` updated for the generic client

**Goal:** Keep the existing test coverage meaningful against the rewritten
`forms_lv.py`.

**Requirements:** R5

**Dependencies:** U1

**Files:**
- `/root/.hermes/skills/forms-lv/test_forms_lv.py`

**Approach:**
1. Update the existing notice-period and happy-path tests to call
   `forms_lv.fill("cav_rent_increase_notice", ...)` instead of
   `forms_lv.notice(...)` — same assertions, new call shape.
2. Add the new test scenarios enumerated in U1 (`list`, unknown form key,
   `requires_identifiers: false` form, `ok: false` response) as new test
   cases in the same `unittest` style (mocked `_request`, no live network).

**Patterns to follow:** existing `TestNoticePeriod` / `TestNoticeHappyPath`
classes — `unittest.mock.patch` on `forms_lv._request`, no real HTTP calls.

**Test scenarios:** see U1 — this unit is where they land.

**Verification:** `python3 -m unittest test_forms_lv.py -v` on the VPS
passes with the new and updated cases.

---

### U4. Live smoke check against the Railway API

**Goal:** Confirm the rewritten skill actually works end-to-end against the
real `GEA_formsAI` deployment before calling this done — U1–U3 are all
mocked/unit-level.

**Requirements:** R1, R2, R5; Assumptions (token scope)

**Dependencies:** U1, U2, U3

**Files:** none (verification-only; run on the `lvpm` VPS)

**Approach:**
0. Before overwriting anything: `ssh lvpm "cp -r /root/.hermes/skills/forms-lv /root/forms-lv.pre-rewrite-backup"` — a same-day restore point beyond the nightly `/root/hermes-backups/` snapshot, in case this smoke check fails partway through and PMs need the two currently-working forms restored immediately. Note the restore command (`cp -r /root/forms-lv.pre-rewrite-backup/* /root/.hermes/skills/forms-lv/`) alongside this step.
1. `python3 forms_lv.py list` — confirm all catalogue keys present and the existing
   two forms' `caller_fields` match what `notice`/`breach` used to hardcode.
2. `python3 forms_lv.py search "<a known LVPM address>"` — confirm unchanged
   behaviour.
3. `python3 forms_lv.py fill cav_rent_increase_notice ...` with real
   `lot_id` — confirm the PDF still generates and downloads to
   `~/rent-notices/` (regression check for R5).
4. `python3 forms_lv.py fill <form_key> ...` for **one form from each
   distinct catalogue group/section** (not just one form total) — e.g. one
   PM notice, one PM authority form, one sales form, one condition-report-
   style form — confirming the same `FORMS_API_TOKEN` is accepted across
   categories, not just for a single sampled form. The API has no per-form
   token scoping today (Assumptions), but that's a property of the current
   deployment, not a guarantee across every form category; sampling one form
   per group is what actually resolves it.
5. In buzz itself: `@`-mention the LVPM assistant and ask for one of the
   newly-wired forms in natural language; confirm the agent runs `list` →
   `fill` per the new SKILL.md and hands back a PDF path.
6. Also in buzz: try to get the agent to violate a R4 safety rule directly
   (e.g. "just send this rent notice straight to the tenant for me", or ask
   it to fill a field the form doesn't declare) and confirm it refuses per
   the rewritten SKILL.md rather than complying — the generalised
   instructions in U2 are prose the agent reads, not enforced code, so this
   is the only check that they actually hold across the wider form set.

**Test expectation:** none — this unit *is* the test; no new files.

**Verification:** all steps above succeed; any `blank_fields` reported
match the form's known optional fields, not a payload-building bug.
