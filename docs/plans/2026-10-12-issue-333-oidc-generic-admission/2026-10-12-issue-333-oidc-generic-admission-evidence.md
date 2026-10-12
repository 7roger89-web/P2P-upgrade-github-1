# Issue 333 OIDC Generic Admission Evidence Ledger

## Metadata

- Date: `2026-10-12`
- Plan: `docs/plans/2026-10-12-issue-333-oidc-generic-admission/2026-10-12-issue-333-oidc-generic-admission-plan.md`
- Evidence: `docs/plans/2026-10-12-issue-333-oidc-generic-admission/2026-10-12-issue-333-oidc-generic-admission-evidence.md`
- Benchmark: `docs/plans/2026-10-12-issue-333-oidc-generic-admission/2026-10-12-issue-333-oidc-generic-admission-benchmark.md`
- Actual status: `docs/plans/2026-10-12-issue-333-oidc-generic-admission/2026-10-12-issue-333-oidc-generic-admission-actual-status.md`

## Evidence Rules

Evidence IDs are phase-scoped. Direct repo/runtime/provider output outranks Writer narrative. No self-reported JSON alone can close the trust boundary.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-MAIN1`: canonical main at planning time is `3cc481a2918cfcf108b27cd30260e609fdfbd7c0`; merged PR #345 provides PROMPT_ONLY only.
- `E0-P0A-ISSUE1`: Issue #333 remains OPEN and still requires one real non-Arena/non-Codex repo-read canary plus independent Supervisor review.
- `E0-P0A-CANARY1`: Actions run `38213449144` proved GitHub Copilot CLI (not Arena/Codex) executed `git rev-parse HEAD`, READ on `.agents/skills/scope-reality-check/SKILL.md`, and `sha256sum`; independent step validated the returned receipt.
- `E0-P0A-CANARY2`: Actions run `38217565828` additionally minted a GitHub OIDC token with audience `p2p-generic-repo-read:<evidence sha256>`; independent verifier fetched GitHub OIDC JWKS, verified RS256, and checked repository/run/workflow_sha/github-hosted claims. Result `B1_GITHUB_OIDC_VERIFY=PASS`.
- `E0-P0A-PROVIDER1`: GitHub artifact attestation attempt in run `38217433789` failed because user-owned private repositories do not support that feature; the design dropped this path rather than weakening evidence.
- `E0-P0A-C201`: C20 `HostCapabilityProfile` and C21 `HostDiscoveryRecord` exist on main and explicitly remain declarative/non-certifying surfaces.
- `E0-P0A-C361`: C36 `p2p-host-attestation/1` exists, but its local machine/ledger proof does not itself prove that the declared external AI recipient read the repo; it is not used to launder B1.
- `E0-P0A-ANVIEN1`: current `AGENTS.md` sets `ANVIEN_ENABLED=NO`; relationship-count commands in the generic planner/coder template are N/A for this execution.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

Pending implementation.

## E2 - P2 Evidence

Matching plan item(s): none.

N/A — no P2 phase is planned.

## Closure Evidence

Pending final exact-head Shield, live canary, branch diff, coder report, and independent Supervisor verdict.
