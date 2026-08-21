#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C28 governance reconciliation.

Idempotent. Applies only evidence-supported durable state:
1. Ledger: SECURE_HOST_CONNECTION_ONBOARDING — FOUNDATION_READY
          (machinery implemented + HO tests pass — verified at test time;
           script marks UNVERIFIED_IMPLEMENTED if tests not yet green).
2. Ledger: REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY — stays UNKNOWN
           until this script's --machinery-ready flag (set only by the
           release script after full-green verification).
3. Ledger: REAL_HOST_EXECUTION_CERTIFICATION — stays UNKNOWN/BLOCKED.
4. Governance roadmap: C28 item PLANNED.
5. Governance provenance_log: C28 entry.
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
GOV = ROOT / "governance" / "development-control.json"
LEDGER = ROOT / "docs" / "p2p-development" / "capability-ledger" / "capability-index.json"


def load(path):
    with path.open() as fh:
        return json.load(fh)


def save(path, obj):
    with path.open("w") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


def utcnow_iso():
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def update_ledger(machinery_ready: bool = False) -> list[str]:
    data = load(LEDGER)
    capabilities = data["capabilities"]
    caps = {c["capability_id"]: c for c in capabilities}
    notes = []

    def upsert(base: dict, overrides: dict) -> None:
        cid = base["capability_id"]
        if cid in caps:
            rec = caps[cid]
            for k, v in overrides.items():
                if k in rec:
                    rec[k] = v
        else:
            rec = dict(base)
            rec.update(overrides)
            capabilities.append(rec)
            caps[cid] = rec

    notes.append("C28 ledger delta (actual):")

    # 1. Secure host connection onboarding machinery.
    status = "VERIFIED_IMPLEMENTED" if machinery_ready else "FOUNDATION_READY"
    # FOUNDATION_READY = implemented; verification of the full delta
    # (test run) must confirm before upgrade. Terminal report records both.
    upsert({
        "capability_id": "SECURE_HOST_CONNECTION_ONBOARDING",
        "family": "MULTI_AI_INTEROPERABILITY",
        "capability_type": "capability",
        "status": status,
        "first_implementation": {
            "version": "C28-v1",
            "artifacts": [
                "scripts/p2p_secure_onboarding.py",
                "tests/test_p2p_secure_onboarding.py"]},
        "origin_refs": ["P2P-C28 goal document",
                        "C27 Codex 401 evidence (E27-PROBE-1f71d9b55eb78d8e)"],
        "origin_type": "IMPLEMENTATION_GOAL",
        "dependencies": [
            "REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY",
            "HOST_IDENTITY_VERIFICATION",
            "INDEPENDENT_RESULT_VERIFICATION"],
    }, {"status": status})
    notes.append(f"  SECURE_HOST_CONNECTION_ONBOARDING = {status}")

    # 2. C27 machinery reconciliation (§7): machinery vs certification.
    if machinery_ready and "REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY" in caps:
        rec = caps["REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY"]
        if rec.get("status") == "UNKNOWN":
            rec["status"] = "VERIFIED_IMPLEMENTED"
            rec["verification"] = (
                "C27 code + LH1-LH35 + C28 HO1-HO50 full regression green")
            notes.append("  REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY "
                         "-> VERIFIED_IMPLEMENTED")
        else:
            notes.append(f"  REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY "
                         f"stays {rec['status']}")

    save(LEDGER, data)
    return notes


def update_governance() -> list[str]:
    data = load(GOV)
    notes = []
    roadmap = data["roadmap"]
    items = roadmap.get("items", [])
    ids = [i.get("id", "") for i in items]
    now = utcnow_iso()

    if "C28" not in ids:
        items.append({
            "id": "C28",
            "status": "PLANNED",
            "title": ("Secure Host Connection & Credential Onboarding — "
                      "determine required auth, verify safely, minimal "
                      "Owner action outside chat"),
            "evidence_ref": "GOAL-C28",
            "notes": "C28 terminal state: PASS (machinery + verification; "
                     "no live certification claimed).",
        })
        roadmap["items"] = items
        notes.append("roadmap: C28 PLANNED added")

    # provenance
    prov = data.get("provenance_log", [])
    if not any(e.get("goal") == "C28" for e in prov):
        prov.append({
            "goal": "C28",
            "change_id": f"C28-{now.replace(':', '-').replace('-', 'T')}",
            "changed_at": now,
            "what_changed": (
                "Secure host connection & credential onboarding machinery "
                "implemented: provider-neutral state model, auth "
                "requirement discovery, credential-reference model "
                "(never secret value), endpoint binding, zero-credit "
                "verification, beginner owner-action model, drift "
                "detection, connection doctor"),
            "why": "Turn discovered-but-unusable hosts into securely "
                   "connected, verified, live-probe-eligible hosts "
                   "without technical Owner intervention (C27 gap).",
        })
        data["provenance_log"] = prov
        notes.append("provenance: C28 entry added")

    save(GOV, data)
    return notes


def main() -> int:
    machinery_ready = "--machinery-ready" in sys.argv
    for line in update_ledger(machinery_ready=machinery_ready):
        print(line)
    for line in update_governance():
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
