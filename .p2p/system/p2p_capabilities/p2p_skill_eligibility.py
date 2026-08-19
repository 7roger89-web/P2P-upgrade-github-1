"""FRAMEWORK-01 skill eligibility for the operating loop.

NO adaptive skill selection, NO learned ranking, NO provider preference.
Eligibility is a deterministic, evidence-driven filter over the canonical
capability registry:

    SKILL_ELIGIBLE = canonical capability metadata
                     AND required readiness states
                     AND (evidence contract present OR evidence NOT_REQUIRED)

The loop consumes this read-only eligibility set; selection remains the
Owner-governed goal/task plan. An activation receipt is written once per
eligible skill only when the loop actually activates it (minimal, not a
selection trace of rejected skills).

Honesty requirement (FW01 acceptance bar): this module records the
provenance level of each eligibility decision exactly
(IMPLEMENTED_VERIFIED / FOUNDATION_READY / PARTIAL / NOT_IMPLEMENTED),
so no eligibility claim is ever stated beyond available evidence.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

SKILL_ELIGIBILITY_SCHEMA = "p2p-skill-eligibility-fw01/1"
ACTIVATION_RECEIPT_SCHEMA = "p2p-skill-activation-receipt-fw01/1"

# Readiness states the registry carries (capability-ledger vocabulary).
IMPLEMENTED_STATES = ("VERIFIED_IMPLEMENTED", "IMPLEMENTED")
FOUNDATION_STATES = ("FOUNDATION_READY",)
PARTIAL_STATES = ("PARTIAL_IMPLEMENTED", "PARTIAL")


def _load_registry(registry_path: Path) -> list[dict]:
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    items = payload.get("capabilities")
    if not isinstance(items, list):
        raise ValueError("CAPABILITY_REGISTRY_INVALID")
    return [item for item in items if isinstance(item, dict)
            and item.get("CAPABILITY_ID")]


def readiness_level(state: Any) -> str:
    """Map a registry readiness state to a provenance level. Unknown or
    absent states are never upgraded: they return NOT_IMPLEMENTED."""
    if state in IMPLEMENTED_STATES:
        return "IMPLEMENTED_VERIFIED"
    if state in FOUNDATION_STATES:
        return "FOUNDATION_READY"
    if state in PARTIAL_STATES:
        return "PARTIAL"
    return "NOT_IMPLEMENTED"


def skill_eligibility_set(registry_path: Path,
                          capability_ids: Iterable[str] | None = None
                          ) -> list[dict[str, Any]]:
    """Deterministic eligibility set. capability_ids=None => full registry.
    Order is stable (registry order), never influence-ranked."""
    items = _load_registry(registry_path)
    if capability_ids is not None:
        wanted = set(str(i) for i in capability_ids)
        items = [i for i in items if str(i["CAPABILITY_ID"]) in wanted]
    result: list[dict[str, Any]] = []
    for item in items:
        cap_id = str(item["CAPABILITY_ID"])
        state = str(item.get("READINESS_STATE") or item.get("READINESS") or "UNKNOWN")
        level = readiness_level(state)
        contract = item.get("EVIDENCE_CONTRACT")
        has_contract = bool(contract)
        eligible = (level in ("IMPLEMENTED_VERIFIED", "FOUNDATION_READY")
                    and has_contract)
        result.append({
            "schema": SKILL_ELIGIBILITY_SCHEMA,
            "capability_id": cap_id,
            "readiness_state": state,
            "provenance_level": level,
            "evidence_contract_present": has_contract,
            "eligible": eligible,
            "computed_utc": datetime.now(timezone.utc).isoformat(),
        })
    return result


class ActivationReceiptStore:
    """Append-only activation receipts: written only when the loop
    activates a skill. No trace of rejected skills is ever stored (Owner
    contract: transcript != state, and no shadow ranking artifacts)."""

    def __init__(self, store_path: Path) -> None:
        self.store_path = store_path
        self.store_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, goal_id: str, task_id: str, capability_id: str,
               activation_ref: str) -> dict[str, Any]:
        receipt = {
            "schema": ACTIVATION_RECEIPT_SCHEMA,
            "receipt_id": hashlib.sha256(
                json.dumps({"goal_id": goal_id, "task_id": task_id,
                            "capability_id": capability_id,
                            "activation_ref": activation_ref,
                            "issued_at": datetime.now(timezone.utc).isoformat()},
                           sort_keys=True).encode()).hexdigest()[:64],
            "goal_id": goal_id,
            "task_id": task_id,
            "capability_id": capability_id,
            "activation_ref": activation_ref,
            "issued_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.store_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(receipt, ensure_ascii=False,
                                    sort_keys=True) + "\n")
        return receipt

    def load(self) -> list[dict[str, Any]]:
        if not self.store_path.exists():
            return []
        receipts = []
        for line in self.store_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            receipts.append(json.loads(line))
        return receipts


def main(argv: list[str] | None = None) -> int:
    """CLI: python3 p2p_skill_eligibility.py eligible <registry> [cap1,cap2,...]"""
    import sys
    args = (argv or sys.argv[1:])
    if not args or args[0] != "eligible":
        print("usage: p2p_skill_eligibility.py eligible <capabilities.json> "
              "[cap_id, ...]", file=sys.stderr)
        return 2
    registry = Path(args[1])
    ids = args[2].split(",") if len(args) > 2 else None
    for entry in skill_eligibility_set(registry, ids):
        print(json.dumps(entry, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
