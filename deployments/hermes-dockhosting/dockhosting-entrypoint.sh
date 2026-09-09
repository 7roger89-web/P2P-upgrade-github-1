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

plugins:
  enabled:
    - hermes-logistics
EOF
fi

# --- Install the read-only Logistics Hermes plugin -------------------------
# The plugin code ships in the image at /opt/hermes-logistics (outside the
# /opt/data volume). Copy it into HERMES_HOME/plugins each boot so it is always
# present even if the /opt/data volume did not persist.
if [ -d /opt/hermes-logistics ]; then
  mkdir -p /opt/data/plugins/hermes-logistics
  cp -rf /opt/hermes-logistics/. /opt/data/plugins/hermes-logistics/
fi

# --- Ensure the Logistics plugin is enabled in the Hermes config -----------
# Plugins are opt-in via plugins.enabled. If /opt/data/config.yaml persisted
# from an earlier boot without this plugin, add it idempotently.
PY_BIN="$(command -v /opt/hermes/.venv/bin/python || command -v python3)"
"$PY_BIN" - <<'PY'
import os
import sys

cfg = "/opt/data/config.yaml"
plugin = "hermes-logistics"
if not os.path.exists(cfg):
    sys.exit(0)
try:
    import yaml
except ImportError:
    print("WARN: yaml unavailable; skipping plugins.enabled merge", file=sys.stderr)
    sys.exit(0)
try:
    with open(cfg, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        data = {}
    plugins = data.get("plugins")
    if not isinstance(plugins, dict):
        plugins = {}
    enabled = plugins.get("enabled")
    if not isinstance(enabled, list):
        enabled = []
    if plugin not in enabled:
        enabled.insert(0, plugin)
    plugins["enabled"] = enabled
    data["plugins"] = plugins
    with open(cfg, "w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, default_flow_style=False, sort_keys=False, allow_unicode=True)
except Exception as exc:  # noqa: BLE001 - never block startup on config merge
    print(f"WARN: could not enable plugin in config.yaml: {exc}", file=sys.stderr)
    sys.exit(0)
PY

exec /opt/hermes/docker/entrypoint-dispatch.sh "$@"
