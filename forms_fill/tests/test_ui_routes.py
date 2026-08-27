import pytest
from fastapi.testclient import TestClient

from forms_fill.api import app

TOKEN = "test-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("FORMS_API_TOKEN", TOKEN)
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://testserver")


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_ui_page_served_without_auth(client):
    # The static page itself needs no bearer token -- only the data calls it
    # makes (/forms, /fill, /files/...) are protected.
    resp = client.get("/ui/")
    assert resp.status_code == 200
    assert "GEA — Forms Fill" in resp.text  # <title> — hero shows just "Forms Fill"


def test_ui_page_is_not_browser_cached(client):
    # no-cache forces ETag revalidation so a deploy is never masked by a
    # heuristically-cached stale page.
    assert client.get("/ui/").headers["cache-control"] == "no-cache"


def test_ui_fill_round_trip_matches_direct_api_payload_shape(client, caller_fields):
    # Exercises the exact payload shape the UI's fetch() builds: form, provider,
    # identifiers, fields.
    payload = {
        "form": "cav_rent_increase_notice",
        "provider": "fixture",
        "identifiers": {"lot_id": "L-2002", "tenancy_id": "T-1001"},
        "fields": caller_fields,
    }
    resp = client.post("/fill", json=payload, headers=AUTH)
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["files"]["pdf"] or body["files"]["docx"]


def test_ui_fill_malformed_field_surfaces_api_error_not_blank_download(client):
    payload = {"form": "does_not_exist", "identifiers": {}, "fields": {}}
    resp = client.post("/fill", json=payload, headers=AUTH)
    assert resp.status_code == 400
    body = resp.json()
    assert body["ok"] is False
    assert body["error"] == "invalid_request"


def test_ui_page_contains_lookup_flow_elements(client):
    text = client.get("/ui/").text
    assert 'id="address-query"' in text
    assert 'id="search-results"' in text
    assert 'id="preview"' in text
    assert "/tenancy/search" in text
    assert "/tenancy/preview" in text


def test_ui_page_prefills_rent_fields_from_preview(client):
    text = client.get("/ui/").text
    assert "RENT_PREFILL_FIELDS" in text
    assert "lastPreviewBundle" in text
    assert "prefillRentFields" in text


def test_ui_page_contains_cma_button(client):
    text = client.get("/ui/").text
    assert 'id="cma-btn"' in text
    assert "geastcma-production.up.railway.app" in text
    assert "reportType" in text
    assert "rent-increase" in text


# ── U7: field kinds + sections ───────────────────────────────────────────────


def test_ui_page_renders_per_field_fetch_button(client):
    text = client.get("/ui/").text
    assert "fetch-btn" in text
    assert "forceFetchField" in text
    assert "FETCHABLE_FIELD_NAMES" in text


def test_ui_page_renders_date_and_select_kinds(client):
    text = client.get("/ui/").text
    assert "kind === 'date'" in text
    assert "kind === 'select'" in text
    assert "kind === 'checkbox'" in text
    assert "field-section-title" in text


# ── U8: review screen ─────────────────────────────────────────────────────────


def test_ui_page_contains_review_screen_elements(client):
    text = client.get("/ui/").text
    assert 'id="review-screen"' in text
    assert 'id="review-rows"' in text
    assert 'id="review-confirm-check"' in text
    assert 'id="review-confirm-btn"' in text


def test_ui_submit_shows_review_before_posting_fill(client):
    # The submit handler must call showReviewScreen(), not POST /fill directly
    # — the actual POST only fires from the review-confirm button (R11).
    text = client.get("/ui/").text
    submit_handler = text.split("form.addEventListener('submit'")[1].split("\n  });")[0]
    assert "showReviewScreen" in submit_handler
    assert "/fill" not in submit_handler
    assert "reviewConfirmBtn.addEventListener('click'" in text


def test_ui_review_confirm_disabled_until_checkbox_ticked(client):
    text = client.get("/ui/").text
    assert "reviewConfirmBtn.disabled = !reviewConfirmCheck.checked" in text


# ── U9: approval ──────────────────────────────────────────────────────────────


def test_ui_page_contains_approval_elements(client):
    text = client.get("/ui/").text
    assert 'id="approve-box"' in text
    assert 'id="approve-name"' in text
    assert 'id="approve-token"' in text
    assert 'id="approve-btn"' in text
    assert "/approve/" in text


def test_ui_approval_uses_separate_credential_not_generation_token(client):
    text = client.get("/ui/").text
    approve_handler = text.split("document.getElementById('approve-btn').addEventListener")[1].split("});")[0]
    # The actual fetch() call must build its Authorization header from the
    # approval-credential input, never from authHeaders() (the stored
    # generation token) — KTD6. Scope to the fetch(...) call itself so the
    # explanatory comment mentioning authHeaders() doesn't trip this.
    fetch_call = approve_handler.split("fetch(")[1].split(");")[0]
    assert "authHeaders()" not in fetch_call
    assert "approveToken" in fetch_call
    assert "approve-token" in approve_handler


