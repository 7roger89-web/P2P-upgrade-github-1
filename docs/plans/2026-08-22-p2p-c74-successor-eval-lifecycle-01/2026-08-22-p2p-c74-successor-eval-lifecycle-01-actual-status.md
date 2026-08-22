# P2P C74 Successor Evaluator Lifecycle Actual Status

Title: P2P C74 Successor Evaluator Lifecycle
Date: 2026-08-22
Status: P1-A Complete / P1-B Validated; repository-wide baseline failures disclosed
Companion plan: `docs/plans/2026-08-22-p2p-c74-successor-eval-lifecycle-01/2026-08-22-p2p-c74-successor-eval-lifecycle-01-plan.md`
Companion evidence: `docs/plans/2026-08-22-p2p-c74-successor-eval-lifecycle-01/2026-08-22-p2p-c74-successor-eval-lifecycle-01-evidence.md`
Companion benchmark: `docs/plans/2026-08-22-p2p-c74-successor-eval-lifecycle-01/2026-08-22-p2p-c74-successor-eval-lifecycle-01-benchmark.md`

## Purpose

This file records the real current state before implementation.

Implementation must not start until the target scope has a completed status row, evidence IDs, and a downstream plan decision.

This file does not replace `evidence.md`. It classifies current state from evidence.

Use exact evidence IDs from `evidence.md`, such as `E0-P0A-SRC1`, not broad section IDs such as `E0` or `E1`.

## Freshness / Refresh Rules

This actual-status file is a living current-state record, not a one-time P0 snapshot.

P0 records the baseline before implementation. After implementation begins, keep the Current Status Matrix updated so the next agent can trust it as the latest repo reality.

Update this file:

- after each completed implementation slice;
- before starting the next phase if repo state changed;
- whenever evidence changes a current-state classification;
- whenever the next phase's status assumptions, next action, or work steps need updating because reality differs from the previous status.

When refreshing status:

- update only the rows affected by the completed work or new evidence;
- use explicit transitions such as `missing -> correct`, `partial -> correct`, `fake-or-stub -> removed`, or `unbound -> bound-correct`;
- append a Status Refresh Log row instead of deleting history;
- keep detailed proof in `evidence.md`; store only classifications, evidence IDs, touch mode, and plan consequences here.

## Scope

Target scope:

- Installed project-eval completion resolver, direct behavior tests, fresh package/consumer lifecycle, ten trial slots, gates, regression, package/provenance/security, and successor handoff.

Out of scope:

