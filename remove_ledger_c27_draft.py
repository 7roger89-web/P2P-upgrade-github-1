#!/usr/bin/env python3
"""Remove the C27 draft record (added with invalid family/origin_type/freshness)
so update_ledger_c27.py can re-add the corrected version. Idempotent."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEDGER_PATH = ROOT / "docs" / "p2p-development" / "capability-ledger" / "capability-index.json"

data = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
before = len(data["capabilities"])
data["capabilities"] = [
    c for c in data["capabilities"]
    if c.get("capability_id") != "REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY"
]
LEDGER_PATH.write_text(
    json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
    encoding="utf-8",
)
print(f"removed draft; {before} -> {len(data['capabilities'])} records")
