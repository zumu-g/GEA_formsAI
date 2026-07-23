---
title: "fix: GEA CRM address search returns 'unsupported', UI stuck on manual entry"
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
execution: code
product_contract_source: ce-plan-bootstrap
---

# fix: GEA CRM address search returns "unsupported", UI stuck on manual entry

## Summary

Selecting **GEA CRM** as the data source on Exclusive Sale Authority (or any form) and typing a property address never returns results, and the Search button looks disabled. Root cause: `GeaCrmProvider` never implemented `search_lots` — it falls through to the base class's `NotImplementedError`-style `SearchUnsupportedError`, which the API maps to `search_unsupported`, which the UI renders as a static "can't search this provider" message and force-switches to manual Lot ID / Tenancy ID entry (`forms_fill/forms_fill/static/index.html:426-429`). The Search button itself isn't actually disabled by CSS/logic bug — it's a `.secondary` outline button that reads as muted; the real defect is that search never runs for this provider.

This plan defines a new **GEA CRM address-search endpoint contract** (mirroring how `crm-data-contract-prompt.md` defined `tenancy-bundle`), implements the client-side `GeaCrmProvider.search_lots()` against it, and updates tests. It does **not** implement the endpoint itself on the GEA CRM service — that's a separate codebase this repo doesn't contain; the contract doc is the handoff artifact for that team/session.

**Product Contract preservation:** no prior requirements doc exists for this fix; scope was set directly with the user (see below).

---

## Problem Frame

- **Symptom:** GEA CRM selected → type address → no autocomplete results, Search button looks inert.
- **Root cause:** `PropertyDataProvider.search_lots()` base implementation raises `SearchUnsupportedError` by design (`forms_fill/forms_fill/providers/base.py:36-43`) for any provider that hasn't opted in. `GeaCrmProvider` (`forms_fill/forms_fill/providers/gea_crm.py`) only implements `fetch_bundle`, never overrides `search_lots`.
- **Confirmed scope (user-selected):** define the new CRM search contract, implement the provider adapter against it, keep the graceful `search_unsupported` degrade as the fallback for as long as the upstream endpoint doesn't exist yet.

---

## Requirements

- **R1.** GEA CRM address search must return real lot/tenancy matches once the upstream endpoint exists, using the same `LotMatch` shape PropertyMe and Fixture already return.
- **R2.** Until the upstream GEA CRM endpoint is live, the UI must continue to degrade gracefully to manual ID entry (no regression to the existing `search_unsupported` fallback for other unfinished providers).
- **R3.** The new contract must be documented in a form the GEA CRM team/session can implement directly, following the existing `docs/integrations/crm-data-contract-prompt.md` pattern.
- **R4.** Provider selection, error handling (`ProviderConfigError`, `UpstreamError`, `TenancyNotFoundError` equivalents), and retry behavior must match the conventions already used in `gea_crm.py`'s `fetch_bundle`/`_fetch_raw`.

---

## Key Technical Decisions

**KTD1 — Mirror the PropertyMe `search_lots` contract, not invent a new shape.** `LotMatch(lot_id, address_label, tenancy_id)` is the interface every provider already returns (`forms_fill/forms_fill/providers/base.py:20-26`). The new GEA CRM search endpoint returns a list of objects mappable 1:1 to that shape — no core/UI changes needed, consistent with how `tenancy-bundle` was added as a pure adapter (`forms_fill/forms_fill/providers/gea_crm.py:16-17`).

**KTD2 — New endpoint: `GET /api/forms/tenancy-search?q=<query>`, same auth as `tenancy-bundle`.** Reuse `x-sync-secret` / `GEA_CRM_SYNC_SECRET` — no new auth mechanism. Response is a JSON array of `{lot_id, address_label, tenancy_id}` (tenancy_id "" if not currently tenanted, matching how vacant lots are handled elsewhere in the contract).

**KTD3 — Same retry/error mapping as `_fetch_raw`.** Reuse the existing 3-attempt backoff on 5xx/transport errors, 401 → `ProviderConfigError`, other non-2xx → `UpstreamError`. Empty query → `ValueError` (matches `FixtureProvider`/`PropertyMeProvider` convention at `forms_fill/forms_fill/providers/propertyme.py:255-257`).

**KTD4 — Cap results client-side at the same `_MAX_SEARCH_RESULTS` convention (10).** Matches `propertyme.py:58,274` so all three providers behave consistently in the UI dropdown.

