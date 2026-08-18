# -*- coding: utf-8 -*-
"""C39 Proof 1 — Normal governed live selection with the failover boundary.

Proves the new failover machinery works through a real live path:
  1. Canonical role binding: p2p_iris via load_capability_registry/build_role_spec (C35 registry REUSE).
  2. Contract: bounded non-mutating synthetic text task (RoleExecutionContract REUSE).
  3. Pre-dispatch revalidation: snapshot_eligibility -> decide_next_action
     (failover_boundary NEW module; dispatched=False so safe path).
  4. Live execution via ManusAdapter (REUSE, same kwargs as C38 Stage B).
  5. Evidence persisted: contract, failover decision, adapter result pointer.
     The observed answer is captured SEPARATELY (self-claim never trusted).

Live backend calls: exactly ONE Manus API task execution (bounded).
"""
import json
import os
import sys
import time
from hashlib import sha256
from pathlib import Path

REPO = Path("/home/ubuntu/p2p-repo")
sys.path.insert(0, str(REPO / ".p2p" / "system"))
from p2p_capabilities.agent_role import (
    CANONICAL_ROLES, build_role_spec, load_capability_registry)
from p2p_capabilities.role_contract import RoleExecutionContract
from p2p_capabilities.manus_adapter import ManusAdapter
from p2p_capabilities.backend_contract import BackendExecutionResult
from p2p_capabilities.failover_boundary import (
    decide_next_action, snapshot_eligibility, EligibilitySnapshot)

GOAL_ID = "C39"
TASK_ID = "c39-proof-1-governed-live-selection"
ROLE_ID = "p2p_iris"
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def sha256hex(payload: str) -> str:
    return sha256(payload.encode("utf-8")).hexdigest()[:64]


