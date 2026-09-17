#!/bin/sh
# CloudDesk deployment-posture probe.
#
# Re-verifies the reverse-proxy / origin / authentication behaviour that a real
# cloud deployment depends on. Run this AFTER putting nginx/Caddy in front of the
# server, pointed at the PUBLIC https origin, to confirm the proxy did not break
# issuer pinning, leak spoofable forwarded headers, or synthesise an Origin.
#
# Usage:
#   TOKEN_FILE=/path/to/bearer.token \
#   PUBLIC_URL=https://mcp.example.com \
#   LOOPBACK_URL=http://127.0.0.1:8765 \
#   PINNED_URL=http://127.0.0.1:8768 \
#   sh probe_deployment_posture.sh
#
# Every probe prints PASS/FAIL. Exit code is nonzero if any probe fails.
# The token is read from a file and never printed.
set -u

TOKEN_FILE="${TOKEN_FILE:-/srv/clouddesk-pilot/secrets/ctm-bearer.token}"
LOOPBACK_URL="${LOOPBACK_URL:-http://127.0.0.1:8765}"
PINNED_URL="${PINNED_URL:-}"
OAUTH_DYNAMIC_URL="${OAUTH_DYNAMIC_URL:-}"
PUBLIC_URL="${PUBLIC_URL:-}"
EXPECTED_ISSUER="${EXPECTED_ISSUER:-}"
ALLOWED_ORIGIN="${ALLOWED_ORIGIN:-https://chatgpt.com}"

[ -r "$TOKEN_FILE" ] || { echo "FATAL: cannot read $TOKEN_FILE" >&2; exit 2; }
TOKEN="$(cat "$TOKEN_FILE")"

INIT='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"posture-probe","version":"1"}}}'
FAILED=0

code() { # code METHOD URL [extra curl args...]
    _m="$1"; _u="$2"; shift 2
    curl -sS -m 20 -o /dev/null -w '%{http_code}' -X "$_m" "$_u" "$@" 2>/dev/null
}

issuer_of() {
    curl -sS -m 20 "$1/.well-known/oauth-authorization-server" 2>/dev/null |
        python3 -c 'import sys,json
try: print(json.load(sys.stdin).get("issuer") or "")
except Exception: print("")'
}

report() { # report NAME EXPECTED ACTUAL
    if [ "$2" = "$3" ]; then
        echo "  [PASS] $1 (expected $2)"
    else
        echo "  [FAIL] $1 (expected $2, got $3)"
        FAILED=$((FAILED + 1))
    fi
}

echo "=== A. authentication ==="
report "anonymous MCP POST rejected" 401 \
    "$(code POST "$LOOPBACK_URL/mcp" -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' --data "$INIT")"
report "invalid bearer rejected" 401 \
    "$(code POST "$LOOPBACK_URL/mcp" -H 'Authorization: Bearer not-a-real-token' -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' --data "$INIT")"
report "valid bearer accepted" 200 \
    "$(code POST "$LOOPBACK_URL/mcp" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' --data "$INIT")"
report "server card public without credentials" 200 "$(code GET "$LOOPBACK_URL/.well-known/mcp.json")"

echo "=== B. browser Origin policy (CSRF / DNS-rebinding defence) ==="
# No Origin header is what a server-to-server MCP client (ChatGPT's connector
# runtime) sends; it must never be blocked by the browser Origin policy.
report "server-to-server request (no Origin) accepted" 200 \
    "$(code POST "$LOOPBACK_URL/mcp" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' --data "$INIT")"
report "loopback browser Origin accepted by default" 200 \
    "$(code POST "$LOOPBACK_URL/mcp" -H "Authorization: Bearer $TOKEN" -H "Origin: $LOOPBACK_URL" -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' --data "$INIT")"
report "unallowlisted remote browser Origin denied" 403 \
    "$(code POST "$LOOPBACK_URL/mcp" -H "Authorization: Bearer $TOKEN" -H "Origin: https://evil.example" -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' --data "$INIT")"
report "Origin with embedded userinfo denied" 403 \
    "$(code POST "$LOOPBACK_URL/mcp" -H "Authorization: Bearer $TOKEN" -H "Origin: ${ALLOWED_ORIGIN}@evil.example" -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' --data "$INIT")"

echo "=== C. reverse-proxy hardening ==="
if [ -n "$PINNED_URL" ] && [ -n "$EXPECTED_ISSUER" ]; then
    report "pinned SERVER_URL yields stable public issuer" "$EXPECTED_ISSUER" "$(issuer_of "$PINNED_URL")"
    report "spoofed Host header cannot move the issuer" "$EXPECTED_ISSUER" \
        "$(curl -sS -m 20 -H 'Host: attacker.example' "$PINNED_URL/.well-known/oauth-authorization-server" 2>/dev/null |
            python3 -c 'import sys,json
try: print(json.load(sys.stdin).get("issuer") or "")
except Exception: print("")')"
else
    echo "  [SKIP] set PINNED_URL and EXPECTED_ISSUER to probe issuer pinning"
fi
if [ -n "$OAUTH_DYNAMIC_URL" ]; then
    _plain="$(issuer_of "$OAUTH_DYNAMIC_URL")"
    _spoofed="$(curl -sS -m 20 -H 'X-Forwarded-Host: attacker.example' -H 'X-Forwarded-Proto: https' \
        "$OAUTH_DYNAMIC_URL/.well-known/oauth-authorization-server" 2>/dev/null |
        python3 -c 'import sys,json
try: print(json.load(sys.stdin).get("issuer") or "")
except Exception: print("")')"
    if [ -n "$_plain" ] && [ "$_plain" = "$_spoofed" ] && ! echo "$_spoofed" | grep -q 'attacker.example'; then
        echo "  [PASS] spoofed X-Forwarded-Host ignored when proxy headers untrusted (issuer stayed $_plain)"
    else
        echo "  [FAIL] spoofed X-Forwarded-Host moved the issuer (plain=$_plain spoofed=$_spoofed)"
        FAILED=$((FAILED + 1))
    fi
else
    echo "  [SKIP] set OAUTH_DYNAMIC_URL to probe forwarded-header trust"
fi

echo "=== D. public HTTPS origin (only when PUBLIC_URL is supplied) ==="
if [ -n "$PUBLIC_URL" ]; then
    report "public origin rejects anonymous" 401 \
        "$(code POST "$PUBLIC_URL/mcp" -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' --data "$INIT")"
    report "public origin accepts valid bearer" 200 \
        "$(code POST "$PUBLIC_URL/mcp" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' --data "$INIT")"
    report "public origin serves the server card" 200 "$(code GET "$PUBLIC_URL/.well-known/mcp.json")"
else
    echo "  [SKIP] set PUBLIC_URL to probe the public HTTPS origin"
fi

echo
if [ "$FAILED" -eq 0 ]; then
    echo "POSTURE_PROBE=PASS"
else
    echo "POSTURE_PROBE=FAIL ($FAILED probe(s) failed)"
fi
exit "$FAILED"
