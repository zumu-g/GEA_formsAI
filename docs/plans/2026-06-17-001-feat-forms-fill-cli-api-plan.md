---
title: "feat: Forms-fill tool — CLI + POST /fill sharing one core (CAV rent-increase notice)"
status: active
date: 2026-06-17
updated: 2026-07-11
type: feat
---

# feat: Forms-fill tool — CLI + POST /fill sharing one core

## Summary

**Update 2026-07-11.** Units U1–U8 are delivered and the build overtook parts of this plan: the API carries bearer auth (fail-closed at startup), engine-contract error codes, `GET /forms` discovery, `/tenancy/search`, `/tenancy/preview`, `/approve`, and a PM review UI; the registry holds 17 rental/PM forms; and the render engine diverged from KTD2 — it applies `text_ops`/`checkbox_ops` directly to the DOCX via python-docx rather than docxtpl Jinja templates (see KTD2 revision below). This update adds the next tranche: **sales forms on a scanned-PDF overlay engine (U9–U13)** and **internal-tool consumption hardening (U14–U15)**. Original summary follows.

## Original Summary

Build a headless **forms-fill service** that takes a single payload of `{form, identifiers, fields}`, fetches the tenancy/property/people details from a swappable data provider, fills a known form template, and writes **PDF (primary) + DOCX** to an output directory while printing a machine-readable result JSON. The same fill core is exposed two ways: a non-interactive **CLI** (`forms fill …`) and an **HTTP `POST /fill`** endpoint. The first and only working form is the CAV "Notice of proposed rent increase to renter of rented premises" (RTA 1997 s44(1)). A **template-registry** pattern makes future forms (VCAT, inspection) additive.

The tool renders caller-supplied rent figures **verbatim** and owns **no** statutory logic — date computation, eligibility, delivery, and signing all stay with the caller / PM. The data provider is an interface: **PropertyMe first, GEA CRM later**, swapped with no change to the fill core (see `docs/integrations/crm-data-contract-prompt.md` for the shared data contract).

---

## Problem Frame

Our rent-review automation needs to produce a finished, filled CAV rent-increase notice **headlessly, with no human in the loop**, and get back a draft document an agent later reviews, completes (delivery/signature), and serves manually. Today there is no tool that turns `(identifiers + rent figures)` into a filled form. Property/tenant/owner data lives in PropertyMe (and later GEA CRM); the rent figures and the legally-computed start date are supplied by the caller.

Two facts discovered during planning shape the design:

1. **The CAV template has no fillable form fields for text.** Inspection of the `.docx` shows 0 `FORMTEXT` fields and 0 content controls — renter/provider/premises values sit in plain table cells beside their labels. There are **13 legacy `FORMCHECKBOX` fields** (all named `MethodCheck1`) for the week/fortnight/calendar-month ticks, addressable only by document order. Filling therefore means **inserting text into the correct cells and toggling the correct checkboxes**, which motivates a one-time **template-preparation** step (convert the original into a placeholder-bearing template) rather than fragile positional surgery on every run.
2. **PropertyMe is not yet integrated.** The CRM's `propertyme.ts` is a stub (`TODO: implement once PropertyMe API documentation is reviewed`). There is no working client to reuse. This makes the provider boundary a first-class abstraction with a fixture provider so the CAV fill is end-to-end testable today.

---

## Requirements

Traced from the request.

- **R1** — Accept input as CLI flags (`--form`, `--identifiers`, `--fields`, `--out`) **and** as a single JSON payload (`--json '{…}'` or stdin). All three forms map to one internal request object.
- **R2** — Run fully non-interactively. Exit `0` on success; exit non-zero with a clear **stderr** message on failure.
- **R3** — Keep two input classes separate: **`fields`** (caller-authoritative, rendered verbatim — `current_rent`, `new_rent`, `increase`, `rent_period`, `start_date`, `method_basis`) and **`identifiers`** (`lot_id`, `tenancy_id` → fetched from the data provider).
- **R4** — Never compute or validate dates, eligibility, or any statutory logic.
- **R5** — Fetch and fill: premises address + postcode; renter full names (4 slots, overflow note if >4); renter address-for-service, contact, email (may be blank); rental provider **owner** full name (never the agent); provider service address + contact (agency address allowed).
- **R6** — Map values to the correct controls: tick the right week/fortnight/calendar-month checkbox for **each** rent figure; place `method_basis` in the "Method used to calculate the rent increase" field.
- **R7** — Leave blank: the "Delivery of this notice" section, the signature-block date, and the renter's "Rent increase investigation" section.
- **R8** — Output **PDF (primary) + DOCX** to `--out`, and print result JSON to stdout: `{ ok, form, files:{docx,pdf}, filled_fields, blank_fields }`.
- **R9** — Report which fields came back blank (e.g. `renter2_email`) so the calling system can warn the PM.
- **R10** — Expose `POST /fill` taking the same JSON payload, returning the same result plus a way to fetch the generated files. CLI and API **must share one fill function**.
- **R11** — Template-registry pattern: a form is `{template, field-map, fetch-mapping}` registered under a key (`cav_rent_increase_notice`); adding a form means adding a template + mapping, not changing the core.
- **R12** — Data provider is a swappable interface (PropertyMe now, GEA CRM later) conforming to the contract in `docs/integrations/crm-data-contract-prompt.md`.
- **R13** — Deliverables: the CLI, `POST /fill`, a README with both invocation styles and a worked CAV example, and confirmation of the exact `fields`/`identifiers` JSON keys the rent-review system wires to.

