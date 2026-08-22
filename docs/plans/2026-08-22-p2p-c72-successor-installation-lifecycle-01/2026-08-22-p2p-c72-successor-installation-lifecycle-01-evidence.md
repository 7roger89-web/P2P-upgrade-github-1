# P2P C72 Successor Installation Lifecycle 01 Evidence Ledger

## Metadata

- Date: `2026-08-22`
- Plan: `docs/plans/2026-08-22-p2p-c72-successor-installation-lifecycle-01/2026-08-22-p2p-c72-successor-installation-lifecycle-01-plan.md`
- Evidence: `docs/plans/2026-08-22-p2p-c72-successor-installation-lifecycle-01/2026-08-22-p2p-c72-successor-installation-lifecycle-01-evidence.md`
- Benchmark: `docs/plans/2026-08-22-p2p-c72-successor-installation-lifecycle-01/2026-08-22-p2p-c72-successor-installation-lifecycle-01-benchmark.md`
- Actual status: `docs/plans/2026-08-22-p2p-c72-successor-installation-lifecycle-01/2026-08-22-p2p-c72-successor-installation-lifecycle-01-actual-status.md`

## Evidence Rules

- Fresh evidence must come from this successor worktree or repo-local disposable pilots.
- `.72`, origin/main, historical approvals, and authoritative projects are preserve-only.
- Source-tree-only helpers are not evidence for installed distribution capability.
- Every implementation slice records source, behavior, cleanup, Anvien, tests, and commit evidence.
- Approval state may be pending only; no approval, promotion, merge, or deployment is performed.

## E0 - P0 Evidence

Matching plan item: `P0-A`.

- `E0-P0A-REF1`: fresh fetch; successor branch starts at `4ce6a85f5991b6d6c464fb4b59e177114698947e`; `origin/main` official governance remains `.19` with SHA `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`.
- `E0-P0A-SUBJECT1`: exact `.72` ZIP rechecked at SHA `70613080d2ddbb92a52d2d79186e125439ec7f5ba8a6fa87bda9208d1b39d872`, size `2899774`, 491 members; no source edit targets the ZIP.
- `E0-P0A-CONTRACT1`: lifecycle doc, installer entrypoints, safe installer, legacy installer, Project Context, Doctor, gate, eval helper, and package builder mechanically inspected. `.72` has no packaged safe-installer producer; project eval suite is project-owned setup.
- `E0-P0A-IMPACT1`: Anvien refreshed successfully (36,412 nodes, 42,097 relationships, 0 parse failures, stale=false); affected Python surfaces were file-detailed and high-scope impact warnings recorded.
- `E0-P0A-VERSION1`: active source is `.72`; no `.73` was found in tracked history/current governance or candidate records; `.73` selected as the smallest unused immediate successor under the existing `<release>-codex.<revision>` policy.

## E1 - P1 Evidence

Matching plan items: `P1-A`, `P1-B`.

- `E1-P1A-PRODUCER1`: pin producer implementation and schema binding.
- `E1-P1A-PACKAGE1`: producer membership in package distribution.
- `E1-P1A-TEST1`: normal lifecycle producer behavior tests.
- `E1-P1B-NEG1..E1-P1B-NEG6`: required fail-closed pin/mutation cases.
- `E1-P1B-RUNTIME1`: focused installer/project-context/Doctor/MAP-BEFORE-WORK results.

## E2 - P2 Evidence

Matching plan items: `P2-A`, `P2-B`.

- `E2-P2A-CLASS1`: project-eval ownership/lifecycle classification.
- `E2-P2A-EVAL1`: normal project-eval setup and PASS evidence.
- `E2-P2B-SOURCE1`: clean source commit/tree/object binding and Anvien detect-changes.
- `E2-P2B-DRIFT1`: derived governance regeneration and drift PASS without historical mutation.

## E3 - P3 Evidence

Matching plan items: `P3-A`, `P3-B`.

- `E3-P3A-MINT1`: one-version selection, artifact identity, inventory/checksum/safety evidence.
- `E3-P3A-SEAL1`: immediate durable seal and fresh remote-derived byte verification.
- `E3-P3B-PILOT1`: fresh package-only install/adoption/pin/eval/Doctor/MAP-BEFORE-WORK matrix.
- `E3-P3B-GATE1`: regression/security/provider-neutral/technical prepare evidence.
- `E3-P3B-PUSH1`: branch push and local/remote match from fresh remote-derived worktree.

## Closure Evidence

Pending. Final verdict must be one of the exact user-specified labels. No promotion or final approval is allowed in this task.
