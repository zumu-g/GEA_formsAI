"""The single fill core (U5, KTD5).

``fill_form`` is the one function the CLI and ``POST /fill`` both call. It owns
all orchestration: resolve the form, fetch the bundle, build the render context
(caller fields verbatim — no statutory logic, R4), render DOCX+PDF, and assemble
the result with blank/filled accounting.
"""

from __future__ import annotations

from .models import FillFiles, FillRequest, FillResult, apply_service_address_defaults
from .providers.base import PropertyDataProvider, select_provider
from .registry import get_form_spec
from .render import compute_blank_fields, render


def fill_form(
    request: FillRequest,
    provider: PropertyDataProvider | None = None,
) -> FillResult:
    spec = get_form_spec(request.form)

    if spec.requires_bundle:
        provider = provider or select_provider(request.provider)
        bundle = provider.fetch_bundle(request.identifiers)
        bundle = apply_service_address_defaults(bundle)
    else:
        # Sales forms (KTD8): caller fields + agency defaults, no tenancy fetch.
        bundle = None
    context = spec.build_context(bundle, request.fields)

    blank_fields = compute_blank_fields(spec, context)
    selectors = set(spec.selector_fields)
    blanks = set(blank_fields)
    filled_fields = [
        f for f in spec.declared_fields if f not in selectors and f not in blanks
    ]

    docx_path, pdf_path, warnings = render(
        spec, context, request.out_dir, pdf=request.pdf
    )
    if spec.validate_warnings is not None:
        warnings = [*warnings, *spec.validate_warnings(context)]
    if bundle is not None and bundle.meta.note:
        # provider data-quality flag (e.g. >1 active tenancy) — the PM must see it
        warnings = [*warnings, bundle.meta.note]

    return FillResult(
        ok=True,
        form=request.form,
        files=FillFiles(
            docx=str(docx_path) if docx_path else None,
            pdf=str(pdf_path) if pdf_path else None,
        ),
        filled_fields=filled_fields,
        blank_fields=blank_fields,
        warnings=warnings,
    )