- Sealed `.72` and `.73`, official `.19`, root owner worktree, existing C72/C73 worktrees, v5, user projects, approvals, promotion, release, deployment, C43, AERG, and multi-AI certification.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `scripts/p2p_eval.py` / `_case_command` | `E0-P0A-FD1`, `E0-P0A-IMPACT1` | 1 inbound file; 51 local relationships; 24 linked flows | evaluator helper is consumed by project-eval tests and workflow/gate processes; completion path uses runtime/root paths | CRITICAL symbol scope warning; edit one resolver branch only |
| `tests/test_p2p_project_eval.py` | file-detail inspected through `E0-P0A-FD1` inbound relationship and source read | 1 direct evaluator consumer | current tests cover parser and recorded suite gate but not target-layout completion selection | high scope warning; edit only after source behavior |
| `scripts/p2p_workflow.py` | source inspection `E0-P0A-WORKFLOW1` | resolver-related consumer | filters UIUX-only helper and enforces project-eval CLI flags | preserve; inspect-only |
| `scripts/p2p_gate.py` / `scripts/doctor.py` | source inspection `E0-P0A-CONTRACT1` | installed gate consumers | both use installed runtime helper and project-local suite; no resolver edit required | preserve; validate-only |
| `install.ps1`, `install.sh`, `scripts/p2p_install_release.py` | source inspection `E0-P0A-CONTRACT1` | installer producers | normal install copies package project-eval helper into `.p2p/system/scripts`; no root consumer script | preserve; validate-only |
| `scripts/package_release.py` | source inspection `E0-P0A-SRC2` | package producer | package contains root project-eval source and distinct UIUX implementation name | preserve unless package verification finds a new defect |
| `.72` / `.73` / official `.19` | `E0-P0A-SEAL1` | protected artifacts | exact byte identities are fixed and not editable | do-not-touch |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve. Add evidence or tests only if needed. |
| `partial` | Some required behavior exists, but gaps remain. | Change only the missing parts. |
| `wrong` | Current behavior, source, or contract is incorrect. | Replace with required behavior. Record the exact reason. |
| `missing` | Required behavior, source, or contract does not exist. | Implement the missing piece only. |
| `unbound` | Surface exists but is not wired to the real source, flow, or contract. | Bind to the real source only. Preserve approved surface. |
| `fake-or-stub` | Prototype, demo, mock, fallback, or placeholder data is being used as real behavior. | Remove fake behavior or replace it with an approved truthful state. |
| `blocked` | Source, authority, contract, or required evidence is unclear. | Stop. Do not implement until resolved. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Installed completion resolver | `_project_eval_path` now selects `runtime_root/scripts/p2p_eval.py` for an installed consumer and keeps root `scripts/p2p_eval.py` only for an unpacked package/development root; missing installed helper remains visible | installed runtime helper is selected when `.p2p/system` exists; missing helper fails closed; package mode remains executable | correct | 4 direct affected symbols / 2 modules / 6 processes; file 177 symbols / 52 local / 24 flows | `E0-P0A-C73FAIL1`, `E1-P1A-ROUTE1`, `E1-P1A-IMPACT1` | preserve source behavior; finish P1-B tests |
| Project-eval source helper | `scripts/p2p_eval.py` is packaged and supports schema-v2 design/validate/run/record/gate | remain the package/source validation authority; no duplicate consumer copy | correct | file-detail `E0-P0A-FD1` | `E0-P0A-SRC2` | preserve; use only package mode |
| Installed `.p2p/system/scripts/p2p_eval.py` in development checkout | UIUX-only helper; correctly rejected by project-eval resolver in development mode | in a real installed consumer, package install must place project-eval helper at this path; development UIUX helper must never be used as a fallback | partial | related through installer/runtime surfaces | `E0-P0A-SRC2`, `E0-P0A-WORKFLOW1` | validate P2-A; no source edit |
| Project-owned suite | suite is project data under `.p2p/evals`; C73 fresh lifecycle did not reach trial execution | suite is created/reused through normal setup and validated by installed helper | partial | gate/Doctor consumers | `E0-P0A-C73FAIL1`, `E0-P0A-CONTRACT1` | prove P2-A |
| Installer/adoption lifecycle | normal packaged scripts copy `scripts/p2p_eval.py` into installed runtime and create project pin/state, but C73 proof reported a helper-path mismatch | fresh consumer is installed through normal lifecycle with no reviewer hand-copy | partial | installer/package/gate/Doctor | `E0-P0A-CONTRACT1`, `E0-P0A-C73FAIL1` | inspect/validate P2-A |
| Direct evaluator tests | three target-layout tests plus the existing project-eval file pass; the source-local disposable matrix has 20 successful case-oracle executions | installed wins, package works, installed absence does not source-fallback; complete focused validation without fake evidence | correct | test file 18 symbols / 6 local / 7 outbound after edit | `E1-P1B-TEST1`, `E1-P1B-TEST2`, `E1-P1B-TEST3` | commit P1-B evidence, then prove the same contract from a fresh installed consumer |
| `.72`, `.73`, official `.19` | exact protected bytes/authority exist | unchanged byte identity and unpromoted candidate boundary | correct | protected identity evidence | `E0-P0A-SEAL1` | preserve-only |
| Root/other worktrees | root and prior review worktrees contain owner/reviewer changes | no edits or cleanup outside successor worktree | correct/preserve-only | N/A | `E0-P0A-AUTH1`, `E0-P0A-STATUS1` | do-not-touch |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-22 | fresh C74 worktree at C72 successor head; graph refreshed before graph queries | evaluator lifecycle and protected boundaries | initial classification: resolver wrong, suite/installer partial, direct route tests missing, seals correct | `E0-P0A-AUTH1`, `E0-P0A-GRAPH1`, `E0-P0A-C73FAIL1`, `E0-P0A-SEAL1` | Option B selected; P1-A is one resolver branch, P1-B adds target-layout tests, P2 proves clean install |
| R1 | 2026-08-22 | P1-A source edit plus focused route checks; post-edit graph refreshed | `scripts/p2p_eval.py` resolver and direct route tests | resolver `wrong -> correct`; route-test coverage `missing -> partial`; ignored source suite remains empty and is not evidence | `E1-P1A-ROUTE1`, `E1-P1A-SYNTAX1`, `E1-P1B-TEST1`, `E1-P1B-TEST2` | P1-A can be committed; complete P1-B validation/commit before P2 |
| R2 | 2026-08-22 | P1-B test file plus disposable source-local suite and parent-commit comparison | project-eval focused coverage and repository-wide regression classification | route coverage `partial -> correct`; source-local matrix `20/20` successful; repository-wide suite remains non-green in both C74 and clean parent, so it is disclosed rather than promoted to a false pass | `E1-P1B-TEST1`, `E1-P1B-TEST2`, `E1-P1B-TEST3`, `E1-P1B-FULL1` | commit only the intended test/docs paths after detect-changes; P2 remains the only clean-consumer proof |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| `scripts/p2p_eval.py` | `tests/test_p2p_project_eval.py` | source-of-truth / test consumer | P1-A | edit | `E0-P0A-FD1`, `E0-P0A-IMPACT1` | one path branch; no schema/grading changes |
| `tests/test_p2p_project_eval.py` | `scripts/p2p_eval.py` | behavior test | P1-B | edit | `E0-P0A-FD1` | disposable target roots; no hand-copy |
| `scripts/p2p_workflow.py` | `scripts/p2p_eval.py` | resolver consumer | P1-A/P2-A | inspect-only | `E0-P0A-WORKFLOW1` | preserve existing helper filtering |
| `scripts/p2p_gate.py` | `scripts/p2p_eval.py` | installed gate consumer | P2-A | validate-only | `E0-P0A-CONTRACT1` | exact project-local suite and helper |
| `scripts/doctor.py` | `scripts/p2p_gate.py` | strict readiness consumer | P2-A | validate-only | `E0-P0A-CONTRACT1` | no warning suppression |
| `install.ps1`, `install.sh`, `scripts/p2p_install_release.py` | `scripts/package_release.py` | lifecycle producer | P2-A | validate-only | `E0-P0A-CONTRACT1` | normal install only; no hand-copy |
| `scripts/package_release.py` | root/runtime eval files | distribution producer | P2-B | validate-only | `E0-P0A-SRC2` | no repo dump or protected baseline rebuild |
| `.72`, `.73`, official `.19` | candidate/governance reports | protected identity | all | do-not-touch | `E0-P0A-SEAL1` | exact bytes and authority unchanged |

