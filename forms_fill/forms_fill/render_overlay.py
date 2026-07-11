"""Scanned-PDF overlay renderer (U9, KTD7, R14).

Fills templates that are scanned images with no text layer or form fields —
e.g. the REIV sales authorities — by stamping text, ticks, and strike-through
lines at known coordinates, then appending the template's untouched terms pages.

Coordinates in a spec are pixels on a reference render of the template
(``spec.overlay_ref_width`` px wide). They are converted to PDF points and
mapped through the page's derotation matrix, because scanned templates commonly
carry a ``/Rotate`` flag that would otherwise render stamped text sideways.

Output is PDF only (there is no meaningful DOCX for a scanned template).
"""

from __future__ import annotations

from pathlib import Path

from .errors import RenderError
from .formspec import FormSpec

INK = (0, 0, 0.6)  # blue-black, reads as pen on the scanned form


def render_overlay(
    spec: FormSpec,
    context: dict[str, str],
    out_dir: str | Path,
    *,
    basename: str | None = None,
) -> tuple[None, Path, list[str]]:
    """Render the overlay form. Returns ``(None, pdf_path, warnings)`` —
    shape-compatible with ``render.render`` (docx slot is None)."""

    try:
        import fitz  # PyMuPDF
    except ImportError as exc:  # pragma: no cover - environment guard
        raise RenderError(
            "pdf_overlay engine requires PyMuPDF — pip install pymupdf"
        ) from exc

    if not Path(spec.template).exists():
        raise RenderError(f"template not found: {spec.template}")

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    pdf_path = out / f"{basename or spec.key}.pdf"

    doc = fitz.open(str(spec.template))

    def _place(page, x_px: float, y_px: float):
        scale = page.rect.width / spec.overlay_ref_width
        return fitz.Point(x_px * scale, y_px * scale) * page.derotation_matrix

    for op in spec.stamp_ops:
        value = str(context.get(op.field_name, "") or "")
        if not value:
            continue
        page = doc[op.page]
        page.insert_text(
            _place(page, op.x, op.y),
            value,
            fontsize=op.size,
            fontname="helv",
            color=INK,
            rotate=page.rotation,
        )

    for op in spec.tick_ops:
        selector = str(context.get(op.selector_field, "") or "")
        if not selector:
            continue
        coords = op.options.get(selector)
        if coords is None:
            raise RenderError(
                f"unknown value {selector!r} for {op.selector_field!r}; "
                f"valid: {', '.join(sorted(op.options))}"
            )
        page = doc[op.page]
        page.insert_text(
            _place(page, *coords),
            "X",
            fontsize=op.size,
            fontname="hebo",
            color=INK,
            rotate=page.rotation,
        )

    for op in spec.strike_ops:
        if str(context.get(op.selector_field, "") or "") != op.when_value:
            continue
        page = doc[op.page]
        page.draw_line(
            _place(page, op.x1, op.y1),
            _place(page, op.x2, op.y2),
            color=INK,
            width=0.8,
        )

    for extra in spec.extra_pages:
        if not Path(extra).exists():
            raise RenderError(f"template page not found: {extra}")
        doc.insert_pdf(fitz.open(str(extra)))

    doc.save(str(pdf_path))
    return None, pdf_path, []
