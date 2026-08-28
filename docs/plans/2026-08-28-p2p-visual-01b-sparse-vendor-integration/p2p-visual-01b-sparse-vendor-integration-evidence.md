# P2P-VISUAL-01B Evidence Log

## Evidence contract

- Evidence is append-only in meaning: later results supplement, never silently rewrite, earlier authority.
- Every claim is tied to a command, file, hash, or report path.
- `PASS` means only the stated technical claim; it does not mean promotion, release, remote authorization, or live certification.
- `UNKNOWN` and `BLOCKED` remain explicit.

## P0 preflight evidence

### E0-P0A-ID1 — Canonical identity

- Canonical path: `D:\AI\P2P_dev\P2P-canonical-runtime-01`
- Remote: `https://github.com/7roger89-web/P2P-upgrade-github-1.git`
- Local HEAD: `1cca4d20c243b5dcecd21f4fabec785fc99cfdfa`
- Local tree: `6693a193802b20c1fc8ce30f73f7d203841c8983`
- Live `refs/heads/main`: same commit
- Result: PASS

### E0-P0A-ID2 — Owner isolation

- The canonical owner checkout contains substantial pre-existing dirty work, including tracked and untracked project governance/skill/report material.
- It is not the implementation target.
- The clean execution clone is inside the canonical owner repository's `.tmp` boundary and is the only mutation target.
- Result: PASS

### E0-P0A-EXEC — Execution clone

- Path: `D:\AI\P2P_dev\P2P-canonical-runtime-01\.tmp\p2p-visual-01b-20260828-120349-f8e51c48409e`
- HEAD: `1cca4d20c243b5dcecd21f4fabec785fc99cfdfa`
- Tree: `6693a193802b20c1fc8ce30f73f7d203841c8983`
- Shallow: false
- Status: detached clean checkout before plan files
- `git fsck --full --no-reflogs --connectivity-only`: no output, exit 0
- Result: PASS

### E0-P0A-UP1 — Upstream current/pin

- Repository: `https://github.com/freestylefly/awesome-gpt-image-2`
- Live `refs/heads/main`: `9a7b2e9c39f816d6c699c2a133e11b6d8bfdc464`
- Audited commit: same
- Audited tree: `56b103dad637a95b9ec366eb7215459f28feb73e`
- Tags observed during preflight include `gpt-image-2-style-library-v1.0.4`; the candidate remains commit-pinned, not tag-floating.
- Result: PASS for preflight; P1-A will repeat exact verification in the session clone.

### E0-P0A-SPEC1 — Contract coverage

- Read full relevant files under `docs/SPEC/`, including capability foundation/context/manifest/routing, execution evidence, trust/data/instruction, host projection, Manus package, provider abstraction, optional specialist, project domain, and test/eval contracts.
- `SPEC-MAP.md` was searched for and is absent from this source tree.
- Result: PASS with absence recorded, not treated as a missing contract.

### E0-P0A-ANV1 — Graph evidence

- `anvien analyze --force` in the execution clone: 975 scanned, 174 parsed code, 0 failed, 40727 nodes, 47091 relationships, current graph.
- Test file detail/impact was run for the capability foundation, vendor integration, host projection, and Manus package surfaces.
- Hidden `.p2p` implementation paths were not found by file-detail; this is a known graph coverage limitation, so filesystem/spec/test evidence remains authoritative for those paths.
- Result: PASS for freshness and test-surface baseline; hidden-path impact is explicitly limited.

## P0 status matrix

| Surface | State before implementation | Authority |
|---|---|---|
| Canonical owner checkout | Correct base, materially dirty, preserve-only | Git status/hash evidence |
| Execution clone | Correct base, clean, editable | Git status/hash/fsck |
| Existing vendor adapter/router/host/Manus | Present and preserve-only unless tests prove deficiency | Source/spec inspection |
| New visual snapshot | Missing | Filesystem |
| New registry record | Missing; current count 15 | JSON parse |
| PNG rights | Unresolved | 01A audit + rights rule |
| New focused tests | Missing | Test inventory |
| Handoff/Supervisor/cleanup evidence | Missing | Session scope |

## P1 implementation evidence

### E1-P1A-SRC — Exact upstream and selected-byte fidelity

