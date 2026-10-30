"""Generic HTML -> branded A4 PDF engine (U2, KTD1/KTD4/KTD5).

``fitz.Story`` lays the HTML out onto A4 portrait pages (block flow and tables
only; Story has no flexbox or grid). A second pass then stamps the page chrome
once the page count is known: the logo top-left, the title top-right, a hairline
under the header, and a footer with ``footer_left`` and "Page X of Y".

Page numbering counts every page, cover included, so the first chromed page of
a document with a cover reads "Page 2 of N". The cover itself carries no chrome.
"""

from __future__ import annotations

import io
from pathlib import Path

import fitz

from .errors import RenderError

ASSETS = Path(__file__).parent / "forms" / "_assets"
FONTS = ASSETS / "fonts"
LOGO = ASSETS / "grants-logo-bw.png"
FONT_FILES = {
    400: "Inter-Regular.ttf",
    500: "Inter-Medium.ttf",
    600: "Inter-SemiBold.ttf",
    700: "Inter-Bold.ttf",
}

INK = (0x1A / 255, 0x1C / 255, 0x1C / 255)
SECONDARY = (0x5E / 255, 0x5E / 255, 0x5E / 255)

MM = 72 / 25.4
PAGE = fitz.paper_rect("a4")  # 595 x 842 pt
BODY = fitz.Rect(20 * MM, 30 * MM, PAGE.width - 20 * MM, PAGE.height - 22 * MM)

_BASE_CSS = "".join(
    f"@font-face {{font-family: Inter; src: url({name}); font-weight: {weight};}}"
    for weight, name in FONT_FILES.items()
) + (
    "* {font-family: Inter;}"
    "body {font-size: 9.5pt; line-height: 1.4; color: #1a1c1c;}"
    ".secondary {color: #5e5e5e;}"
    "table {border-collapse: collapse; width: 100%;}"
    "td, th {border-bottom: 0.5pt solid #cfc4c5; padding: 3pt 4pt; vertical-align: top;}"
)


def _check_assets() -> None:
    missing = [p for p in (LOGO, *(FONTS / f for f in FONT_FILES.values())) if not p.is_file()]
    if missing:
        raise RenderError(
            "html engine brand asset missing: " + ", ".join(str(p) for p in missing)
        )


def render_html_pdf(
    html: str,
    out_path: str | Path,
    *,
    title: str,
    footer_left: str,
    cover: bool = True,
) -> Path:
    """Lay ``html`` out onto A4 in Inter, stamp chrome, write ``out_path``.

    With ``cover=True`` page 1 is left bare; otherwise every page is chromed.
    Raises ``RenderError`` if a font or the logo is missing, rather than
    producing an unbranded PDF.
    """

    _check_assets()
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    buf = io.BytesIO()
    writer = fitz.DocumentWriter(buf)
    story = fitz.Story(html=html, user_css=_BASE_CSS, archive=fitz.Archive(str(FONTS)))
    more = True
    while more:
        device = writer.begin_page(PAGE)
        more, _ = story.place(BODY)
        story.draw(device)
        writer.end_page()
    writer.close()

    doc = fitz.open("pdf", buf.getvalue())
    total = doc.page_count
    for index, page in enumerate(doc):
        if cover and index == 0:
            continue
        _stamp_chrome(page, title, footer_left, index + 1, total)
    doc.save(str(out), garbage=3, deflate=True)
    return out


def _stamp_chrome(page: fitz.Page, title: str, footer_left: str, n: int, total: int) -> None:
    left, right = BODY.x0, BODY.x1
    regular = fitz.Font(fontfile=str(FONTS / FONT_FILES[400]))
    medium = fitz.Font(fontfile=str(FONTS / FONT_FILES[500]))
    page.insert_font(fontname="InterR", fontbuffer=regular.buffer)
    page.insert_font(fontname="InterM", fontbuffer=medium.buffer)

    # Header: logo ~18mm wide, title right-aligned in tracked capitals.
    logo_w = 18 * MM
    logo = fitz.Pixmap(str(LOGO))
    logo_h = logo_w * logo.height / logo.width
    top = 10 * MM
    page.insert_image(fitz.Rect(left, top, left + logo_w, top + logo_h), filename=str(LOGO))
    # shortcut: capitals at small size, no letter tracking; per-glyph tracking
    # breaks text extraction ("R E S I ..."), revisit if the design needs it.
    size, caps = 7.0, title.upper()
    page.insert_text(
        (right - medium.text_length(caps, size), top + logo_h - 1.5),
        caps,
        fontname="InterM",
        fontsize=size,
        color=INK,
    )
    rule_y = top + logo_h + 3 * MM
    page.draw_line((left, rule_y), (right, rule_y), color=INK, width=0.5)

    # Footer: hairline, address left, page count right.
    foot_rule = PAGE.height - 15 * MM
    page.draw_line((left, foot_rule), (right, foot_rule), color=INK, width=0.5)
    base = foot_rule + 4.5 * MM
    page.insert_text((left, base), footer_left, fontname="InterR", fontsize=7.5, color=SECONDARY)
    label = f"Page {n} of {total}"
    page.insert_text(
        (right - regular.text_length(label, 7.5), base),
        label,
        fontname="InterR",
        fontsize=7.5,
        color=SECONDARY,
    )