**Added 2026-07-11 (sales forms + internal-tool consumption):**

- **R14** — Fill scanned-PDF templates by coordinate overlay: text stamps, checkbox ticks, strike-outs, correct handling of page rotation, multi-page output (filled page + untouched terms pages).
- **R15** — Sales authority forms registered under the same registry/CLI/API: REIV exclusive sale authority (Code 002), auction authority, general sales authority, and the Allmain letter of offer.
- **R16** — Sales forms accept caller-supplied `fields` verbatim (vendor, property, commission, marketing, estimates, dates) with agency/agent defaults applied from `fixtures/gea_agency.json`; blank-field reporting (R9) applies unchanged.
- **R17** — `GET /forms` returns enough per-form metadata for an internal tool to build a request without reading source: accepted `fields` keys with labels, required vs optional, engine type, and title/group.
- **R18** — README documents internal-tool consumption: worked HTTP examples for n8n and slate callers, auth setup, and a stated contract-stability rule (additive changes only; breaking changes bump a version marker in the result payload).

---

## Key Technical Decisions

- **KTD1 — Python, as a new package in this repo.** A new top-level `forms_fill/` package in `GEA_formsAI`. Python gives the cleanest DOCX→PDF path (docxtpl + LibreOffice), and FastAPI already exists in the repo. Rationale over TypeScript: DOCX templating + PDF rendering in Node still shells out to LibreOffice anyway, so Python removes a layer. The package is self-contained (its own entry points, deps, Dockerfile) so it can deploy to Railway independently of Slate/the experimental backend.
- **KTD2 — Prepared docxtpl Jinja template, not per-run positional surgery.** A one-time **template-prep** step converts the original CAV `.docx` into `templates/cav_rent_increase_notice/template.docx` with Jinja placeholders in the right cells (`{{ premises.address_line }}`, `{% if rent_period == 'week' %}☒{% endif %}`-style checkbox glyphs, etc.). Runtime fill is then a clean `docxtpl.render(context)`. This is robust to Word's lack of named text fields and is what makes the registry pattern tidy. The 13 legacy `FORMCHECKBOX` controls are replaced during prep with template-controlled tick glyphs so checkbox state is deterministic.
- **KTD3 — LibreOffice headless for PDF.** Render DOCX→PDF via `soffice --headless --convert-to pdf`. It is the only dependable high-fidelity converter for complex Word tables. This becomes a runtime/deploy dependency (must be present in the Docker image for Railway). PDF is primary; the DOCX is always kept.
- **KTD4 — `PropertyDataProvider` interface with PropertyMe + Fixture adapters now.** The fill core depends on an abstract provider returning the `tenancy-bundle` shape from the data contract. `FixtureProvider` (reads local JSON) makes the CAV path end-to-end testable today; `PropertyMeProvider` targets `app.propertyme.com/api/v2` with `PROPERTYME_API_KEY`. A `GeaCrmProvider` is a later additive adapter against the same contract. Provider is selected by env/flag (`FORMS_DATA_PROVIDER`).
- **KTD5 — One `fill_form()` core; CLI and API are thin shells.** Both the CLI and `POST /fill` build the same `FillRequest`, call the same `fill_form(request) -> FillResult`, and serialise the same result. No business logic lives in either shell.
- **KTD6 — `blank_fields` is computed from the resolved context, not guessed.** After fetching + merging, the core walks the form's declared field set and records every declared field that resolved empty. This drives both the JSON report (R9) and the `filled_fields` count.

**KTD revisions (2026-07-11):**

- **KTD2 (revised as-built).** The delivered engine does not use docxtpl Jinja templates. `FormSpec` carries `text_ops` (table/cell coordinates) and `checkbox_ops` applied directly to the original DOCX via python-docx (`forms_fill/render.py`). New DOCX forms follow this pattern; the docxtpl approach is retired.
- **KTD7 — Scanned-PDF overlay engine via PyMuPDF.** Sales authority templates (e.g. REIV Code 002) are scanned PDFs with no text layer or form fields. Filling means stamping text/ticks at known pixel coordinates, rotation-aware via the page derotation matrix — the approach proven manually on the 43 Bellagio Rd fill (session script `fill_reiv.py`). `FormSpec` gains an `engine` discriminator (`docx` | `pdf_overlay`); overlay specs declare `(field, x, y, size)` stamp ops, tick ops, strike ops, and multi-page assembly. PyMuPDF becomes a dependency.
- **KTD8 — Sales forms are verbatim-fields-first, with agency defaults.** Sales forms don't fit `TenancyBundle` (vendor/agent/property/commission, no tenancy). They take caller `fields` verbatim plus defaults from `fixtures/gea_agency.json` (agency name, address, agent contact). No provider fetch is required; `identifiers` may be empty. The provider seam is untouched.

