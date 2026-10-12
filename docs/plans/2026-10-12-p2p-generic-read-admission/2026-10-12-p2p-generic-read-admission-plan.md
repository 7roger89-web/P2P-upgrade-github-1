# P2P Generic Repo-Read Admission Plan

## Metadata

- Date: `2026-10-12`
- Status: `ready-for-supervisor`
- Plan: `docs/plans/2026-10-12-p2p-generic-read-admission/2026-10-12-p2p-generic-read-admission-plan.md`
- Evidence: `docs/plans/2026-10-12-p2p-generic-read-admission/2026-10-12-p2p-generic-read-admission-evidence.md`
- Benchmark: `docs/plans/2026-10-12-p2p-generic-read-admission/2026-10-12-p2p-generic-read-admission-benchmark.md`
- Actual status: `docs/plans/2026-10-12-p2p-generic-read-admission/2026-10-12-p2p-generic-read-admission-actual-status.md`

## Goal

Close Issue #333's remaining B1 trust boundary without reviving PR #334: admit `GENERIC_EXACT_REPO_READ` only when a non-Arena/non-Codex executor presents current C21 discovery evidence plus independently verifiable GitHub-signed evidence that binds the exact repository, revision, skill path/hash, workflow/run and consumption receipt.

## Rules

- Supreme Law and current `AGENTS.md` outrank this plan.
- Reuse the existing Skill Consumption Wire and C20/C21 contracts; no second router, registry, daemon, vector DB or provider-specific Claude/Grok/Manus adapter.
- `PROMPT_ONLY != EXECUTION_AUTHORIZATION`.
- Signed evidence is necessary but never widens task/Owner permissions.
- Any missing verifier, invalid signature, wrong signer/source/repo/head/skill/hash/host, stale evidence or malformed receipt fails closed.
- Arena/Codex behavior stays byte-semantically unchanged.
- `ANVIEN_ENABLED=NO` by current `AGENTS.md`; relationship evidence uses current source/tests/runtime instead.
- Record evidence and benchmark deltas as work completes.
- Independent Supervisor review is required before merge.

## Problem

Current `main` ships the safe `GENERIC_PROMPT_ONLY` slice. The old generic execution path remains absent/fail-closed because C21 JSON alone cannot prove the declared external actor actually read the repository. A live GitHub Copilot CLI canary now proves a real non-Arena/non-Codex actor can read and apply the exact repo-native skill, but runtime admission still needs a verifier-backed trust primitive.

## Scope

- Add a bounded GitHub Actions canary that produces and verifies a GitHub-signed evidence subject for the real Copilot CLI read/apply run.
- Add one verifier/admission path to the existing Skill Consumption Wire for that evidence.
- Wire existing Control Tower/CLI surfaces only as required by Issue #333.
- Add focused happy/fail-closed tests and exact-head Shield evidence.

## Non-Goals

- Universal attestation for Claude/Grok/Manus.
- Release, deploy, promotion or auto-merge.
- New generic host registry/router.
- Trusting actor-authored JSON or C21 provenance labels by themselves.
- Reusing or merging old PR #334 code wholesale.

## Requirements

1. Trusted evidence must cryptographically bind a subject digest to GitHub Actions provenance and exact source revision.
2. Evidence payload must bind actor, repo, revision, selected skill path/hash and `p2p-skill-consumption-receipt/1`.
3. Admission revalidates C21 host/project/freshness/transport/read capability and signed evidence; both are required.
4. Signed evidence verification must pin repository + signer workflow + source digest and reject self-hosted provenance for this lane.
5. CLI accepts the evidence as a file input; no hidden network fallback when evidence or verifier is unavailable.
6. Cached generic handoff reuse revalidates current trusted evidence.
7. NO_MATCH remains honest and does not require generic read evidence.

## Acceptance Criteria

- Real GitHub Copilot CLI canary yields actor-bound evidence and GitHub OIDC cryptographic verification PASS on exact branch head.
- Positive generic selected-skill path returns `GENERIC_EXACT_REPO_READ` with exact skill path/hash only when C21 + signed evidence both validate.
- Negative controls block forged subject, wrong repo/head/host/skill/hash/signer, stale evidence, self-hosted provenance, missing/invalid OIDC token or verifier network, malformed evidence and C21-only input.
- Arena/Codex regression tests pass.
- Shield focused suite passes on exact PR head.
- Independent Supervisor reviews exact final head before merge.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish current main reality.
  - Work Steps: inspect Issue #333, `skill_consumption.py`, Control Tower, CLI, focused tests, live canary evidence and current main drift.
  - Implementation Gate: no runtime editing before actual-status matrix is populated.
  - Acceptance: actual-status identifies prompt-only as correct, generic runtime as missing/fail-closed, and signed external read proof as experimentally proven but not admitted.

### P1: Signed external-read evidence

- Phase Goal: produce a GitHub-verifiable evidence subject for one real non-Arena/non-Codex actor.
- Phase Boundary:
  - In scope: one canary workflow and exact-run evidence.
  - Out of scope: runtime admission code.
  - Dependencies: GitHub Actions, Copilot CLI, GitHub Actions OIDC.
- Ordered Slice List:
  - P1-A: Run signed Copilot read/apply canary.
  - P1-B: Verify signer/source/subject constraints independently.

