# Audit Findings: Artifact Addressing & Evidence Representation

## 1. Artifact Addressing Scheme
ZaoFu implements a robust artifact addressing and resolution mechanism primarily located in `src/zf/runtime/artifact_refs.py`. The core function `resolve_runtime_artifact_ref` determines the canonical path of an artifact. It utilizes a deterministic state-directory precedence where references starting with `.zf` map to the `state_dir`, and those starting with `artifacts` map to `state_dir/artifacts`. Fallbacks exist for `project_root`, and worktrees are searched if configured. The `ArtifactRef` dataclass in `src/zf/runtime/artifact_manifest.py` represents an artifact with fields like `kind`, `path`, `sha256`, `summary`, `workdir_path`, `commit`, `artifact_id`, `version`, `supersedes`, `status`, etc. This system is heavily used by admission, Goal closure, and worker handoff to ensure consistent resolution. It depends on `pathlib.Path` for file resolution and is tested in e2e scenarios. The logic is file-system based and provider-neutral.

## 2. Evidence Representation
Evidence representation is handled in `src/zf/runtime/artifact_delivery_evidence.py`. The function `artifact_delivery_evidence_binding_issues` checks if verification evidence is properly bound to admitted envelopes. It extracts authorized refs from `input_result_refs`, `artifacts`, `open_gap_refs`, and various envelope descriptors such as `control_result`, `artifact_manifest_ref`, and `provider_operation_summary_ref`. It returns a list of issues where `verification_evidence_refs` are not bound to authorized refs. This logic depends on `Mapping` and basic typing utilities and is used in artifact-delivery verification results. It operates on generic payload structures and is provider-neutral.

## 3. Artifact Matrix Gate
The artifact matrix gate is implemented in `src/zf/runtime/artifact_matrix_gate.py`. It evaluates artifacts and matrices to determine if quality gates are passed. The implementation defines `ArtifactMatrixGateResult` and `ArtifactMatrixFinding` dataclasses. It loads rows from refs, checks for missing or invalid JSON, and determines if rows are blocking based on priority fields. The gate returns a result containing whether it passed, findings, checked artifacts, and checked matrices. It depends on `json`, `pathlib`, and `dataclasses`, and is used for generic artifact and matrix gate evaluation. The implementation is intentionally project-agnostic and provider-neutral.

## 4. Candidate Rework Evidence
Candidate rework evidence is handled in `src/zf/runtime/candidate_rework_evidence.py`. Functions like `feedback_lines_from_payload`, `plan_rejection_feedback`, and `gap_tasks_from_payload` extract evidence and feedback from payloads for candidate-level rework planning. It generates bounded synth feedback from findings and identifies gap tasks from verification payloads. This module depends on the `verification_result` module and is used in the rework generation pipeline. The payload parsing logic is complex but operates on generic dictionaries, making it provider-neutral.

## 5. Candidate Rework Fingerprint
Implemented in `src/zf/runtime/candidate_rework_fingerprint.py`, this module generates a stable semantic identity for candidate recovery. The `rejection_fingerprint` function creates a retry identity without volatile diagnostic paths or times, while `dedupe_feedback` dedupes feedback lines based on normalized identity. It depends on `hashlib` and `re` to identify unique failure modes. The sophisticated normalization logic removes timestamps and commits, ensuring stability. It is provider-neutral.

## 6. Candidate Rework Identity
This module is implemented in `src/zf/runtime/candidate_rework_identity.py` and tracks candidate success closures and determines if a failure is superseded by a later success. Functions like `_candidate_success_closures` and `_candidate_failure_superseded` match failures to successes based on `pdd_id`, `trace_id`, `target_ref`, and `candidate_ref`. It depends on event payloads and fanout IDs and is used in the state machine for candidate resolution. The complex matching logic for events is provider-neutral.

## 7. Candidate Rework Scope
Implemented in `src/zf/runtime/candidate_rework_scope.py`, the `prepare_candidate_rework_scope` function prepares the scope for candidate rework. It identifies unowned paths and creates a replacement gap task, setting fields like `allowed_paths_reason`, `acceptance`, and `verify_commands`. It depends on source events and task items and is used to dispatch rework tasks. The detailed scope preparation logic is provider-neutral.

## 8. Export Manifest
The export manifest is defined in `PUBLIC_EXPORT_MANIFEST.md`. It specifies included files such as `src`, `web`, `tests`, and `skills`, and explicitly excludes files like `.git`, `.claude` local settings, and `.zf` runtime state. It requires manual checks before publishing, including secret scanning and copyright attribution. It governs the public release process and has clear exclusion rules for private and local state. It is provider-neutral.

| Area | Key Implementation | Coupling/Boundaries | Maturity | Provider Neutrality |
|---|---|---|---|---|
| Artifact Addressing | `src/zf/runtime/artifact_refs.py:resolve_runtime_artifact_ref` | Admission, Goal closure, worker handoff | Tested in e2e | Neutral |
| Evidence Representation | `src/zf/runtime/artifact_delivery_evidence.py:artifact_delivery_evidence_binding_issues` | Artifact-delivery verification | Core runtime verification | Neutral |
| Artifact Matrix Gate | `src/zf/runtime/artifact_matrix_gate.py:ArtifactMatrixGateResult` | Generic artifact evaluation | Well-defined dataclasses | Neutral |
| Candidate Rework Evidence | `src/zf/runtime/candidate_rework_evidence.py:feedback_lines_from_payload` | `verification_result` module | Complex payload parsing | Neutral |
| Candidate Rework Fingerprint | `src/zf/runtime/candidate_rework_fingerprint.py:rejection_fingerprint` | `hashlib`, `re` | Sophisticated normalization | Neutral |
| Candidate Rework Identity | `src/zf/runtime/candidate_rework_identity.py:_candidate_success_closures` | Event payloads, fanout IDs | Complex matching logic | Neutral |
| Candidate Rework Scope | `src/zf/runtime/candidate_rework_scope.py:prepare_candidate_rework_scope` | Source events, task items | Detailed scope preparation | Neutral |
| Export Manifest | `PUBLIC_EXPORT_MANIFEST.md` | Public release process | Clear exclusion rules | Neutral |
