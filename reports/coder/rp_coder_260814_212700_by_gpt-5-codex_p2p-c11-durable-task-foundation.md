# Coder Report: P2P-C11 Durable Task State and Minimal Dependency Graph Foundation

Status: READY FOR INDEPENDENT REVIEW

## Metadata

- Review scope: bounded P2P-C11 durable task state and minimal dependency graph foundation.
- Authority: attached P2P-C11 request, repository `AGENTS.md`, C10 evidence/permission contracts, and the C11 plan ledgers.
- Invariant family: durable task projection, dependency/state safety, evidence-bound completion, owner/capability/permission gates, interruption reconstruction, and package boundary.
- Git reference: unavailable; `anvien detect-changes --repo P2P-8.4.6-C-Codex-Edition-v4 --scope all` returned `Git diff failed: exit status 129`; no Git repository was initialized.
- Protected facts: official `.15` and C10 `.20` remain preserve-only; C09 remains `BLOCKED / EVENT_EVIDENCE_UNAVAILABLE`; C08 was not rerun.

## Implementation

- `.p2p/system/p2p_capabilities/task_state.py`: standard-library-only logical owner, task contract, seven-state transition kernel, dependency graph, EvidenceClaim-bound completion, preflight/owner gates, plan revision provenance, deterministic selection/handoff, checkpoint/resume classification, atomic state projection, and additive events in the existing Execution Ledger.
- `.p2p/system/p2p_capabilities/__init__.py`: exports the additive task-state surface without adding a capability identity or router.
- `scripts/p2p_task_state.py`: explicit foreground CLI for init/show/ready/transition/preflight/complete/checkpoint/resume/handoff/events/revise/owner operations; runtime lookup works from checkout and installed `.p2p/system/scripts` layout.
- Final hardening: malformed task-list entries are rejected with a bounded `TASK_INPUT_ENTRY_MUST_BE_OBJECT` error instead of being silently discarded.
- `tests/test_p2p_task_state.py`: six isolated behavioral tests covering contract/graph, evidence, gates, revision/checkpoint/resume/handoff, durable store/ledger, and subprocess CLI.
- `scripts/package_release.py`, `install.ps1`, `install.sh`: package and installer allowlists include the task module and CLI; embedded `VERSION` remains `.15`.

## Boundary Decision

The task layer is a durable projection and synchronous foreground control plane. It does not create agents, select models/providers, install capabilities, grant permissions, spawn workers, schedule work, retry in the background, claim host identity, or create a second ledger/database.

## Verification

- Focused task-state tests: 20/20 PASS in 1.344 seconds.
- Full unit suite: 139/139 PASS in 162.323 seconds.
- Decision Trace: 24/24 PASS; exact canonical 8 and `8/8`; AESTHETICA noncanonical.
- Project eval v2: validation and gate PASS; 5 paired cases, no regressions.
- Capability doctor: PASS; canonical denominator 8, no provider installation, trust boundary denies permission grants.
- Governance drift: PASS; only known noncanonical/historical reference findings.
- Security suite: 2/2 PASS.
- Development doctor: PASS.
- Package lifecycle: candidate build/extracted verify PASS; 401 content files and 402 checksums; installed-runtime CLI `--help` smoke PASS.
- Compileall and targeted `py_compile`: PASS.

## Candidate Boundary

- Candidate label: `.tmp/p2p-c11-candidate-8.4.7-C-codex.15-r2.zip`.
- Embedded package version: `8.4.7-C-codex.15`.
- Candidate SHA-256: `684018d1a563e35e32eed2e06bbfee3e9625d9caef95771bf04a848fa3868926`.
- This is a new unpromoted candidate; no release/promotion/approval command was run.

## Handoff

Supervisor Review must verify the source, same-invariant sibling surfaces, current evidence, candidate/version separation, canonical/C09 preservation, and the bounded workflow-helper timeout before closure.
