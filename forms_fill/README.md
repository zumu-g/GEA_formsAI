# GEA forms-fill tool

Fills known legal form templates from **caller-supplied fields** plus **data
fetched from a property-data provider**, and writes a completed **PDF (primary)
+ DOCX** for an agent to review, complete (delivery/signature), and serve
manually. Runs headlessly — no human in the loop.

First (and currently only) form: the CAV **Notice of proposed rent increase to
renter of rented premises** (RTA 1997 s44(1)).

The CLI and the `POST /fill` endpoint share **one** fill core (`fill_form`).

---

## Two input classes (keep them separate)

| Class | Who owns it | Used for |
|-------|-------------|----------|
| **`fields`** | The **caller** (authoritative, rendered **verbatim**) | rent figures + the legally-computed start date |
| **`identifiers`** | Looked up from the **data provider** (PropertyMe now, GEA CRM later) | premises, renters, rental provider (owner) |

This tool **never** computes or validates dates, eligibility, or any statutory
logic. The caller owns all of that.

### Accepted JSON keys (wire the rent-review system to these)

`identifiers`:

| key | type | notes |
|-----|------|-------|
| `lot_id` | string | PropertyMe lot id |
| `tenancy_id` | string | PropertyMe tenancy id (preferred) |

`fields` (all rendered verbatim):

| key | type | notes |
|-----|------|-------|
| `current_rent` | number/string | current rent amount ($) |
| `new_rent` | number/string | new rent amount ($) |
| `increase` | number/string | amount of increase ($) |
| `rent_period` | string | one of `week`, `fortnight`, `calendar month` (synonyms `weekly`/`fortnightly`/`monthly` accepted) |
| `start_date` | string | start date of increased rent (printed as-is) |
| `method_basis` | string | method used to calculate the increase |

**Left blank by design:** the "Delivery of this notice" section, the
signature-block date, and the renter's "Rent increase investigation" section.

---

## CLI

```bash
forms fill \
  --form cav_rent_increase_notice \
  --identifiers '{"lot_id":"L-2002","tenancy_id":"T-1001"}' \
  --fields '{"current_rent":615,"new_rent":650,"increase":35,"rent_period":"weekly","start_date":"2026-09-15","method_basis":"market comparison (rental CMA)"}' \
  --out ./out/
```

Whole payload as one JSON object (stdin), which the HTTP endpoint reuses:

```bash
echo '{"form":"cav_rent_increase_notice","identifiers":{"lot_id":"L-2002"},"fields":{"current_rent":615,"new_rent":650,"increase":35,"rent_period":"week","start_date":"2026-09-15","method_basis":"CPI"}}' \
  | forms fill --json -
```

Result JSON is printed to **stdout**; exit code is `0` on success and non-zero
with a clear **stderr** message on failure:

```json
{
  "ok": true,
  "form": "cav_rent_increase_notice",
  "files": { "docx": "out/cav_rent_increase_notice.docx", "pdf": "out/cav_rent_increase_notice.pdf" },
  "filled_fields": ["premises_address", "renter1_name", "current_rent", "new_rent", "start_date"],
  "blank_fields": ["renter3_name", "renter4_name", "provider_after_hours"],
  "warnings": []
}
```

`blank_fields` lists declared fields that came back empty (e.g. a missing renter
email) so the calling system can warn the PM.

> If the `forms` console script fails to resolve on a path containing spaces
> (e.g. iCloud Drive), use `python -m forms_fill.cli …` — identical behaviour.

---

## Programmatic API (HTTP)

The engine contract the rent-review system is built against.

- **Auth:** every route (except `GET /health` and the `/auth/*` login flow)
  requires `Authorization: Bearer <token>` — either the machine
  `$FORMS_API_TOKEN` or an agent session token; missing/wrong →
  `401 {"ok":false,"error":"unauthorized"}`.
- **Agent accounts:** admins invite via `POST /agents/invite` (UI has a form);
  invites are restricted to `@grantsea.com.au`. The invite email goes out via
  Resend when `RESEND_API_KEY` (+ `MAIL_FROM`) is set; otherwise the response's
  `accept_url` is a copyable fallback link. Accounts/sessions persist in SQLite
  at `$FORMS_DATA_DIR/accounts.db` (default `./data`) — **on Railway, mount a
  volume at that path or accounts are wiped each deploy**. First invited agent
  is automatically admin; the machine token always counts as admin.
