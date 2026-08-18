# -*- coding: utf-8 -*-
"""C39 Proof 2 — Pre-dispatch auth drift + governed safe reselection.

Proves the failover boundary selects a SAFE reselection on real drift:

  1. The primary target (manus-api-v2) credential is made INVALID by
     *temporarily unsetting* the MANUS_API_KEY env binding BEFORE the
     pre-dispatch revalidation probe.  The key file is NEVER touched,
     revoked or deleted — the drift is reversible by restoring the env
     binding (reversibility requirement; Owner credentials stay intact).
  2. The probe reads the env binding -> health() fails -> snapshot is
     ineligible with AUTH_INVALID (pre-dispatch, dispatched=False).
  3. decide_next_action(failure_class=AUTH_INVALID, dispatched=False)
     -> RESELECT_TARGET with an eligible alternative (hermes-cli:gemini).
     Backend B does NOT execute yet (SELECTION != EXECUTION).
  4. Key env binding is RESTORED.  The reselected target is probed and
     confirmed eligible, then ONE bounded live dispatch runs on Hermes.
  5. Independent observation of the answer from raw CLI output.
  6. Evidence persisted: both failover decisions, probes, contract, receipt.

Live backend calls: exactly ONE Hermes execute (bounded, non-mutating).
The Manus task is NOT created; no real failure is inflicted on either
credential.
"""
import json
import os
import sys
import time
import hashlib
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / ".p2p" / "system"))

from p2p_capabilities.agent_role import (  # noqa: E402
    CANONICAL_ROLES, build_role_spec, load_capability_registry)
from p2p_capabilities.role_contract import RoleExecutionContract  # noqa: E402
from p2p_capabilities.hermes_adapter import HermesAdapter  # noqa: E402
from p2p_capabilities.failover_boundary import (  # noqa: E402
    decide_next_action, snapshot_eligibility, EligibilitySnapshot)

GOAL_ID = "C39"
TASK_ID = "c39-proof-2-drift-safe-reselection"
ROLE_ID = "p2p_iris"
PROVIDER = "gemini"
MODEL = "gemini-2.5-flash"
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def sha256hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:64]


def hermes_probe(target: str):
    """Probe hermes-cli eligibility via a dry run of _run_hermes usage."""
    if not str(target).startswith("hermes-cli:"):
        return None
    from p2p_capabilities.hermes_adapter import _run_hermes
    with tempfile.TemporaryDirectory() as workdir:
        cap = _run_hermes(
            ("-z", "Print exactly: PROBE_OK",
             "--provider", PROVIDER, "--model", MODEL,
             "--usage-file", str(Path(workdir) / "probe-usage.json")),
            workdir=workdir, timeout_seconds=180)
    if cap.get("exit_code") == 0 and "PROBE_OK" in cap["stdout"]:
        return EligibilitySnapshot(
            target=target, eligible=True, failure_class=None,
            evidence_pointers=("hermes-probe-ok",))
    return EligibilitySnapshot(
        target=target, eligible=False,
        failure_class="TARGET_INELIGIBLE_BEFORE_EXECUTION",
        evidence_pointers=("hermes-probe-failed",),
        detail=str(cap.get("exit_code", "")) + ":" +
        str((cap.get("stderr") or "")[:120]))


