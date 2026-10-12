# P2P Generic Repo-Read Admission Evidence Ledger

## Metadata

- Date: `2026-10-12`
- Plan: `docs/plans/2026-10-12-p2p-generic-read-admission/2026-10-12-p2p-generic-read-admission-plan.md`
- Evidence: `docs/plans/2026-10-12-p2p-generic-read-admission/2026-10-12-p2p-generic-read-admission-evidence.md`
- Benchmark: `docs/plans/2026-10-12-p2p-generic-read-admission/2026-10-12-p2p-generic-read-admission-benchmark.md`
- Actual status: `docs/plans/2026-10-12-p2p-generic-read-admission/2026-10-12-p2p-generic-read-admission-actual-status.md`

## Evidence Rules

Only current source, exact runtime output, GitHub-signed provenance and exact-head CI count as closure evidence. Actor-authored prose or receipt JSON alone does not authorize generic execution.

## E0 - P0 Evidence

- `E0-P0A-ISSUE1`: Issue #333 is OPEN and requires generic repo-read, real non-native canary, exact path/hash, Shield and independent Supervisor.
- `E0-P0A-SRC1`: current main `skill_consumption.py` preserves bounded source selection/loading and no admitted generic signed-evidence lane.
- `E0-P0A-SRC2`: current main Control Tower prepares skill handoff only for native ARENA/CODEX; prompt-only generic path is separate and non-authorizing.
- `E0-P0A-SRC3`: current main CLI exposes `prepare-prompt-only` and no trusted generic evidence-file input.
- `E0-P0A-SRC4`: focused tests prove prompt-only never starts a session and blocks project-internal inline disclosure.
- `E0-P0A-CANARY1`: GitHub Actions run `38213449144`, job `114692621545`, actor `GITHUB_COPILOT_CLI_ACTIONS`, exact tool trace read `.agents/skills/scope-reality-check/SKILL.md`, observed SHA-256 `e2b894509e4c8987d5d509edb98a06ee85ad98ebae088b88edde6efe40bd7688`, `SKILL_CONSUMPTION=CONSUMED`, `GENERIC_EXACT_REPO_READ`; this proves read/apply for one external actor but is not yet runtime admission.

## E1 - P1 Evidence

- `E1-P1A-RUN1`: run `38235241033`, job `114764178308`, exact head `6020a3c7fbbda46ccc572678916ab828faa25dac`, SUCCESS; `B1_REAL_EXTERNAL_ACTOR_READ=PASS`; exact skill SHA-256 `e2b894509e4c8987d5d509edb98a06ee85ad98ebae088b88edde6efe40bd7688`.
- `E1-P1B-OIDC1`: same run emits `B1_GITHUB_OIDC_VERIFY=PASS`; evidence SHA-256 `7db1aeda5f42c3d6e386b53fd41befb04d08c2bb9137725747764a2e8d9dfd93`; workflow SHA equals exact head; GitHub-hosted runner and push/branch claims verified.
- `E1-P1B-CORRECTION1`: `actions/attest` was experimentally rejected because GitHub Artifact Attestations are unavailable for this user-owned private repo. The dead path was removed; the accepted primitive is GitHub Actions OIDC JWT verified against discovery/JWKS and exact claims/evidence digest.
- `E1-P1B-TRIGGER1`: a temporary `pull_request` canary trigger was removed because GitHub checks out a synthetic merge SHA there. The final canary uses exact feature-branch push evidence.

## E2 - P2 Evidence

- `E2-P2A-SRC1`: `generic_repo_read_evidence.py` validates actor/repo/revision/probe, GitHub RS256 signature, evidence-digest audience, trusted workflow, run, push branch ref, github-hosted runner and <=3600s freshness.
- `E2-P2A-NEG1`: C21-only remains BLOCKED; bad/missing/stale/mismatched signed evidence fails closed.
- `E2-P2A-TEST1`: negative matrix covers malformed schema, missing token, bad signature/audience/repo/revision/actor/probe path/hash/workflow/run, pull_request event, non-branch ref, self-hosted runner and stale evidence.
- `E2-P2B-LIVE1`: exact-head canary production gate calls the real Skill Consumption Wire and Control Tower and succeeds with `GENERIC_EXACT_REPO_READ`.
- `E2-P2B-CLI1`: CLI exposes explicit discovery/evidence-file inputs and consumes the OIDC JWT via `P2P_GENERIC_READ_OIDC_JWT`.
- `E2-P2B-CACHE1`: cached generic handoff is revalidated and rejects stale evidence.
- `E2-P2B-SHIELD1`: exact-head Shield `38235247660`, job `114764200901`, SUCCESS: focused 366 PASS; FW02 26 PASS; QI 44 PASS; AERG 32 PASS; governance 6 PASS; Slice PASS; OSV/Zizmor VERIFIED; CI acceptance PASS.
- `E2-P2B-ZIZMOR1`: a temporary +1 `adhoc-packages` diagnostic from the pinned Copilot CLI install was localized/documented; final current-workflow diagnostic returns to baseline `FAIL / 22 findings` and is not claimed clean.

## Closure Evidence

Source/runtime scope is technically verified. This closure-artifact commit must receive fresh exact-head canary + Shield; independent Supervisor remains the final acceptance gate. Issue #333 remains OPEN.
