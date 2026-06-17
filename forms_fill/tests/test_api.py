import docx
from fastapi.testclient import TestClient

from forms_fill.api import OUTPUT_ROOT, app

client = TestClient(app)


def _payload(caller_fields, tmp_out):
    return {
        "form": "cav_rent_increase_notice",
        "identifiers": {"lot_id": "L-2002"},
        "fields": caller_fields,
    }


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_post_fill_returns_result_and_urls(caller_fields):
    resp = client.post("/fill", json={
        "form": "cav_rent_increase_notice",
        "identifiers": {"lot_id": "L-2002"},
        "fields": caller_fields,
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    assert body["filled_fields"] > 0
    assert body["fetch"]["docx"].startswith("/files/")

    # the docx is fetchable
    docx_url = body["fetch"]["docx"]
    fetched = client.get(docx_url)
    assert fetched.status_code == 200
    assert len(fetched.content) > 0


def test_post_fill_unknown_form_is_400(caller_fields):
    resp = client.post("/fill", json={"form": "bogus", "fields": caller_fields})
    assert resp.status_code == 400


def test_cli_and_api_produce_same_text(caller_fields, tmp_path):
    # API render
    resp = client.post("/fill", json={
        "form": "cav_rent_increase_notice",
        "identifiers": {"lot_id": "L-2002"},
        "fields": caller_fields,
    })
    body = resp.json()
    api_docx = OUTPUT_ROOT / body["request_id"]
    api_file = next(api_docx.glob("*.docx"))

    # Core render directly (same core the CLI uses)
    from forms_fill.core import fill_form
    from forms_fill.models import FillRequest
    from forms_fill.providers.fixture import FixtureProvider

    req = FillRequest(
        form="cav_rent_increase_notice",
        identifiers={"lot_id": "L-2002"},
        fields=caller_fields,
        out_dir=str(tmp_path),
    )
    result = fill_form(req, provider=FixtureProvider())

    def text(p):
        d = docx.Document(str(p))
        return " ".join(
            c.text for t in d.tables for r in t.rows for c in r.cells
        )

    assert text(api_file) == text(result.files.docx)
