"""Agent accounts: invites, passwords, sessions (persisted in SQLite).

One module owns the whole surface — DB, scrypt hashing, invite lifecycle,
session tokens, and the Resend invite email. Stdlib only plus httpx (already
a dependency). Invites are restricted server-side to @grantsea.com.au.

The shared FORMS_API_TOKEN (machine callers) is untouched — api.py tries it
first and falls back to a session token here.
"""

from __future__ import annotations

import hashlib
import json
import hmac
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

ALLOWED_EMAIL_DOMAIN = "@grantsea.com.au"
INVITE_TTL_DAYS = 7
SESSION_TTL_DAYS = 30

# ponytail: scrypt stdlib, swap to argon2 only if a security review demands it
_SCRYPT = {"n": 2**14, "r": 8, "p": 1}


def _db_path() -> Path:
    return Path(os.environ.get("FORMS_DATA_DIR", "./data")) / "accounts.db"


def _connect() -> sqlite3.Connection:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS agents (
              id INTEGER PRIMARY KEY,
              email TEXT UNIQUE NOT NULL COLLATE NOCASE,
              name TEXT NOT NULL DEFAULT '',
              mobile TEXT NOT NULL DEFAULT '',
              pw_hash BLOB,
              pw_salt BLOB,
              is_admin INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS invites (
              token TEXT PRIMARY KEY,
              agent_id INTEGER NOT NULL REFERENCES agents(id),
              expires_at TEXT NOT NULL,
              used_at TEXT
            );
            CREATE TABLE IF NOT EXISTS sessions (
              token TEXT PRIMARY KEY,
              agent_id INTEGER NOT NULL REFERENCES agents(id),
              expires_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS agent_defaults (
              agent_id INTEGER NOT NULL REFERENCES agents(id),
              form_key TEXT NOT NULL,
              "values" TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              PRIMARY KEY (agent_id, form_key)
            );
            CREATE TABLE IF NOT EXISTS drafts (
              id INTEGER PRIMARY KEY,
              agent_id INTEGER,
              form_key TEXT NOT NULL,
              label TEXT NOT NULL DEFAULT '',
              state TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            """
        )


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_in(days: int) -> str:
    return (_now() + timedelta(days=days)).isoformat()


def _expired(iso: str) -> bool:
    return datetime.fromisoformat(iso) < _now()


def hash_password(password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    salt = salt or secrets.token_bytes(16)
    return hashlib.scrypt(password.encode(), salt=salt, **_SCRYPT), salt


def verify_password(password: str, pw_hash: bytes, pw_salt: bytes) -> bool:
    candidate, _ = hash_password(password, pw_salt)
    return hmac.compare_digest(candidate, pw_hash)


class AccountError(ValueError):
    """Raised with a caller-facing message; api.py maps it to an HTTP error."""


def create_invite(
    email: str, name: str = "", mobile: str = "", is_admin: bool = False
) -> str:
    """Upsert the agent row and return a fresh invite token.

    Re-inviting is allowed until the agent has set a password (covers lost
    invites and acts as the password-reset path for admins later, by design).
    """

    email = email.strip().lower()
    if not email.endswith(ALLOWED_EMAIL_DOMAIN):
        raise AccountError(f"invites are restricted to {ALLOWED_EMAIL_DOMAIN} addresses")
    with _connect() as conn:
        row = conn.execute("SELECT id, pw_hash FROM agents WHERE email = ?", (email,)).fetchone()
        if row and row["pw_hash"] is not None:
            raise AccountError("that agent already has an account — no invite needed")
        # First-ever agent becomes admin regardless of the flag passed.
        first = conn.execute("SELECT COUNT(*) AS n FROM agents").fetchone()["n"] == 0
        if row:
            conn.execute(
                "UPDATE agents SET name = ?, mobile = ?, is_admin = ? WHERE id = ?",
                (name, mobile, int(is_admin), row["id"]),
            )
            agent_id = row["id"]
        else:
            agent_id = conn.execute(
                "INSERT INTO agents (email, name, mobile, is_admin) VALUES (?, ?, ?, ?)",
                (email, name, mobile, int(is_admin or first)),
            ).lastrowid
        token = secrets.token_urlsafe(32)
        conn.execute(
            "INSERT INTO invites (token, agent_id, expires_at) VALUES (?, ?, ?)",
            (token, agent_id, _iso_in(INVITE_TTL_DAYS)),
        )
    return token


def send_invite_email(email: str, accept_url: str) -> bool:
    """Send the invite via Resend. Returns False (not an error) when no
    RESEND_API_KEY is configured — the accept link is always returned to the
    admin as a copyable fallback, so email is best-effort."""

    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key:
        return False
    resp = httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "from": os.environ.get("MAIL_FROM", "forms@grantsea.com.au"),
            "to": [email],
            "subject": "You're invited to GEA forms-fill",
            "html": (
                "<p>You've been invited to the GEA forms-fill tool.</p>"
                f'<p><a href="{accept_url}">Set your password to get started</a> '
                "(link expires in 7 days).</p>"
            ),
        },
        timeout=15.0,
    )
    resp.raise_for_status()
    return True


def accept_invite(token: str, password: str) -> str:
    """Validate the invite, set the password, and return a session token."""

    if len(password) < 8:
        raise AccountError("password must be at least 8 characters")
    with _connect() as conn:
        inv = conn.execute("SELECT * FROM invites WHERE token = ?", (token,)).fetchone()
        if not inv or inv["used_at"] is not None or _expired(inv["expires_at"]):
            raise AccountError("invite link is invalid, used, or expired — ask for a new invite")
        pw_hash, pw_salt = hash_password(password)
        conn.execute(
            "UPDATE agents SET pw_hash = ?, pw_salt = ? WHERE id = ?",
            (pw_hash, pw_salt, inv["agent_id"]),
        )
        conn.execute(
            "UPDATE invites SET used_at = ? WHERE token = ?", (_now().isoformat(), token)
        )
        return _new_session(conn, inv["agent_id"])


def _new_session(conn: sqlite3.Connection, agent_id: int) -> str:
    token = secrets.token_urlsafe(32)
    conn.execute(
        "INSERT INTO sessions (token, agent_id, expires_at) VALUES (?, ?, ?)",
        (token, agent_id, _iso_in(SESSION_TTL_DAYS)),
    )
    return token


def login(email: str, password: str) -> str | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, pw_hash, pw_salt FROM agents WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()
        if not row or row["pw_hash"] is None:
            return None
        if not verify_password(password, row["pw_hash"], row["pw_salt"]):
            return None
        return _new_session(conn, row["id"])


def logout(token: str) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))


def session_agent(token: str) -> dict | None:
    """The agent behind a session token, or None. Sweeps expired sessions."""

    if not token:
        return None
    with _connect() as conn:
        conn.execute("DELETE FROM sessions WHERE expires_at < ?", (_now().isoformat(),))
        row = conn.execute(
            """SELECT a.id, a.email, a.name, a.mobile, a.is_admin
               FROM sessions s JOIN agents a ON a.id = s.agent_id
               WHERE s.token = ?""",
            (token,),
        ).fetchone()
        return dict(row) if row else None


# ── per-agent sticky defaults (lease-flow speed-up U3) ──────────────────────
# Signed-in agents only: the machine token / dev bypass have no row here by
# design (invisible seeds must never cross callers). Blank value clears a key.

DEFAULTS_ALLOWLIST = frozenset(
    {"emergency_contact_name", "emergency_phone", "emergency_email", "agent_acn"}
)
_DEFAULT_VALUE_CAP = 500


def save_defaults(agent_id: int, form_key: str, values: dict) -> dict:
    """Merge allowlisted string values into the agent's defaults; blank clears."""

    clean = {
        k: v
        for k, v in values.items()
        if k in DEFAULTS_ALLOWLIST and isinstance(v, str) and len(v) <= _DEFAULT_VALUE_CAP
    }
    with _connect() as conn:
        current = get_defaults(agent_id, form_key)
        for k, v in clean.items():
            if v.strip():
                current[k] = v
            else:
                current.pop(k, None)
        conn.execute(
            """INSERT INTO agent_defaults (agent_id, form_key, "values", updated_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(agent_id, form_key) DO UPDATE SET "values" = excluded."values",
               updated_at = excluded.updated_at""",
            (agent_id, form_key, json.dumps(current), _now().isoformat()),
        )
    return current


def get_defaults(agent_id: int, form_key: str) -> dict:
    with _connect() as conn:
        row = conn.execute(
            'SELECT "values" FROM agent_defaults WHERE agent_id = ? AND form_key = ?',
            (agent_id, form_key),
        ).fetchone()
        return json.loads(row["values"]) if row else {}


# ── in-progress form drafts ─────────────────────────────────────────────────
# agent_id None = the machine-token shared bucket. Ownership lives in the
# WHERE clause of every read/write — "agent_id IS ?" matches NULL correctly.


def save_draft(
    agent_id: int | None, draft_id: int | None, form_key: str, label: str, state: str
) -> int:
    with _connect() as conn:
        now = _now().isoformat()
        if draft_id is not None:
            cur = conn.execute(
                """UPDATE drafts SET form_key = ?, label = ?, state = ?, updated_at = ?
                   WHERE id = ? AND agent_id IS ?""",
                (form_key, label, state, now, draft_id, agent_id),
            )
            if cur.rowcount:
                return draft_id
        return conn.execute(
            "INSERT INTO drafts (agent_id, form_key, label, state, updated_at) VALUES (?, ?, ?, ?, ?)",
            (agent_id, form_key, label, state, now),
        ).lastrowid


def list_drafts(agent_id: int | None) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            """SELECT id, form_key, label, updated_at FROM drafts
               WHERE agent_id IS ? ORDER BY updated_at DESC""",
            (agent_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_draft(agent_id: int | None, draft_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, form_key, label, state, updated_at FROM drafts WHERE id = ? AND agent_id IS ?",
            (draft_id, agent_id),
        ).fetchone()
        return dict(row) if row else None


def delete_draft(agent_id: int | None, draft_id: int) -> bool:
    with _connect() as conn:
        return bool(
            conn.execute(
                "DELETE FROM drafts WHERE id = ? AND agent_id IS ?", (draft_id, agent_id)
            ).rowcount
        )


def list_agents() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            """SELECT id, email, name, mobile, is_admin, created_at,
                      pw_hash IS NOT NULL AS active
               FROM agents ORDER BY created_at"""
        ).fetchall()
        return [dict(r) for r in rows]
