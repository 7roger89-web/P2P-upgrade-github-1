#!/usr/bin/env python3
"""C27 governance update: host-by-host BLOCKED verdict + roadmap item +
provenance entry. Honesty rules: no fabricated PASS records; no candidate
record (candidate fabrication forbidden for BLOCKED goals). Idempotent.
"""
from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GOVERN_PATH = ROOT / "governance" / "development-control.json"


def main() -> int:
    change_id = "P2P-C27-BLOCKED-LIVE-HOST-EVIDENCE-UNAVAILABLE"
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    data = json.loads(GOVERN_PATH.read_text(encoding="utf-8"))

    prov = data.setdefault("provenance_log", [])
    if any(e.get("change_id") == change_id for e in prov):
        print(f"provenance entry {change_id} already present; skipping")
    else:
        prov.append({
            "change_id": change_id,
            "changed_at": now,
            "changed_by": "manus-agent",
            "change_type": "GOAL_C27_BLOCKED",
            "what_changed": (
                "C27 Real Host Execution Certification concluded BLOCKED / "
                "LIVE_HOST_EVIDENCE_UNAVAILABLE after host-by-host discovery. "
                "Codex CLI 0.147.0 installed but unreachable (api.openai.com 401; "
                "env OPENAI_API_KEY is a Manus proxy key, not accepted by the Responses "
                "API; default/never-approval/danger-sandbox/--local-provider variants "
                "all failed pre-model-contact, mutation KNOWN_NONE). Claude Code, Gemini "
                "CLI, Cursor ACP, GitHub Copilot CLI not installed. Manus API connector "
                "not configured in this session. Certification machinery "
                "(scripts/p2p_live_certification.py + LH1-LH35) delivered as the "
                "certified pathway; HOST_LIVE_EXECUTION_CERTIFICATION remains UNKNOWN."
            ),
            "why": (
                "C26 delta standard + honesty rule: never fabricate a live PASS; "
                "block and record evidence when no real host is reachable."
            ),
            "evidence_refs": [
                "P2P-C27 terminal report (docs/p2p-development/reports/)",
                "codex doctor health summary (auth env, 401 evidence)",
                "probe attempts 1-4 evidence (E27-PROBE, session ids, request ids)",
            ],
        })

    roadmap = data.setdefault("roadmap", {})
    items = roadmap.setdefault("items", [])
    if not any(i.get("id") == "C27" for i in items):
        items.append({
            "id": "C27",
            "title": "Real Host Execution Certification",
            "status": "BLOCKED",
            "notes": (
                "BLOCKED: LIVE_HOST_EVIDENCE_UNAVAILABLE. Host-by-host: Codex CLI 0.147.0 "
                "installed but 401 on api.openai.com (no real OpenAI key); Claude Code / "
                "Gemini CLI / Cursor ACP / Copilot CLI absent; Manus API connector "
                "unconfigured. C26 remains the active goal (CANDIDATE_UNPROMOTED)."
            ),
            "evidence_ref": "docs/p2p-development/reports/P2P-C27-terminal-report.md",
        })
    # Keep C26 as the active development goal; C27 is the likely next goal, blocked.
    roadmap["current"] = {"id": "C26", "status": "DONE"}
    roadmap["likely_next"] = {"id": "C27", "status": "BLOCKED"}

    GOVERN_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=1, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    print("governance updated (C27 BLOCKED roadmap item; C26 remains current)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
