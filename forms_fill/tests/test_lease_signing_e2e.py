"""U4b (R8, KTD6): tenant signing on a REAL rendered lease, end to end.

/fill renders the actual residential rental agreement PDF, the PM approves,
both renters sign, and the stamped PDF must carry each signature and date in
the renter's own row. Only Resend and the ingoing engine are mocked."""

import base64
import shutil
from datetime import datetime
from zoneinfo import ZoneInfo

import fitz
import pytest

from forms_fill.api import OUTPUT_ROOT
from tests.test_ingoing_lease import (  # noqa: F401  (fixtures)
    APPROVE, AUTH, FACTS, LEASE, TENANTS, _env, _link_token, agency_file, client, emails, engine,
)


def _png_data_url():
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 60, 20), False)
    pix.set_rect(pix.irect, (10, 10, 10))
    return "data:image/png;base64," + base64.b64encode(pix.tobytes("png")).decode()


@pytest.fixture()
def rendered_lease(client):
    resp = client.post("/fill", headers=AUTH, json={
        "form": LEASE, "identifiers": {"tenancy_id": "T-1001"}, "idem_key": "OAK12:ingoing",
        "fields": {**FACTS, **TENANTS}, "pdf": True,
    })
    if resp.status_code != 200 or not resp.json()["files"]["pdf"]:
        pytest.skip(f"lease renderer can't produce a PDF here: {resp.status_code} {resp.text[:300]}")
    request_id = resp.json()["request_id"]
    yield request_id
    shutil.rmtree(OUTPUT_ROOT / request_id, ignore_errors=True)


def test_real_lease_is_signed_in_each_renters_row(client, rendered_lease, emails, agency_file, engine):
    resp = client.post(f"/lease/{rendered_lease}/approve-send",
                       json={"approver": "Stuart Grant"}, headers=APPROVE)
    assert resp.status_code == 200, resp.text
    for email, name in zip(emails, ("Jane Renter", "Sam Renter")):
        body = {"consent": True, "full_name": name, "signature_png": _png_data_url()}
        signed = client.post(f"/sign/{_link_token(email)}", json=body)
        assert signed.status_code == 200, signed.text
    assert len(engine) == 1

    pdf = client.get(f"/files/{rendered_lease}/signed", headers=AUTH)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    doc = fitz.open(stream=pdf.content, filetype="pdf")
    today = datetime.now(ZoneInfo("Australia/Melbourne")).strftime("%d/%m/%Y")

    for slot in (1, 2):
        page = next(p for p in doc if p.search_for(f"Signature of renter {slot}"))
        label = page.search_for(f"Signature of renter {slot}")[0]
        images = [r for img in page.get_images(full=True) for r in page.get_image_rects(img[0])]
        assert any(r.x0 >= label.x1 and r.y0 < label.y1 and r.y1 > label.y0 for r in images), \
            f"no signature image right of renter {slot} label"
        date_label = min((d for d in page.search_for("Date") if label.y1 <= d.y0 <= label.y1 + 70),
                         key=lambda d: d.y0)
        assert any(h.x0 >= date_label.x1 and h.y0 < date_label.y1 and h.y1 > date_label.y0
                   for h in page.search_for(today)), f"no signing date beside renter {slot} Date"

    record = doc[-1].get_text()
    assert "Electronic signing record" in record
    assert "Renter 1: Jane Renter <jane@example.com>" in record
    assert "Renter 2: Sam Renter <sam@example.com>" in record
