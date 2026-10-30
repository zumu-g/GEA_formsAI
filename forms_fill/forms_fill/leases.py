"""Lease signing records for the Ingoing (move-in) workflow.

One row per filled residential lease: the engine's ``idem_key``, the resolved
lease facts, the Annature envelope, and the ingoing-engine notification state.
Lives in the accounts SQLite file (same volume) but owns its own table.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timezone

from .accounts import _connect

LEASE_FORM = "residential_rental_agreement"

_COLUMNS = (
    "idem_key", "facts", "status", "signers_expected", "signers",
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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS lease_signers (
              request_id TEXT NOT NULL REFERENCES lease_signings(request_id),
              slot INTEGER NOT NULL,
              name TEXT NOT NULL,
              email TEXT NOT NULL,
              token_hash TEXT UNIQUE NOT NULL,
              status TEXT NOT NULL DEFAULT 'pending',
              signed_name TEXT,
              signature_png BLOB,
              signed_at TEXT,
              ip TEXT,
              user_agent TEXT,
              declined_reason TEXT,
              PRIMARY KEY (request_id, slot)
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
            out.append({"slot": n, "name": name, "email": email})
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


# ── tenant signers: formsAI's own e-signing ──────────────────────────────────


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_signers(request_id: str, tenants: list[dict]) -> dict[int, str]:
    """One signing link per tenant. Returns {slot: raw token}; only the hash
    is stored, so the DB alone can't be used to sign."""

    # slot = renter number on the lease, so each signature lands in its own box
    slots = [t.get("slot", i) for i, t in enumerate(tenants, start=1)]
    tokens = {slot: secrets.token_urlsafe(32) for slot in slots}
    with _connect() as conn:
        conn.executemany(
            "INSERT INTO lease_signers (request_id, slot, name, email, token_hash) VALUES (?, ?, ?, ?, ?)",
            [(request_id, slot, t["name"], t["email"], _hash(tokens[slot]))
             for slot, t in zip(slots, tenants)],
        )
    return tokens


def delete_signers(request_id: str) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM lease_signers WHERE request_id = ?", (request_id,))


def signer_by_token(token: str) -> dict | None:
    with _connect() as conn:
        r = conn.execute(
            """SELECT s.*, l.status AS lease_status FROM lease_signers s
               JOIN lease_signings l USING (request_id) WHERE s.token_hash = ?""",
            (_hash(token),),
        ).fetchone()
    return dict(r) if r else None


def signers_for(request_id: str) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM lease_signers WHERE request_id = ? ORDER BY slot", (request_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def _open_signer(conn, token: str):
    """The pending signer for a token on a lease still out for signing."""

    return conn.execute(
        """SELECT s.request_id, s.slot FROM lease_signers s
           JOIN lease_signings l USING (request_id)
           WHERE s.token_hash = ? AND s.status = 'pending' AND l.status = 'sent'""",
        (_hash(token),),
    ).fetchone()


def record_signature(token: str, signed_name: str, signature_png: bytes, ip: str, user_agent: str) -> str:
    """'signed', 'complete' (this was the last tenant), or 'invalid'.

    BEGIN IMMEDIATE serialises concurrent signers, so exactly one call can
    ever see the lease become complete."""

    with _connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = _open_signer(conn, token)
        if row is None:
            return "invalid"
        now = _now()
        conn.execute(
            """UPDATE lease_signers SET status = 'signed', signed_name = ?, signature_png = ?,
               signed_at = ?, ip = ?, user_agent = ? WHERE request_id = ? AND slot = ?""",
            (signed_name, signature_png, now, ip, user_agent, row["request_id"], row["slot"]),
        )
        pending = conn.execute(
            "SELECT COUNT(*) FROM lease_signers WHERE request_id = ? AND status != 'signed'",
            (row["request_id"],),
        ).fetchone()[0]
        signed = conn.execute(
            "SELECT COUNT(*) FROM lease_signers WHERE request_id = ? AND status = 'signed'",
            (row["request_id"],),
        ).fetchone()[0]
        conn.execute(
            "UPDATE lease_signings SET signers = ?, updated_at = ? WHERE request_id = ?",
            (signed, now, row["request_id"]),
        )
        return "signed" if pending else "complete"


def record_decline(token: str, reason: str) -> str:
    with _connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = _open_signer(conn, token)
        if row is None:
            return "invalid"
        now = _now()
        conn.execute(
            "UPDATE lease_signers SET status = 'declined', declined_reason = ? WHERE request_id = ? AND slot = ?",
            (reason[:1000], row["request_id"], row["slot"]),
        )
        conn.execute(
            "UPDATE lease_signings SET status = 'declined', updated_at = ? WHERE request_id = ?",
            (now, row["request_id"]),
        )
        return "declined"


def void(request_id: str) -> bool:
    """Atomic: only a lease still awaiting signatures can be voided."""

    with _connect() as conn:
        cur = conn.execute(
            "UPDATE lease_signings SET status = 'voided', updated_at = ? WHERE request_id = ? AND status = 'sent'",
            (_now(), request_id),
        )
        return cur.rowcount == 1