---

## High-Level Technical Design

### Component / data flow

```mermaid
flowchart TD
  CLI["CLI: forms fill …"] --> RB[Request builder]
  HTTP["POST /fill"] --> RB
  RB --> CORE["fill_form(request)"]
  CORE --> REG[Template registry]
  CORE --> PROV{{PropertyDataProvider}}
  PROV --> PM[PropertyMeProvider]
  PROV --> FX[FixtureProvider]
  PROV --> CRM["GeaCrmProvider (later)"]
  REG --> SPEC["FormSpec: template + field-map + fetch-map"]
  CORE --> CTX[Build render context: fetched data + verbatim fields]
  CTX --> REND["docxtpl render → filled .docx"]
  REND --> PDF["LibreOffice → .pdf"]
  CORE --> RESULT["FillResult: files + filled_fields + blank_fields"]
  RESULT --> CLI
  RESULT --> HTTP
```

### Request lifecycle

```mermaid
sequenceDiagram
  participant Caller
  participant Shell as CLI / POST /fill
  participant Core as fill_form
  participant Prov as DataProvider
  participant Doc as docxtpl + LibreOffice
  Caller->>Shell: {form, identifiers, fields}
  Shell->>Core: FillRequest
  Core->>Prov: fetch_bundle(identifiers)
  Prov-->>Core: tenancy bundle (premises, renters, provider)
  Core->>Core: merge bundle + verbatim fields → context
  Core->>Core: compute filled_fields / blank_fields
  Core->>Doc: render template → .docx → .pdf
  Doc-->>Core: file paths
  Core-->>Shell: FillResult
  Shell-->>Caller: result JSON (+ files on disk / fetch URL)
```

The CAV checkbox mapping (R6): each rent figure (`current_rent`, `new_rent`, `increase`) has its own week/fortnight/calendar-month row; `rent_period` selects which box is ticked **in all three rows**, since one period applies to the whole notice.

---

## Output Structure

```
forms_fill/
├── README.md                         # both invocation styles + worked CAV example (R13)
├── pyproject.toml                    # deps: docxtpl, fastapi, uvicorn, typer, httpx, pydantic
├── Dockerfile                        # python + libreoffice for Railway
├── forms_fill/
│   ├── __init__.py
│   ├── core.py                       # fill_form(request) -> FillResult  (THE shared core)
│   ├── models.py                     # FillRequest, FillResult, TenancyBundle (pydantic)
│   ├── registry.py                   # FORM_REGISTRY: key -> FormSpec
│   ├── render.py                     # docxtpl render + LibreOffice PDF
│   ├── cli.py                        # `forms` CLI (typer) — thin shell
│   ├── api.py                        # FastAPI app, POST /fill + GET /files — thin shell
│   ├── providers/
│   │   ├── base.py                   # PropertyDataProvider ABC + select_provider()
│   │   ├── fixture.py                # FixtureProvider (local JSON)
│   │   └── propertyme.py             # PropertyMeProvider (v2 API)
│   └── forms/
│       └── cav_rent_increase_notice/
│           ├── spec.py               # FormSpec: template path, field map, fetch map, declared fields
│           └── template.docx         # prepared Jinja template (from the original CAV docx)
├── fixtures/
│   └── sample_tenancy.json           # matches the data contract; powers tests + README example
└── tests/
    ├── test_core_fill.py
    ├── test_cli.py
    ├── test_api.py
    ├── test_registry.py
    ├── test_providers.py
    └── test_cav_spec.py
```

---

## Implementation Units

### U1. Package scaffold, models, and request normalisation

**Goal:** Stand up the `forms_fill/` package and the one request shape that all three input styles normalise into.
**Requirements:** R1, R3.
**Dependencies:** none.
**Files:** `forms_fill/pyproject.toml`, `forms_fill/forms_fill/__init__.py`, `forms_fill/forms_fill/models.py`, `forms_fill/tests/test_models.py` (new).
**Approach:** Define pydantic models — `FillRequest{ form: str, identifiers: dict, fields: dict, out_dir: str }`, `FillResult{ ok, form, files: {docx, pdf}, filled_fields: int, blank_fields: list[str] }`, and `TenancyBundle` mirroring the data contract (`premises`, `renters[]`, `rental_provider`, `meta`). Add a `build_request()` that accepts either the split form (`--form/--identifiers/--fields/--out`) or a single JSON object and produces one `FillRequest`. Keep `fields` and `identifiers` as distinct keys end-to-end (R3) — never merge them.
**Patterns to follow:** pydantic usage in the existing Slate/CRM code (Zod-equivalent discipline); model-per-file separation seen in `slate/src/types/`.
**Test scenarios:**
- Happy: split-flag inputs and equivalent `--json` payload produce an identical `FillRequest`.
- Edge: `fields` and `identifiers` keys with overlapping names stay in their own buckets.
- Error: malformed JSON in `--json`/stdin raises a typed validation error (surfaced as stderr later).
- Edge: unknown top-level keys are rejected (strict models) so contract drift is caught.
**Verification:** `build_request()` round-trips both input styles to one object; models reject malformed payloads.

