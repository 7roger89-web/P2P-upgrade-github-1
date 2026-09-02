# P2P-MPFB2 provisioning root drift ISSUE 56 Evidence Ledger

## Metadata

- Date: `2026-09-02`
- Plan: `docs/plans/2026-09-02-p2p-mpfb2-provisioning-root-drift-01/2026-09-02-p2p-mpfb2-provisioning-root-drift-01-plan.md`
- Evidence: `docs/plans/2026-09-02-p2p-mpfb2-provisioning-root-drift-01/2026-09-02-p2p-mpfb2-provisioning-root-drift-01-evidence.md`
- Benchmark: `docs/plans/2026-09-02-p2p-mpfb2-provisioning-root-drift-01/2026-09-02-p2p-mpfb2-provisioning-root-drift-01-benchmark.md`
- Actual status: `docs/plans/2026-09-02-p2p-mpfb2-provisioning-root-drift-01/2026-09-02-p2p-mpfb2-provisioning-root-drift-01-actual-status.md`

## Evidence Rules

The evidence file explains why the work is known to be correct.

- Evidence is current, exact-subject-bound, and traceable to source, filesystem, command output, runtime, or report.
- User-supplied values are recorded as declared inputs, not independent proof, until reverified.
- Root-delta and pinned-byte evidence must precede any cleanup, source edit, or manifest decision.
- Runtime evidence must distinguish each gate and stop at the first downstream blocker.
- Evidence IDs are stable and phase-scoped; long metric tables belong in the benchmark ledger.

### Evidence ID Naming

