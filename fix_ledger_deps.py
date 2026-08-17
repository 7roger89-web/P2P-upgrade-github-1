#!/usr/bin/env python3
"""Fix dependency defects introduced/flagged during C30 ledger reconciliation."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEDGER = ROOT / "docs" / "p2p-development" / "capability-ledger" / "capability-index.json"

data = json.loads(LEDGER.read_text(encoding="utf-8"))
by_id = {c["capability_id"]: c for c in data["capabilities"]}

# 1. SAFE_QUIESCE_AND_DRAIN must not depend on itself.
sq = by_id.get("SAFE_QUIESCE_AND_DRAIN")
if sq and "SAFE_QUIESCE_AND_DRAIN" in sq.get("dependencies", []):
    sq["dependencies"] = ["COMPOSABLE_EXECUTION_TARGET", "HEALTH_OWNERSHIP_LADDER"]
    print("SAFE_QUIESCE_AND_DRAIN: self-dep removed")

# 2. DRIFT_GATE <-> TARGET_FINGERPRINT_DRIFT cycle: fingerprint/drift builds ON
#    the drift gate; DRIFT_GATE must not depend on TARGET_FINGERPRINT_DRIFT.
dg = by_id.get("DRIFT_GATE")
if dg and "TARGET_FINGERPRINT_DRIFT" in dg.get("dependencies", []):
    dg["dependencies"] = [d for d in dg["dependencies"] if d != "TARGET_FINGERPRINT_DRIFT"]
    print("DRIFT_GATE: TARGET_FINGERPRINT_DRIFT dep removed (cycle broken)")

# 3. PROGRESSIVE_DISCLOSURE etc.: keep all provenance deps.

LEDGER.write_text(
    json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("deps fixed")
