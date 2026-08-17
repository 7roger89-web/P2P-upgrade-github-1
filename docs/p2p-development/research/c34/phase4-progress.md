# Phase 4 progress state (2026-08-17)

## Completed artifacts
1. `.p2p/system/p2p_capabilities/backend_contract.py` — conformance contract (C34 Phase 1). Contains ADAPTER_STATES (5 states incl CURRENTLY_ELIGIBLE), BackendContractError, BackendAdapterIdentity, AdapterHealthState, BackendExecutionResult (request_fingerprint_hex validated 64 hex, to_dict), normalize_adapter_error(message, backend_error_tags), verify_request_receipt_binding(contract, result) (checks goal_id/task_id/fingerprint; returns bool), state_family_schema_for(path) (matches on path keywords).
2. `.p2p/system/p2p_capabilities/hermes_adapter.py` — HermesAdapter: execute() via `hermes -z <prompt> [--provider --model --usage-file]` (options AFTER prompt confirmed live), execute_with_toolsets() via `hermes chat -q --max-turns`, classify: credentials markers → FAILED/AUTH_REQUIRED/NO_CREDENTIALS; 401/invalid-key → AUTH_INVALID; 403/access-denied → AUTH_INVALID; rate limit → RATE_LIMIT; exit!=0 unknown → UNKNOWN + normalize_adapter_error. Never passes --yolo. Evidence dir → usage.json. HERMES_EXPECTED_RELEASE="0.20.2". HERMES_ADAPTER_ID="hermes-cli".
3. `.p2p/system/p2p_capabilities/manus_adapter.py` — ManusAdapter(api_key): executes POST /v2/task.create → poll GET /v2/task.detail → GET /v2/task.listMessages(asc,200) → map terminal. Status running/stopped/waiting/error. usage_evidence = credit_usage (manus-credits). Evidence files saved under evidence_dir. agent_profile default manus-1.6-lite. task.stop attempted on expiry. _request uses urllib x-manus-api-key. Key read from /home/ubuntu/.secrets/manus_api_key. MANUS_ADAPTER_ID="manus-api".
4. `.p2p/system/p2p_capabilities/backend_execution_bridge.py` — BackendExecutionBridge(registry, target_profile) satisfying fake_execution_backend.execute(contract) duck interface: validate_task_contract, contract_request_fingerprint (sha256 json goal/task/objective/workspace/target), canonical_error_class_for (9 canonical classes + UNKNOWN fails closed), BackendAdapterRegistry (register/resolve/summary; NO rank/best/fallback/route/select), state_family_identifier_for_adapter. _normalize_receipt binds goal/task/fingerprint (bound_to_contract), verdict_hint ACCEPTABLE/UNKNOWN/UNACCEPTABLE, outcome PASS/MUTATION_UNKNOWN/VERIFY_FAIL/CRASH_BEFORE_VERIFY. Fail-closed only when execution_status UNKNOWN.
5. `tests/test_p2p_c34_real_backend_contract.py` — full C34 deterministic suite (10 classes).

## Live proofs
- Manus live: task_id 8Eqa4QGo4x35raVTPnnA7c, answer "Four", SUCCEEDED/stopped, LIVE_VALIDATED.
- Hermes: binary installed, v0.20.2, no credentials → FAILED/AUTH_INVALID, ADAPTER_VALIDATED_AUTH_BLOCKED.
- Bridge live: Manus via bridge works; fingerprint bound true.

## Remaining Phase 4 work
- Run pytest on new suite; fix failures.
- Candidate policy check: `python3 scripts/p2p_goal_closure.py audit p2p-c33-bounded-autopilot-core p2p-c34-real-backend-contract-validation` (in tests).
- Check ledger canonical agents key name (test assumes "canonical_agents" or "agents" — verify key).
- Baseline regression: run full pytest, compare to baseline (681 pass / 17 fail pre-existing on this env: drift scan diff, PR lineage, ET hardcoded path /home/ubuntu/p2p, project_eval, secure_onboarding; 1786960599 era).
- C33 baseline debt file exists: c34-notes/phase0-baseline-tests.md.

## Git (Phase 5+6)
- Repo: /home/ubuntu/p2p-upgrade; branch p2p-c33-bounded-autopilot-core @ 2a000e0; GH token in /home/ubuntu/.secrets/github_token; remote needs credentials via token.
- New branch: p2p-c34-real-backend-contract-validation. Draft PR #9 exists against C33 branch (per spec "cập nhật Draft PR #9"? — actually spec says push branch + Draft PR; PR #9 mentioned in user's original repo context).
- Forbidden: merge/force-rewrite/destructive-rebase/release/deploy/promotion.

## Terminal report (Phase 6)
- docs/p2p-development/research/c34/ dir + P2P-C34-terminal-report.md. Classify DUAL PASS or SINGLE PARTIAL (Manus LIVE_VALIDATED + Hermes ADAPTER_VALIDATED_AUTH_BLOCKED → likely SINGLE PARTIAL unless Hermes also proven... per spec: classify honestly).
