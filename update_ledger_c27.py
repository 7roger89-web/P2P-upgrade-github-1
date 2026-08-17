#!/usr/bin/env python3
"""C27 ledger delta: add the C27 certification-machinery record (UNKNOWN, blocked
lineage intake) consistent with schema v2 field vocabulary. Idempotent.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEDGER_PATH = ROOT / "docs" / "p2p-development" / "capability-ledger" / "capability-index.json"

NOW = "2026-08-17"

C27_RECORD = {
    "capability_id": "REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY",
    "name": "Real Host Execution Certification Machinery",
    "family": "MULTI_AI_INTEROPERABILITY",
    "beginner_value": "The certified pathway to prove an AI host is really controlled: bounded task, execution binding, independent result verification, and reconciliation. Machinery is delivered; live host execution remains NOT_CERTIFIED (blocked).",
    "principle": "UNKNOWN_REMAINS_UNKNOWN",
    "origin_refs": [
        "P2P-C27 goal document (real host execution certification)",
        "scripts/p2p_live_certification.py (C27 certification machinery)",
        "docs/p2p-development/reports/P2P-C27-terminal-report.md",
    ],
    "status": "UNKNOWN",
    "implementation_refs": ["scripts/p2p_live_certification.py", "tests/test_p2p_live_certification.py"],
    "evidence_refs": [
        "P2P-C27 terminal report (60 items, host-by-host discovery)",
        "codex doctor health evidence (auth env, 401 pre-model-contact)",
        "probe attempt evidence records (blocked pre-model-contact; mutation KNOWN_NONE)",
    ],
    "dependencies": [
        "C22_C24_ADAPTER_LIVE_CERTIFICATION",
        "INDEPENDENT_RESULT_VERIFICATION",
        "HOST_IDENTITY_VERIFICATION",
    ],
    "known_gaps": ["No reachable real host: Codex CLI 401 (api.openai.com), other CLIs absent, Manus API connector unconfigured in C27 session"],
    "do_not_duplicate_with": "BOUNDED_EXECUTION (sandbox task execution; this is host-control certification of an external AI host)",
    "next_condition": "A reachable real AI host with accepted credentials (OpenAI key, Anthropic, Google AI, Cursor, Copilot, or Manus API connector) — then run the bounded non-destructive probe and record the live certificate.",
    "last_reviewed": NOW,
    "freshness": "from_plan_or_report",
    "notes": "C27 goal is BLOCKED (LIVE_HOST_EVIDENCE_UNAVAILABLE) after honest host-by-host discovery. Machinery is the certified pathway; no fabricated PASS. Host-by-host: Codex CLI 0.147.0 installed (401), Claude Code/Gemini CLI/Cursor ACP/Copilot CLI absent, Manus API not configured, own proxy excluded (not externally controlled).",
    "origin_type": "IMPLEMENTATION_GOAL",
}

DEPENDENCY_NAMES = (
    "C22_C24_ADAPTER_LIVE_CERTIFICATION",
    "INDEPENDENT_RESULT_VERIFICATION",
    "HOST_IDENTITY_VERIFICATION",
)


def main() -> int:
    data = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    caps = data["capabilities"]
    ids = {c["capability_id"] for c in caps}

    # Validate dependency names exist.
    for dep in DEPENDENCY_NAMES:
        if dep not in ids:
            print(f"ERROR: dependency {dep} not in ledger")
            return 2

    if C27_RECORD["capability_id"] in ids:
        print("record already present; skipping")
        return 0

    caps.append(C27_RECORD)
    data["capabilities"] = caps
    LEDGER_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    print(f"added REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY; ledger now {len(caps)} records")
    return 0


if __name__ == "__main__":
    sys.exit(main())
