# Supervisor Report: P2P-TMPGC01 Current-Main Reconciliation

## Exact subject reviewed

- Functional candidate SHA: `2ec61632c1bfe78a685cb575eaf8495c658fa46b`
- Functional candidate tree: `051faf6438f24dd206d5401b78965215e5fa9dfb`
- Fresh-main parent: `d661654746f090136f37370f76578ee345b74994`
- Fresh-main tree: `92895a93a560221bdcd4664992ab16a4e8ec8cb4`
- Previous reviewed candidate: `dab3e858dcace307f4bd77fdb43145df70e75da2`
- Previous reviewed tree: `d9ab934f16a9517dccee3e847362795ec66f719b`

The candidate is an isolated descendant of fresh main. The later closure
commit, if any, is permitted only for bounded evidence/process files and must
not alter the five functional TMPGC paths.

## Independent source review

PASS. The fresh-main blobs for the existing FW06 and C27 baseline exactly
match the reviewed candidate's reconciliation base, so no hidden baseline
conflict was found. The five functional candidate blobs also match the
supplied previous candidate byte-for-byte.

The FW06 implementation keeps the existing serialized writer boundary around
lease/state writers and the delete critical section. Delete revalidation covers
pressure, classification, containment/reparse identity, complete size,
registry/audit validity, record identity, duplicate binding, and relevant lock
state before intent, physical operation, audit success, and lifecycle update.
Failure records remain fail-closed and preserve `UNKNOWN`/`KEEP`.

The audit validator preserves semantic identity and ordering, including
`prior_lifecycle == lifecycle_from`, intent-before-success, and the requirement
that a `DELETED` lifecycle requires verified physical success.

C27 archives evidence first and delegates only to the FW06 TMPGC path. Missing,
malformed, unregistered, or unsafe workspace identity returns `KEEP`; no second
physical-deletion authority was introduced.

The protection family remains KEEP for `ACTIVE`, `CANDIDATE`, `OWNER_GATE`,
`ROLLBACK_REQUIRED`, `UNKNOWN`, `DIRTY`, `DEPENDENCY`, and
`EVIDENCE_NOT_DURABLE`. Lifecycle remains `ACTIVE -> COMPLETE -> DISPOSABLE ->
DELETED`. CLI execution remains dry-run by default; schedule output is an
inactive Owner-gated preview, and physical/legacy delete, schedule activation,
and auto-GC are not enabled by default.

## Evidence review

- Focused suite on the exact functional subject: `67 passed in 28.89s`.
- Earlier bounded run: `67 passed in 38.65s`.
- Changed-file `py_compile`: PASS.
- AST/JSON/static invariant checks: PASS.
- `git diff --check`: PASS.
- Fresh-main ancestry and path allowlist: PASS; no unrelated path changed.
- Anvien refresh/detect-changes was unavailable because the isolated worktree
  is not registered. The limitation is explicit; direct Git/source/AST/test
  evidence is used instead.

## Decision

`PASS` for the exact functional candidate above, `READY_FOR_OWNER_REVIEW`.
This is technical readiness only. No Owner approval, promotion, push, delete
run, schedule activation, or automatic GC is authorized or implied.
