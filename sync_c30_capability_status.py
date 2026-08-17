#!/usr/bin/env python3
"""Sync C30 capability_status entry with the built C30 candidate (idempotent)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GOV = ROOT / "governance" / "development-control.json"

SHA = "94b09b596dab04a8bff5042c44753fed96881c89658d3db4e7be09fe034017b7"
LABEL = "P2P-8.4.7-C-Codex-Edition-v24-c30-composable-execution-target-foundation-candidate-v1.zip"


def main() -> None:
    data = json.loads(GOV.read_text(encoding="utf-8"))
    for c in data["capability_status"]:
        if c.get("id") == "C30":
            c["candidate_id"] = "C30"
            c["candidate_version"] = "8.4.7-C-codex.24"
            c["candidate_sha256"] = SHA
            c["promotion_status"] = "UNPROMOTED"
            if "C30-PACKAGING" not in c.get("evidence_ref", ""):
                c["evidence_ref"] = "E0-C30-ET1-ET60; C30 candidate built, verify PASS, UNPROMOTED"
    GOV.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("C30 capability_status synced")


if __name__ == "__main__":
    main()
