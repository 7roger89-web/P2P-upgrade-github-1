# Coder Handoff Report: P2P-CONTEXT-HYGIENE-01 Authority-Aware Context / Plan Lifecycle

Issue #42. Bounded architecture-quality workstream. Candidate only —
unpromoted, no merge, no promotion, no release.

## Result

Implemented the minimum authority-aware context / plan lifecycle on
EXISTING P2P machinery only, so stale plans, historical evidence, old
session material, and semantically similar obsolete records cannot regain
active task authority. No new project manager, database, daemon, scheduler,
memory graph, or second router was introduced.

## Exact bases

- Fresh canonical main SHA: `39a1573457cc257eb96bbaf862e6ef59608b5939`
- Fresh canonical main tree: (base of candidate; fetched, not advanced)
- Candidate head SHA: `34eeff4c310aab548bacf990527f0585f73dd944`
- Candidate head tree: `0ace43203215c037a3c4818ba2e6aa84ae28d83b`
- Candidate descends directly from fresh main.

## Scope and machinery map

Changed functional paths (all existing files):

- `.p2p/system/p2p_capabilities/task_state.py` — plan-level authority
  lifecycle on the existing durable Task State projection:
  `plan_lifecycle` (ACTIVE/CLOSED/SUPERSEDED) with a single
  provenance-linked lifecycle event (`ACTIVE -> CLOSED|SUPERSEDED` only —
  no transition back to ACTIVE exists), one-shot durable `PlanIdentity`
  binding (repository + workstream + subject + optional Git commit OID /
  Git tree OID / PR — 40-character lowercase object IDs, canonical
  _GIT_SHA_RE shape, NOT SHA-256; not rebindable), `resolve_authoritative_plan`
  (exact durable identity outranks text similarity; similarity is never
  consulted; closed/superseded candidates never win; unpinned multi-match
  fails closed with AUTHORITY_CONFLICT), and fail-closed `_require_active`
  guards on every mutating path (transition, refresh_ready, revise,
  preflight, complete, checkpoint, owner request/resolve). Read-only paths
  (resume summary, events, handoff) remain available for retained history.
  `TaskStateStore` persists closures/supersessions through the EXISTING
  `task-state.json` + `execution-ledger.jsonl` surfaces (no second ledger).
- `scripts/p2p_task_state.py` — the existing foreground CLI gains
  `close-plan` / `supersede-plan` subcommands and `plan_lifecycle` /
  `active_authority` / `plan_identity` in the summary. Still foreground,
  bounded, no background work.
- `.p2p/system/p2p_capabilities/context.py` — the C19 task-targeted
  retrieval is lifecycle-aware: source records carry `lifecycle`
  (CURRENT default; HISTORICAL/SUPERSEDED/CLOSED/ARCHIVED); default
  retrieval excludes non-CURRENT sources with the explicit reason
  `HISTORICAL_EXCLUDED_BY_DEFAULT` (retained, not deleted); explicit
  historical retrieval via `include_historical=True` (carried across
  bounded escalation); selected sources and materialized worker items are
  flagged `lifecycle` + `instruction_authority`, so EVIDENCE-class sources
  are data only, never instruction authority, even when textually relevant.
- `.p2p/system/p2p_capabilities/orchestration_policy.py` —
  `classify_owner_escalation` under `OWNER_MICRO_LOOP_SUPPRESSION`: the 7
  real Owner Gates (merge/promotion, production deploy, destructive
  mutation, secrets, major spend/infrastructure, hard rollback,
  scope-changing blocker) always route to OWNER_GATE; a bounded finding and
  its directly induced repairs (fixture, focused test, evidence-count,
  remote-sync) route back to WRITER_REPAIR_LOOP; unknown actions fail
  closed. Grants nothing, removes no gate.
- `.p2p/system/p2p_capabilities/__init__.py` — package exports for the new
  public names only.

Changed canonical documents (required by the implementation):