- **Drafts:** part-completed forms auto-save server-side per agent
  (`/drafts` CRUD, same SQLite file); the UI lists them under "In progress"
  and deletes the draft once the form is generated.
- **E-signature:** `POST /esign/send {request_id, recipients:[{name,email}]}`
  creates an Annature envelope from a generated PDF — Annature emails each
  signer. Needs `ANNATURE_ID` + `ANNATURE_KEY` (already in Railway), optional
  `ANNATURE_ACCOUNT_ID`; unset → 503.
- **Fail-closed startup:** the app refuses to start unless `FORMS_API_TOKEN`
  **and** `PUBLIC_BASE_URL` are set (local dev:
  `PUBLIC_BASE_URL=http://localhost:8080`). Optional `FORMS_OUTPUT_DIR`
  overrides the `./out` output root.
- **Form key:** `cav_rent_increase_notice`.
- **File delivery:** `files.pdf` / `files.docx` are **absolute, token-protected
  URLs** built from `PUBLIC_BASE_URL` — fetch with the same bearer token.
  Files live on the instance's disk (ephemeral across redeploys) — callers
  should fetch promptly after the fill.
- **Error codes** (`{"ok":false,"error":<code>,"message":...}`):
  `unauthorized` (401), `invalid_request` (400), `no_current_tenancy` (404),
  `fetch_failed` (502 upstream / 500 provider config), `template_error` (500).

```bash
uvicorn forms_fill.api:app --host 0.0.0.0 --port 8080

curl -s https://<host>/fill \
  -H "Authorization: Bearer $FORMS_API_TOKEN" -H 'content-type: application/json' -d '{
  "form": "cav_rent_increase_notice",
  "identifiers": {"lot_id": "<LOT_ID>", "tenancy_id": "<TENANCY_ID>"},
  "fields": {"current_rent":615,"new_rent":650,"increase":35,"rent_period":"week","start_date":"15/10/2026","method_basis":"market comparison (rental CMA)"}
}'
# → { "ok": true, "request_id": "...", "filled_fields": [...], "blank_fields": [...],
#     "warnings": [...], "files": { "pdf": "https://<host>/files/<id>/pdf",
#                                    "docx": "https://<host>/files/<id>/docx" } }

curl -s -H "Authorization: Bearer $FORMS_API_TOKEN" https://<host>/files/<id>/pdf -o notice.pdf
```

---

## Data provider (PropertyMe now → GEA CRM later)

The fill core depends on a `PropertyDataProvider` returning a `TenancyBundle`
(see `../docs/integrations/crm-data-contract-prompt.md` — that JSON shape *is*
the interface). Select with `FORMS_DATA_PROVIDER`:

| value | provider | env | when |
|-------|----------|-----|------|
| `fixture` (default) | reads `fixtures/sample_tenancy.json` | `FORMS_FIXTURE_PATH` | dev/test, demos |
| `propertyme` | PropertyMe API (OAuth2, confirmed live) | `PME_CLIENT_ID`, `PME_CLIENT_SECRET`, `PME_REFRESH_TOKEN` or `PME_TOKEN_FILE` (optional `PME_TOKEN_URL`, `PME_API_BASE`) | production now |
| `gea_crm` | GEA CRM `GET /api/forms/tenancy-bundle` | `GEA_CRM_BASE_URL`, `GEA_CRM_SYNC_SECRET` | flip the default here later |

Swapping providers changes **nothing** in the fill core — only which adapter is
selected (`FORMS_DATA_PROVIDER`).

**PropertyMe OAuth bootstrap (one-time, already done for GEA):** the refresh
token comes from an Authorization Code flow against
`https://login.propertyme.com/connect/authorize` (scope includes
`property:read contact:read offline_access`). Confirmed live 2026-07-06:
PropertyMe does **not** rotate refresh tokens on use, so the token is a stable
secret; the provider still persists a rotated token to `PME_TOKEN_FILE` if one
ever arrives. GEA's working credentials live in the rent-review repo at
`secrets/propertyme.env` + `secrets/propertyme-tokens.json`. Note: PropertyMe's
edge 403s default library user agents — the provider sends its own UA.

