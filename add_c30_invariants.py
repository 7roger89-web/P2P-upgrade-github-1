#!/usr/bin/env python3
"""Add only enduring C30 invariants to the machine-readable list (idempotent).

These are derived from the C30 instruction §9 (charter reconciliation):
only enduring, principle-level invariants — no implementation claims.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GOV = ROOT / "governance" / "development-control.json"

NEW = [
    dict(
        id="component-is-not-interchangeable",
        statement=("Harness, provider, model, protocol, and workspace are distinct "
                   "composition dimensions; the identity of one is never a proxy for "
                   "the capability or auth state of another."),
        authority_refs=["scripts/p2p_execution_target.py",
                        "docs/p2p-development/research/execution-target-pattern-research.md"],
    ),
    dict(
        id="compatibility-is-not-certification",
        statement=("Transport or API compatibility never implies behavioral "
                   "certification; certification requires the live-certification "
                   "path, never a declaration."),
        authority_refs=["scripts/p2p_execution_target.py"],
    ),
    dict(
        id="permission-envelope-never-widens",
        statement=("Composing permission envelopes can only narrow or preserve the "
                   "allowed set; composition never produces a permission neither "
                   "side allowed."),
        authority_refs=["scripts/p2p_execution_target.py"],
    ),
    dict(
        id="drift-fail-closed",
        statement=("Unknown contract or quiesce states fail closed for destructive "
                   "lifecycle changes; an old certification never silently remains "
                   "current."),
        authority_refs=["scripts/p2p_execution_target.py", "governance/drift-policy.json"],
    ),
    dict(
        id="registry-is-not-router",
        statement=("A neutral execution backend registry enumerates; it never "
                   "ranks, selects, routes, or auto-falls-back for a task."),
        authority_refs=["scripts/p2p_execution_target.py"],
    ),
]


def main() -> None:
    data = json.loads(GOV.read_text(encoding="utf-8"))
    existing = {i["id"] for i in data["architectural_invariants"]}
    added = []
    for inv in NEW:
        if inv["id"] not in existing:
            data["architectural_invariants"].append(inv)
            existing.add(inv["id"])
            added.append(inv["id"])
    GOV.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"added {len(added)} invariants: {added} "
          f"(total {len(data['architectural_invariants'])})")


if __name__ == "__main__":
    main()
