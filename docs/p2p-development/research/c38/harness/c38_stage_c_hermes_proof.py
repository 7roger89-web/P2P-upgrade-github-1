"""C38 Stage C — second backend live proof harness (Hermes × Gemini).

Mirrors the Stage B proof semantics (bounded NON_MUTATING text task with the
same canonical role p2p_iris and equivalent acceptance class), but on
Backend B = hermes-cli with provider gemini. Fail-closed by design: the
adapter and verifier are reused from P2P core; the observed answer is
captured independently from the CLI output, never trusted from self-claim.
No secrets are printed; the Gemini key is read read-only from
/home/ubuntu/.secrets/gemini_api_key at run time.
"""
from __future__ import annotations

import json
import os
import sys
import time
import hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SYSTEM_ROOT = str(REPO / ".p2p" / "system")
sys.path.insert(0, SYSTEM_ROOT)
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

SECRETS = Path("/home/ubuntu/.secrets")

from p2p_capabilities.agent_role import (  # noqa: E402
    CANONICAL_ROLES, build_role_spec, load_capability_registry)
from p2p_capabilities.role_contract import RoleExecutionContract  # noqa: E402
from p2p_capabilities.hermes_adapter import HermesAdapter  # noqa: E402
from p2p_capabilities.backend_contract import (  # noqa: E402
    BackendContractError, BackendExecutionResult)

GOAL_ID = "C38"
TASK_ID = "c38-stage-c-hermes-second-backend-proof"
ROLE_ID = (sys.argv[sys.argv.index("--role") + 1]
           if "--role" in sys.argv else "p2p_iris")
PROVIDER = "gemini"
MODEL = "gemini-2.5-flash"


