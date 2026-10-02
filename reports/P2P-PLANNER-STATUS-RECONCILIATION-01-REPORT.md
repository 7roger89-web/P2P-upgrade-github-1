# P2P-PLANNER-STATUS-RECONCILIATION-01 — Evidence Report

**Issue:** #287 — Planner reconciliation: fresh current-main rerun and durable status closure
**Role:** Arena Writer (one bounded branch / one PR; left unmerged for Independent Supervisor)
**BASE_MAIN:** `3e2309a83920fd0c923b376058fa0316e160a889` (tree `f99c4e6b46038730c20cae9bd5675b01953b4e31`)
**Branch:** `arena/01a0fac1-p2p-upgrade-github-1`
**Planner version:** `scripts/p2p_roadmap_planner.py` VERSION=4 (unchanged; SHA-256 `00d8bfafd7bfc64b...`)

## 1. Scope (status/evidence reconciliation only)

- No planner refactor, no new planner/router/registry/state store/daemon/execution loop.
- No promotion, no release, no deploy, no Owner Gate change.
- The goal recommended by the final planner run was **not** started (`RECOMMENDED_GOAL_STARTED=NO`).
- Historical planner runs RUN-07 / RUN-08 are untouched; the next unused artifact is RUN-09.

## 2. Pre-reconciliation rerun (transient, not committed)

Command: `python scripts/p2p_roadmap_planner.py --repo . --output /tmp/P2P-PLANNER-RUN-09-PRE.json`

| Field | Value |
| --- | --- |
| PLANNING_STATUS | `PLANNING_COMPLETE` |
| PLAN_COMPLETE | `true` |
| ROADMAP_COVERAGE_GAP | `false` |
| ROADMAP_COVERAGE_GAPS | `[]` |
| RECOMMENDED_NEXT_GOAL | `RM-PRIORITY-PLANNER` |
| PLANNER_SELECTION_DOES_NOT_AUTO_EXECUTE | `true` |

All canonical input hashes equal the RUN-08 binding (roadmap `55ec032e…`, research-adoption-ledger `50417aad…`, capability-index `5cb76f09…`, development-control `3fc6cebd…`, intake-contract `609e10fa…`, research-intake-ledger `5617e00c…`), i.e. RUN-08 was exactly reproduced before any edit.

## 3. Reconciliation applied

