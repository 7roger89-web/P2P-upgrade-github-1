#!/bin/sh
set -eu

export HERMES_HOME="/opt/data"
export API_SERVER_ENABLED="true"
export API_SERVER_HOST="0.0.0.0"
export API_SERVER_PORT="${PORT:-8642}"

mkdir -p /opt/data

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

if [ ! -s /opt/data/config.yaml ]; then
  MODEL="${HERMES_DEFAULT_MODEL:-gemini-3.7-flash}"
  cat > /opt/data/config.yaml <<EOF
model:
  default: ${MODEL}
  provider: gemini
  base_url: https://generativelanguage.googleapis.com/v1beta

display:
  final_response_markdown: keep
  streaming: false
  platforms:
    telegram:
      streaming: false
  runtime_footer:
    enabled: true
    fields:
      - model
      - prompt_tokens
      - cache_read
      - output_tokens
      - context_pct
      - elapsed_time

telegram:
  extra:
    rich_messages: true
    allow_cjk_rich: true
    rich_drafts: false
EOF
fi

exec /opt/hermes/docker/entrypoint-dispatch.sh "$@"