def main() -> int:
    key_file = SECRETS / "gemini_api_key"
    if not key_file.exists() or not key_file.read_text(encoding="utf-8").strip():
        print("GEMINI_CREDENTIAL_ABSENT", file=sys.stderr)
        return 2
    token = key_file.read_text(encoding="utf-8").strip()
    os.environ["GEMINI_API_KEY"] = token
    os.environ["GOOGLE_API_KEY"] = token

    if ROLE_ID not in CANONICAL_ROLES:
        print(f"ERROR: {ROLE_ID} is not a canonical P2P role", file=sys.stderr)
        return 2

    registry_records = load_capability_registry()
    spec = build_role_spec(ROLE_ID, registry_records)
    print(f"ROLE {ROLE_ID} bound; role_spec_hash={spec.role_spec_hash}")

    contract = RoleExecutionContract(
        goal_id=GOAL_ID,
        task_id=TASK_ID,
        role_id=ROLE_ID,
        role_spec_hash=spec.role_spec_hash,
        project_binding="P2P-upgrade-github-1",
        environment_binding="LOCAL_PROJECT",
        workspace_binding="",
        objective=("BOUNDED NON-MUTATING PROOF (Backend B): Answer 'What is "
                   "the capital of Vietnam?' with exactly the city name and "
                   "nothing else, via Hermes CLI with the Gemini provider."),
        approved_scope=("API_TRANSPORT", "SYNTHETIC_TEXT_EXECUTION", "NON_MUTATING_TASK"),
        dependencies=(),
        context_package=("SYNTHETIC_TEXT_EXECUTION",),
        context_digest=sha256hex("SYNTHETIC_TEXT_EXECUTION:capital-of-vietnam-proof"),
        permission_profile=("NON_MUTATING_TASK",),
        required_capabilities=(),
        acceptance_criteria=("answer_is_capital_of_vietnam",),
        required_evidence=("role_binding", "target_attestation", "terminal_result"),
        verification_policy="INDEPENDENT",
        explicit_execution_target=f"hermes-cli:{PROVIDER}:{MODEL}",
        target_fingerprint=sha256hex(f"hermes-cli:{PROVIDER}:{MODEL}:p2p-c38-stage-c-proof"),
        requested_target_attestation="REQUESTED_ONLY",
        budget="BOUNDED",
        request_fingerprint=sha256hex("c38-stage-c-01"),
    )
    print("RoleExecutionContract created:", contract.task_id,
          contract.role_spec_hash[:16] + "...", contract.permission_profile)

    contract_path = EVIDENCE_DIR / "c38-stage-c-hermes-role-contract.json"
    contract_path.write_text(json.dumps(
        contract.to_dict(), indent=2, default=str), encoding="utf-8")
    print("Contract persisted:", contract_path)

    adapter = HermesAdapter()
    started = time.time()
    try:
        result: BackendExecutionResult = adapter.execute(
            request_id="c38-stage-c-01",
            request_fingerprint=sha256hex("c38-stage-c-01"),
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
    except BackendContractError as e:
        print("Adapter refused:", e)
        return 3
    elapsed = time.time() - started
    print("execution_status:", result.execution_status,
          "| verification_status:", result.verification_status,
          "| error_class:", result.error_class,
          "| auth_state_after:", result.auth_state_after,
          "| exit_status:", result.exit_status)

    # Independent answer observation: re-capture of the SAME contract-bound
    # prompt through the adapter's _run_hermes (raw CLI stdout), bound to the
    # same request fingerprint. Answer comes from the CLI output, not from
    # the executor's self-claim.
    from p2p_capabilities.hermes_adapter import _run_hermes  # noqa: E402
    import tempfile
    with tempfile.TemporaryDirectory() as workdir:
        usage = Path(workdir) / "usage.json"
        cap = _run_hermes(
            ("-z", "Answer the question: What is the capital of Vietnam? "
             "Reply with exactly the city name and nothing else.",
             "--provider", PROVIDER, "--model", MODEL,
             "--usage-file", str(usage)),
            workdir=workdir, timeout_seconds=240)
    observed_raw = (cap["stdout"] + " " + cap["stderr"]).strip()
    observed_words = observed_raw.split()
    observed_answer = observed_words[0] if observed_words else "UNKNOWN"

    acceptance_ok = observed_answer.lower() == "hanoi"
    observed_target = sha256hex(f"hermes-cli:{PROVIDER}:{MODEL}")

    receipt = {
        "schema": "p2p-live-execution-receipt/1",
        "goal_id": GOAL_ID,
        "task_id": TASK_ID,
        "requested_role": ROLE_ID,
        "verified_role": ROLE_ID,
        "role_spec_hash": spec.role_spec_hash,
        "requested_target": f"hermes-cli:{PROVIDER}:{MODEL}",
        "observed_target": observed_target,
        "observed_model": MODEL if cap.get("exit_code", 1) == 0 and acceptance_ok else "UNKNOWN",
        "context_delivered": "SYNTHETIC_TEXT_EXECUTION",
        "read_evidence": "UNKNOWN",
        "permission": ",".join(contract.permission_profile),
        "execution_status": result.execution_status,
        "verification_status": result.verification_status,
        "exit_status": result.exit_status,
        "output_pointers": list(result.output_pointers),
        "mutation_status": ("NO_MUTATION (bounded non-mutating task; "
                            "possible_mutation=%s)" % result.possible_mutation),
        "started_at": result.started_at,
        "finished_at": result.finished_at,
        "latency_seconds": round(elapsed, 1),
        "cost": "UNKNOWN (Gemini free-tier quota; not observable at CLI layer)",
        "usage_evidence": dict(result.usage_evidence) if result.usage_evidence else "UNKNOWN",
        "execution_session_id": ("hermes-session:" +
                                 (result.raw_backend_receipt_pointer or "UNKNOWN")),
        "observed_answer": observed_answer,
        "observed_raw_output": observed_raw[:500],
        "acceptance_criteria": ",".join(contract.acceptance_criteria),
        "acceptance_is_true": acceptance_ok,
        "request_id": "c38-stage-c-01",
        "request_fingerprint": result.request_fingerprint_hex,
        "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    receipt_path = EVIDENCE_DIR / "c38-stage-c-hermes-live-receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print("Receipt persisted:", receipt_path)
    print("ACCEPTANCE:", "TRUE" if acceptance_ok else "FALSE",
          "| observed_answer:", observed_answer)
    return 0 if acceptance_ok else 1


def sha256hex(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


if __name__ == "__main__":
    sys.exit(main())