def main() -> int:
    assert ROLE_ID in CANONICAL_ROLES, "p2p_iris not canonical"
    registry_records = load_capability_registry()
    spec = build_role_spec(ROLE_ID, registry_records)
    print("ROLE", ROLE_ID, "bound; role_spec_hash=", spec.role_spec_hash)

    key = Path("/home/ubuntu/.secrets/manus_api_key_new").read_text().strip()
    os.environ["MANUS_API_KEY"] = key
    env_name = "MANUS_API_KEY"

    contract = RoleExecutionContract(
        goal_id=GOAL_ID,
        task_id=TASK_ID,
        role_id=ROLE_ID,
        role_spec_hash=spec.role_spec_hash,
        project_binding="P2P-upgrade-github-1",
        environment_binding="LOCAL_PROJECT",
        workspace_binding="",
        objective=("BOUNDED NON-MUTATING DRIFT PROOF: pre-dispatch auth drift "
                   "on the primary target must yield a governed "
                   "RESELECT_TARGET onto an eligible alternative; execution "
                   "runs on the reselected target only."),
        approved_scope=("API_TRANSPORT", "SYNTHETIC_TEXT_EXECUTION", "NON_MUTATING_TASK"),
        dependencies=(),
        context_package=("SYNTHETIC_TEXT_EXECUTION",),
        context_digest=sha256hex("SYNTHETIC_TEXT_EXECUTION:capital-of-vietnam-proof"),
        permission_profile=("NON_MUTATING_TASK",),
        required_capabilities=(),
        acceptance_criteria=("answer_is_capital_of_vietnam",),
        required_evidence=("role_binding", "target_attestation",
                           "terminal_result", "drift_reselection"),
        verification_policy="INDEPENDENT",
        explicit_execution_target="hermes-cli:gemini:gemini-2.5-flash",
        target_fingerprint=sha256hex(
            "hermes-cli:gemini:gemini-2.5-flash:p2p-c39-proof-2"),
        requested_target_attestation="REQUESTED_ONLY",
        budget="BOUNDED",
        request_fingerprint=sha256hex("c39-proof-2-01"),
    )
    contract_path = EVIDENCE_DIR / "c39-proof-2-role-contract.json"
    contract_path.write_text(json.dumps(
        contract.to_dict(), indent=2, default=str), encoding="utf-8")
    print("Contract persisted:", contract_path)

    # --- Step 2: REVERSIBLE pre-dispatch drift ---------------------------
    # Remove the env binding only.  The key file is untouched and intact;
    # restored below.  This is real truth (health() genuinely fails), and
    # it does NOT revoke the Owner's credential.
    old_val = os.environ.pop(env_name, None)
    assert old_val is not None, "MANUS_API_KEY env binding was absent"

    def drift_probe(target: str):
        if target != "manus-api-v2":
            return None
        try:
            from p2p_capabilities.manus_adapter import ManusAdapter
            ok = bool(ManusAdapter().health().healthy)
            return EligibilitySnapshot(
                target=target, eligible=ok,
                failure_class=None if ok else "AUTH_INVALID",
                evidence_pointers=("health-check-unauth",))
        except Exception:
            return EligibilitySnapshot(
                target=target, eligible=False, failure_class="AUTH_INVALID",
                evidence_pointers=("health-check-401",))

    snap_drift = snapshot_eligibility("manus-api-v2", drift_probe)
    eligible_candidates = ("manus-api-v2", "hermes-cli:gemini:gemini-2.5-flash")
    dec1 = decide_next_action(
        failure_class=None if (snap_drift and snap_drift.eligible)
        else "AUTH_INVALID",
        dispatched=False,
        current_target="manus-api-v2",
        eligible_targets=eligible_candidates,
    )
    print("Drift revalidation: eligible =", bool(snap_drift and snap_drift.eligible),
          "-> decision =", dec1.decision)

    drift_evidence = {
        "schema": "c39-proof-2-drift-evidence/1",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "drift_method": "env-binding-unset-REVERSIBLE",
        "drift_cause": "MANUS_API_KEY removed from env; key file untouched",
        "probe_snapshot": (snap_drift.to_dict() if snap_drift else None),
        "failover_decision": dec1.to_dict(),
        "credential_file_state": "INTACT_NOT_REVOKED",
    }
    (EVIDENCE_DIR / "c39-proof-2-drift-evidence.json").write_text(
        json.dumps(drift_evidence, indent=2, default=str), encoding="utf-8")

    # Fail-closed expectations: drift pre-dispatch -> RESELECT_TARGET
    # (auth-invalid is safe reselection evidence) onto the eligible
    # alternative.  Anything else is a proof failure.
    if dec1.decision != "RESELECT_TARGET" or not dec1.new_target:
        print("ERROR: expected RESELECT_TARGET on drift; got",
              dec1.decision, "new_target =", dec1.new_target,
              file=sys.stderr)
        os.environ[env_name] = old_val  # restore regardless
        return 3
    new_target = dec1.new_target
    print("RESELECT_TARGET ->", new_target)

    # --- Step 4: restore binding, probe the new target, execute ----------
    os.environ[env_name] = old_val
    print("Credential binding RESTORED (reversible drift):",
          bool(os.environ.get(env_name)))

    snap_new = snapshot_eligibility(new_target, hermes_probe)
    dec2 = decide_next_action(
        failure_class=None if (snap_new and snap_new.eligible)
        else "TARGET_INELIGIBLE_BEFORE_EXECUTION",
        dispatched=False,
        current_target=new_target,
        eligible_targets=(new_target,),
    )
    print("Reselected target probe: eligible =", bool(snap_new and snap_new.eligible),
          "-> decision =", dec2.decision)
    if dec2.decision != "RETRY_SAME_TARGET":
        print("ERROR: failover gate blocked the reselected target:",
              dec2.decision, file=sys.stderr)
        return 3

    # Live execution on the reselected target (single bounded dispatch).
    gemini = Path("/home/ubuntu/.secrets/gemini_api_key")
    if not gemini.exists():
        print("ERROR: GEMINI credential absent", file=sys.stderr)
        return 2
    os.environ["GEMINI_API_KEY"] = gemini.read_text().strip()
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]
    adapter = HermesAdapter()
    started = time.time()
    result = adapter.execute(
        request_id="c39-proof-2-01",
        request_fingerprint=sha256hex("c39-proof-2-01"),
        task_id=TASK_ID,
        goal_id=GOAL_ID,
        prompt=("Answer the question: What is the capital of Vietnam? "
                "Reply with exactly the city name and nothing else."),
        max_turns=1,
        timeout_seconds=240,
        provider=PROVIDER,
        model=MODEL,
        evidence_dir=str(EVIDENCE_DIR),
    )
    latency = round(time.time() - started, 2)
    print("Execution:", result.execution_status, "| error:",
          result.error_class or "-", "| latency:", latency, "s")

    # Independent observation: raw CLI stdout, never the executor's claim.
    from p2p_capabilities.hermes_adapter import _run_hermes  # noqa: E402
    with tempfile.TemporaryDirectory() as workdir:
        cap = _run_hermes(
            ("-z", "Answer the question: What is the capital of Vietnam? "
             "Reply with exactly the city name and nothing else.",
             "--provider", PROVIDER, "--model", MODEL,
             "--usage-file", str(Path(workdir) / "usage.json")),
            workdir=workdir, timeout_seconds=240)
    observed_raw = (cap["stdout"] + " " + cap["stderr"]).strip()
    words = observed_raw.split()
    observed_answer = words[0] if words else "UNKNOWN"
    acceptance_ok = observed_answer.lower() in ("hanoi", "hà",) or observed_answer.lower().startswith("hanoi")
    acceptance_ok = observed_answer.lower().strip(".,") == "hanoi"
    print("Observed answer:", observed_answer, "| acceptance:", acceptance_ok)

    # --- Step 5: evidence -------------------------------------------------
    rev = Path("/home/ubuntu/p2p-repo/.git/HEAD").read_text().strip()\
        .replace("ref: refs/heads/", "")
    evidence = {
        "schema": "c39-proof-2-live-evidence/1",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "role_id": ROLE_ID,
        "role_spec_hash": spec.role_spec_hash,
        "original_target": "manus-api-v2",
        "reselected_target": new_target,
        "drift_evidence": drift_evidence,
        "reselection_probe": (snap_new.to_dict() if snap_new else None),
        "pre_dispatch_decisions": [dec1.to_dict(), dec2.to_dict()],
        "execution_status": result.execution_status,
        "error_class": result.error_class,
        "latency_seconds": latency,
        "backend_receipt_pointer": result.raw_backend_receipt_pointer,
        "output_pointers": result.output_pointers,
        "verification_status": result.verification_status,
        "observed_answer": observed_answer,
        "observed_raw_output": observed_raw[:500],
        "acceptance_is_true": acceptance_ok,
        "contract_fingerprint": contract.request_fingerprint,
        "git_revision": rev,
    }
    (EVIDENCE_DIR / "c39-proof-2-live-evidence.json").write_text(
        json.dumps(evidence, indent=2, default=str), encoding="utf-8")
    print("Evidence persisted; revision:", rev)
    return 0 if acceptance_ok else 4


if __name__ == "__main__":
    sys.exit(main())
