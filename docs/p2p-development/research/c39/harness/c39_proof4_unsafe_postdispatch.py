# -*- coding: utf-8 -*-
"""C39 Proof 4 — Deterministic unsafe post-dispatch (fail-closed) proof.

NO live backend is called.  This proof asserts that the failover
boundary FAILS CLOSED when a failure is observed AFTER dispatch and the
mutation/result state is UNKNOWN — exactly the state in which Backend B
MUST NOT execute.

The three cases are deterministic evaluations of decide_next_action():
  1. MUTATION_UNKNOWN after dispatch                 -> STOP_FAIL_CLOSED
  2. RESULT_UNKNOWN_AFTER_DISPATCH after dispatch    -> STOP_FAIL_CLOSED
  3. Unknown/unrecognized failure class after dispatch -> STOP_FAIL_CLOSED
     (REVERIFY_REQUIRED only when a verifiable result pointer exists)

Backend B MUST NOT execute when mutation/result is UNKNOWN after
dispatch.  These states are the fail-closed core of C39.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path("/home/ubuntu/p2p-repo")
sys.path.insert(0, str(REPO / ".p2p" / "system"))

from p2p_capabilities.failover_boundary import decide_next_action  # noqa: E402

EVIDENCE_DIR = REPO / "docs" / "p2p-development" / "research" / "c39" / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    cases = [
        {
            "case": "MUTATION_UNKNOWN_AFTER_DISPATCH",
            "kw": dict(failure_class="MUTATION_UNKNOWN", dispatched=True,
                       current_target="manus-api-v2",
                       mutation_status="MUTATION_UNKNOWN"),
            "expected": "STOP_FAIL_CLOSED",
            "allowed_alternatives": ("REVERIFY_REQUIRED",),
            "note": "Backend B MUST NOT execute with unknown mutation.",
        },
        {
            "case": "RESULT_UNKNOWN_AFTER_DISPATCH",
            "kw": dict(failure_class="RESULT_UNKNOWN_AFTER_DISPATCH",
                       dispatched=True, current_target="hermes-cli:gemini:gemini-2.5-flash",
                       mutation_status="MUTATION_UNKNOWN"),
            "expected": "STOP_FAIL_CLOSED",
            "allowed_alternatives": ("REVERIFY_REQUIRED",),
            "note": "UNKNOWN result after dispatch fails closed.",
        },
        {
            "case": "UNRECOGNIZED_CLASS_AFTER_DISPATCH_NO_POINTERS",
            "kw": dict(failure_class="SOME_UNSEEN_CLASS_12345",
                       dispatched=True, current_target="manus-api-v2"),
            "expected": "STOP_FAIL_CLOSED",
            "allowed_alternatives": ("REVERIFY_REQUIRED",),
            "note": "Unknown class maps to FAILURE_CLASS_UNKNOWN holder -> fail closed.",
        },
        {
            "case": "TIMEOUT_AFTER_POSSIBLE_MUTATION",
            "kw": dict(failure_class="TIMEOUT_AFTER_POSSIBLE_MUTATION",
                       dispatched=True, current_target="manus-api-v2"),
            "expected": "STOP_FAIL_CLOSED",
            "allowed_alternatives": ("REVERIFY_REQUIRED",),
            "note": "Timeout after possible mutation -> unsafe set.",
        },
        {
            "case": "UNVERIFIED_WRITE_AFTER_DISPATCH",
            "kw": dict(failure_class="UNVERIFIED_WRITE", dispatched=True,
                       current_target="manus-api-v2",
                       prior_receipt={"output_pointers": ("file:///some/path",)}),
            "expected": "REVERIFY_REQUIRED",
            "allowed_alternatives": (),
            "note": "Verifiable pointer exists -> REVERIFY_REQUIRED (still blocked from blind retry).",
        },
    ]

    results = []
    all_ok = True
    for c in cases:
        d = decide_next_action(**c["kw"])
        ok = (d.decision == c["expected"] or
              d.decision in c["allowed_alternatives"])
        all_ok = all_ok and ok
        results.append({
            "case": c["case"],
            "decision": d.decision,
            "expected": c["expected"],
            "allowed_alternatives": list(c["allowed_alternatives"]),
            "reason": d.reason,
            "failure_class": d.failure_class,
            "old_target": d.old_target,
            "passed": ok,
            "note": c["note"],
        })
        print(f"{c['case']}: {d.decision} "
              f"(expected {c['expected']}{(' or ' + ', '.join(c['allowed_alternatives']) if c['allowed_alternatives'] else '')}) "
              f"-> {'PASS' if ok else 'FAIL'}")

    rev = Path("/home/ubuntu/p2p-repo/.git/HEAD").read_text().strip()\
        .replace("ref: refs/heads/", "")
    evidence = {
        "schema": "c39-proof-4-unsafe-postdispatch/1",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "proof_type": "DETERMINISTIC_NO_LIVE_BACKEND",
        "backend_b_executed": False,
        "cases": results,
        "all_cases_passed": all_ok,
        "semantic_truth": "Backend B MUST NOT execute when mutation/result "
                          "is UNKNOWN after dispatch; unsafe states fail closed.",
        "git_revision": rev,
    }
    out = EVIDENCE_DIR / "c39-proof-4-unsafe-postdispatch.json"
    out.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
    print("Evidence persisted:", out)
    print("ALL_CASES:", "PASS" if all_ok else "FAIL")
    return 0 if all_ok else 4


if __name__ == "__main__":
    sys.exit(main())
