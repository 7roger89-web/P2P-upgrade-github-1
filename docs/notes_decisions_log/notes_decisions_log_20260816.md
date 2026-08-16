# Notes and Decisions Log — 2026-08-16

## P2P-C15 Bounded Foreground Delegation & Worker Handoff Controller

- Decision: implement C15 as one additive C11/C12 adapter with deterministic `DIRECT`/`DELEGATE`/`BLOCKED` selection before execution-class/profile resolution.
- Boundary: one synchronous child callback at depth one; no grandchildren, parallelism, background work, scheduler, queue, remote bridge, second router, second executor, or second ledger.
- Safety: child permission/scope must be a subset of the parent; child delegation is false; output is proposal-only; parent independently verifies current candidate/evidence before C11 `DONE`.
- Identity: preserve `UNKNOWN`; generic work may proceed without identity proof; identity-required work blocks without supported host proof. No live host child probe was simulated.
- Governance: C09 remains blocked/unavailable, C08 remains deferred, canonical quorum remains 8/8, and Aesthetica remains optional/noncanonical.
- Validation: focused C15 23 tests, C15/C11/C12 63 tests, full suite 198 tests, beginner/UIUX paired eval PASS, DT1-DT24 PASS, doctors/secret scan/drift/package candidate PASS.
- Artifact: unpromoted candidate `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4\.tmp\p2p-c15\candidates\P2P-8.4.7-C-Codex-Edition-v15-c15-candidate.zip`; official `.19` unchanged.
- Limitation: no `.git` directory; Anvien change detection returns Git exit 129 and no commit was created.
- Coder report: `reports/coder/rp_coder_260816_002800_by_gpt-5-codex_p2p-c15-bounded-foreground-delegation.md`.

## P2P-C16 Durable Roadmap and Release Lineage Foundation

- Decision: add one compact `governance/development-control.json` projection that references existing Goal/project status/Execution Ledger/FACT_LEDGER/Live Specs/approval/drift authorities; it is not a second ledger or certification system.
- Authority: official `8.4.7-C-codex.19` remains `PROMOTED_VERIFIED` with SHA-256 `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`; C14 approval/report references remain bound and the ZIP was not modified.
- Recovery: fresh-process status derives C10-C15 complete, C09 `BLOCKED / EVENT_EVIDENCE_UNAVAILABLE`, C08 `DEFERRED`, C16 `ACTIVE`, and C17 `PLANNED — Safe bounded parallel foreground execution`; C15 foundation is ready while live delegation remains `NOT_CERTIFIED`.
- Lineage: the current `.15` source and C15 `.15` candidate remain explicitly stale/unpromoted; root cause is `RELEASE_BASELINE_NOT_PROPAGATED` with `PACKAGER_INPUT_STALE` and `DEVELOPMENT_BRANCH_METADATA_DRIFT`. The release builder now blocks below `.19` before runtime-lock/checksum/stage writes and never trusts filenames.
- Validation: focused C16 R1-R18 plus embedded-control compatibility test `19/19` PASS; affected regression `116/116` PASS; full suite `216/216` PASS before the final embedded-control test addition, then focused suite `19/19` PASS. Final full regression rerun is recorded in the coder/supervisor reports.
- Governance: runtime lock refreshed with 836 protected files; drift and development doctor PASS; project eval validation/gate PASS; secret scan PASS. No C17 implementation, promotion, release finalization, network, hooks, or external connector was used.
- Limitation: no `.git` directory; Anvien detect-changes returned `Git diff failed: exit status 129`; no commit is claimed.