**GEA CRM notes:** `rental_provider.full_name` is always the property **owner**
(guaranteed upstream); `*.phone_after_hours` is always blank (single phone
stored); `renters[].address_for_service` is `null` when it equals the premises;
and `meta.note` (optional) carries a data-quality flag (e.g. >1 active lease) —
when present it's logged as a warning for the PM. A missing contract key fails
loudly (`ProviderContractError`).

---

## Adding a new form (registry pattern)

1. **Prepare the template** — drop the form's `.docx` at
   `forms_fill/forms/<form_key>/template.docx`.
2. **Write a spec** — `forms_fill/forms/<form_key>/spec.py` defining the
   `FormSpec`: `declared_fields`, `text_ops` (which value goes in which
   table/row/cell), `checkbox_ops`, and a `build_context(bundle, fields)`.
3. **Register it** — add the spec to `FORM_REGISTRY` in
   `forms_fill/registry.py`.

No change to the core, renderer, CLI, or API.

For **scanned-PDF templates** (no text layer — e.g. the REIV sales authorities),
set `engine="pdf_overlay"` on the spec and declare `stamp_ops` / `tick_ops` /
`strike_ops` with pixel coordinates on a reference render of the page
(`overlay_ref_width`, default 1240px = 150dpi A4). Extra pre-printed pages go in
`extra_pages`. Output is PDF-only (`files.docx` is null). Scan rotation is
handled by the engine. See `forms/reiv_exclusive_sale_authority/spec.py`.

**Sales forms** set `requires_bundle=False`: no tenancy fetch — context is caller
`fields` (verbatim) over agency defaults from `fixtures/gea_agency.json`
(override with `FORMS_AGENCY_FILE`).

---

## Consuming from internal tools

Everything a caller needs is discoverable:

1. **Auth** — send `Authorization: Bearer $FORMS_API_TOKEN` on every request
   (the server fails closed at startup if the token env var is unset).
2. **Discover forms** — `GET /forms` lists every form with `engine`,
   `requires_identifiers`, and `fields[]` (`key`, `label`, `kind`, and
   `options` for selector fields). Build your payload from this — no need to
   read the source.
3. **Fill** — `POST /fill` with `{form, identifiers, fields, ...}`. Sales
   forms (`requires_identifiers: false`) take `"identifiers": {}`.

Worked sales-form payload (n8n HTTP Request node or any client):

```json
{
  "form": "reiv_exclusive_sale_authority",
  "identifiers": {},
  "fields": {
    "vendor_name": "Australia and New Zealand Banking Group Limited,",
    "vendor_capacity": "in the capacity only as mortgagee exercising power of sale",
    "vendor_abn": "11 005 357 522",
    "property_address": "43 Bellagio Road, Berwick VIC 3806",
    "exclusive_days": "90",
    "possession": "vacant_possession",
    "payment": "full_purchase_price",
    "commission_pct": "4.125% inclusive of GST",
    "advertising": "3,380.00",
    "marketing_payable": "written_request"
  }
}
```

### `reiv_exclusive_sale_authority` — full field contract

`POST /fill` with `{"form": "reiv_exclusive_sale_authority", "identifiers": {},
"fields": {...}}`. This is a sales form (`requires_identifiers: false`,
`engine: pdf_overlay`), so:

- **`identifiers` is unused — send `{}`.** It only carries `lot_id` /
  `tenancy_id` for *tenancy-backed* forms that fetch a bundle from the data
  provider. Sales authorities have no tenancy; every value comes from `fields`.
- **No field is hard-required by the API** — the engine renders whatever it's
  given verbatim and reports anything left empty in `blank_fields` (it never
  rejects a fill for a missing value). "Required" below means *required for a
  legally usable authority*, not an API validation gate. Discover the live list
  any time with `GET /forms`.
- **Agent/agency fields default** from `fixtures/gea_agency.json` (override with
  `FORMS_AGENCY_FILE`); a caller value always wins over the default.

