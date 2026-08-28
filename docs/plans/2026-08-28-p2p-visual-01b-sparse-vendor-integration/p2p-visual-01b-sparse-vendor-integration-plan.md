# P2P-VISUAL-01B Sparse Vendor Integration Plan

## 0. Metadata

- Date: 2026-08-28
- Status: in_progress
- Goal: bind the exact audited `awesome-gpt-image-2` prompt-construction skill as a sparse, on-demand, local vendor snapshot while preserving P2P's existing registry, router, progressive context, host projection, Manus packaging, quorum, and governance boundaries.
- Execution: `P2P-VISUAL-01B`
- Session: `P2P-VISUAL-01B-20260828-120349-f8e51c48409e`
- Parent: `P2P-VISUAL-01`
- Phase: `SPARSE_VENDOR_INTEGRATION`
- Execution root: `D:\AI\P2P_dev\P2P-canonical-runtime-01\.tmp\p2p-visual-01b-20260828-120349-f8e51c48409e`
- Canonical owner checkout: `D:\AI\P2P_dev\P2P-canonical-runtime-01`
- Base commit: `1cca4d20c243b5dcecd21f4fabec785fc99cfdfa`
- Base tree: `6693a193802b20c1fc8ce30f73f7d203841c8983`
- Upstream repository: `https://github.com/freestylefly/awesome-gpt-image-2`
- Upstream pinned commit: `9a7b2e9c39f816d6c699c2a133e11b6d8bfdc464`
- Upstream audited tree: `56b103dad637a95b9ec366eb7215459f28feb73e`

## 1. Scope and invariants

### In scope

- Acquire and re-verify the exact upstream commit/tree and selected source bytes.
- Vendor only the allowlisted prompt-skill files under a new versioned snapshot directory.
- Add one noncanonical `TYPE=SKILL` registry record with `LOCAL_VENDOR_SNAPSHOT`, `MODEL_ROUTABLE`, `ON_DEMAND`, no network, no credentials, disabled install, and explicit-only external render.
- Extend the existing vendor, routing, context, host-projection, Manus, governance, and regression evidence surfaces only where the new manifest requires it.
- Keep the asset out of the runtime snapshot while recording its unresolved rights decision and preserving the upstream reference in the vendored `SKILL.md`.
- Produce the exact handoff file, SHA-256 packet, candidate commit/tree, cleanup evidence, and fresh independent Supervisor report.

### Out of scope and hard stops

- No new router, provider, image API, renderer, runtime, framework, truth store, registry system, canonical identity, quorum member, or `PROVIDES` entry.
- No changes to the eight canonical identities or the 8/8 denominator.
- No modification of the canonical owner dirty checkout, release ZIP, v5 artifact, immutable baseline, or user projects.
- No upstream execution, dependency installation, authentication, website/app integration, gallery/data/template vendoring, or generator/install-script execution.
- No promotion, merge, push, deploy, release, live runtime claim, Arena claim, game-specific pipeline, or commercial rights claim.

### Acceptance terminal

The preferred terminal is `P2P_VISUAL_01B_SPARSE_VENDOR_CANDIDATE_READY_FOR_OWNER_GATE`. If any mandatory technical gate fails, use the exact applicable `BLOCKED`, `RECONCILIATION_REQUIRED`, `REJECTED`, or `FAILED` terminal and preserve the evidence.

## 2. P0 preflight result

P0 is complete before implementation:

- Canonical live `main` and the clean execution clone both bind to the required base commit/tree.
- The canonical owner checkout is materially dirty; it is preserve-only and will not be used as the mutation target.
- The execution clone is detached, clean, non-shallow, and passes connectivity-only `git fsck`.
- Live upstream `main` currently resolves to the required audited commit; the candidate remains pinned and will not silently upgrade.
- The full relevant capability, routing, context, execution-evidence, host, Manus, provider, optional-specialist, project-domain, trust, manifest, and test-eval SPEC files were read. No `SPEC-MAP.md` exists in this source tree, so the full relevant SPEC cluster is the reading record.
- Anvien was refreshed in the execution clone. Hidden `.p2p` implementation paths are not indexed by the current graph; filesystem and targeted test-file evidence will supplement that known limitation.
- The workflow preflight classified the request as separate bounded goals with no post-preflight Goal Contract creation. This plan is the bounded execution record and does not invent persistent project state.

## 3. Work phases

### P1-A — Exact upstream acquisition and sparse snapshot

#### Goal

Create an immutable, versioned local snapshot from the exact upstream pin and retain enough provenance to independently reproduce the selected-byte decision.

#### Work steps