**KTD5 — `search_unsupported` fallback path stays intact.** No changes to `base.py`'s default behavior or the UI's `search_unsupported` handling (`static/index.html:426-429`) — this is the correct degrade for any provider not yet wired for search, and remains load-bearing if the upstream endpoint isn't deployed yet when this ships.

---

## Scope Boundaries

**In scope:**
- New `## Address search endpoint` section added to `docs/integrations/crm-data-contract-prompt.md` (or a new sibling doc if the existing one is considered "shipped" — implementer's call, see U1).
- `GeaCrmProvider.search_lots()` implementation in `forms_fill/forms_fill/providers/gea_crm.py`.
- Updated test coverage in `forms_fill/tests/test_provider_search.py` and `forms_fill/tests/test_gea_crm.py`.

**Deferred to Follow-Up Work:**
- Actually building the `/api/forms/tenancy-search` endpoint on the GEA CRM service — out of this repo's control; the contract doc is the handoff.
- Any change to the manual-entry UI copy/UX for other unsupported providers — not part of this fix.

---

## Implementation Units

### U1. Document the GEA CRM address-search contract

**Goal:** Give the GEA CRM team/session an unambiguous spec to implement, mirroring the existing `tenancy-bundle` contract.

**Requirements:** R1, R3, R4

**Dependencies:** none

**Files:** `docs/integrations/crm-data-contract-prompt.md` (add a new section) — or, if that file is treated as a closed/shipped artifact, a new `docs/integrations/crm-search-contract-prompt.md` following the same structure. Implementer decides based on whether the existing file is still being actively handed to the CRM team as a living doc.

**Approach:**
- Endpoint: `GET /api/forms/tenancy-search?q=<query>`, same `x-sync-secret` auth as `tenancy-bundle`.
- Request: free-text `q`, case-insensitive substring match against address (matches `PropertyMeProvider.search_lots` behavior).
- Response: JSON array, each item `{"lot_id": "...", "address_label": "...", "tenancy_id": "..." }` (`tenancy_id` `""` when the lot has no current active tenancy — vacant/owner-occupied, consistent with how `fetch_bundle` already handles that case via `TenancyNotFoundError` → `no_current_tenancy`).
- Cap: server may return up to N results; client also caps at 10 for consistent UX regardless of upstream limit.
- Empty/missing `q` → `400`.
- No auth/session → `401` (same as `tenancy-bundle`).

**Patterns to follow:** Structure and tone of the existing `## Endpoint` / `## Response shape` sections in `crm-data-contract-prompt.md:29-80`.

**Test scenarios:** Test expectation: none — this is a documentation-only unit with no runtime behavior.

**Verification:** Doc reads as a standalone, pasteable spec (matches the file's own instruction: "Paste this into a `GEA_crmAI` session").

---

### U2. Implement `GeaCrmProvider.search_lots()`

**Goal:** Add the client-side adapter so GEA CRM address search works once the upstream endpoint exists, and fails predictably until then.

**Requirements:** R1, R2, R4

**Dependencies:** U1 (contract shape must be settled first, even though implementation doesn't literally require the doc to exist)

**Files:**
- `forms_fill/forms_fill/providers/gea_crm.py` (modify — add `search_lots`, reuse `_RETRY_BACKOFFS`, `_err`, `_s` helpers already defined)
- `forms_fill/tests/test_provider_search.py` (modify — replace/extend `test_gea_crm_search_raises_unsupported`)
- `forms_fill/tests/test_gea_crm.py` (modify — add search-specific cases if that file organizes by provider rather than by behavior)

**Approach:**
- New method calls `GET {base_url}/api/forms/tenancy-search?q=<query>` with the same headers as `_fetch_raw` (`x-sync-secret`, `Accept: application/json`).
- Reuse the existing retry loop shape from `_fetch_raw` (3 attempts, `_RETRY_BACKOFFS` on 5xx/transport errors) — consider factoring a shared `_get(path, params)` helper if duplicating the loop verbatim feels wrong, but this is an implementer judgment call, not a requirement.
- Map response array → `list[LotMatch]`, capping at the same `_MAX_SEARCH_RESULTS = 10` convention used in `propertyme.py`.
- Empty/whitespace-only query → raise `ValueError` before making any request (matches `PropertyMeProvider.search_lots:256-257`).
- Non-2xx responses map the same way `_fetch_raw` does: 401 → `ProviderConfigError`, 5xx (after retries) → `UpstreamError`, other → `UpstreamError` with status/body in the message.

**Technical design (directional):**
```
def search_lots(self, query):
    q = query.strip()
    if not q: raise ValueError(...)
    raw = self._get("/api/forms/tenancy-search", {"q": q})  # shares retry/error handling with _fetch_raw
    return [LotMatch(lot_id=..., address_label=..., tenancy_id=...) for row in raw[:_MAX_SEARCH_RESULTS]]
```

**Patterns to follow:** `PropertyMeProvider.search_lots` (`forms_fill/forms_fill/providers/propertyme.py:247-276`) for the LotMatch-mapping shape; `GeaCrmProvider._fetch_raw` (`forms_fill/forms_fill/providers/gea_crm.py:85-137`) for auth/retry/error-mapping conventions.

**Test scenarios:**
- Happy path: mocked 200 response with 2-3 rows → `search_lots` returns matching `LotMatch` list with correct field mapping.
- Empty query (`""` or whitespace) → raises `ValueError`, no HTTP call made.
- Result capping: mocked response with >10 rows → returned list capped at 10 (mirrors `test_propertyme_search_caps_results`).
- Vacant lot in results (row with blank/null tenancy id) → `LotMatch.tenancy_id == ""`, not dropped from results.
- Error paths: mocked 401 → `ProviderConfigError`; mocked 500 (after retries exhausted) → `UpstreamError`; transport error (e.g. `httpx.ConnectError`) → `UpstreamError` after retry backoff.
- Existing `test_gea_crm_search_raises_unsupported` in `test_provider_search.py` must be updated or removed — it currently asserts the base-class unsupported behavior, which this unit intentionally overrides for `gea_crm`.

**Verification:** `pytest forms_fill/tests/test_provider_search.py forms_fill/tests/test_gea_crm.py` passes; manually confirm via the CRM sandbox/staging URL if `GEA_CRM_BASE_URL` is configured for one, otherwise verification is test-only until the upstream endpoint ships.

---

### U3. Confirm the `/tenancy/search` API route needs no changes

**Goal:** Verify the existing `/tenancy/search` FastAPI route (`forms_fill/forms_fill/api.py:124-142`) requires zero changes — it already dispatches to `provider.search_lots(q)` generically and maps `SearchUnsupportedError`/`ValueError`/`ProviderConfigError`/`UpstreamError` correctly for any provider.

**Requirements:** R4

**Dependencies:** U2

**Files:** `forms_fill/tests/test_api.py` (modify — add a `provider=gea_crm` case to whatever existing `/tenancy/search` test coverage exists, if not already parametrized across providers)

**Approach:** This is a verification-only unit, not a code-change unit — the route is provider-agnostic by design (KTD1). Confirm by reading `api.py:124-142` against the new `search_lots` signature and adding API-level test coverage so a future refactor can't silently break GEA CRM search at the route layer.

**Test scenarios:**
- `GET /tenancy/search?q=...&provider=gea_crm` with a mocked provider returning matches → 200 with `{"matches": [...]}` shape.
- Same route with `provider=gea_crm` and empty `q` → 400 `invalid_request` (existing behavior, confirm it still holds).

**Verification:** `pytest forms_fill/tests/test_api.py -k search` passes.

---

## Risks & Dependencies

- **External dependency:** R1's actual runtime fix depends entirely on the GEA CRM service team implementing `/api/forms/tenancy-search` from U1's contract. Until then, U2/U3 ship correct, tested client code that simply isn't reachable yet — the UI will keep degrading to manual entry via the existing `search_unsupported` path, which is the correct interim behavior (R2).
- **Contract drift risk:** if the CRM team implements a shape that differs from U1's spec (e.g., different field names, pagination instead of a flat array), `GeaCrmProvider.search_lots()` will need a follow-up patch. `_assert_contract`-style validation (already used in `_to_bundle`) should be considered for the search response too, to fail loudly rather than silently mis-map fields — implementer's call on whether to add strict validation given search results are lower-stakes than a full tenancy bundle.

---

## Open Questions

- Should `docs/integrations/crm-data-contract-prompt.md` be extended in place, or should this be a new sibling doc? (Left to U1's implementer — depends on whether that file is still an actively-referenced living handoff doc or considered historically shipped.)