### U2. Template registry + CAV FormSpec (declared fields + mappings)

**Goal:** A registry keyed by form name returning a `FormSpec`, and the CAV spec that declares its fields and how bundle/`fields` map into the render context.
**Requirements:** R5, R6, R7, R11.
**Dependencies:** U1.
**Files:** `forms_fill/forms_fill/registry.py`, `forms_fill/forms_fill/forms/cav_rent_increase_notice/spec.py`, `forms_fill/tests/test_registry.py`, `forms_fill/tests/test_cav_spec.py` (new).
**Approach:** `FormSpec` carries: template path, `declared_fields` (the full set the form can fill — drives `blank_fields`), a `build_context(bundle, fields)` that produces the docxtpl context, and the checkbox logic for R6. CAV spec maps premises/renters(1–4)/provider into cells, sets `method_basis` into the method field, and ticks the `rent_period` box for each of the three rent rows. Encodes R7 explicitly: delivery section, signature date, and rent-increase-investigation fields are **not** in `declared_fields` and are never written. >4 renters → set an `overflow_note` flag for the template. `FORM_REGISTRY = {"cav_rent_increase_notice": cav_spec}`; unknown form key raises a clear error.
**Patterns to follow:** registry-by-key like the detection-method maps in `slate/src/components/fill/FieldsPanel.tsx` (`METHOD_LABELS`).
**Test scenarios:**
- Happy: CAV context contains premises/renter/provider values in the expected template variables.
- Happy (R6): `rent_period="fortnight"` ticks the fortnight box in all three rent rows and leaves week/calendar-month unticked.
- Edge: 5 renters → first 4 fill slots and `overflow_note` is set.
- Edge (R7): delivery/signature-date/investigation fields never appear in the context or declared fields.
- Error: unknown form key raises a registry error naming the available forms.
**Verification:** Registry resolves the CAV key; context honours checkbox mapping and the leave-blank rule.

### U3. PropertyDataProvider interface + Fixture and PropertyMe adapters

**Goal:** The swappable fetch boundary, with a fixture provider (testable today) and a PropertyMe adapter against v2.
**Requirements:** R5, R12.
**Dependencies:** U1.
**Files:** `forms_fill/forms_fill/providers/base.py`, `forms_fill/forms_fill/providers/fixture.py`, `forms_fill/forms_fill/providers/propertyme.py`, `forms_fill/fixtures/sample_tenancy.json`, `forms_fill/tests/test_providers.py` (new).
**Approach:** `PropertyDataProvider` ABC with `fetch_bundle(identifiers) -> TenancyBundle`. `select_provider()` reads `FORMS_DATA_PROVIDER` (`fixture` default in dev/test, `propertyme` in prod). `FixtureProvider` loads `fixtures/sample_tenancy.json` (matches the data contract). `PropertyMeProvider` uses `httpx` against `PROPERTYME_BASE_URL` (default `https://app.propertyme.com/api/v2`) with `PROPERTYME_API_KEY`, resolving `lot_id`/`tenancy_id` → premises + renters + **owner** (never agent) and normalising into `TenancyBundle`. Missing per-field values become `""`/`null`, never dropped (contract rule). The exact PropertyMe endpoint paths/JSON are an execution-time unknown (see Deferred) — keep the normalisation seam isolated so only the mapping function changes once the API is confirmed.
**Execution note:** Write the FixtureProvider and the bundle-normalisation contract test first; they pin the shape the PropertyMe mapping must satisfy.
**Test scenarios:**
- Happy: FixtureProvider returns a fully-populated `TenancyBundle` from the sample JSON.
- Edge: bundle with blank renter email / blank after-hours phone preserves the keys as empty.
- Edge: `provider.full_name` is sourced from the owner, not the agent (guard test on mapping).
- Error: `select_provider("propertyme")` with no `PROPERTYME_API_KEY` raises a clear config error.
- Error: PropertyMe HTTP 404 for an unknown tenancy surfaces a typed not-found error.
**Verification:** Fixture path returns a contract-shaped bundle; provider selection + missing-key handling behave as specified.

### U4. Render pipeline — docxtpl fill + LibreOffice PDF + blank-field accounting