- [x] P1-A: Run signed Copilot read/apply canary.
  - Goal: prove actual tool read + skill application and sign the resulting evidence subject.
  - Scope Boundary:
    - Editable: `.github/workflows/p2p-b1-real-generic-read-canary.yml`
    - Inspect-only: skill file, Issue #333, GitHub official attestation contract.
    - Preserve-only: production runtime.
    - Out of scope: Control Tower authorization.
  - Non-Goals: no production code.
  - Pre-flight Questions: UI/DB/Docker/Playwright = N/A; behavior target is the GitHub Actions run; external side effect is one attestation write.
  - Work Steps:
    1. Run Copilot CLI with read-only tool allowlist, validate exact HEAD/path/hash and tool transcript.
    2. Build a canonical evidence subject; bind its SHA-256 into the GitHub Actions OIDC audience; verify RS256 using GitHub discovery/JWKS plus exact repo/workflow/source/run/ref and GitHub-hosted-runner claims.
  - Implementation Gate: GitHub Actions OIDC is available to this private repository with `id-token: write`; Artifact Attestations were experimentally rejected for this user-owned private repo and are not used.
  - Acceptance: exact run success with `B1_REAL_EXTERNAL_ACTOR_READ=PASS` and signed-evidence verification PASS.
  - Evidence Targets: E1-P1A-RUN1, E1-P1A-ATTEST1.
  - Actual-status Update: external proof becomes bound-correct for one actor.
  - Commit Boundary: commit after exact run passes.

### P2: Runtime admission

- Phase Goal: admit only verified signed external-read evidence through the existing wire.
- Phase Boundary:
  - In scope: `skill_consumption.py`, Control Tower/CLI only as required, focused tests.
  - Out of scope: provider-specific adapters and release.
  - Dependencies: P1 PASS.
- Ordered Slice List:
  - P2-A: Add verifier-backed evidence validation.
  - P2-B: Wire CLI/Control Tower and cached-session revalidation.

- [x] P2-A: Add verifier-backed evidence validation.
  - Goal: replace B1 unconditional fail-closed only for a signed, current, source-bound evidence subject.
  - Scope Boundary:
    - Editable: existing skill-consumption invariant family plus one small evidence verifier helper if SRP requires it.
    - Inspect-only: host selection/C21 and current prompt-only code.
    - Preserve-only: native ARENA/CODEX and prompt-only.
    - Out of scope: provider adapters.
  - Work Steps:
    1. Validate evidence schema/field types/freshness and exact actor/repo/head/skill/hash/receipt binding.
    2. Verify the GitHub OIDC signature and exact claims; discovery/JWKS/network failure or any mismatch blocks.
  - Implementation Gate: P1 signed canary PASS.
  - Acceptance: positive fixture + real signed evidence admitted; forged/missing variants block.
  - Evidence Targets: E2-P2A-SRC1, E2-P2A-TEST1.
  - Actual-status Update: generic selected-skill lane partial -> bound-correct.
  - Commit Boundary: commit after focused tests pass.

- [x] P2-B: Wire CLI/Control Tower and cached-session revalidation.
  - Goal: make existing start/next paths consume the same evidence without bypass.
  - Scope Boundary: edit only existing CLI/Control Tower argument plumbing and tests.
  - Work Steps:
    1. Add explicit evidence-file input beside current C21 discovery input.
    2. Revalidate evidence before generic prompt/session reuse; preserve NO_MATCH and native paths.
  - Implementation Gate: P2-A PASS.
  - Acceptance: direct API, CLI, next-session and cached-session tests close the same invariant.
  - Evidence Targets: E2-P2B-CLI1, E2-P2B-CACHE1.
  - Actual-status Update: all sibling entrypoints aligned.
  - Commit Boundary: separate traceable commit.

- [ ] Pn-A: Call Supervisor for exact-head review.
  - Goal: independent acceptance of source, tests, canary and Shield.
  - Implementation Gate: all planned slices pass.
  - Acceptance: Supervisor PASS or explicit blocker; Writer does not self-merge.

- [x] Pn-B: Remove dead work created during this plan.
  - Goal: final diff contains no abandoned attestation experiment or stale helper.
  - Acceptance: the abandoned `actions/attest` path and PR-event canary trigger are removed; the final canary is exact-branch-push only.

- [ ] Pn-C: Close plan.
  - Goal: final exact-head Shield, coder report, notes log and handoff.
  - Acceptance: exact evidence recorded; no release/deploy/promotion.

## Risk Notes

- A GitHub signature proves workflow provenance, not arbitrary truth in a caller-controlled predicate; admission must pin the trusted workflow/source and validate the evidence subject produced by that workflow.
- Network/API availability for attestation verification is an irreducible runtime dependency; unavailable verification must BLOCK rather than fall back to self-report.


## Current closure checkpoint

- Source/runtime verification head: `6020a3c7fbbda46ccc572678916ab828faa25dac`.
- Exact-head B1 canary `38235241033`: SUCCESS; real external read PASS; GitHub OIDC verification PASS; production generic admission gate PASS.
- OIDC evidence SHA-256: `7db1aeda5f42c3d6e386b53fd41befb04d08c2bb9137725747764a2e8d9dfd93`.
- Exact-head Shield `38235247660`: SUCCESS; focused 366 PASS; FW02 26 PASS; QI 44 PASS; AERG 32 PASS; governance 6 PASS; Slice/CI acceptance PASS.
- Current-workflow diagnostic remains `FAIL / 22 findings`, equal to the known baseline shape and not claimed clean.
- Next gate: fresh CI on this closure-artifact commit, then independent Supervisor. Writer does not merge.