**Vendor & property (caller must supply — no defaults):**

| field | required | notes |
|---|---|---|
| `vendor_name` | ✅ | vendor's full legal name |
| `vendor_capacity` | optional | e.g. `in the capacity only as mortgagee exercising power of sale` |
| `vendor_abn` | optional | vendor ABN |
| `vendor_address` | optional | vendor address, or `C/-` legal representative |
| `vendor_phone`, `vendor_email` | optional | vendor contact |
| `property_address` | ✅ | address of the property being sold |
| `goods` | optional | goods sold with the property |

**Authority terms:**

| field | required | notes |
|---|---|---|
| `exclusive_days` | ✅ | exclusive authority period, in days (e.g. `90`) |
| `continuing_days` | optional | continuing (post-exclusive) authority period |
| `possession` | ✅ selector | `subject_to_tenancy` \| `vacant_possession` |
| `payment` | selector | `full_purchase_price` (only option) |
| `marketing_payable` | selector | `on_signing` \| `written_request` |

**Price & estimate** (all optional; supply the ones relevant to the deal):
`vendors_price`, `payable_in_days`, `estimate_single`, `estimate_low`,
`estimate_high`, `sold_at_price`. If both `estimate_low` and `estimate_high` are
given and the high exceeds the low by >10%, a `warnings` entry flags s47A Estate
Agents Act 1980.

**Commission & expenses** (optional): `fixed_commission`, `commission_pct`
(e.g. `4.125% inclusive of GST`), `commission_estimate`, `commission_gst`,
`advertising` ($ incl GST), `other_expenses`, `total_expenses`.

**Signing date** (optional, split): `date_day`, `date_month`, `date_year`.

**Agent/agency** (optional — default from `gea_agency.json`): `agent_name`,
`agent_acn`, `agency_address`, `attention`, `agent_mobile`, `agent_email`,
`agent_phone` (no default — blank unless supplied).

**Response shape** (confirmed — top-level keys):

```jsonc
{
  "ok": true,
  "form": "reiv_exclusive_sale_authority",
  "contract": "v1",
  "request_id": "b3cda60a0fe4453a83f0e35079f17987",
  "files": {
    "pdf": "https://<PUBLIC_BASE_URL>/files/<request_id>/pdf",
    "docx": null      // always null for pdf_overlay sales forms — PDF only
  },
  "filled_fields": ["vendor_name", "property_address", ...],
  "blank_fields":  ["vendor_abn", "goods", ...],   // declared fields left empty
  "warnings":      []                               // e.g. s47A estimate-range flag
}
```

`files.pdf` is an absolute, **bearer-protected** URL — fetch it with the same
`Authorization: Bearer $FORMS_API_TOKEN`. Files are ephemeral on the instance
disk; fetch promptly. Errors use `{"ok": false, "error": <code>, "message": ...}`
with the codes listed under **Programmatic API** above.

TypeScript (slate) sketch:

```ts
const res = await fetch(`${FORMS_BASE_URL}/fill`, {
  method: "POST",
  headers: { Authorization: `Bearer ${FORMS_API_TOKEN}`, "Content-Type": "application/json" },
  body: JSON.stringify(payload),
});
const result = await res.json(); // { ok, contract: "v1", files: { pdf, docx }, blank_fields, warnings }
```

**Contract stability:** the result carries `contract: "v1"`. Changes are
additive-only; a breaking change to the request or result shape bumps the
version. Treat unknown keys as ignorable.

**Speed:** the whole fill is ~0.2s except the LibreOffice DOCX→PDF conversion
(1–3s). Callers that only need the DOCX should send `"pdf": false` in the
payload (CLI: `--no-pdf`) — `files.pdf` comes back null and the conversion is
skipped entirely. Overlay forms (`engine: pdf_overlay`) are always fast
(~50ms) and always produce PDF natively.

---

## Deploy (Railway)

The `Dockerfile` installs **LibreOffice** so DOCX→PDF works in the container,
and runs the API by default. If LibreOffice is absent, the DOCX is still
produced and the result carries a `warnings` note (PDF is skipped, not fatal).

---

## Develop / test

```bash
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest -q
```