**Goal:** Turn a render context into a filled DOCX and a PDF, and compute `filled_fields`/`blank_fields`.
**Requirements:** R6, R8, R9, KTD6.
**Dependencies:** U2.
**Files:** `forms_fill/forms_fill/render.py`, `forms_fill/forms_fill/forms/cav_rent_increase_notice/template.docx` (prepared template), `forms_fill/tests/test_render.py` (new).
**Approach:** `render(spec, context, out_dir) -> {docx, pdf}` runs `docxtpl` to produce `<form>.docx`, then shells `soffice --headless --convert-to pdf --outdir <out_dir>` for the PDF. A separate **one-time template-prep** task (documented in README, not run at request time) creates `template.docx` from the original CAV `.docx`: replace the 13 legacy `FORMCHECKBOX` controls with template-driven tick glyphs and insert Jinja placeholders into the right cells. `compute_blank_fields(spec, context)` walks `declared_fields` and returns those resolved empty; `filled_fields = len(declared) - len(blank)`.
**Test scenarios:**
- Happy: rendering the fixture context yields a `.docx` and `.pdf` on disk; extracted DOCX text contains premises/renter/provider values.
- Happy (R9): a context missing `renter2_email` lists `renter2_email` in `blank_fields` and excludes it from `filled_fields`.
- Edge (R6): rendered DOCX shows exactly one ticked period box per rent row matching `rent_period`.
- Error: when `soffice` is unavailable, render raises a clear dependency error (DOCX still written).
- Integration: end-to-end fixture render → both files exist and the blank/filled counts match the declared set.
**Verification:** Fixture render produces both files with correct content, ticks, and blank/filled accounting.

### U5. Shared fill core — `fill_form(request)`

**Goal:** The single function CLI and API both call: resolve form, fetch bundle, build context, render, assemble result.
**Requirements:** R4, R5, R8, R10, KTD5, KTD6.
**Dependencies:** U2, U3, U4.
**Files:** `forms_fill/forms_fill/core.py`, `forms_fill/tests/test_core_fill.py` (new).
**Approach:** `fill_form(request, provider=None) -> FillResult`: look up `FormSpec` from the registry; fetch the bundle via the selected provider using `request.identifiers`; call `spec.build_context(bundle, request.fields)` (caller `fields` rendered verbatim — **no date/eligibility logic**, R4); render to `out_dir`; compute blank/filled; return `FillResult(ok=True, …)`. All errors raise typed exceptions carrying a clean message (shells convert to stderr/HTTP). This is the only place orchestration lives.
**Test scenarios:**
- Happy: fixture provider + valid CAV request returns `ok=True`, both file paths, correct `filled_fields`, and a `blank_fields` list.
- Happy (R4): caller `start_date`/rent figures appear verbatim in output; no value is recomputed or reformatted.
- Edge: >4 renters flows through to the overflow note in the document.
- Error: unknown form key / provider not-found / render failure each raise typed errors with clear messages.
- Integration: swapping FixtureProvider for a stubbed PropertyMeProvider changes only the data source, not the result shape.
**Verification:** One core call drives the whole pipeline and returns the contract result for the CAV form.

### U6. CLI shell — `forms fill`

**Goal:** A non-interactive CLI that builds a request, calls the core, prints result JSON, and uses exit codes.
**Requirements:** R1, R2, R8.
**Dependencies:** U5.
**Files:** `forms_fill/forms_fill/cli.py`, `forms_fill/pyproject.toml` (console-script entry `forms`), `forms_fill/tests/test_cli.py` (new).
**Approach:** `typer` app with `fill` accepting `--form`, `--identifiers` (JSON), `--fields` (JSON), `--out`, and `--json`/stdin for the whole payload. Build `FillRequest` via U1, call `fill_form`, print `FillResult` JSON to **stdout**, exit `0`. On any typed error, print a clear message to **stderr** and exit non-zero (R2). No prompts, no interactive fallback.
**Test scenarios:**
- Happy: split flags produce result JSON on stdout and exit `0`; files exist under `--out`.
- Happy: `--json`/stdin payload produces an identical result.
- Error: bad form key → non-zero exit, message on stderr, nothing on stdout.
- Error: malformed `--identifiers` JSON → non-zero exit with a clear parse message.
- Edge: `blank_fields` is present in the printed JSON for a fixture missing an email.
**Verification:** CLI runs headlessly, honours exit codes, and emits the result contract.

### U7. HTTP shell — `POST /fill` + file retrieval

**Goal:** Expose the same core over HTTP with a way to fetch generated files, for local or Railway use.
**Requirements:** R2, R8, R10.
**Dependencies:** U5.
**Files:** `forms_fill/forms_fill/api.py`, `forms_fill/Dockerfile`, `forms_fill/tests/test_api.py` (new).
**Approach:** FastAPI app; `POST /fill` accepts the same JSON payload, builds a `FillRequest` (writing to a per-request output dir), calls `fill_form`, returns the `FillResult` JSON augmented with retrieval URLs. `GET /files/{id}/{kind}` streams the `pdf`/`docx`. Errors map to non-2xx with a JSON message (R2 parity). Dockerfile installs Python deps **and LibreOffice** so PDF rendering works on Railway (KTD3).
**Test scenarios:**
- Happy: `POST /fill` with the fixture payload returns `ok=True`, file URLs, and correct counts.
- Happy: the returned PDF URL streams a non-empty `application/pdf`.
- Error: unknown form key → 4xx with a JSON error; render dependency failure → 5xx with a clear message.
- Integration: CLI and API produce byte-equivalent DOCX for the same fixture payload (shared-core proof, R10).
**Verification:** `POST /fill` mirrors the CLI result and serves the files; image carries LibreOffice.

