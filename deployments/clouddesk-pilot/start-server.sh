#!/bin/sh
# CloudDesk pilot launcher for upstream coding-tools-mcp.
#
# Intended to run as root (the systemd pattern): root reads the credential file,
# then drops privileges to a dedicated NON-ROOT pilot user before exec. The MCP
# process itself is never root.
#
# Where Docker is unavailable, isolation = dedicated Unix user + upstream
# workspace-root confinement + upstream Linux Landlock for exec_command.
# Where Docker is available, prefer deployments/clouddesk-pilot/docker-compose.yml.
#
# Environment:
#   PILOT_ROOT        pilot root (default /srv/clouddesk-pilot)
#   PILOT_USER        unprivileged user the server runs as (default ctmpilot)
#   PILOT_WORKSPACE   the ONE approved workspace (default $PILOT_ROOT/workspace)
#   PILOT_MODE        safe | trusted | dangerous   (default trusted)
#   PILOT_AUTH_MODE   bearer | oauth | noauth      (default bearer)
#   PILOT_HOST        bind host                    (default 0.0.0.0)
#   PILOT_PORT        bind port                    (default 8765)
#   PILOT_SERVER_URL  stable public origin, no /mcp (OAuth issuer pinning)
#   PILOT_TRUST_PROXY_HEADERS  1 only behind a proxy you control
#   PILOT_ALLOWED_ORIGINS      comma-separated exact browser origins
set -e

PILOT_ROOT="${PILOT_ROOT:-/srv/clouddesk-pilot}"
PILOT_USER="${PILOT_USER:-ctmpilot}"
AUTH_MODE="${PILOT_AUTH_MODE:-bearer}"
MODE="${PILOT_MODE:-trusted}"
HOST="${PILOT_HOST:-0.0.0.0}"
PORT="${PILOT_PORT:-8765}"

TOKEN_FILE="$PILOT_ROOT/secrets/ctm-bearer.token"
OAUTH_PASSWORD_FILE="$PILOT_ROOT/secrets/oauth-password"

if [ "$AUTH_MODE" = "oauth" ]; then
    # OAuth mode needs no static bearer token; the authorize-page password is
    # generated once and kept in a 0600 file the operator reads, never logged.
    [ -f "$OAUTH_PASSWORD_FILE" ] || {
        umask 077
        python3 -c 'import secrets;print(secrets.token_urlsafe(24))' > "$OAUTH_PASSWORD_FILE"
        chown "$PILOT_USER:$PILOT_USER" "$OAUTH_PASSWORD_FILE" 2>/dev/null || true
    }
    CREDENTIAL_ARGS="CODING_TOOLS_MCP_OAUTH_PASSWORD=$(cat "$OAUTH_PASSWORD_FILE")"
else
    [ -f "$TOKEN_FILE" ] || {
        echo "FATAL: missing $TOKEN_FILE" >&2
        exit 2
    }
    CREDENTIAL_ARGS="CODING_TOOLS_MCP_AUTH_TOKEN=$(cat "$TOKEN_FILE")"
fi

mkdir -p "$PILOT_ROOT/runtime/tmp"
chown "$PILOT_USER:$PILOT_USER" "$PILOT_ROOT/runtime" "$PILOT_ROOT/runtime/tmp"

exec setpriv --reuid="$PILOT_USER" --regid="$PILOT_USER" --init-groups env \
  HOME="$PILOT_ROOT/runtime" \
  TMPDIR="$PILOT_ROOT/runtime/tmp" \
  CODING_TOOLS_MCP_WORKSPACE="${PILOT_WORKSPACE:-$PILOT_ROOT/workspace}" \
  CODING_TOOLS_MCP_AUTH_MODE="$AUTH_MODE" \
  CODING_TOOLS_MCP_PERMISSION_MODE="$MODE" \
  CODING_TOOLS_MCP_HOST="$HOST" \
  CODING_TOOLS_MCP_PORT="$PORT" \
  ${PILOT_SERVER_URL:+CODING_TOOLS_MCP_SERVER_URL=$PILOT_SERVER_URL} \
  ${PILOT_TRUST_PROXY_HEADERS:+CODING_TOOLS_MCP_TRUST_PROXY_HEADERS=$PILOT_TRUST_PROXY_HEADERS} \
  ${PILOT_ALLOWED_ORIGINS:+CODING_TOOLS_MCP_ALLOWED_ORIGINS=$PILOT_ALLOWED_ORIGINS} \
  CODING_TOOLS_MCP_TELEMETRY=off \
  DO_NOT_TRACK=1 \
  $CREDENTIAL_ARGS \
  "$PILOT_ROOT/venv/bin/coding-tools-mcp"