1. Clone upstream into a session-owned directory inside the execution root.
2. Verify live `main`, detached `HEAD`, commit tree, selected paths, and exact SHA-256 bytes.
3. Read the selected prompt skill, host metadata, style reference, license, and disclaimer as untrusted upstream data; do not execute any upstream script or install anything.
4. Static-audit excluded data/templates/gallery/website/install surfaces and record the exclusion rationale.
5. Copy exactly `SKILL.md`, `agents/openai.yaml`, `references/style-library.md`, `LICENSE`, and `docs/disclaimer.md` into `.p2p/vendor/skill/gpt-image-2-style-library-9a7b2e9/`.
6. Exclude `assets/city-life-system-map.png` because asset-level/commercial rights are unresolved; preserve the upstream `SKILL.md` reference and record `PNG_STATUS=EXCLUDED_OR_INACTIVE_RIGHTS_UNRESOLVED`.

#### Implementation gate

- Exact upstream commit/tree and selected source hashes match the audited pin.
- Snapshot tree hash is deterministic and contains no unallowlisted file.
- No network/dependency/install/render side effect is observed.
- A new snapshot directory is used; no prior snapshot is altered.

#### Acceptance

`P1-A` is accepted only with a complete source inventory, provenance record, rights decision, and before/after tree evidence.

### P1-B — Registry manifest and integration contract

#### Goal

Register the snapshot through the existing capability foundation without changing shared architecture or live authority.

#### Work steps

1. Add exactly one registry record and raise the registry count from 15 to 16.
2. Set `TYPE=SKILL`, noncanonical, non-optional, `MODEL_ROUTABLE`, `LOCAL_VENDOR_SNAPSHOT`, `DISCOVERED`, `ON_DEMAND`, network disabled, credentials none, install disabled, and external render explicit-only.
3. Declare narrow visual-prompt positive triggers and negative triggers for code/UI implementation, marketing copy, actual rendering/API use, and the existing whiteboard boundary.
4. Bind entrypoint, explicit references, no assets, no script entrypoints, exact upstream provenance, snapshot hash, license scope, and unresolved rights state.
5. Verify canonical IDs, denominator, 8/8 quorum, one-router invariant, no provider/image adapter, and no `PROVIDES` field for the new capability.

#### Implementation gate

- Registry validation passes with 16 capabilities, six classes, exact eight canonical identities, and 8/8 quorum.
- The record is loadable by existing vendor code and has no permission-granting content route.
- Status remains `DISCOVERED`; no active/promotion claim is introduced.

#### Acceptance

`P1-B` is accepted only after the manifest and source snapshot agree on every declared path/hash and the existing foundation invariants remain unchanged.

### P2-A — Behavior and collision regression matrix

#### Goal

Prove routing and capability behavior at the existing seams, including collisions with `p2p-uiux`, `creative.copywriting`, `media.whiteboard_animation`, and implementation/marketing requests.

#### Work steps

1. Add focused tests for metadata-only discovery, exact selected-file loading, tree/hash drift, missing/extra/path-set/EOL changes, and no network/install behavior.
2. Test positive visual prompt cases and all mandatory negative/collision prompts.
3. Test that implementation requests are routed to UI/code boundaries rather than hijacked by the prompt skill.
4. Test progressive `DISCOVERY`, `MATCH`, `LOAD`, and explicit `DEEP_LOAD` behavior with no full-tree injection.
5. Test unknown/unsupported render operations remain blocked and provider-neutral.

#### Implementation gate

- New tests fail for the missing behavior before the corresponding test-support change and pass after the behavior is implemented.
- Existing vendor, foundation, host, and Manus tests retain their prior meaning; inherited failures are separated from candidate failures.

#### Acceptance

`P2-A` is accepted with fresh machine-readable and human-readable test evidence and an explicit collision table.

### P2-B — Host projection, Manus package, and governance evidence

#### Goal

Show that the new manifest is projected through existing Codex/other-host/Manus surfaces without claiming runtime certification or creating a second control plane.

#### Work steps

1. Extend host projection matrix for `Codex=MAPPING_SUPPORTED` and Claude/Gemini/Cursor/Copilot=`MAPPING_PLANNED`.
2. Verify deterministic metadata-only projection, provenance/hash preservation, no writes, no provider/model/auth/task mutation, and no runtime-certification claim.
3. Extend Manus package matrix; verify repo-local deterministic package plan/export, no network/credentials/import/task execution, and runtime `NOT_CERTIFIED`.
4. Run governance/doctor/drift checks and preserve exact reports. If the generated lock or report is a candidate artifact, hash it and keep it separate from owner approval.

#### Implementation gate

- Host and Manus evidence uses only existing adapters.
- Governance is technically passing or reports a precise pre-existing/inherited block; no user approval is inferred.

#### Acceptance

`P2-B` is accepted when all supported/planned/not-certified distinctions are visible and reproducible.

### P2-C — Full validation and candidate sealing

#### Goal

Finish with full build/validation, isolated cleanup, handoff, and candidate identity binding.

#### Work steps

