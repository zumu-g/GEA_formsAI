"""VCAT online lodgement (U5, R6/R7 — KTD5/KTD6).

Lodges the *follow-on application* for an approved notice in VCAT's online
portal (online.vcat.vic.gov.au). Notices themselves are always served on the
renter manually by the PM — this module never automates service.

Gates, in order:
1. Approval — ``verify_approval`` must pass (hash-checked sidecar, U4).
2. Mapping — the notice's ground must map to a VCAT application type; grounds
   with no tribunal follow-on refuse with a clear message.
3. Credentials — ``VCAT_USERNAME`` / ``VCAT_PASSWORD`` env vars (never repo,
   never logged; all errors pass through ``_redact``).
4. Confirm — the browser flow stops at VCAT's final review screen and
   screenshots it; only ``confirm=True`` performs the actual submission.

The portal-driving flow itself is intentionally not implemented yet: the
portal must be walked manually once to record real screens and selectors
(plan U5 execution note) — coding the flow blind against a login-gated legal
portal would ship guesses. ``lodge`` runs every gate, then raises
``LodgementError('portal flow not yet recorded…')`` at the browser boundary.
"""

from __future__ import annotations

import os
from pathlib import Path

from ..approval import verify_approval
from ..errors import FormsFillError
from ..grounds import Ground, get_ground

PORTAL_URL = "https://online.vcat.vic.gov.au/vol/"


class LodgementError(FormsFillError):
    """Lodgement refused or failed. Messages are always credential-redacted."""


# Ground family -> VCAT application type. Conservative: only families whose
# provider-side follow-on application is unambiguous are mapped; everything
# else refuses and the PM lodges manually.
_FAMILY_APPLICATIONS = {
    "vacate": "possession_order",       # RTA s 322 possession application
    "breach_of_duty": "compliance_order",  # RTA s 209 compliance/compensation
}


def vcat_application_type(section: str) -> str:
    """Map a ground section to its VCAT application type, or refuse."""

    ground: Ground = get_ground(section)
    app_type = _FAMILY_APPLICATIONS.get(ground.family)
    if app_type is None:
        raise LodgementError(
            f"ground {ground.section} ({ground.description}) has no automated "
            "VCAT follow-on application — lodge manually if one is required"
        )
    return app_type


def _redact(message: str) -> str:
    for var in ("VCAT_USERNAME", "VCAT_PASSWORD"):
        value = os.environ.get(var)
        if value:
            message = message.replace(value, f"<{var}>")
    return message


def _credentials() -> tuple[str, str]:
    user = os.environ.get("VCAT_USERNAME", "")
    password = os.environ.get("VCAT_PASSWORD", "")
    if not user or not password:
        raise LodgementError(
            "VCAT credentials not configured: set VCAT_USERNAME and "
            "VCAT_PASSWORD environment variables (never commit them)"
        )
    return user, password


def lodge(approved_path: str | Path, section: str, confirm: bool = False) -> dict:
    """Lodge the follow-on VCAT application for an approved notice.

    Stops at the portal's final review screen (screenshot) unless
    ``confirm=True``. Returns a result dict; never contains credentials.
    """

    path = Path(approved_path)
    approval = verify_approval(path)          # gate 1 — raises ApprovalError
    app_type = vcat_application_type(section)  # gate 2 — raises LodgementError
    _credentials()                             # gate 3 — raises LodgementError

    try:
        # gate 4 boundary: the recorded portal flow goes here (Playwright,
        # selectors in selectors.py, review-screen stop unless confirm).
        raise LodgementError(
            "portal flow not yet recorded: walk the VCAT portal manually once "
            "and populate forms_fill/vcat/selectors.py before automated "
            f"lodgement (application type: {app_type}, approved by "
            f"{approval['approver']}, confirm={confirm})"
        )
    except LodgementError:
        raise
    except Exception as exc:  # pragma: no cover — future browser errors
        raise LodgementError(_redact(f"lodgement failed: {exc}")) from None
