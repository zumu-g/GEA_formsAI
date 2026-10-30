"""Lease signing records for the Ingoing (move-in) workflow.

One row per filled residential lease: the engine's ``idem_key``, the resolved
lease facts, the Annature envelope, and the ingoing-engine notification state.
Lives in the accounts SQLite file (same volume) but owns its own table.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from .accounts import _connect

LEASE_FORM = "residential_rental_agreement"

_COLUMNS = (
    "idem_key", "facts", "status", "envelope_id", "signers_expected", "signers",
    "signed_at", "notify_status", "notify_attempts", "notify_sent_at",
    "notify_response", "updated_at",
)


def init() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS lease_signings (
              request_id TEXT PRIMARY KEY,
              idem_key TEXT,
              facts TEXT NOT NULL,
              status TEXT NOT NULL,
              envelope_id TEXT UNIQUE,
              signers_expected INTEGER,
              signers INTEGER,
              signed_at TEXT,
              notify_status TEXT,
              notify_attempts INTEGER NOT NULL DEFAULT 0,
              notify_sent_at TEXT,
              notify_response TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            )
            """
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row(r) -> dict | None:
    if r is None:
        return None
    row = dict(r)
    row["facts"] = json.loads(row["facts"])
    return row


def save(request_id: str, idem_key: str | None, facts: dict) -> None:
    now = _now()
    with _connect() as conn:
        conn.execute(
            """INSERT INTO lease_signings
               (request_id, idem_key, facts, status, created_at, updated_at)
               VALUES (?, ?, ?, 'draft', ?, ?)""",
            (request_id, idem_key, json.dumps(facts, default=str), now, now),
        )


def get(request_id: str) -> dict | None:
    with _connect() as conn:
        return _row(
            conn.execute(
                "SELECT * FROM lease_signings WHERE request_id = ?", (request_id,)
            ).fetchone()
        )


def get_by_envelope(envelope_id: str) -> dict | None:
    with _connect() as conn:
        return _row(
            conn.execute(
                "SELECT * FROM lease_signings WHERE envelope_id = ?", (envelope_id,)
            ).fetchone()
        )


def update(request_id: str, **changes) -> None:
    unknown = set(changes) - set(_COLUMNS)
    if unknown:
        raise ValueError(f"unknown lease_signings columns: {sorted(unknown)}")
    changes["updated_at"] = _now()
    cols = ", ".join(f"{k} = ?" for k in changes)
    with _connect() as conn:
        conn.execute(
            f"UPDATE lease_signings SET {cols} WHERE request_id = ?",
            (*changes.values(), request_id),
        )


def list_all() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM lease_signings ORDER BY created_at DESC"
        ).fetchall()
    return [_row(r) for r in rows]


# ── pre-send check: rent in advance + bond (never send placeholders) ─────────

_LEASE_FACTS = ("rent_amount", "first_rent_due_date", "bond_amount")
_AGENCY_PAYMENTS = ("rent_payment_details", "bond_payment_instructions")


def _blank(value) -> bool:
    return value is None or not str(value).strip()


def missing_payment_facts(facts: dict, payments: dict) -> list[str]:
    """Names of the values the signing pack needs but doesn't have."""

    return [k for k in _LEASE_FACTS if _blank(facts.get(k))] + [
        k for k in _AGENCY_PAYMENTS if _blank(payments.get(k))
    ]


def _date(value) -> str:
    try:
        return datetime.fromisoformat(str(value)).strftime("%d/%m/%Y")
    except ValueError:
        return str(value)  # already in display form


def signing_message(facts: dict, payments: dict) -> str:
    """The email text Annature sends with the lease. Call only when
    ``missing_payment_facts`` is empty."""

    period = str(facts.get("rent_period") or "").strip()
    rent = f"${str(facts['rent_amount']).lstrip('$')}" + (f" per {period.removesuffix('ly')}" if period else "")
    return (
        "Please review and sign your residential rental agreement.\n\n"
        "Rent in advance\n"
        f"Amount: {rent}\n"
        f"Due: {_date(facts['first_rent_due_date'])}\n"
        f"How to pay: {payments['rent_payment_details']}\n\n"
        "Bond\n"
        f"Amount: ${str(facts['bond_amount']).lstrip('$')}\n"
        f"How to pay: {payments['bond_payment_instructions']}\n"
        "Your bond is lodged with the Residential Tenancies Bond Authority (RTBA), Victoria."
    )


def tenants(facts: dict) -> list[dict]:
    """Every renter named on the lease (slots 1-4) as an Annature signer."""

    out = []
    for n in range(1, 5):
        name = str(facts.get(f"renter{n}_name") or "").strip()
        email = str(facts.get(f"renter{n}_email") or "").strip()
        if name or email:
            out.append({"name": name, "email": email})
    return out


def claim_notify(request_id: str) -> bool:
    """Atomically take the right to notify the ingoing engine, so two webhook
    deliveries racing each other can never both post. False = already sent,
    already in flight, or not signed."""

    with _connect() as conn:
        cur = conn.execute(
            """UPDATE lease_signings SET notify_status = 'sending', updated_at = ?
               WHERE request_id = ? AND status = 'signed'
                 AND (notify_status IS NULL OR notify_status = 'ingoing_notify_failed')""",
            (_now(), request_id),
        )
        return cur.rowcount == 1