- Fresh upstream clone: `.tmp/upstream-awesome-gpt-image-2-20260828` inside the execution root.
- Live `refs/heads/main`: `9a7b2e9c39f816d6c699c2a133e11b6d8bfdc464`.
- Detached commit: `9a7b2e9c39f816d6c699c2a133e11b6d8bfdc464`.
- Commit tree: `56b103dad637a95b9ec366eb7215459f28feb73e`.
- Five vendored raw source hashes match the prior audit: `SKILL.md=8c628df135c27ef4b7f7a085cdd60868eee2180c21401a89a140b321148f0b2e`, `agents/openai.yaml=592f53bfba40639571e45e534245615a453f866822b649cc993578eec442431a`, `references/style-library.md=c98f3d9a178670235dd6e37f0bb8ed07eb8d4bb77c56e7e300d44a4f6d50f8bc`, `LICENSE=70e109c69f4c92ca03a7d37ac045b4f5584e442004b5eb8b93329e7a1eec7c16`, `docs/disclaimer.md=acb1e6b8f0bfa58ff5964ce749a65af20269a8f57bb9d3b4aa849ba55e161e43`.
- The text loader canonical hashes are retained separately in the registry because the source checkout is CRLF and P2P normalizes text EOL for loader identity.
- Result: PASS.

### E1-P1A-TREE — Sparse allowlist

- Snapshot path: `.p2p/vendor/skill/gpt-image-2-style-library-9a7b2e9`.
- Runtime files: exactly 5; total bytes `32877`.
- Snapshot tree hash: `29121408bbfdd4994ec4738b6ee181c80ba123cb7554c297e8a07091faddc482`.
- Included: `SKILL.md`, `agents/openai.yaml`, `references/style-library.md`, `LICENSE`, `docs/disclaimer.md`.
- Excluded: `data/style-library.json`, `docs/templates.md`, gallery/cases, website/app, installers/generators/dependencies, and all upstream non-allowlisted surfaces.
- Result: PASS.

### E1-P1A-RIGHTS — PNG rights gate

- Upstream asset path is `agents/skills/gpt-image-2-style-library/assets/city-life-system-map.png` and its verified raw SHA-256 is `cd14766cbce862146f909aa0b0cf966804d079df3775a7a706827a490a459d95`.
- Asset is not present in the candidate snapshot. The exact upstream `SKILL.md` reference remains intact.
- Registry status is `DISCOVERED`; rights record is `UNRESOLVED`; `png_status=EXCLUDED_OR_INACTIVE_RIGHTS_UNRESOLVED`; commercial clearance is `UNKNOWN`.
- Result: PASS for the technical rights gate; not a clearance claim.

### E1-P1B-REG — Registry/invariant contract

- Registry JSON parses and `load_registry` returns 16 records.
- New record is `visual.gpt_image_2_style_library`, `TYPE=SKILL`, `INVOCATION_CLASS=MODEL_ROUTABLE`, `CANONICAL_QUORUM_MEMBER=false`, `OPTIONAL_SPECIALIST=false`, `STATUS=DISCOVERED`.
- No `PROVIDES` field, no new provider, no image adapter, no new router, and no canonical identity change.
- Integration is `LOCAL_VENDOR_SNAPSHOT`, `ON_DEMAND`, no network, no credentials, install disabled, explicit-only external render, no assets, no script entrypoints.
- Result: PASS.

### E1-P1B-TEST — Affected test suites

- Base baseline: `88/88` passed in `11.410s` before candidate changes.
- Candidate affected/focused suites: `96/96` passed in `17.038s` after snapshot, manifest, and test updates.
- Result: PASS; this is validation evidence, not product performance evidence.

## Later evidence slots

The following IDs are reserved and must be filled with exact command/file/hash results as work completes:

- E1-P1A-SRC — source inventory and selected-byte hashes
- E1-P1A-TREE — sparse snapshot tree hash and allowlist proof
- E1-P1A-RIGHTS — PNG exclusion and rights status
- E1-P1B-REG — registry count/classes/quorum/manifest validation
- E2-P2A-ROUTE — routing positive/negative/collision matrix
- E2-P2A-CTX — progressive stage matrix
- E2-P2A-HASH — drift/missing/extra/path-set/EOL matrix
- E2-P2B-HOST — host projection matrix
- E2-P2B-MANUS — Manus plan/export matrix
- E2-P2B-GOV — doctor/drift/governance evidence
- E2-P2C-BUILD — compile/build/regression evidence
- E2-P2C-CLEAN — dry-run and safe-delete evidence
- E2-P2C-CANDIDATE — final commit/tree/hash binding
- E3-P3-SUP — fresh independent Supervisor report and hash
