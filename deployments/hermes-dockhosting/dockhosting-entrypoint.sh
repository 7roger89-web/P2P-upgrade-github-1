#!/bin/sh
set -eu

export HERMES_HOME="/opt/data"
export API_SERVER_ENABLED="true"
export API_SERVER_HOST="0.0.0.0"
export API_SERVER_PORT="${PORT:-8642}"

mkdir -p /opt/data

# API server requires a bearer key even though /health is intentionally public.
# Generate and persist one automatically so the user does not need another secret.
if [ -z "${API_SERVER_KEY:-}" ]; then
  KEY_FILE="/opt/data/.dockhosting_api_server_key"
  if [ ! -s "$KEY_FILE" ]; then
    python3 - <<'PY'
from pathlib import Path
import secrets
p = Path("/opt/data/.dockhosting_api_server_key")
p.write_text(secrets.token_urlsafe(48), encoding="utf-8")
p.chmod(0o600)
PY
  fi
  export API_SERVER_KEY="$(cat "$KEY_FILE")"
fi

# First-boot model config. Can be overridden later by editing /opt/data/config.yaml
# or setting HERMES_DEFAULT_MODEL before the first successful boot.
if [ ! -s /opt/data/config.yaml ]; then
  MODEL="${HERMES_DEFAULT_MODEL:-gemini-3-flash-preview}"
  cat > /opt/data/config.yaml <<EOF
model:
  provider: gemini
  default: ${MODEL}
  base_url: https://generativelanguage.googleapis.com/v1beta
EOF
fi

exec /opt/hermes/docker/entrypoint-dispatch.sh "$@"