# ── Wizard U1: stage framework + stepper ─────────────────────────────────────


def test_ui_page_contains_stage_containers_and_stepper(client):
    text = client.get("/ui/").text
    assert 'id="stage-start"' in text
    assert 'id="stage-fill"' in text
    assert 'id="stage-review"' in text
    assert 'id="stepper"' in text
    assert "setStage" in text
    assert "aria-current" in text


# ── Wizard U2: Start stage ───────────────────────────────────────────────────


def test_ui_lease_mode_has_plain_english_helper(client):
    text = client.get("/ui/").text
    near = text.split('id="lease-mode"')[1].split("Data source")[0]
    assert 'id="lease-mode-help"' in near
    assert "same renters" in near


def test_ui_start_stage_has_continue_without_crm_action(client):
    text = client.get("/ui/").text
    start = text.split('id="stage-start"')[1].split('id="stage-fill"')[0]
    assert 'id="skip-crm-btn"' in start
    assert "Continue without CRM data" in start
    assert "skip-crm-btn" in text.split("<script>")[1]  # wired, not just markup


def test_ui_preview_success_auto_advances_to_fill(client):
    # renderPreview() must advance a guided form to Fill (setStage(2)) after
    # maybeAutoCrmFetch fires; failure paths return before renderPreview.
    text = client.get("/ui/").text
    render_preview = text.split("function renderPreview")[1].split("async function fetchPreview")[0]
    assert "maybeAutoCrmFetch" in render_preview
    assert "setStage(2)" in render_preview


def test_ui_last_used_form_persisted_in_local_storage(client):
    text = client.get("/ui/").text
    assert text.count("forms_fill_last_form") >= 2  # write on change + read on load


def test_ui_reseed_guard_confirms_before_overwriting_fill(client):
    text = client.get("/ui/").text
    assert "confirmReseed" in text
    # address pick and lease-type change both route through the guard
    assert text.count("confirmReseed(") >= 3  # definition + 2 call sites
    # lease-mode change handler: accept path records the choice, decline
    # path reverts the radios to the last accepted value
    handler = text.split("leaseModeBox.addEventListener('change'")[1].split("\n  });")[0]
    assert "lastLeaseMode = " in handler  # accept path
    assert "r.checked = r.value === lastLeaseMode" in handler  # revert path
    # guard is reachable once Fill has been visited, not keyed on stage
    guard = text.split("function confirmReseed")[1].split("\n  }")[0]
    assert "!visitedFill" in guard


def test_ui_submit_gates_on_date_validation(client):
    # Invalid dates must block the submit → Review transition, not just Enter.
    text = client.get("/ui/").text
    handler = text.split("form.addEventListener('submit'")[1].split("\n  });")[0]
    assert "validateDateField" in handler
    assert "showReviewScreen()" in handler
    assert handler.index("validateDateField") < handler.index("showReviewScreen()")


def test_ui_async_fetches_guarded_by_generation_counter(client):
    # Stale previews / CRM tenant fetches must not seed after a form switch,
    # Start-next, skip-CRM, or a newer search/preview cycle.
    text = client.get("/ui/").text
    assert "let fetchGen = 0" in text
    assert text.count("gen !== fetchGen") >= 4  # search, preview, CRM (x2) bails
    crm = text.split("async function fetchCrmTenants")[1].split("\n  }")[0]
    assert "fetchGen" in crm


# ── Wizard U3: Fill stage — skeleton, gaps, context strip, renewal diffs ─────


def test_ui_fill_stage_has_collapsed_row_machinery(client):
    text = client.get("/ui/").text
    assert "cf-collapsed-row" in text
    assert "refreshFieldPresentation" in text
    # collapse applies only to seeded (fetched/defaults) fields, never typed
    assert "src !== 'typed'" in text
    # collapsed rows are real buttons — keyboard reachable
    assert "collapsedBtn.type = 'button'" in text


def test_ui_fill_stage_has_context_strip(client):
    text = client.get("/ui/").text
    assert 'id="context-strip"' in text
    assert "updateContextStrip" in text
    # pinned inside the Fill stage, above the caller fields
    fill = text.split('id="stage-fill"')[1].split('id="caller-fields"')[0]
    assert "context-strip" in fill


def test_ui_fill_stage_has_gap_navigation(client):
    text = client.get("/ui/").text
    assert 'id="gap-count"' in text
    assert 'id="next-gap-btn"' in text
    assert "focusNextGap" in text
    assert "to go" in text


def test_ui_renewal_verify_prompt_and_was_now_marker(client):
    text = client.get("/ui/").text
    assert "RENEWAL_CRITICAL" in text
    assert "seededValue" in text
    # untouched seeded value → verify prompt; edited → text-badged was/now marker
    assert "against the new agreement" in text
    assert "CHANGED — was " in text
    mark_fn = text.split("function updateRenewalMark")[1].split("\n  function ")[0]
    assert "isRenewalChecked()" in mark_fn  # new lease: no prompts or markers