Use stable phase-scoped IDs in the form `E<phase>-<item>-<kind><n>`.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-USER1`: User-declared ISSUE=56 inputs: canonical main/tree, runtime root, expected/observed hashes, MPFB2 version/release pin, and execution boundary. Pending independent verification.
- `E0-P0A-GIT1`: Current working directory contains `.git` but Git commands report `not a git repository`; current metadata is preserve-only and must not be repaired.
- `E0-P0A-HIST1`: Prior runtime evidence says addon initialization passed and the route previously stopped at GLB skeleton validation; historical evidence is context only and must not substitute for the fresh run.
- `E0-P0A-REMOTE1`: Fresh clone/fetch from `https://github.com/7roger89-web/P2P-upgrade-github-1.git` bound `origin/main`, `HEAD`, and tree to `e7c040d87dacf7b5cfee1e57536edc0b27f5768b` / `9649785f0104259bac05b244a2162e2a7321657f`; fetch reached `Merge PR #57: accept omitted optional skin.skeleton`.
- `E0-P0A-WORKFLOW1`: `python scripts\\p2p_workflow.py inspect --request ... --json` classified the request as a bounded direct task with no Goal Contract required; it did not authorize scope expansion.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-SUBJECT1`: Fresh exact-main checkout exists at `.tmp\\issue56-fresh-subject-20260902`; `origin` is the requested repository, `origin/main`, `HEAD`, and `HEAD^{tree}` match the exact canonical SHA/tree.
- `E1-P1A-MAP1`: The canonical root contract is `.p2p/system/p2p_capabilities/mpfb_adapter.py:187-214`; `hash_provisioned_root()` hashes every regular file by stable relative POSIX path and excludes only the explicitly supplied manifest file. The entrypoint reuses that function at `mpfb_blender_entrypoint.py:230-236`.
- `E1-P1A-HASH1`: Runtime MPFB root is `D:\\AI\\P2P_runtime\\mpfb2-runtime-01\\mpfb2`. Its current 3,336-file, manifest-excluded computed root is `10ebf09a8b425f6e1081f9624ccf9365e471522b01527820e89d27b20de705bf`; the manifest records `f6907ef03674ddc995e8b0fdd988e9a003cad61df0d4f707e2a7aaeda4d4e788`.
- `E1-P1B-ARCHIVE1`: Existing pinned archive `D:\\AI\\P2P_runtime\\mpfb2-runtime-01\\staging\\mpfb2-80919fa4682335c41847f761a4d79dcad4124732.zip` has SHA-256 `9a1efbb7e42590a72404be35a2a71082dd6e5cd9472167f4a977d336e77e7d20`, matching `runtime-manifest.json`; its computed manifest-excluded root is exactly `f6907ef03674ddc995e8b0fdd988e9a003cad61df0d4f707e2a7aaeda4d4e788`.
- `E1-P1B-DELTA1`: Complete path-level comparison is recorded in `.tmp\\issue56-root-delta-20260902.json`. It found exactly `526` `ADDED`, `0` `MODIFIED`, and `0` `DELETED` paths: every added path is an immediate `.pyc` file under a `__pycache__` directory, with no unknown delta.
- `E1-P1B-PIN1`: The runtime has `3,336` non-manifest files versus `2,810` pinned archive files; all `2,810` pinned paths are present and byte-identical. MPFB2 commit `80919fa4682335c41847f761a4d79dcad4124732` and tree `189a1d6694515ecfbdc40067218c5024389b4e43` are proven from the existing staged Git object and manifest/archive.
- `E1-P1B-ASSET1`: All four manifest-bound CORE_CC0 assets match their manifest SHA-256 values; the full pinned path map has no modified/deleted entries.
- `E1-P1B-CLASS1`: Exact evidence selects `HASH_SCOPE_DEFECT=YES`: the current hash scope includes 526 post-provisioning Python bytecode files absent from the pinned archive. `RUNTIME_CLEANUP_DEFECT=NO` and `PINNED_RUNTIME_CORRUPTION=NO`; no manifest update or pinned restoration is authorized.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-IMPACT1`: Fresh separate capability-subtree Anvien graph on exact canonical main reports `mpfb_adapter.py` with 92 symbols, 80 local relationships, 3 linked flows, and HIGH file risk; exact `hash_provisioned_root` impact is HIGH with two same-file callers, `build_execution_plan` and `execute_plan`. The graph limitation for the unresolved cross-file entrypoint import is recorded, not treated as zero impact.
- `E2-P2A-FIX1`: Candidate `.p2p/system/p2p_capabilities/mpfb_adapter.py:187-216` changes only the root hash docstring and the exact predicate `relative_path.parent.name == "__pycache__" and relative_path.suffix == ".pyc"`; the manifest exclusion and symlink/reparse checks remain intact.
- `E2-P2A-ROOT1`: With the existing runtime unchanged, candidate `hash_provisioned_root(D:\\AI\\P2P_runtime\\mpfb2-runtime-01\\mpfb2, exclude=...\\provisioning-manifest.json)` returns `f6907ef03674ddc995e8b0fdd988e9a003cad61df0d4f707e2a7aaeda4d4e788` while 526 generated `.pyc` files remain present.
- `E2-P2A-BOUNDARY1`: Isolated direct probe proves an approved immediate-child `__pycache__/*.pyc` leaves the hash unchanged, an unknown file inside `__pycache__` changes it, and a `.pyc` outside `__pycache__` changes it.
- `E2-P2B-TEST1`: Focused tests added at `tests/test_p2p_game_truyen_mpfb_adapter_01.py:329-370` cover pinned source mutation, pinned asset byte mutation, approved generated bytecode, unknown cache extra, outside-cache bytecode, and exact manifest root binding.
- `E2-P2B-TEST2`: `python -m unittest tests.test_p2p_game_truyen_mpfb_adapter_01.AdapterBoundaryTests -v` passes `22/22`; `python -m compileall -q .p2p scripts tests` exits 0 with one unrelated pre-existing SyntaxWarning; `python -m compileall -q .p2p/system/p2p_capabilities tests/test_p2p_game_truyen_mpfb_adapter_01.py` and `git diff --check` pass.
- `E2-P2B-BUILD1`: `python -B scripts\\doctor.py --package . --role development --json` reaches package checks but returns `ok=false` on pre-existing `governance-drift` entries; no Issue 56 source/runtime repair was made for that unrelated package-wide drift.
- `E2-P2B-DETECT1`: Fresh candidate Anvien analysis and detect-changes evidence must be rerun after final ledger/report files are added; the pre-ledger detection already identified only the two intended implementation files plus the intended test file.

## E3 - P3 Evidence

Matching plan item(s): `P3-A`

Pending exactly-one real continuation evidence. P3 may run only after the source checkpoint is bound and the reconciled hash is freshly reverified.

## Closure Evidence

P2 implementation evidence is complete; final detect-changes, commit hash, coder report, one real continuation, supervisor report, and requested terminal fields remain pending.
