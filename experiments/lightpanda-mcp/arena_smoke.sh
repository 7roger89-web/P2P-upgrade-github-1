#!/usr/bin/env bash
# Arena Linux smoke test: no Chromium; no application repo changes.
set -Eeuo pipefail
export LIGHTPANDA_DISABLE_TELEMETRY=true LIGHTPANDA_DISABLE_CORE_DUMP=1
OUT="${1:-/tmp/lightpanda-pilot}"
mkdir -p "$OUT"
python3 -m venv "$OUT/.venv"
"$OUT/.venv/bin/python" -m pip install --disable-pip-version-check --no-input --retries 1 --timeout 25 lightpanda==1.0.2
"$OUT/.venv/bin/lightpanda" version
"$OUT/.venv/bin/lightpanda" fetch --obey-robots --dump markdown https://example.com > "$OUT/example.md"
grep -qi "Example Domain" "$OUT/example.md" || { echo "FETCH=FAIL"; exit 1; }
echo "FETCH=PASS"
"$OUT/.venv/bin/lightpanda" mcp --host 127.0.0.1 --port 19223 --block-private-networks > "$OUT/mcp.log" 2>&1 &
PID=$!
trap 'kill "$PID" 2>/dev/null || true' EXIT
python3 - <<'PY'
import json,time,urllib.request,sys
data=json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"arena-lightpanda-pilot","version":"1"}}}).encode()
for i in range(20):
 try:
  req=urllib.request.Request("http://127.0.0.1:19223/mcp",data=data,headers={"Content-Type":"application/json","Accept":"application/json, text/event-stream"})
  with urllib.request.urlopen(req,timeout=5) as r:
   body=r.read(16000).decode("utf-8","replace")
   if "protocolVersion" in body:
    print("MCP_INITIALIZE=PASS");sys.exit(0)
 except Exception as e:
  if i==19:print("MCP_INITIALIZE=FAIL",e)
 time.sleep(.5)
sys.exit(1)
PY
echo "ARENA_PILOT=PASS"
