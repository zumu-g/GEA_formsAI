"""Form-spec primitives shared by every form in the registry (U2).

A ``FormSpec`` is the declarative description of one form:

- ``template`` — path to the .docx template.
- ``declared_fields`` — the full set of fields this form can fill. Drives the
  ``blank_fields`` / ``filled_fields`` accounting (KTD6); membership here is the
  single source of truth for "this form writes this value".
- ``text_ops`` — where each field's text goes (table / row / cell).
- ``checkbox_ops`` — which checkbox a selector field ticks.
- ``build_context`` — turns a fetched ``TenancyBundle`` + caller ``fields`` into a
  flat ``{field_name: str}`` context. Caller fields are rendered verbatim (R4).

The renderer (``render.py``) consumes these ops generically, so adding a form is
data + a ``build_context`` — never a change to the core or renderer (R11).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .models import TenancyBundle


@dataclass(frozen=True)
class TextOp:
    """Write ``context[field_name]`` into a table cell."""

    field_name: str
    table_index: int
    cell_index: int
    row_index: int = 0


@dataclass(frozen=True)
class CheckboxOp:
    """Tick one legacy form checkbox in ``table_index`` based on a selector field.

    ``options`` maps a normalised selector value to the 0-based position of the
    checkbox within the table (document order). Example: ``{"week": 0,
    "fortnight": 1, "calendar month": 2}``.
    """

    selector_field: str
    table_index: int
    options: dict[str, int]


@dataclass(frozen=True)
class StampOp:
    """Stamp ``context[field_name]`` onto a scanned-PDF page (pdf_overlay engine).

    ``x``/``y`` are pixel coordinates on the reference render of the template
    (``FormSpec.overlay_ref_width`` wide); ``y`` is the text baseline. The
    renderer converts to points and maps through the page's derotation matrix.
    """

    field_name: str
    x: float
    y: float
    page: int = 0
    size: float = 9.0


@dataclass(frozen=True)
class OverlayTickOp:
    """Stamp an ``X`` at the coordinates chosen by a selector field's value."""

    selector_field: str
    options: dict[str, tuple[float, float]]
    page: int = 0
    size: float = 11.0


@dataclass(frozen=True)
class StrikeOp:
    """Draw a strike-through line when ``context[selector_field] == when_value``."""

    selector_field: str
    when_value: str
    x1: float
    y1: float
    x2: float
    y2: float
    page: int = 0


@dataclass(frozen=True)
class FormSpec:
    key: str
    template: Path
    declared_fields: tuple[str, ...]
    text_ops: tuple[TextOp, ...]
    checkbox_ops: tuple[CheckboxOp, ...]
    build_context: Callable[[TenancyBundle | None, dict], dict[str, str]]
    # Selector fields drive checkboxes, not text cells; they should not count
    # toward blank/filled text accounting.
    selector_fields: tuple[str, ...] = field(default=())
    # Catalogue metadata (U1) — display-only, never consumed by the renderer.
    # ``title`` is the human-readable form name; ``group`` clusters related
    # forms in the UI (e.g. "notice_to_vacate", "breach_of_duty"); ``caller_field_labels``
    # gives each caller-supplied field a short UI label (falls back to the raw
    # field name when absent).
    title: str = ""
    group: str = ""
    caller_field_labels: dict[str, str] = field(default_factory=dict)
    # Presentation metadata (U7, KTD7) — all optional, all additive. A form
    # that declares none of these renders exactly as it did before this
    # existed: every field a plain text input, no section grouping. Only the
    # rental agreement specs opt in today; the other forms are unaffected.
    #   kind: "date" | "select" | "checkbox" | "textarea" | "text" (default)
    #   options: explicit allowed values for a "select" kind. A selector field
    #     already tied to a CheckboxOp/OverlayTickOp/StrikeOp derives its
    #     options from those ops and does not need an entry here; this is for
    #     "select" fields with no such op (e.g. a mode flag).
    #   section: groups the field under this label in section order of first
    #     appearance in ``declared_fields``. A field with no entry renders in
    #     an implicit "" (ungrouped) section.
    caller_field_kinds: dict[str, str] = field(default_factory=dict)
    caller_field_options: dict[str, tuple[str, ...]] = field(default_factory=dict)
    caller_field_sections: dict[str, str] = field(default_factory=dict)
    # Wizard U4 (R7/R10, KTD7) — per-field one-line help with a real format
    # example, and a blank-field classification for the review screen:
    #   "blocking" — the agreement is incomplete without it
    #   "informational" — commonly left blank on real agreements
    # A field with no entry publishes "" and the UI treats its blank as
    # informational (today's behaviour).
    caller_field_help: dict[str, str] = field(default_factory=dict)
    caller_field_required: dict[str, str] = field(default_factory=dict)
    # Wizard U1 (R1/R13): opt the form into the guided three-stage flow
    # (Start / Fill / Review) in the web UI. Forms that don't declare this
    # keep the current single-page behaviour unchanged.
    guided: bool = False
    # --- pdf_overlay engine (KTD7, U9) ---------------------------------------
    # ``engine`` selects the renderer: "docx" (text_ops/checkbox_ops above) or
    # "pdf_overlay" (stamp values onto a scanned-PDF template).
    engine: str = "docx"
    # Ops for the overlay engine. Coordinates are pixels on a reference render
    # of the template that is ``overlay_ref_width`` px wide.
    stamp_ops: tuple[StampOp, ...] = ()
    tick_ops: tuple[OverlayTickOp, ...] = ()
    strike_ops: tuple[StrikeOp, ...] = ()
    overlay_ref_width: float = 1240.0
    # Extra template pages appended untouched after the stamped page(s)
    # (e.g. pre-printed terms and conditions).
    extra_pages: tuple[Path, ...] = ()
    # Sales forms build their context from caller fields + agency defaults and
    # never fetch a tenancy bundle (KTD8, U10).
    requires_bundle: bool = True
    # Optional non-blocking checks run after context build; returned strings
    # become result warnings (e.g. estimate range spread >10%).
    validate_warnings: Callable[[dict], list[str]] | None = None
