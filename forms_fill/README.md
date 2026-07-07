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

- **Auth:** every route (except `GET /health`) requires `Authorization: Bearer
  $FORMS_API_TOKEN`; missing/wrong → `401 {"ok":false,"error":"unauthorized"}`.
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
