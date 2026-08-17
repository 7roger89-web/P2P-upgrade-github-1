#!/usr/bin/env python3
"""Regenerate the derived C30 sections of current-roadmap.md (idempotent).

Sections touched:
- §3 header line (record count/families)
- §3 family table (regenerated from ledger)
- new §3e. C30 composable execution target foundation (foundation record + honest gaps)
- §5 recommended next goals: insert C31+ ordering after the C27/C28 block
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ROADMAP = ROOT / "docs/p2p-development/current-roadmap.md"
LEDGER = ROOT / "docs/p2p-development/capability-ledger/capability-index.json"

data = json.loads(LEDGER.read_text(encoding="utf-8"))
caps = data["capabilities"]
print(f"ledger records: {len(caps)}, families: {len(data['families'])}")

text = ROADMAP.read_text(encoding="utf-8")
lines = text.split("\n")
out = []
i = 0
n = len(lines)

FAMILY_LABEL = {
    "TRUTH_AND_GOVERNANCE": "Truth & Governance",
    "DURABLE_PROJECT_INTELLIGENCE": "Durable Project Intelligence",
    "CONTEXT_AND_KNOWLEDGE": "Context & Knowledge",
    "SKILL_AND_LEARNING": "Skill & Learning",
    "EXECUTION_AND_ORCHESTRATION": "Execution & Orchestration",
    "DESIGN_AND_PRODUCT_INTELLIGENCE": "Design & Product Intelligence",
    "MULTI_AI_INTEROPERABILITY": "Multi-AI Interoperability",
    "ROUTING_AND_COGNITIVE_ECONOMY": "Routing & Cognitive Economy",
    "VERIFICATION_AND_EVALUATION": "Verification & Evaluation",
    "RECOVERY_AND_CONTINUATION": "Recovery & Continuation",
    "BEGINNER_LIFECYCLE": "Beginner Lifecycle",
    "OUTCOME_LEARNING": "Outcome Learning",
}

from collections import Counter
counts = Counter(FAMILY_LABEL[c["family"]] for c in caps)
statuses = {}
for fam in set(c["family"] for c in caps):
    lbl = FAMILY_LABEL[fam]
    fam_caps = [c for c in caps if c["family"] == fam]
    top = [st for st, _ in Counter(c["status"] for c in fam_caps).most_common(2)]
    statuses[lbl] = " + ".join(top)

order = ["Truth & Governance", "Durable Project Intelligence", "Context & Knowledge",
         "Skill & Learning", "Execution & Orchestration", "Design & Product Intelligence",
         "Multi-AI Interoperability", "Routing & Cognitive Economy",
         "Verification & Evaluation", "Recovery & Continuation", "Beginner Lifecycle",
         "Outcome Learning"]

def rewrite_family_section() -> list[str]:
    rows = ["Counts per family in `capability-index.json` at generation time "
            f"({len(caps)} records, {len(data['families'])} families):",
            "| Family | Count | Dominant statuses |",
            "| --- | --- | --- |"]
    for fam in order:
        rows.append(f"| {fam} | {counts.get(fam, 0)} | {statuses.get(fam, 'mix')} |")
    rows.append("Status vocabulary used by the ledger: "
                "`VERIFIED_IMPLEMENTED`, `FOUNDATION_READY`, `PARTIAL`, `PLANNED`, "
                "`DEFERRED`, `REJECTED`, `OBSOLETE`, `UNKNOWN`.")
    return rows

# State machine
mode = None  # 'count' or 'family_table'
new_text = []
added_3e = False
skipped_family_table = False

i = 0
while i < n:
    line = lines[i]

    # Header count line
    if line.startswith("Counts per family in `capability-index.json`"):
        new_text.extend(rewrite_family_section())
        i += 1
        continue

    # Family table (drop old rows until 'Status vocabulary' line)
    if line.startswith("| Family | Count | Dominant statuses |"):
        # skip until Status vocabulary line consumed
        j = i
        while j < n and not lines[j].startswith("Status vocabulary used by the ledger"):
            j += 1
        if j < n:
            # 'Status vocabulary' line retained at end of rewrite; skip whole block
            i = j + 1
            continue
        # no vocabulary line: just rewrite and continue below
        new_text.extend(rewrite_family_section())
        i += 1
        continue

    # Insert §3e after the ### 3d. block (before ## 5.)
    if line.startswith("## 5. Recommended next goals") and not added_3e:
        new_text.append("### 3e. C30 composable execution target foundation (2026-08-17)")
        new_text.append(
            "C30 delivered the **provider-neutral, deterministic composable execution "
            "target foundation** — `scripts/p2p_execution_target.py` — with 60 passing "
            "tests (`tests/test_p2p_execution_target.py` ET1..ET60) and a durable "
            "research intake artifact "
            "(`docs/p2p-development/research/execution-target-pattern-research.md`, "
            "nine source repositories, patterns A\u2013O, no code copied). The module "
            "models execution as an honest composition of a harness, a provider, a "
            "model, a protocol, a toolset, a workspace, an environment, auth "
            "(harness and provider kept separate), and a permission envelope; "
            "`UNKNOWN` and stale evidence fail closed, protocol compatibility is "
            "never certification, permission composition never widens, and the "
            "registry enumerates but never routes. Honest gaps are durably recorded: "
            "no router, no autopilot, no background autonomy, no real execution, no "
            "second executor, and no secrets stored. Terminal state: **PASS "
            "(foundation)**, candidate UNPROMOTED per the C29 deterministic policy.")
        new_text.append("")
        added_3e = True

    # Rewrite recommended next goals section ordering
    if line.startswith("2. **C30 — Live delegation and parallel execution certification.**"):
        # Replace ordering: C30 is now DONE-foundation; next are C31/C32/C33/C34
        new_text.append(
            "2. **C31 — Cross-host continuation and round-trip binding.** Depends on "
            "C27/C28. Upgrades `CROSS_HOST_CONTINUATION_CONTRACT`, "
            "`ROUND_TRIP_BINDING`, `CROSS_HOST_RESUME`.")
        new_text.append(
            "3. **C32 — Beginner control center view layer.** Depends on nothing new; "
            "beginner-friendly dashboard for status/decisions (control center, health "
            "views, decision inbox).")
        new_text.append(
            "4. **C33 — Context/session/cache efficiency implementation (first batch).** "
            "Owner-accepted intakes (\u00a73a); pick the batch with the strongest "
            "beginner value and dependency readiness, with one primary objective per "
            "goal contract.")
        new_text.append(
            "5. **Roadmap hygiene (ongoing):** reconcile the recovered C23/C24 "
            "packages' internals against the original implementations, and search for "
            "the C22 package in other copies the owner may hold, before claiming "
            "progression beyond recovery-level provenance.")
        # skip remaining old numbered lines until next section
        i += 1
        while i < n and (lines[i].startswith(("3. **", "4. **", "5. **", "6. **"))) \
                and not lines[i].startswith("6. **Regeneration"):
            i += 1
        continue

    new_text.append(line)
    i += 1

text = "\n".join(new_text)
ROADMAP.write_text(text, encoding="utf-8")
print("roadmap regenerated; 3e added:", added_3e)