1. Run the project/package doctor and full Python compile/build boundary; Docker is not applicable because this is an offline development-source capability snapshot with no service image.
2. Run the affected suites and the broader relevant regression suite.
3. Refresh Anvien, run change detection, inspect diff/status, and record blast radius.
4. Commit each verified logical batch in the execution clone only.
5. Perform a dry-run cleanup inventory, delete only exact session-created disposable upstream/cache/log paths, and preserve snapshot/provenance/evidence/handoff/rollback.
6. Compute candidate `HEAD`/tree and SHA-256 for the handoff, technical reports, and return packet.

#### Implementation gate

- No protected remote mutation is attempted.
- Candidate files, hashes, tests, cleanup, and remaining risks are complete.

#### Acceptance

`P2-C` is accepted only after the handoff is internally consistent with the final candidate commit/tree and all nonclaims are explicit.

### P3 — Fresh independent Supervisor

#### Goal

Review the actual candidate diff and evidence from a zero-trust perspective after implementation is complete.

#### Work steps

1. Re-read the final diff, registry record, snapshot inventory, handoff, reports, and technical evidence.
2. Verify source/hash/provenance alignment, sparse allowlist, rights state, routing collisions, host/Manus boundaries, no provider/quorum mutation, and cleanup safety.
3. Re-run or inspect the minimum acceptance commands independently; do not repair during review.
4. Write the required report under `reports/supervisor/` with exact result `PASS` or `REJECT` and its SHA-256.

#### Acceptance

Only a fresh Supervisor `PASS` permits the preferred candidate-ready terminal. A `REJECT` or unresolved gate remains the terminal and is returned honestly.

## 4. Verification matrix

| Evidence ID | Claim | Planned evidence | Result |
|---|---|---|---|
| E0-P0A-ID1 | Canonical base and live remote authority | `git rev-parse`, tree, remote URL, live `ls-remote` | PASS |
| E0-P0A-ID2 | Owner worktree preserved | status inventory and no mutation target use | PASS |
| E0-P0A-UP1 | Upstream pin and main drift | live `ls-remote`, detached commit/tree, selected hashes | PASS for preflight; refresh in P1-A |
| E0-P0A-SPEC1 | Relevant contract coverage | full SPEC cluster read; no `SPEC-MAP.md` present | PASS |
| E0-P0A-ANV1 | Graph freshness and impact baseline | `anvien analyze --force`, file detail/impact on affected test surfaces | PASS with hidden-path limitation |
| E1-P1A-SRC | Sparse snapshot byte fidelity | inventory, raw/canonical per-file SHA-256, tree hash | PASS: 5 files, 32877 bytes, tree `29121408bbfdd4994ec4738b6ee181c80ba123cb7554c297e8a07091faddc482` |
| E1-P1A-RIGHTS | PNG rights gate | explicit exclusion and unresolved-rights record | PASS: `EXCLUDED_OR_INACTIVE_RIGHTS_UNRESOLVED` |
| E1-P1B-REG | Registry/invariant contract | JSON validation and foundation tests | PASS: 16 records, exact 8 canonical, 8/8 |
| E2-P2A-ROUTE | Positive/negative/collision routing | focused unittest evidence | PENDING |
| E2-P2A-CTX | Progressive context boundary | stage-by-stage load evidence | PENDING |
| E2-P2B-HOST | Host projection truth | host matrix and deterministic projection tests | PENDING |
| E2-P2B-MANUS | Manus mapping boundary | package plan/export tests | PENDING |
| E2-P2B-GOV | Governance/drift/doctor | fresh reports and exact hashes | PENDING |
| E2-P2C-BUILD | Full build/package validation | compile, doctor, relevant regression suites | PENDING |
| E3-P3-SUP | Independent acceptance | Supervisor report and SHA-256 | PENDING |

## 5. Explicit nonclaims

- This candidate is not promoted, merged, pushed, deployed, released, or live-certified.
- `DISCOVERED` is not `ACTIVE` and is not Owner approval.
- The upstream project is a prompt-construction source, not an image-generation API/client/renderer.
- No commercial, asset-level, third-party, or model-output rights clearance is claimed.
- Manus mapping is not Manus runtime certification.
- Planned host mappings are not host runtime support.
- Local tests, reports, and Supervisor evidence are technical candidate evidence, not remote access control or Owner authorization.

## 6. Rollback and stop rule

Rollback is by retaining the prior base commit/tree and deleting only the candidate clone or reverting candidate commits in that isolated clone; the canonical owner checkout remains untouched. Stop immediately on source/tree mismatch, unresolved mandatory path/hash drift, accidental architecture expansion, authority ambiguity, failed security/data-boundary gate, or Supervisor rejection. Do not repair a failed gate by weakening the test or changing the acceptance contract.

## 7. Plan update record

- 2026-08-28: P0 completed; clean execution clone created inside canonical owner repository `.tmp` and bound to exact base.
- 2026-08-28: P1-A is next; PNG rights remain unresolved and therefore excluded from the candidate runtime snapshot.
- 2026-08-28: P1-A/P1-B technical gates passed; upstream selected bytes, sparse snapshot, registry contract, and `96/96` affected suites are green. P2 is now in progress.