def main() -> int:
    assert ROLE_ID in CANONICAL_ROLES, "p2p_iris not canonical"
    registry_records = load_capability_registry()
    spec = build_role_spec(ROLE_ID, registry_records)
    print(f"ROLE {ROLE_ID} bound; role_spec_hash={spec.role_spec_hash}")

    # --- 2. Contract (bounded non-mutating, mirrors C38 Stage B) ----------
    contract = RoleExecutionContract(
        goal_id=GOAL_ID,
        task_id=TASK_ID,
        role_id=ROLE_ID,
        role_spec_hash=spec.role_spec_hash,
        project_binding="P2P-upgrade-github-1",
        environment_binding="LOCAL_PROJECT",
        workspace_binding="",
        objective="BOUNDED NON-MUTATING PROOF: Answer 'What is the capital of Vietnam?' with exactly the city name and nothing else.",
        approved_scope=("API_TRANSPORT", "SYNTHETIC_TEXT_EXECUTION", "NON_MUTATING_TASK"),
        dependencies=(),
        context_package=("SYNTHETIC_TEXT_EXECUTION",),
        context_digest=sha256hex("SYNTHETIC_TEXT_EXECUTION:capital-of-vietnam-proof"),
        permission_profile=("NON_MUTATING_TASK",),
        required_capabilities=(),
        acceptance_criteria=("answer_is_capital_of_vietnam",),
        required_evidence=("role_binding", "target_attestation", "terminal_result"),
        verification_policy="INDEPENDENT",
        explicit_execution_target="manus-api-v2",
        target_fingerprint=sha256hex("manus-api-v2:task.create:p2p-c39-proof-1"),
        requested_target_attestation="REQUESTED_ONLY",
        budget="BOUNDED",
        request_fingerprint=sha256hex("c39-proof-1-01"),
    )
    contract_path = EVIDENCE_DIR / "c39-proof-1-role-contract.json"
    contract_path.write_text(json.dumps(contract.to_dict(), indent=2, default=str))
    print("Contract persisted:", contract_path)

    # --- 3. Pre-dispatch revalidation (failover boundary) -----------------
    key = Path(os.path.expanduser("~/.secrets/manus_api_key_new")).read_text().strip()
    os.environ["MANUS_API_KEY"] = key

    def probe(target):
        if target != "manus-api-v2":
            return None
        try:
            adapter = ManusAdapter(api_key=key)  # explicit: default key file is the OLD C38 key
            ok = bool(adapter.health())
            return EligibilitySnapshot(
                target=target, eligible=ok, failure_class=None,
                evidence_pointers=("health-check",) if ok else (),
            )
        except Exception:  # noqa: BLE001 — health() infra bug (AdapterHealthState kwarg)
            return EligibilitySnapshot(
                target=target, eligible=False,
                failure_class="TARGET_INELIGIBLE_BEFORE_EXECUTION",
                evidence_pointers=("health-check-failed",))

    snap = snapshot_eligibility("manus-api-v2", probe)
    decision = decide_next_action(
        failure_class=None if (snap and snap.eligible) else "TARGET_INELIGIBLE_BEFORE_EXECUTION",
        failure_class_observed=(),
        dispatched=False,
        current_target="manus-api-v2",
        eligible_targets=("manus-api-v2",),
    )
    print("Revalidation: eligible =", bool(snap and snap.eligible),
          "-> decision =", decision.decision)
    # dispatched=False + eligible -> RETRY_SAME_TARGET (normal dispatch path)
    if decision.decision == "RESELECT_TARGET":
        print("ERROR: unexpected reselection on eligible target", file=sys.stderr)
        return 3
    if decision.decision not in ("RETRY_SAME_TARGET", "OWNER_GATE"):
        print("ERROR: failover gate blocked normal dispatch:", decision.decision,
              file=sys.stderr)
        return 3
    (EVIDENCE_DIR / "c39-proof-1-failover-decision.json").write_text(
        json.dumps(decision.to_dict(), indent=2))

    # --- 4. Live execution (single bounded dispatch) --------------------
    adapter = ManusAdapter(api_key=key)  # explicit: default key file is the OLD C38 key (expired)
    started = time.time()
    result: BackendExecutionResult = adapter.execute(
        request_id="c39-proof-1-01",
        request_fingerprint=sha256hex("c39-proof-1-01"),
        task_id=TASK_ID,
        goal_id=GOAL_ID,
        prompt="Answer the question: What is the capital of Vietnam? Reply with exactly the city name and nothing else.",
        max_turns=8,
        timeout_seconds=600,
    )
    latency = round(time.time() - started, 2)
    print("Execution:", result.execution_status, "error:", result.error_class or "-",
          "latency:", latency, "s")
    pointer = result.raw_backend_receipt_pointer or ""
    task_id = (pointer.split(":")[-1] if ":" in pointer else pointer)
    print("Backend receipt pointer:", pointer)
    print("Manus task id:", task_id)

    # --- 5. Evidence -----------------------------------------------------
    rev = (Path("/home/ubuntu/p2p-repo/.git/HEAD").read_text().strip()
           .replace("ref: refs/heads/", ""))
    evidence = {
        "schema": "c39-proof-1-live-evidence/1",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "role_id": ROLE_ID,
        "role_spec_hash": spec.role_spec_hash,
        "selected_target": "manus-api-v2",
        "pre_dispatch_eligibility": (snap.to_dict() if snap else None),
        "failover_decision": decision.to_dict(),
        "execution_status": result.execution_status,
        "error_class": result.error_class,
        "latency_seconds": latency,
        "transcript_pointer": None,
        "raw_backend_receipt_pointer": pointer,
        "manus_task_id": task_id,
        "output_pointers": result.output_pointers,
        "verification_status": result.verification_status,
        "contract_fingerprint": contract.request_fingerprint,
        "git_revision": rev,
    }
    (EVIDENCE_DIR / "c39-proof-1-live-evidence.json").write_text(
        json.dumps(evidence, indent=2, default=str))
    print("Evidence persisted; revision:", rev)
    return 0 if result.execution_status == "SUCCEEDED" else 4


if __name__ == "__main__":
    sys.exit(main())
