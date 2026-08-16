# Coder Report: P2P beginner workflow

## Metadata

- Date: 2026-08-10
- Scope: upgrade the canonical P2P Codex Edition with a reusable beginner-facing project workflow
- Plan: `docs/plans/2026-08-10-p2p-beginner-workflow/2026-08-10-p2p-beginner-workflow-plan.md`
- Evidence: `docs/plans/2026-08-10-p2p-beginner-workflow/2026-08-10-p2p-beginner-workflow-evidence.md`
- Repository state: unpacked package without `.git`; no commit hash exists

## Invariant family map

| Family | Authority / SSOT | Implemented closure |
|---|---|---|
| Bounded goal and stop | `scripts/p2p_workflow.py`, `.agents/skills/p2p/SKILL.md` | Goal Contract, finite work list, measurable criteria, PASS/BLOCKED/REJECT, and stop reason |
| Project initialization and reuse | project-local `.p2p/` plus existing governance templates | idempotent profile/policy/status/evidence/ledger/capsule/eval initialization; valid artifacts are reused |
| Adaptive agent routing | eight `.codex/agents/p2p-*.toml` profiles and quorum guidance | smallest exact named-agent selection; explicit full quorum is preserved and never simulated |
| Project-specific eval | `scripts/p2p_eval.py`, eval schema | five bounded case types; valid suite reuse without overwrite |
| Governance continuity | existing FACT_LEDGER/Live Specs/Approval/Drift/doctor/runtime lock | helper references existing controls and maps only affected controls after changes |

## Implementation

- Added the single orchestration helper at `scripts/p2p_workflow.py`.
- Added project-specific eval design/reuse to `scripts/p2p_eval.py`.
- Wired normal entry guidance and related scope/eval/capsule/quorum/state guidance.
- Distributed and validated the helper through `install.ps1`, `install.sh`, `scripts/doctor.py`, and `manifest/package.json`.
- Added safe new/existing project fixtures and four direct workflow tests.
- Preserved the 152-file immutable source snapshot, eight agent identities, and existing governance semantics.

## Verification

- `python -m py_compile scripts/p2p_workflow.py scripts/p2p_eval.py scripts/doctor.py`: PASS.
- `python -m unittest discover -s tests -p 'test_*.py' -v`: PASS, 4 tests.
- `python scripts/p2p_workflow.py acceptance --package .`: PASS for new and existing fixtures; selective evidence reuse and PASS stop asserted.
- Fresh project install in `.tmp/fresh-installed-project-4`: installer PASS, installed doctor PASS, installed helper `run --acceptance` PASS with Vietnamese beginner report.
- Package doctor and final package drift/runtime-lock results are recorded in the companion evidence ledger after the last lock refresh.

## Scope and residual risks

- No application project was modified; acceptance uses safe deterministic fixtures only.
- No real project-quality eval score or live eight-thread Codex runtime proof is claimed.
- The unpacked package has no Git metadata, so no commit checkpoint was created.

## Handoff

The implementation is ready for independent supervisor acceptance. The supervisor report is the final acceptance authority.