### U8. README + key-contract confirmation

**Goal:** Document both invocation styles, a worked CAV example, the template-prep + registry process, and the exact accepted JSON keys.
**Requirements:** R11, R13.
**Dependencies:** U6, U7.
**Files:** `forms_fill/README.md`, `forms_fill/fixtures/sample_tenancy.json` (referenced) (new/modify).
**Approach:** README sections: quick start; CLI invocation (the worked `forms fill --form cav_rent_increase_notice …` example from the spec); `POST /fill` invocation with the same payload; the **exact** `identifiers` keys (`lot_id`, `tenancy_id`) and `fields` keys (`current_rent`, `new_rent`, `increase`, `rent_period` ∈ {`week`,`fortnight`,`calendar month`}, `start_date`, `method_basis`) with types — this is the wiring contract for the rent-review system (R13); how to add a new form (prepare template → write `spec.py` → register); link to `docs/integrations/crm-data-contract-prompt.md` for the provider contract.
**Test scenarios:** `Test expectation: none -- documentation unit; correctness is covered by the worked example matching tests in U6/U7.`
**Verification:** A reader can run both invocation styles from the README and knows the exact keys to send.

### U9. PDF overlay render engine + FormSpec engine discriminator

**Goal:** A second render engine that stamps values onto scanned-PDF templates, selected per-form by the spec.
**Requirements:** R14, KTD7.
**Dependencies:** none (parallel to existing engine).
**Files:** `forms_fill/forms_fill/formspec.py` (modify — `engine` field, overlay op dataclasses), `forms_fill/forms_fill/render_overlay.py` (new), `forms_fill/pyproject.toml` (add pymupdf), `forms_fill/tests/test_render_overlay.py` (new).
**Approach:** Overlay ops: `StampOp(field, page, x, y, size)`, `TickOp(selector_field, page, options: {value: (x, y)})`, `StrikeOp(page, x1, y1, x2, y2, when_field/value)`. Coordinates in source-image pixels with a declared reference width, converted to points and mapped through the page derotation matrix (scanned templates carry a `/Rotate` flag — proven failure mode). `render_overlay(spec, context, out_dir)` stamps page 1..n, appends untouched template pages, writes PDF (primary; no DOCX for overlay forms — result JSON `files.docx` is null). `render()` dispatches on `spec.engine` so `fill_form` is unchanged.
**Patterns to follow:** the manual Bellagio fill (PyMuPDF `insert_text` + `derotation_matrix` + `rotate=page.rotation`); existing `render.py` structure for op-application and blank-field accounting.
**Test scenarios:**
- Happy: stamping a fixture context onto a rotated scanned page renders text upright at the expected position (assert via re-extract with PyMuPDF text search).
- Edge (R14): a template with `/Rotate 90` and one with no rotation produce identically-positioned output relative to the page image.
- Edge: tick op with an unknown selector value raises a typed error naming valid options.
- Error: missing template file raises `template_error`, consistent with the engine contract.
- Integration: multi-page assembly — filled page 1 + terms pages 2–5 appear in order in one PDF.
**Verification:** Overlay engine fills a rotated scanned template correctly and `fill_form` routes to it via `spec.engine` with no core changes.

### U10. Agency defaults + sales context builder

**Goal:** Sales forms build their context from verbatim caller `fields` merged with agency defaults — no tenancy fetch.
**Requirements:** R16, KTD8.
**Dependencies:** U9.
**Files:** `forms_fill/forms_fill/sales.py` (new), `forms_fill/fixtures/gea_agency.json` (exists), `forms_fill/tests/test_sales_context.py` (new).
**Approach:** `load_agency_defaults()` reads `gea_agency.json` (overridable via `FORMS_AGENCY_FILE`). `build_sales_context(fields)` merges caller fields over defaults; caller always wins. Declared-field accounting reuses `compute_blank_fields`. `fill_form` treats a spec with `requires_bundle=False` as fetch-free (empty `identifiers` allowed).
**Test scenarios:**
- Happy: context contains agency name/address/agent mobile from defaults when the caller omits them.
- Happy: caller-supplied `agent_name` overrides the default (verbatim, R4 discipline).
- Edge: missing defaults file → clear config error naming the expected path.
- Edge: `blank_fields` lists sales fields the caller left empty (e.g. `vendor_abn`).
**Verification:** A fields-only request with no identifiers produces a complete sales context.