1. `governance/p2p-development-roadmap.json`
   - `RM-PRIORITY-PLANNER.status`: `PLANNED` → `DONE` (the file's own `status_vocabulary` contains `DONE`; precedent for read-only / no-promotion completions: `RM-PRIORITY-CONTEXT` and `RM-PRIORITY-RELEASE-LIFECYCLE` are `DONE`).
   - `current_evidence` now points at the current implementation (v4 script + SHA) and the latest current-main validation evidence (RUN-09), plus the capability/charter state and the disclosed open gap.
   - `next_safe_when` no longer says `now`: replaced with a truthful terminal statement (the issue flagged `next_safe_when = now` as a stale marker alongside `PLANNED`).
   - Bounded `reconciliation_note` records the change and that the historical capability identity was preserved.
   - `roadmap_reader_status.planned_capability` → `verified_capability` (the runtime still has no automatic roadmap auto-consumption; that `fact` is unchanged). Leaving `planned_capability` naming a DONE capability would have preserved the stale contradiction.
   - `target_evidence` semantics preserved unchanged.
2. `docs/P2P-DEVELOPMENT-ROADMAP.md` (human projection, minimal edits only)
   - Planner row removed from **“Future roadmap items (priority-ordered, PLANNED)”** and recorded as `DONE` with evidence pointers.
   - §7 “Roadmap reader status (honest)” updated: no longer claims `ROADMAP_AWARE_DEVELOPMENT_PLANNER = PLANNED, not VERIFIED`; states `DONE` / capability `VERIFIED_IMPLEMENTED` and keeps the honest disclosure that runtime execution-loop integration is an open gap.
   - Beginner-first view row 4 replaced by a `DONE` note. No whole-file regeneration.
3. Capability ledger identity preserved: `ROADMAP_AWARE_DEVELOPMENT_PLANNER_PLANNED` was **not** renamed or duplicated; `status=VERIFIED_IMPLEMENTED`, `origin_refs`, `known_gaps` and historical evidence refs are unchanged (no ledger/projection churn).
4. `docs/p2p-development/P2P-DEVELOPMENT-CHARTER.md` unchanged: `MACHINE_READABLE_ROADMAP_VERIFIED` already describes the planner accurately and “Runtime execution-loop integration remains planned” is still true.

## 4. Final planner run (durable, binds post-reconciliation truth)

Artifact: `reports/planner/P2P-PLANNER-RUN-09.json`
SHA-256: `2141400321b2923aa43dcaa378fea168c370e467e79ff3bc2d4a122570f36a8c`

| Field | Value |
| --- | --- |
| PLANNING_STATUS | `PLANNING_COMPLETE` |
| PLAN_COMPLETE | `true` |
| ROADMAP_COVERAGE_GAP | `false` |
| ROADMAP_COVERAGE_GAPS | `[]` |
| UNKNOWN_STATUS_ITEMS | `[]` |
| ORPHAN_OWNER_DECISIONS | `[]` |
| INTAKE_UNKNOWN_RECORDS | `[]` |
| UNKNOWN_ADOPTION_RECORDS | `[]` |
| FUZZY_MATCHES_USED_FOR_AUTHORITY | `0` |
| PLANNER_SELECTION_DOES_NOT_AUTO_EXECUTE | `true` |
| RM-PRIORITY-PLANNER graph class | `DONE_SHIPPED_VERIFIED` (terminal `DONE`) |
| RECOMMENDED_NEXT_GOAL | `RM-PRIORITY-DRIFT-SWEEP` (changed as expected) |

Bound canonical hashes (post-edit): roadmap `2e234e2d…` (matches the working file byte-for-byte), others unchanged. Re-running the planner produces structurally identical output apart from `planning_timestamp_utc`.

## 5. Validation on the reconciled tree

| Check | Result | Note |
| --- | --- | --- |
| `scripts/p2p_roadmap_planner.py` current-main run | PASS (final run above) | reproducible; hash-bound |
| `scripts/test_planner_dynamic.py` | `ALL DYNAMIC PLANNER TESTS PASSED` | identical pre/post |
| `scripts/p2p_planner_strictbind_test.py` | **18/18 PASS** | run from a `/tmp` copy with only the hardcoded legacy `REPO` path substituted (checked-in file hardcodes `/home/ubuntu/fw01_work/auth-f01`, absent here); test logic unchanged |
| `scripts/p2p_planner_01b_test.py` | **12/12 PASS** | same path substitution |
| `scripts/p2p_planner_01a_test.py` | 32/35 (B3, J1, J3 fail) | identical failures on base main (J1 message differs only by the expected new recommendation) |
| `scripts/p2p_planner_test.py` | 2 pre-existing failures (T1, T8) | identical failures on base main; legacy `/tmp` fixture + baseline-mismatch fixture expectations |
| pytest consistency set (govrec01, charter, c43, development-control, capability-foundation, goal-closure, ledger-provenance) | `45 failed, 167 passed, 3 skipped` | **identical failure set** pre/post; all failures pre-exist on base main |
| Framework validator `scripts/validate_p2p_development_framework.py` | `52/58` — 6 failures (V03, V05, V06, V09, V12, V20) | **identical failure set** pre/post; pre-existing unrelated validator debt, not repaired (out of scope) |
| `git diff --check` | clean | |

## 6. Pre-existing divergences observed (not repaired)

- The human projection `docs/P2P-DEVELOPMENT-ROADMAP.md` §4 still lists `RM-PRIORITY-CONTEXT` (#3) and `RM-PRIORITY-RELEASE-LIFECYCLE` (#10) as future/PLANNED while the canonical JSON marks both `DONE`. This predates this task; repairing it would widen scope.
- Framework-validator V03/V05/V06/V09/V12/V20 debt pre-exists on base main and is explicitly out of scope.

## 7. Acceptance

`RM-PRIORITY-PLANNER` no longer says `PLANNED`; canonical and human roadmap agree on the planner item; capability identity/provenance preserved; `ROADMAP_COVERAGE_GAP=false`; Owner Gate untouched; planner read-only; no recommended goal started; no release/promotion/deploy; one bounded PR, left unmerged pending Independent Supervisor.
