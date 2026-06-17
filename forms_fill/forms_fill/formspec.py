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
class FormSpec:
    key: str
    template: Path
    declared_fields: tuple[str, ...]
    text_ops: tuple[TextOp, ...]
    checkbox_ops: tuple[CheckboxOp, ...]
    build_context: Callable[[TenancyBundle, dict], dict[str, str]]
    # Selector fields drive checkboxes, not text cells; they should not count
    # toward blank/filled text accounting.
    selector_fields: tuple[str, ...] = field(default=())