- `docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md` — RULE 11 assimilated
  with OWNER_MICRO_LOOP_SUPPRESSION (real Owner Gates preserved verbatim);
  new RULE 16 CONTEXT_HYGIENE_AND_PLAN_LIFECYCLE stating the law set
  (SESSION_CONTEXT != AUTHORITY; DEFAULT_RETRIEVAL = ACTIVE_TASK +
  REQUIRED_CANONICAL_SPECS; historical retained/explicitly retrievable/
  excluded by default; exact identity outranks text similarity; closed
  plans cannot silently regain ACTIVE authority; evidence non-instructional;
  NO_BLIND_DELETE_AFTER_MERGE = YES); RULE_ASSIMILATION_LEDGER entry
  `BACKLOG_I` CONTEXT_HYGIENE_01 recorded truthfully as `PENDING` until
  Control Tower independently verifies the exact PR head/tree.
- `AGENTS.md` — installed digest kept consistent (RULE 11 micro-loop
  sentence + RULE 16 line; rules 01-16).
- `governance/development-control.json` — one new architectural invariant
  `session-context-is-not-authority` beside the existing invariants; no
  other governance surface touched.

Tests:

- `tests/test_p2p_context_hygiene.py` (new, focused) — acceptance laws A-I.
- `tests/test_p2p_operations_notebook.py` — induced focused test repair
  (ledger id set now includes the truthful BACKLOG_I entry; RULE 16 +
  OWNER_MICRO_LOOP_SUPPRESSION structural checks). Same Writer repair loop.

## Law-to-evidence map

| Law | Enforcement | Test |
| --- | --- | --- |
| SESSION_CONTEXT != AUTHORITY | governance invariant + notebook RULE 16 + `retrieved_content_is_data` posture unchanged | H: governance_invariants_preserved_and_extended |
| DEFAULT_RETRIEVAL = ACTIVE_TASK + REQUIRED_CANONICAL_SPECS | context.py default retrieval (CURRENT only) | A |
| Historical retained / explicitly retrievable / excluded by default | `HISTORICAL_EXCLUDED_BY_DEFAULT` + `include_historical` | B, C |
| Closed plan cannot regain ACTIVE authority | lifecycle events one-way + fail-closed mutation guards + reload/reinstantiate stay closed; no reopen API | D |
| Exact durable identity outranks text similarity | `PlanIdentity` + `resolve_authoritative_plan` (similarity never consulted) | E |
| Evidence durable, queryable, non-instructional | `instruction_authority=false` on evidence selections/materialization; closure events in existing ledger | F, D |
| OWNER_MICRO_LOOP_SUPPRESSION (gates intact) | `classify_owner_escalation` + notebook RULE 11 | G |
| Existing authority surfaces intact | all pre-existing suites pass with identical pre-existing env failures only | H |
| No duplicate infrastructure | changes confined to existing modules; no new runtime files; no process/store machinery | I |
| NO_BLIND_DELETE_AFTER_MERGE | closed/superseded plans and historical sources are retained and readable, never deleted | D, H |

## Validation (focused, STOP_WHEN_EVIDENCE_SUFFICIENT)

- `tests/test_p2p_context_hygiene.py`: 31 passed.
- `tests/test_p2p_task_state.py`: 19 passed, 1 pre-existing env error
  (`test_t18` reads git-ignored local `.p2p/state/project-status.json`).
- `tests/test_p2p_task_targeted_context.py` + comparison: 19 + 1 passed.
- `tests/test_p2p_c36_evidence_bound_context.py`: 69 passed.
- `tests/test_p2p_operations_notebook.py`: 21 passed.
- `tests/test_p2p_development_control.py`: 19 passed, 2 skipped
  (official artifact absent in sandbox).
- `tests/test_p2p_adaptive_orchestration.py`: 6 passed.
- `tests/test_p2p_kp01_knowledge_lifecycle.py`: 14 passed, 2 pre-existing
  date-dependent errors (unchanged vs base main).
- Control Tower / EFF01 / goal-closure / fastpath / cognitive-economy
  batch: failure set byte-identical to fresh main in a clean worktree
  (all pre-existing, sandbox-dependent); zero new failures.
- `git diff --check`: clean.

## Boundary statements

- No release/deploy, no secrets, no destructive mutation, no spend.
- No integration of Impeccable / Front-End Checklist / Goose / OpenMAIC /
  OpenMontage / Scientific Skills / Cybersecurity Skills / Claude SEO.
- PR #41 (backlog source) not edited; it is referenced as backlog source
  only, not implementation authority.
- ONE CHAT -> ONE BOUNDED GOAL -> ONE BRANCH -> ONE PR (this branch/PR).
- Candidate is ready for INDEPENDENT SUPERVISOR review before any Owner
  Gate.
