# C38 Provisional Task Graph (2026-08-18)

Built per §3. Each task: one primary objective, one bounded surface, one dominant verification story, one recovery boundary.

| # | Task | Objective | Bounded surface | Dominant verification | Recovery boundary |
| --- | --- | --- | --- | --- | --- |
| T1 | Starting truth verification | Confirm C37 HEAD / clean worktree / candidate SHA | git metadata only (read) | sha256sum + git rev-parse vs expected | Non-blocking; re-verify any time |
| T2 | Operating digest + provisional task graph | Durable execution memory | `docs/p2p-development/research/c38/` (2 files) | File presence + content check | Recreate from repo evidence |
| T3 | Auth preflight — per-backend health check | Classify CURRENT auth state Manus / Hermes / Codex without exposing secrets | read-only config probes + smallest non-mutating ping where safe | AUTH_VALID / INVALID / ABSENT / UNKNOWN per provider | STOP: BLOCKED / OWNER_AUTH_REQUIRED if none valid |
| T4 (if T3 passes) | Target selection via C37 machinery | One eligible backend via hard gates | `selection_*.py` inputs | SelectionReceipt (synthetic-safe) | New governed reselection decision |
| T5 (if T3 passes) | Stage B: one role × one backend × non-mutating task | First live role proof | one adapter + one canonical role + one role contract | Verified receipt + contract binding | Preserve evidence; PARTIAL possible |
| T6 (conditional) | Stage C: same role × second distinct backend | Multi-backend stability proof | equivalent bounded task on 2nd adapter | Equivalent contract semantics | PARTIAL / SINGLE_BACKEND_LIVE_CERTIFIED |
| T7 (conditional) | Continuation capsule + bounded fresh-context proof | Stage D capsule proof | capsule file in research/c38 | STATE_RECOVERED / CONTEXT_DELIVERED honest classification | NOT_PROVEN allowed |
| T8 (conditional) | Capability widening proofs (E) | FILE_WORKSPACE / TEST_EXECUTION / CODE_MUTATION in isolated fixtures only | disposable workspace, isolated branch | Read-back + diff + tests | CODE_MUTATION optional; NOT_CERTIFIED allowed |
| T9 (conditional) | Deterministic checks + regression + closure + candidate policy | Closure machine consistency | full pytest @ C38 head vs 4e5ef54 baseline; validator; secret scan | NEW_UNEXPLAINED_FAILURES = 0 | No forced fixes of 30 inherited failures |
| T10 (conditional) | Terminal report + ONE candidate if policy requires + project-use assessment | Closeout | terminal report + `reports/candidates/` c38 zip + LOGISTICS/GIA PHẢ/GAME TRUYỆN assessment | Advisory only; NO install into real projects | STOP; no C39, no 8/8, no merge/promote/release |

**Material revision policy:** graph may be split/merged/reordered/invalidated on new evidence; revisions recorded in this file.

**Current status:** T1 done (verified), T2 done (written), T3 in progress. Branch creation and T5+ are gated on T3 outcome per §24/§29.
