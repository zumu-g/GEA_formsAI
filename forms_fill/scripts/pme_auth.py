"""One-shot PropertyMe OAuth: run, log in, token lands in secrets/propertyme-tokens.json.

Usage: PME_CLIENT_ID=... PME_CLIENT_SECRET=... python scripts/pme_auth.py
"""

import json
import os
import secrets
import sys
import urllib.parse
import webbrowser

import httpx
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

CLIENT_ID = os.environ["PME_CLIENT_ID"]
CLIENT_SECRET = os.environ["PME_CLIENT_SECRET"]
REDIRECT = "http://localhost:65385/home/callback"
SCOPE = "activity:read communication:read contact:read property:read transaction:read offline_access"
OUT = Path(__file__).resolve().parent.parent / "secrets" / "propertyme-tokens.json"

state = secrets.token_urlsafe(16)
auth_url = "https://login.propertyme.com/connect/authorize?" + urllib.parse.urlencode(
    {
        "response_type": "code",
        "state": state,
        "client_id": CLIENT_ID,
        "scope": SCOPE,
        "redirect_uri": REDIRECT,
    }
)


class Handler(BaseHTTPRequestHandler):
    code = None

    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if q.get("state", [""])[0] != state or "code" not in q:
            self.send_error(400, "bad state or missing code")
            return
        Handler.code = q["code"][0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h2>Done - you can close this tab.</h2>")

    def log_message(self, *a):
        pass


srv = HTTPServer(("localhost", 65385), Handler)
print("Opening browser for PropertyMe login...", file=sys.stderr)
webbrowser.open(auth_url)
while Handler.code is None:
    srv.handle_request()

resp = httpx.post(
    "https://login.propertyme.com/connect/token",
    data={
        "grant_type": "authorization_code",
        "code": Handler.code,
        "redirect_uri": REDIRECT,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    },
    headers={"User-Agent": "gea-forms-fill/0.1"},
    timeout=30.0,
)
resp.raise_for_status()
tokens = resp.json()
assert "refresh_token" in tokens, tokens
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(tokens, indent=2))
os.chmod(OUT, 0o600)
print(f"Saved tokens to {OUT}")
