# P2P-CLEANUP-INSPECTION-AUTHORITY-01 — Coder Report

- Date: `2026-08-30`
- Session: `P2P-CLEANUP-INSPECTION-AUTHORITY-01` (one branch, one PR)
- Goal: extend the existing P2P authority model with the minimum authority
  needed to inspect temporary workspaces safely (READ_ONLY) and restore
  proven lifecycle bindings (OWNER_GATED). No new authority framework.

## Fresh base

- EXPECTED_MAIN_SHA (session base): `d1dbf94a71c9db8a0c8d5fe9bfac62a2c539132a`
- FRESH_MAIN_SHA (fetched `origin/main`): `f71080e6e9062a1e96bb19bf49e852089f4afe53`
  - `d1dbf94` is an ancestor of fresh main; main advanced by `#27`
    (AGENTS.md prompt/effort policy only) while this session ran.
- Branch rebased onto `f71080e`; PR diff contains only this workstream.

## Files changed

- `.p2p/system/p2p_capabilities/fw06_operational_resilience.py`
  (existing FW06/TMPGC seam, additive authority section + deletion denial)
- `.p2p/system/p2p_capabilities/authority_chain_registry.py`
  (existing authority-chain certification ledger, additive restore kind)
- `tests/test_p2p_cleanup_authority.py` (focused acceptance tests)
- `reports/coder/rp_coder_20260830T110528Z_by_p2p-agent_p2p-cleanup-inspection-authority-01.md`
  (this report)

## Existing authority seams reused

- FW06 operational-resilience workspace registry/lease/audit/event seams.
- TMPGC policy, scope identity (`_tmp_path_identity`), durable-evidence
  refs (`_durable_ref`), classifier (`classify_tmp_workspace`), audit
  validation (`_tmp_gc_audit_is_well_formed`).
- Existing authority-chain certification ledger
  (`authority_chain_registry.py`, Owner-bound `owner-*` authorization idiom).
- Existing fail-closed lease/serialization boundary for the one allowed
  lifecycle write.

## New authority framework created

NONE. Constants and enforcement live inside the existing FW06 module; the
only new registry addition is one additive certification kind in the existing
authority-chain ledger.

## Authorities delivered

- `CLEANUP_INSPECTION_AUTHORITY = "cleanup-inspection-read-only"`:
  - lists files/directories only inside canonical cleanup scope;
  - reads size/timestamps/attributes, Git HEAD/status/worktree metadata,
    reports/receipts/return packets/decision logs;
  - hashes local files for equality comparison and compares local evidence
    with canonical Git/archive/remote history via the existing history seam;
  - reads lifecycle registry/audit state and determines durable evidence;
  - classifies `SAFE_DISPOSABLE_CANDIDATE` / `KEEP` / `UNKNOWN`;
  - denies DELETE / MOVE / RENAME / GIT_CLEAN / RESET / STASH /
    WRITE_LIFECYCLE_STATE / SCHEDULE / AUTO_GC before any state change
    (`InspectionAuthorityError: MUTATION_DENIED_UNDER_INSPECTION`).
- `LIFECYCLE_BINDING_RESTORE_AUTHORITY = "lifecycle-binding-restore-owner-gated"`:
  - restores one missing existing lifecycle record only when all required
    identity fields (`workspace_id`, `project_id`, `task_id`, `session_id`,
    `root_path`, `base_revision`) are proven from durable canonical evidence
    (durable FW06 registry and/or schema-valid binding evidence documents
    under `durable_roots`);
  - requires explicit `owner-*` authorization id;
  - missing/contradictory evidence => `BLOCKED` / `KEEP`
    (`AMBIGUOUS_BINDING_FAIL_CLOSED`, `BINDING_CONTRADICTS_DURABLE_REGISTRY`,
    `EVIDENCE_DOCUMENT_UNREADABLE_OR_INCOMPLETE`, `EVIDENCE_INSUFFICIENT`);
  - never infers any identity from a directory name;
  - never implies physical deletion (`DELETE_NOT_GRANTED_TO_LIFECYCLE_RESTORE`).

## Acceptance evidence (focused tests)

- `tests/test_p2p_cleanup_authority.py`: **8 passed**
  1. inspection collects evidence (`scope_listing`, hashes, git/worktree,
     durable documents, registry/audit) and classifies;
  2. `inspect_authority.mutate`, `cleanup_workspace(authority=inspection)`,
     `run_tmp_gc(apply=True, authority=inspection)` denied, fs unchanged;
  3. restore without Owner authorization => BLOCKED, no write;
  4. incomplete evidence => BLOCKED; two disagreeing evidence documents =>
     `AMBIGUOUS_BINDING_FAIL_CLOSED`;
  5. exact proven binding + explicit Owner authorization restored and
     representable (restore receipt + authority-chain certification);
  6. restore authority denied on delete paths, workspace untouched;
  7. UNKNOWN => KEEP invariant preserved (`unknown_keep_invariant_preserved`).
- Regression: `tests/test_p2p_tmp_gc.py` — 65 passed; 2 failures
  (`test_TOCTOU_*`, `test_AUDIT_lifecycle_identity_regression_*`) are
  pre-existing on pristine `d1dbf94` (historical git objects absent from
  this shallow checkout) and unrelated to this change.
- Regression: `p2p_capabilities/tests/test_bounded_mutation_authority_chain.py`
  — 26 passed.

## Termination

- No physical deletion executed; schedule remains inactive;
  `DELETE` remains separately unauthorized.
- No merge performed; PR left for Owner review.
- TERMINAL_VERDICT: `FRESH_MAIN_DIVERGED_FROM_EXPECTED_SHA (d1dbf94 -> f71080e, PR#27 ancestor-only AGENTS.md change); implementation + focused tests PASS; not merged; UNKNOWN->KEEP invariant preserved; DELETE not granted.`