def test_ui_force_fetch_shows_diff_chip_instead_of_overwriting_typed(client):
    text = client.get("/ui/").text
    fetch_fn = text.split("function forceFetchField")[1].split("\n  function ")[0]
    assert "fieldSource[name] === 'typed'" in fetch_fn
    assert "showDiffChip" in fetch_fn
    assert "diff-chip" in text
    # two keyboard-focusable choices, either dismisses the chip
    assert "'Keep " in text or '"Keep ' in text
    assert "'Use " in text or '"Use ' in text
    assert "dismissDiffChip" in text


# ── Wizard U4: field help, date validation, blocking/informational review ────


def test_ui_renders_field_help_under_expanded_fields(client):
    text = client.get("/ui/").text
    assert "cf-help" in text  # help line element class
    assert "f.help" in text  # driven by the catalogue's help text, not hardcoded


def test_ui_date_validation_blocks_and_echoes(client):
    text = client.get("/ui/").text
    fn = text.split("function validateDateField")[1].split("\n  function ")[0]
    assert "cf-invalid" in fn  # visible invalid state, usable by U5 to block Enter
    assert "must be after" in fn  # end-after-start message
    assert "date-echo" in text  # plain-words advisory echo element
    # compliance: the echo never writes a value back into any field
    echo_fn = text.split("function updateDateEcho")[1].split("\n  function ")[0]
    assert ".value =" not in echo_fn


def test_ui_review_splits_blank_fields_blocking_vs_informational(client):
    text = client.get("/ui/").text
    assert 'id="review-blank-blocking"' in text
    assert 'id="review-blank-informational"' in text
    assert "Needed to complete the agreement" in text
    assert "Commonly left blank" in text


# ── Wizard U5: keyboard flow and resume-to-field ─────────────────────────────


def test_ui_enter_advances_gap_and_blocks_on_invalid(client):
    text = client.get("/ui/").text
    # Delegated Enter handler on the Fill fields only (review mirrors live
    # outside callerFieldsBox, textareas keep their newline behaviour).
    fn = text.split("callerFieldsBox.addEventListener('keydown'")[1].split("\n  //")[0]
    assert "TEXTAREA" in fn
    assert "validateDateField" in fn  # invalid input blocks the advance (R8)
    assert "focusNextGap()" in fn


def test_ui_last_gap_enter_reaches_review_with_mouse_affordance(client):
    text = client.get("/ui/").text
    assert 'id="go-review-btn"' in text  # mouse path when gaps hit zero
    assert "Go to Review" in text
    assert "form.requestSubmit()" in text  # last gap Enter → existing submit→review


def test_ui_review_confirm_and_generate_keyboard_reachable(client):
    text = client.get("/ui/").text
    assert "reviewConfirmCheck.focus()" in text  # entering Review focuses the checkbox
    assert "reviewConfirmBtn.focus()" in text  # ticking moves focus so Enter generates


def test_ui_draft_saves_stage_and_focus_and_resume_restores_them(client):
    text = client.get("/ui/").text
    state_fn = text.split("function draftState")[1].split("\n  function ")[0]
    assert "stage: stage" in state_fn  # KTD6 — inside the opaque blob
    assert "focus:" in state_fn
    resume_fn = text.split("async function resumeDraft")[1].split("\n  async function ")[0]
    assert "state.stage" in resume_fn and "setStage(" in resume_fn
    assert "state.focus" in resume_fn
    assert 'id="last-saved"' in text
    assert "Last saved " in text  # from the draft's updated_at


def test_ui_review_actions_carry_consequence_labels(client):
    # R10: each action states its consequence on the button itself.
    text = client.get("/ui/").text
    assert "Generate PDF — nothing is sent to anyone yet" in text
    assert "Send for e-signing — emails the renters immediately" in text


def test_ui_start_next_button_loops_to_a_fresh_start_stage(client):
    # R11: one action from a finished lease to typing the next address.
    text = client.get("/ui/").text
    assert 'id="start-next-btn"' in text
    fn = text.split("function startNextLease")[1].split("\n  }\n")[0]
    # Coverage guard: clearing derives from the rendered fields, not a
    # hardcoded name list — new fields can't be silently missed.
    assert "querySelectorAll('[data-field]')" in fn
    assert "AGENT_BLOCK_FIELDS" in fn  # agent block survives
    assert "REMEMBER_FIELDS" in fn  # sticky defaults survive
    assert "applyRememberedDefaults" in fn  # ...and re-seed
    assert "setStage(1)" in fn  # back to Start
    assert "queryInput.focus()" in fn  # cursor in address search
    # Preserved: form key, lease mode, handling agent — the handler never
    # touches the form selector or the lease-mode radios.
    assert "formSelect" not in fn
    assert "lease-mode" not in fn
    assert "is_renewal" in fn  # lease-mode carrier explicitly skipped
