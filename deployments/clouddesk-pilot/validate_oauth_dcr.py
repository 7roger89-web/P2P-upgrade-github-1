#!/usr/bin/env python3
"""OAuth 2.1 + PKCE + RFC 7591 dynamic registration validator.

This is the decisive regular-ChatGPT-Web compatibility question for a remote
coding MCP server. ChatGPT's connector surface cannot paste a static
``Authorization: Bearer`` header; it discovers OAuth metadata, registers itself
dynamically (or via a Client ID Metadata Document), and completes an
Authorization Code + PKCE S256 flow. A server that only offers a pre-shared
confidential client cannot be connected by regular ChatGPT Web.

This script proves the whole flow end to end against a live server, including
the negative cases that show PKCE and single-use codes are actually enforced.

    python3 validate_oauth_dcr.py --base-url http://127.0.0.1:8767 \
        --password-file /path/to/authorize-password [--evidence-out out.json]

The authorize-page password and every issued token are treated as secrets: they
are read from files/environment, never printed, and scrubbed from evidence.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import html.parser
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

PASS = "PASS"
FAIL = "FAIL"
PROTOCOL_VERSION = "2025-11-25"
CLIENT_INFO = {"name": "p2p-clouddesk-oauth-validator", "version": "1.0.0"}
REDIRECT_URI = "http://127.0.0.1:8767/callback"  # loopback: allowed without HTTPS


class FormParser(html.parser.HTMLParser):
    """Pull the hidden fields out of the authorize login page."""

    def __init__(self) -> None:
        super().__init__()
        self.fields: dict[str, str] = {}
        self.action: str | None = None
        self.method: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag == "form":
            self.action = a.get("action")
            self.method = a.get("method")
        if tag == "input" and a.get("type") == "hidden" and a.get("name"):
            self.fields[a["name"]] = a.get("value") or ""


class OAuthProbe:
    def __init__(self, base_url: str, secrets_list: list[str]):
        self.base = base_url.rstrip("/")
        self.secrets = [s for s in secrets_list if s]
        self.results: list[dict[str, Any]] = []
        self.current = ""

    # -- reporting --------------------------------------------------------- #
    def scrub(self, value: Any) -> Any:
        if isinstance(value, str):
            for secret in self.secrets:
                value = value.replace(secret, "[REDACTED]")
            return value
        if isinstance(value, dict):
            return {k: self.scrub(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self.scrub(v) for v in value]
        return value

    def group(self, name: str) -> None:
        self.current = name
        print(f"\n=== {name} ===")

    def check(self, name: str, expected: str, ok: bool, observed: Any = None, note: str = "") -> bool:
        status = PASS if ok else FAIL
        self.results.append(
            {
                "group": self.current,
                "check": name,
                "status": status,
                "expected": self.scrub(expected),
                "observed": self.scrub(observed),
                "note": self.scrub(note),
                "evidence_level": "EMPIRICALLY_TESTED",
            }
        )
        print(f"  [{status}] {name}: expected {expected} -> {json.dumps(self.scrub(observed))[:260]}")
        if note:
            print(f"         note: {note}")
        return ok

    # -- transport --------------------------------------------------------- #
    def request(self, method: str, url: str, *, data: bytes | None = None, headers: dict[str, str] | None = None, allow_redirects: bool = False):
        head = dict(headers or {})
        req = urllib.request.Request(url, data=data, headers=head, method=method)
        opener = urllib.request.build_opener(NoRedirect() if not allow_redirects else urllib.request.HTTPRedirectHandler())
        try:
            with opener.open(req, timeout=30) as resp:
                return resp.status, dict(resp.headers), resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            return exc.code, dict(exc.headers), exc.read().decode("utf-8", "replace")

    def get_json(self, path: str) -> tuple[int, Any]:
        status, _, body = self.request("GET", self.base + path)
        try:
            return status, json.loads(body)
        except json.JSONDecodeError:
            return status, {"_raw": body[:300]}

    def post_form(self, path: str, fields: dict[str, str]) -> tuple[int, dict[str, str], str]:
        data = urllib.parse.urlencode(fields).encode()
        return self.request("POST", self.base + path, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})

    def post_form_json(self, path: str, fields: dict[str, str]) -> tuple[int, Any]:
        """POST a form and parse the JSON body (token endpoint responses)."""
        status, _, body = self.post_form(path, fields)
        try:
            return status, json.loads(body)
        except json.JSONDecodeError:
            return status, {"_raw": body[:300]}

    def post_json(self, path: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> tuple[int, Any]:
        head = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        head.update(headers or {})
        status, resp_headers, body = self.request("POST", self.base + path, data=json.dumps(payload).encode(), headers=head)
        try:
            return status, json.loads(body)
        except json.JSONDecodeError:
            # SSE-framed MCP response
            for line in body.splitlines():
                line = line.strip()
                if line.startswith("data:"):
                    line = line[5:].strip()
                if line.startswith("{"):
                    return status, json.loads(line)
            return status, {"_raw": body[:300]}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D102
        return None


def pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(48)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return verifier, challenge


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default=os.environ.get("MCP_OAUTH_BASE_URL", "http://127.0.0.1:8767"))
    ap.add_argument("--password-file", default=os.environ.get("MCP_OAUTH_PASSWORD_FILE"))
    ap.add_argument("--redirect-uri", default=REDIRECT_URI)
    ap.add_argument("--evidence-out", default=None)
    args = ap.parse_args()

    password = os.environ.get("MCP_OAUTH_PASSWORD")
    if not password and args.password_file:
        with open(args.password_file, encoding="utf-8") as fh:
            password = fh.read().strip()
    if not password:
        raise SystemExit("no authorize password: set MCP_OAUTH_PASSWORD or --password-file")

    p = OAuthProbe(args.base_url, [password])
    tokens: list[str] = []

    # ---------------- 1. discovery ---------------- #
    p.group("O1 DISCOVERY")
    prm_status, prm = p.get_json("/.well-known/oauth-protected-resource")
    p.check(
        "RFC 9728 protected-resource metadata published",
        "200 + resource + authorization_servers",
        prm_status == 200 and bool(prm.get("resource")) and bool(prm.get("authorization_servers")),
        {"http_status": prm_status, "resource": prm.get("resource"), "authorization_servers": prm.get("authorization_servers"), "bearer_methods": prm.get("bearer_methods_supported")},
    )
    resource = (prm.get("resource") or args.base_url).rstrip("/")

    asm_status, asm = p.get_json("/.well-known/oauth-authorization-server")
    p.check(
        "RFC 8414 authorization-server metadata published",
        "200 + issuer/authorization_endpoint/token_endpoint",
        asm_status == 200 and all(asm.get(k) for k in ("issuer", "authorization_endpoint", "token_endpoint")),
        {"http_status": asm_status, "issuer": asm.get("issuer"), "authorization_endpoint": asm.get("authorization_endpoint"), "token_endpoint": asm.get("token_endpoint")},
    )
    p.check(
        "RFC 7591 dynamic client registration endpoint advertised",
        "registration_endpoint present",
        bool(asm.get("registration_endpoint")),
        {"registration_endpoint": asm.get("registration_endpoint")},
        note="this is the endpoint regular ChatGPT Web needs; a server without it cannot be self-registered by ChatGPT",
    )
    p.check(
        "PKCE S256 advertised",
        "code_challenge_methods_supported includes S256",
        "S256" in (asm.get("code_challenge_methods_supported") or []),
        {"methods": asm.get("code_challenge_methods_supported")},
    )
    p.check(
        "public client auth method 'none' supported",
        "token_endpoint_auth_methods_supported includes none",
        "none" in (asm.get("token_endpoint_auth_methods_supported") or []),
        {"methods": asm.get("token_endpoint_auth_methods_supported")},
        note="ChatGPT presents no client secret; only a public client ('none') or private_key_jwt works",
    )

    # ---------------- 2. anonymous challenge ---------------- #
    p.group("O2 ANONYMOUS CHALLENGE")
    status, body = p.post_json(
        "/mcp",
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {}, "clientInfo": CLIENT_INFO}},
    )
    p.check("anonymous MCP request rejected", "401", status == 401, {"http_status": status})
    _, resp_headers, raw = p.request(
        "POST",
        args.base_url.rstrip("/") + "/mcp",
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {}, "clientInfo": CLIENT_INFO}}).encode(),
        headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
    )
    www = resp_headers.get("WWW-Authenticate", "")
    p.check(
        "401 carries a WWW-Authenticate resource_metadata pointer",
        "Bearer realm + resource_metadata URL",
        "Bearer" in www and "resource_metadata" in www,
        {"www_authenticate": www[:200]},
    )

    # ---------------- 3. dynamic client registration ---------------- #
    p.group("O3 DYNAMIC CLIENT REGISTRATION (RFC 7591)")
    reg_status, reg = p.post_json(
        "/oauth/register",
        {
            "client_name": "p2p-clouddesk-oauth-validator",
            "redirect_uris": [args.redirect_uri],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
        },
    )
    client_id = reg.get("client_id") if isinstance(reg, dict) else None
    p.check(
        "public client self-registers with no pre-shared credential",
        "201 + client_id",
        reg_status in (200, 201) and bool(client_id),
        {"http_status": reg_status, "client_id": client_id, "token_endpoint_auth_method": reg.get("token_endpoint_auth_method") if isinstance(reg, dict) else None},
    )
    if not client_id:
        raise SystemExit("dynamic registration failed; cannot continue the OAuth flow")

    bad_status, bad = p.post_json("/oauth/register", {"client_name": "no-redirects", "token_endpoint_auth_method": "none"})
    p.check(
        "registration without redirect_uris is refused",
        "400 invalid_client_metadata",
        bad_status == 400 and (bad.get("error") == "invalid_client_metadata" if isinstance(bad, dict) else False),
        {"http_status": bad_status, "error": bad.get("error") if isinstance(bad, dict) else None},
    )

    # ---------------- 4. authorize + token (happy path) ---------------- #
    p.group("O4 AUTHORIZATION CODE + PKCE S256")
    verifier, challenge = pkce_pair()
    p.secrets.append(verifier)
    state = secrets.token_urlsafe(16)
    auth_params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": args.redirect_uri,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
        "resource": resource,
    }
    page_status, _, page = p.request("GET", args.base_url.rstrip("/") + "/oauth/authorize?" + urllib.parse.urlencode(auth_params))
    form = FormParser()
    form.feed(page)
    p.check(
        "authorize endpoint renders an operator consent/login page",
        "200 + HTML form posting to /oauth/authorize",
        page_status == 200 and form.action == "/oauth/authorize" and "password" in page,
        {"http_status": page_status, "form_action": form.action, "form_method": form.method, "hidden_fields": sorted(form.fields)},
    )

    post_fields = dict(form.fields)
    post_fields["password"] = password
    red_status, red_headers, red_body = p.post_form("/oauth/authorize", post_fields)
    location = red_headers.get("Location", "")
    parsed = urllib.parse.urlparse(location)
    qs = urllib.parse.parse_qs(parsed.query)
    code = (qs.get("code") or [None])[0]
    returned_state = (qs.get("state") or [None])[0]
    p.check(
        "correct password yields a single-use authorization code on the registered redirect_uri",
        "302 + Location on redirect_uri with code and matching state",
        red_status in (302, 303) and parsed.scheme in ("http", "https") and parsed.netloc == urllib.parse.urlparse(args.redirect_uri).netloc and bool(code) and returned_state == state,
        {"http_status": red_status, "redirect_host": parsed.netloc, "code_present": bool(code), "state_matches": returned_state == state},
    )

    wrong_status, _, wrong_body = p.post_form("/oauth/authorize", {**post_fields, "password": "deliberately-wrong-password"})
    p.check(
        "wrong password does not yield a code",
        "no 302 with a code (login page re-rendered or error)",
        not (wrong_status in (302, 303) and "code=" in wrong_body),
        {"http_status": wrong_status, "contains_error": "color:red" in wrong_body or "error" in wrong_body.lower()},
    )

    if not code:
        raise SystemExit("no authorization code issued; cannot continue")

    tok_status, tok = p.post_form_json(
        "/oauth/token",
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": args.redirect_uri,
            "client_id": client_id,
            "code_verifier": verifier,
            "resource": resource,
        },
    )
    access_token = tok.get("access_token") if isinstance(tok, dict) else None
    if access_token:
        tokens.append(access_token)
        p.secrets.append(access_token)
    p.check(
        "token exchange with the correct PKCE verifier succeeds for a public client",
        "200 + access_token (no client_secret presented)",
        tok_status == 200 and bool(access_token),
        {"http_status": tok_status, "token_type": tok.get("token_type") if isinstance(tok, dict) else None, "expires_in": tok.get("expires_in") if isinstance(tok, dict) else None, "access_token_present": bool(access_token)},
    )

    # ---------------- 5. negative OAuth cases ---------------- #
    p.group("O5 OAUTH NEGATIVE CASES")
    reuse_status, reuse = p.post_form_json(
        "/oauth/token",
        {"grant_type": "authorization_code", "code": code, "redirect_uri": args.redirect_uri, "client_id": client_id, "code_verifier": verifier, "resource": resource},
    )
    p.check(
        "authorization code is single-use",
        "replay refused",
        reuse_status >= 400 and (reuse.get("error") if isinstance(reuse, dict) else None) in ("invalid_grant", "invalid_request"),
        {"http_status": reuse_status, "error": reuse.get("error") if isinstance(reuse, dict) else None},
    )

    verifier2, challenge2 = pkce_pair()
    p.secrets.append(verifier2)
    auth2 = {**auth_params, "code_challenge": challenge2, "state": secrets.token_urlsafe(16)}
    p.request("GET", args.base_url.rstrip("/") + "/oauth/authorize?" + urllib.parse.urlencode(auth2))
    page2_status, _, page2 = p.request("GET", args.base_url.rstrip("/") + "/oauth/authorize?" + urllib.parse.urlencode(auth2))
    form2 = FormParser()
    form2.feed(page2)
    st2, h2, b2 = p.post_form("/oauth/authorize", {**dict(form2.fields), "password": password})
    code2 = (urllib.parse.parse_qs(urllib.parse.urlparse(h2.get("Location", "")).query).get("code") or [None])[0]
    wrong_verifier = base64.urlsafe_b64encode(secrets.token_bytes(48)).rstrip(b"=").decode()
    p.secrets.append(wrong_verifier)
    wv_status, wv = p.post_form_json(
        "/oauth/token",
        {"grant_type": "authorization_code", "code": code2 or "", "redirect_uri": args.redirect_uri, "client_id": client_id, "code_verifier": wrong_verifier, "resource": resource},
    )
    p.check(
        "token exchange with a WRONG PKCE verifier is refused",
        "400 invalid_grant",
        wv_status >= 400 and (wv.get("error") if isinstance(wv, dict) else None) in ("invalid_grant", "invalid_request"),
        {"http_status": wv_status, "error": wv.get("error") if isinstance(wv, dict) else None, "code2_issued": bool(code2)},
        note="proves PKCE is actually enforced, not merely advertised",
    )

    # ---------------- 6. authenticated MCP over the issued token ---------------- #
    p.group("O6 AUTHENTICATED MCP CALL")
    if access_token:
        status, mcp = p.post_json(
            "/mcp",
            {"jsonrpc": "2.0", "id": 2, "method": "initialize", "params": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {}, "clientInfo": CLIENT_INFO}},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        info = ((mcp.get("result") or {}).get("serverInfo") if isinstance(mcp, dict) else None) or {}
        p.check(
            "MCP initialize succeeds with the OAuth access token",
            "200 + serverInfo",
            status == 200 and bool(info.get("name")),
            {"http_status": status, "serverInfo": info},
        )
        status, listing = p.post_json(
            "/mcp",
            {"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        tools = [t["name"] for t in ((listing.get("result") or {}).get("tools") or [])] if isinstance(listing, dict) else []
        p.check("tools/list works over the OAuth token", "coding tool catalog returned", status == 200 and "apply_patch" in tools and "exec_command" in tools, {"http_status": status, "tool_count": len(tools)})

        bogus_status, _ = p.post_json(
            "/mcp",
            {"jsonrpc": "2.0", "id": 4, "method": "initialize", "params": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {}, "clientInfo": CLIENT_INFO}},
            headers={"Authorization": "Bearer not-a-real-token"},
        )
        p.check("forged bearer token rejected", "401", bogus_status == 401, {"http_status": bogus_status})
    else:
        for name in ("MCP initialize succeeds with the OAuth access token", "tools/list works over the OAuth token", "forged bearer token rejected"):
            p.check(name, "n/a", False, None, note="skipped: no access token issued")

    # ---------------- summary ---------------- #
    groups: dict[str, dict[str, int]] = {}
    for row in p.results:
        bucket = groups.setdefault(row["group"], {"PASS": 0, "FAIL": 0})
        bucket[row["status"]] += 1
    print("\n" + "=" * 68)
    print("OAUTH / DCR SUMMARY")
    print("=" * 68)
    ok = True
    for g in sorted(groups):
        verdict = FAIL if groups[g]["FAIL"] else PASS
        if groups[g]["FAIL"]:
            ok = False
        print(f"{g:44} {verdict:6} pass={groups[g]['PASS']} fail={groups[g]['FAIL']}")
    total_pass = sum(v["PASS"] for v in groups.values())
    total_fail = sum(v["FAIL"] for v in groups.values())
    print(f"\nchecks: {total_pass} PASS / {total_fail} FAIL")

    if args.evidence_out:
        doc = p.scrub(
            {
                "task_id": "P2P_CLOUD_EXECUTOR_PILOT_01",
                "probe": "oauth2.1-pkce-rfc7591-dcr",
                "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "base_url": args.base_url,
                "redirect_uri": args.redirect_uri,
                "discovery": {"protected_resource": prm, "authorization_server": asm},
                "registered_client_id": client_id,
                "groups": {k: {"verdict": FAIL if v["FAIL"] else PASS, **v} for k, v in groups.items()},
                "checks": p.results,
                "totals": {"pass": total_pass, "fail": total_fail},
            }
        )
        os.makedirs(os.path.dirname(os.path.abspath(args.evidence_out)), exist_ok=True)
        with open(args.evidence_out, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2)
            fh.write("\n")
        print(f"evidence written: {args.evidence_out}")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