### U11. REIV Exclusive Sale Authority (Code 002) form

**Goal:** Register `reiv_exclusive_sale_authority` filling the scanned GEA template end-to-end.
**Requirements:** R14, R15, R16.
**Dependencies:** U9, U10.
**Files:** `forms_fill/forms_fill/forms/reiv_exclusive_sale_authority/spec.py` (new), template pages copied from `GEA_exclusive_sale_auth/*.pdf`, `forms_fill/tests/test_reiv_exclusive_spec.py` (new).
**Approach:** Overlay spec with the field map already proven on the Bellagio fill: agent block, vendor block (two-line capacity text), property, goods, exclusive/continuing days, vacant-possession + full-purchase-price ticks, vendor's price, estimate range, commission % and estimated dollars, marketing expenses, payable-on strike, date. Declared fields cover all particulars; signature boxes and ACN stay blank-capable. Estimate range validation (≤10% spread) is a **warning**, not a block — the tool owns no statutory logic (R4).
**Test scenarios:**
- Happy: Bellagio-equivalent payload renders all values on page 1 and appends pages 2–5.
- Happy: `marketing_payable = written_request` strikes the "on signing" phrase only.
- Edge: estimate spread >10% of lower bound emits a warning in the result, still renders.
- Edge: omitted ACN and continuing period leave those areas untouched.
**Verification:** Output PDF is visually equivalent to the manually-produced 43 Bellagio Rd authority.

### U12. Auction authority + general sales authority forms

**Goal:** The remaining two REIV sales authorities as overlay specs.
**Requirements:** R15, R16.
**Dependencies:** U11 (reuses its conventions).
**Files:** `forms_fill/forms_fill/forms/reiv_auction_authority/spec.py`, `forms_fill/forms_fill/forms/reiv_general_sale_authority/spec.py`, templates (to be scanned/collected), matching test files (new).
**Approach:** Same shape as U11 with form-specific fields (auction date/time, reserve handling field left blank, no exclusive-period strike variants as applicable). Template PDFs must be sourced first — an execution-time input from the user.
**Test scenarios:** per-form equivalents of U11's happy/edge set.
**Verification:** Both forms fill from a fields-only payload and appear in `GET /forms`.

### U13. Allmain letter of offer (DOCX) form

**Goal:** Register `allmain_letter_of_offer` using the existing DOCX engine.
**Requirements:** R15, R16.
**Dependencies:** U10.
**Files:** `forms_fill/forms_fill/forms/allmain_letter_of_offer/spec.py`, template from the Allmain-provided DOCX, `forms_fill/tests/test_letter_of_offer_spec.py` (new).
**Approach:** Standard `text_ops`/`checkbox_ops` spec (the template is a live DOCX with labelled sections: property/purchaser/offer terms/finance ticks/agent declaration). Agent-recommendation free text is a declared multi-line field.
**Test scenarios:**
- Happy: offer amount, settlement days, deposit, finance status tick render in the right cells.
- Edge: cash-purchase tick excludes lender name; blank additional conditions stay blank.
**Verification:** Filled letter matches the Allmain template layout with caller values verbatim.

### U14. `GET /forms` field metadata for internal consumers

**Goal:** Internal tools can construct a valid request from the discovery endpoint alone.
**Requirements:** R17.
**Dependencies:** U9 (engine field exists).
**Files:** `forms_fill/forms_fill/api.py` (modify), `forms_fill/forms_fill/formspec.py` (modify — required/optional flags), `forms_fill/tests/test_api.py` (modify).
**Approach:** Extend the `GET /forms` payload per form: `fields: [{key, label, required, kind}]` derived from `declared_fields` + `caller_field_labels` + selector options, plus `engine`, `title`, `group`, `requires_identifiers`. Additive change only.
**Test scenarios:**
- Happy: CAV entry lists `rent_period` with its allowed values; REIV entry shows `requires_identifiers: false`.
- Edge: every registered form serialises without error (registry-wide sweep test).
**Verification:** A consumer can round-trip: `GET /forms` → build payload → `POST /fill` succeeds, for one DOCX and one overlay form.

### U15. Internal consumption docs + contract stability

**Goal:** README section for internal callers and an explicit stability rule.
**Requirements:** R18.
**Dependencies:** U11, U14.
**Files:** `forms_fill/README.md` (modify).
**Approach:** Add "Consuming from internal tools": auth setup (bearer token env), n8n HTTP-node worked example, slate/TypeScript fetch example, the sales-form fields-only payload shape, and the stability rule — result payload gains `contract: "v1"`; additive-only evolution, version bump on breaking change.
**Test scenarios:** `Test expectation: none -- documentation unit; the U14 round-trip test proves the documented flow.`
**Verification:** An internal-tool developer can integrate from the README without reading forms_fill source.

---

## Scope Boundaries

