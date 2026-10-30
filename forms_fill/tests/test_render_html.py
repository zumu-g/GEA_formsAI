"""U2 — generic HTML -> branded A4 PDF engine (render_html + render() html branch)."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from forms_fill import render_html
from forms_fill.errors import RenderError
from forms_fill.formspec import FormSpec, HtmlDocument
from forms_fill.render import render

TITLE = "Residential Rental Agreement"
FOOTER = "12 Example Street, Berwick VIC 3806"


def _three_page_html() -> str:
    # Each section is forced onto its own page.
    parts = [
        "<h1>Cover</h1><p>Cover page body.</p>",
        "<h2>Part A</h2>" + "<p>Body text paragraph.</p>" * 5,
        "<h2>Part B</h2><table><tr><td>Label</td><td>Value</td></tr></table>",
    ]
    return '<div style="page-break-after: always"></div>'.join(parts)


@pytest.fixture
def pdf(tmp_path: Path) -> fitz.Document:
    out = render_html.render_html_pdf(
        _three_page_html(), tmp_path / "doc.pdf", title=TITLE, footer_left=FOOTER
    )
    return fitz.open(out)


def test_three_pages_a4(pdf):
    assert pdf.page_count == 3
    for page in pdf:
        assert (round(page.rect.width), round(page.rect.height)) == (595, 842)


def test_chrome_on_later_pages_only(pdf):
    first = pdf[0].get_text()
    assert "Page" not in first
    assert TITLE.upper() not in first.upper()
    assert pdf[0].get_images() == []
    for n in (2, 3):
        text = pdf[n - 1].get_text()
        assert f"Page {n} of 3" in text
        assert TITLE.upper() in text.upper()
        assert FOOTER in text
        assert len(pdf[n - 1].get_images()) == 1  # the logo


def test_body_set_in_inter(pdf):
    names = {f[3] for page in pdf for f in page.get_fonts()}
    assert any("Inter" in n for n in names), names


def test_missing_asset_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(render_html, "LOGO", tmp_path / "nope.png")
    with pytest.raises(RenderError, match="nope.png"):
        render_html.render_html_pdf(
            "<p>x</p>", tmp_path / "x.pdf", title=TITLE, footer_left=FOOTER
        )


def test_render_dispatches_html_engine(tmp_path):
    spec = FormSpec(
        key="fake_html",
        template=Path(),
        declared_fields=("name",),
        text_ops=(),
        checkbox_ops=(),
        build_context=lambda bundle, fields: dict(fields),
        engine="html",
        build_html=lambda ctx: HtmlDocument(
            html=f"<p>{ctx['name']}</p>", title=TITLE, footer_left=FOOTER
        ),
    )
    docx_path, pdf_path, warnings = render(spec, {"name": "Jo"}, tmp_path)
    assert docx_path is None
    assert pdf_path == tmp_path / "fake_html.pdf"
    assert "Jo" in fitz.open(pdf_path)[0].get_text()
    assert warnings == []
