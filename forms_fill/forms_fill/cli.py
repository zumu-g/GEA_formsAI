"""CLI shell (U6, R1/R2).

Thin wrapper over ``fill_form``. Accepts split flags or a whole-payload
``--json`` / stdin. Prints the result JSON to stdout and exits 0 on success;
prints a clear message to stderr and exits non-zero on any expected error.
"""

from __future__ import annotations

import sys

import typer

from .core import fill_form
from .errors import FormsFillError
from .models import build_request

app = typer.Typer(add_completion=False, help="GEA forms-fill tool.")


@app.callback()
def _root() -> None:
    # Keeps `fill` as a named subcommand (`forms fill ...`) — Typer collapses
    # a single-command app onto the root otherwise, breaking the documented CLI.
    pass


@app.command()
def fill(
    form: str = typer.Option(None, "--form", help="Form key, e.g. cav_rent_increase_notice"),
    identifiers: str = typer.Option(None, "--identifiers", help="JSON object of identifiers"),
    fields: str = typer.Option(None, "--fields", help="JSON object of caller-supplied fields"),
    out: str = typer.Option(None, "--out", help="Output directory"),
    json_payload: str = typer.Option(
        None, "--json", help="Whole request as one JSON object (use '-' for stdin)"
    ),
) -> None:
    """Fill a form and print the result JSON."""

    try:
        if json_payload == "-":
            json_payload = sys.stdin.read()
        elif json_payload is None and not sys.stdin.isatty() and form is None:
            # No flags and stdin is piped → treat stdin as the JSON payload.
            piped = sys.stdin.read().strip()
            json_payload = piped or None

        request = build_request(
            form=form,
            identifiers=identifiers,
            fields=fields,
            out_dir=out,
            json_payload=json_payload,
        )
        result = fill_form(request)
    except (FormsFillError, ValueError) as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1)

    typer.echo(result.model_dump_json())


@app.command()
def grounds(
    family: str = typer.Option(None, "--family", help="Filter: vacate | breach_of_duty | general | rent_increase"),
) -> None:
    """Print the statutory grounds catalogue as JSON."""

    import json

    from .grounds import UnknownGroundError, grounds_catalogue

    try:
        typer.echo(json.dumps({"grounds": grounds_catalogue(family)}, indent=2))
    except UnknownGroundError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1)


@app.command()
def approve(
    file: str = typer.Argument(..., help="Path to the generated notice (PDF or DOCX)"),
    by: str = typer.Option(..., "--by", help="Approving PM's name"),
) -> None:
    """Record PM approval of a generated notice (writes <file>.approval.json)."""

    import json

    from .approval import ApprovalError, approve as _approve

    try:
        record = _approve(file, by)
    except ApprovalError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1)
    typer.echo(json.dumps(record, indent=2))


@app.command("vcat-lodge")
def vcat_lodge(
    file: str = typer.Argument(..., help="Path to the approved notice"),
    ground: str = typer.Option(..., "--ground", help="Statutory ground section, e.g. 91ZM"),
    confirm_submit: bool = typer.Option(
        False, "--confirm-submit", help="Actually submit (default stops at VCAT's review screen)"
    ),
) -> None:
    """Lodge the follow-on VCAT application for an approved notice."""

    import json

    from .vcat import LodgementError, lodge

    try:
        result = lodge(file, ground, confirm=confirm_submit)
    except FormsFillError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1)
    typer.echo(json.dumps(result, indent=2))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
