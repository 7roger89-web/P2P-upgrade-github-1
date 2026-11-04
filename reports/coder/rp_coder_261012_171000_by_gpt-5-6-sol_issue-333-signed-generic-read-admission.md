# Coder Handoff Report: Issue #333 Signed Generic Repo-Read Admission

Issue #333 bounded trust/admission workstream. Candidate only — no merge, release, deploy or promotion.

## Result

Implemented the minimum fail-closed path from a proven real external repo/skill read to `GENERIC_EXACT_REPO_READ` admission. The candidate reuses C20/C21 and the existing Skill Consumption Wire; it adds no second router, registry, daemon, scheduler, state store or provider-specific Claude/Grok/Manus adapter.

## Exact bases

- Canonical main/base: `db9d39798ddb80990757c65ddf2eb95f9f734fd6`
- Source/runtime verification head: `6020a3c7fbbda46ccc572678916ab828faa25dac`
- PR: #348
- External actor: `GITHUB_COPILOT_CLI_ACTIONS`
- Probe: `.agents/skills/scope-reality-check/SKILL.md`
- Probe SHA-256: `e2b894509e4c8987d5d509edb98a06ee85ad98ebae088b88edde6efe40bd7688`

## Invariant family

`C21_VALID && GITHUB_SIGNED_ACTOR_BOUND_READ_VALID => GENERIC_EXACT_REPO_READ`

- C21-only != trusted actor read.
- Self-authored receipt != authorization.
- Missing/bad/stale OIDC evidence => BLOCK.
- PROMPT_ONLY != execution authorization.
- Native ARENA/CODEX stay native.
- Evidence never widens task/Owner permission.

## Implementation surfaces

- `.p2p/system/p2p_capabilities/generic_repo_read_evidence.py`: GitHub OIDC RS256/evidence verifier.
- `.p2p/system/p2p_capabilities/skill_consumption.py`: existing generic handoff gate now requires C21 + verified evidence.
- `.p2p/system/p2p_capabilities/control_tower_handoff.py`: start/recommend/next/cached reuse use the same gate.
- `scripts/p2p_control_tower.py`: explicit discovery/evidence inputs; JWT from `P2P_GENERIC_READ_OIDC_JWT`.
- canary workflow: pinned Copilot CLI read/apply + OIDC binding + production-gate proof.
- focused evidence/admission tests plus existing native/PROMPT_ONLY regressions.

## Reality correction

The first signed-evidence attempt used `actions/attest`, but GitHub rejected persistence because Artifact Attestations are unavailable for this user-owned private repository. That dead path was removed. Final proof uses GitHub Actions OIDC: evidence SHA-256 is embedded in JWT audience and the verifier checks GitHub discovery/JWKS, RS256, repo/workflow/source/run/ref/runner/time claims.

A temporary PR-event canary was also removed because GitHub checks out a synthetic merge SHA for `pull_request`; the exact-revision admission invariant correctly uses branch-push evidence.

## Validation

### Live B1 + production gate

Run `38235241033`, job `114764178308`, exact head `6020a3c7fbbda46ccc572678916ab828faa25dac`: SUCCESS.

- `B1_REAL_EXTERNAL_ACTOR_READ=PASS`
- `B1_GITHUB_OIDC_VERIFY=PASS`
- evidence SHA-256 `7db1aeda5f42c3d6e386b53fd41befb04d08c2bb9137725747764a2e8d9dfd93`
- workflow SHA = exact head
- production generic admission gate = PASS

### Exact-head Shield

Run `38235247660`, job `114764200901`, same head: SUCCESS.

- 366 focused PASS
- FW02 26 PASS
- Quality Intelligence 44 PASS
- AERG 32 PASS
- governance 6 PASS
- Slice PASS
- OSV/Zizmor VERIFIED
- CI acceptance PASS
- current-workflow diagnostic `FAIL / 22 findings` — baseline shape, not claimed clean

A one-off new Zizmor `adhoc-packages` finding from the pinned Copilot CLI install was handled by one localized documented ignore; final findings returned from 23 to baseline 22.

## Fail-closed matrix

Covers missing token, malformed schema, bad signature/audience/repo/revision/actor/probe path/hash/workflow/run, non-push event, non-branch ref, self-hosted runner, stale evidence, C21-only, false transport, mismatched discovery identity, cached stale evidence, NO_MATCH honesty and native ARENA preservation.

## E2E flow

`external actor -> exact repo/skill read -> independent trace validation -> canonical evidence -> GitHub OIDC -> crypto verification -> C21 revalidation -> existing skill router/load -> exact source-bound GENERIC_EXACT_REPO_READ handoff/session`

## Residual unverified surfaces

- Claude/Grok/Manus live proof: not claimed.
- Independent Supervisor: pending.
- Merge/Issue #333 closure: not authorized in Writer role.

## Handoff

This closure commit contains only plan/evidence/report/notes plus an induced allowlist-test update. After fresh exact-head canary + Shield PASS, hand PR #348 to independent Supervisor. Writer does not merge.