## Detailed Findings

### Installed completion resolver

Current state:

`_case_command` resolves the completion case to `target_root / "scripts" / "p2p_eval.py"`. The independent C73 consumer has `.p2p/system/scripts/p2p_eval.py` after normal installation and no root `scripts/p2p_eval.py`, so the completion oracle exits before creating a trial record.

Required state:

```text
If target_root/.p2p/system exists, completion must execute runtime_root/scripts/p2p_eval.py. If no installed runtime exists, an unpacked package/source validation target may execute target_root/scripts/p2p_eval.py. No installed target may fall back to a root/ancestor source path.
```

Evidence:

- `E0-P0A-C73FAIL1`: clean C73 lifecycle failure.
- `E0-P0A-SRC1`: current code path.
- `E0-P0A-CONTRACT1`: installer/bootstrap contract and Option B decision.

Relationship and impact:

- Related file count: 1 direct inbound test file; 51 local relationships; 24 linked flows.
- Relationship summary: evaluator path participates in project eval design/run/gate flows and six Anvien affected processes for `_case_command`.
- Impact note: CRITICAL blast-radius warning; narrow branch edit plus direct target-layout tests required.

Classification:

`wrong` — the consumer path is wrong even though the source helper and installed package producer are otherwise correct.

Allowed next action:

Edit P1-A only after P0 completion to select the installed canonical helper and preserve package-mode validation.

Forbidden next action:

Do not copy a helper into the consumer, use an ancestor checkout, suppress missing-helper errors, or alter suite schema/policy.

### Installer and project-owned suite

Current state:

The normal installer copies the project-eval source helper into `.p2p/system/scripts`; the project suite remains project-owned under `.p2p/evals`. C73 did not prove the complete consumer lifecycle because its completion case resolved the wrong path.

Required state:

```text
Normal install/adoption creates the installed runtime helper and project-local state; normal suite setup creates/reuses the project suite; ten trials and gates execute using only consumer-local paths.
```

Evidence:

- `E0-P0A-CONTRACT1`: docs and installer source.
- `E0-P0A-C73FAIL1`: lifecycle stopped before records.

Relationship and impact:

- Related file count: installer/package/gate/Doctor surfaces inspected; exact file-detail evidence is not a source edit gate for P0 because these files are validate-only in the chosen slice.
- Relationship summary: package producer -> installer -> installed helper -> gate/Doctor.
- Impact note: lifecycle evidence is P2-gated; no installer edit is currently justified.

Classification:

`partial` — contract and producer exist, but fresh independent proof is missing.

Allowed next action:

Validate through the canonical package lifecycle in P2-A.

Forbidden next action:

Do not manufacture a project suite or trial evidence in the installer.

### Protected artifact and worktree boundary

Current state:

The new worktree is separate from the root owner worktree and historical review worktrees. `.72` and `.73` exact hashes are known; official `.19` authority is preserved.

Required state:

```text
Only a new unpromoted successor may be produced; protected bytes and external project worktrees remain unchanged.
```

Evidence:

- `E0-P0A-AUTH1`: worktree/branch boundary.
- `E0-P0A-SEAL1`: exact hash boundary.
- `E0-P0A-STATUS1`: newline-only noise is excluded from staging.

Relationship and impact:

- Related file count: protected artifacts are preserve-only, not graph-edit targets.
- Relationship summary: candidate identity/governance reports bind them but do not authorize mutation.
- Impact note: preserve-only.

Classification:

`correct/preserve-only`.

Allowed next action:

Read-only comparison before/after candidate mint.

Forbidden next action:

No rewrite, rezip, promotion, approval, finalize, or destructive cleanup.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | completion resolver is wrong; Option B is resolved from current source and docs | keep P1-A unchanged; edit one resolver branch only |
| P1-B | direct target-layout tests and source-local project-eval matrix are green; repository-wide suite has the same pre-existing non-green family on the clean parent | mark P1-B validated for its scoped acceptance, record the full-suite limitation, commit the test/docs slice, and continue to P2 |
| P2-A | installer/project suite contract is partial; C73 proof is failed, not reusable | keep P2-A; require fresh candidate/install and ten slots; no historical reuse |
| P2-B | protected artifact/source boundary is correct; successor not yet minted | keep P2-B; defer mint until P1/P2-A gates pass |
| Pn-A/B/C | no implementation or supervisor review yet | remain pending until P2 evidence is complete |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Each target file has relationship count evidence from `file-detail` when applicable.
- [x] Phase Touch Map lists plan-relevant relationship files that can affect the current phase/slice.
- [x] Phase Touch Map defines touch mode for every plan-relevant relationship unit that may be affected.
- [x] Correct parts are marked preserve-only.
- [x] Partial, missing, wrong, unbound, and fake-or-stub parts have exact next actions.
- [x] Blockers are recorded, if any.
- [x] Next phase status assumptions, next action, and work steps have been updated from this status file when needed.
- [x] Status Refresh Log has an R0 baseline row.
- [x] If implementation has started, affected Current Status Matrix rows have been refreshed from latest evidence.
- [x] If refreshed statuses changed next work, only the stale next-phase status assumptions, next action, or work steps have been updated before the next phase.

## Final P0 Decision

Choose one:

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [ ] P0 complete. Next phase can proceed unchanged.
- [x] P0 complete. Next phase status, next action, or work steps must be updated before implementation.
- [ ] P0 complete. Next phase status, next action, or work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

P0 is complete and P1-A/P1-B are validated for the scoped evaluator contract. Fresh repo truth and independent C73 evidence establish a single narrow defect: the installed completion oracle used a project-root path that normal packaged adoption does not provide. Option B is consistent with the installed command examples and installer producer: installed consumers use `.p2p/system/scripts/p2p_eval.py`, while package/source validation uses the packaged root helper without allowing installed-root fallback. The source syntax, three target-layout tests, five-test project-eval file, and 20-execution source-local matrix pass. The repository-wide suite remains non-green in the clean parent and C74 worktree with the same legacy governance/closure family, so that limitation is explicitly recorded. P2 must prove the real fresh consumer before any successor handoff can be declared ready.