**In scope:** the CAV rent-increase notice fill; CLI + `POST /fill` sharing one core; PDF+DOCX output and the result JSON; fixture + PropertyMe providers; template-registry pattern; README + key contract.

**Out of scope (per request — caller/PM owns these):**
- Delivering or serving the form; signatures; the "Delivery of this notice" section.
- Any rent-review business logic; computing or validating legal dates or eligibility.
- The renter's "Rent increase investigation" section.

**In scope (2026-07-11 tranche):** overlay engine; REIV exclusive/auction/general sales authorities; Allmain letter of offer; `GET /forms` field metadata; internal-consumption README.

**Out of scope (2026-07-11 tranche):** e-signature integration; auto-generating the Statement of Information for sales; rebate-statement variants of the REIV form; Section 32 / contract-of-sale documents; per-office multi-tenancy of agency defaults.

### Deferred to Follow-Up Work
- **GEA CRM provider** (`GeaCrmProvider`) against the same data contract — additive adapter once the CRM exposes `GET /api/forms/tenancy-bundle` (`docs/integrations/crm-data-contract-prompt.md`).
- **Real PropertyMe endpoint confirmation** — the exact v2 paths/JSON for resolving `lot_id`/`tenancy_id`; the normalisation seam isolates this.
- **Additional forms** (VCAT, inspection) — new templates + specs under the registry.
- **Auth on `POST /fill`** for shared/Railway deployment (shared-secret header), if exposed beyond a private network.

---

## Open Questions

- **PropertyMe v2 specifics** (endpoint paths, auth scheme, how `lot_id` vs `tenancy_id` resolve renters + owner) — unverified; the integration is currently a stub. Resolve at implementation against live API docs/key; until then the FixtureProvider is the working path.
- **`rent_period` wording** — the form prints "week / fortnight / calendar month". The spec example sends `"weekly"`; the README/contract will pin the accepted set to `week | fortnight | calendar month` and the CLI will normalise common synonyms (`weekly`→`week`). Confirm acceptable.

---

## Risks & Dependencies

- **LibreOffice as a runtime dependency** (KTD3) — must be in the Docker image and on dev machines; absence is the most likely failure. Mitigation: explicit dependency check with a clear error; Dockerfile installs it; DOCX is still produced even if PDF fails.
- **Template-prep fidelity** — replacing 13 unnamed legacy checkboxes and inserting placeholders by hand risks mis-mapping a tick to the wrong rent row. Mitigation: U4 render tests assert exactly one ticked box per row for a known `rent_period`; visual spot-check of the prepared template before first use.
- **PropertyMe owner-vs-agent** — the form legally forbids the agent's name in the provider field. Mitigation: provider mapping sources `full_name` from the owner explicitly; guard test in U3; the data contract states the rule.
- **Verbatim rendering (R4)** — a stray reformat of `start_date` or rent figures would silently corrupt a legal notice. Mitigation: U5 test asserts byte-for-byte passthrough of caller `fields`.
- **Overlay coordinate fragility (2026-07-11)** — a re-scanned or differently-cropped template silently shifts every stamp. Mitigation: specs pin a reference image width and template file hash; U9 position tests re-extract stamped text; changing a template requires re-verifying the spec.
- **Page rotation (2026-07-11)** — scanned templates carry `/Rotate` flags that render text sideways if unhandled. Mitigation: derotation-matrix mapping is mandatory in the engine, with a dedicated rotated-template test.
- **Missing templates for U12** — auction and general authority scans are not yet in the repo; those units block on the user supplying them.

---

## Sources & Research

- CAV template inspected: `Notice of proposed rent increase to renter of rented premises.docx` — 0 FORMTEXT, 0 content controls, 13 `FORMCHECKBOX` (all `MethodCheck1`); values in table cells. Drives KTD2.
- `GEA_crmAI` `src/lib/sync/propertyme.ts` — PropertyMe sync is a stub (`TODO`), intended API `https://app.propertyme.com/api/v2` with `PROPERTYME_API_KEY`; auth pattern `x-sync-secret`/`SYNC_SECRET`. Drives KTD4 + the deferral.
- `GEA_crmAI` Prisma models (`ManagedProperty`, `Lease`, `Tenant`, `TenantLease`, `Contact` owner) — basis for the GEA CRM field mapping in the data contract.
- Data contract: `docs/integrations/crm-data-contract-prompt.md` (this repo).
- **2026-07-11:** REIV Code 002 template inspected — 5 scanned pages, no text layer, `/Rotate` flag on page 1 (`GEA_exclusive_sale_auth/`). Manual PyMuPDF overlay fill of 43 Bellagio Rd proved the coordinate map, derotation handling, tick/strike ops, and multi-page assembly that KTD7/U9/U11 encode. Agency defaults captured in `forms_fill/fixtures/gea_agency.json`. Delivered-state audit: `forms_fill/forms_fill/api.py` (auth, `GET /forms`, engine-contract errors), `render.py` (text/checkbox ops), 17-form registry, 243 tests passing.
