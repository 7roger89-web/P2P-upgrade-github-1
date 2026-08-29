# P2P img2threejs executable projection Actual Status

Title: P2P img2threejs executable projection
Date: 2026-08-29
Status: P1 Complete; closure checks pending
Companion plan: `docs/plans/2026-08-29-p2p-img2threejs-exec-01/plan.md`
Companion evidence: `docs/plans/2026-08-29-p2p-img2threejs-exec-01/evidence.md`
Companion benchmark: `docs/plans/2026-08-29-p2p-img2threejs-exec-01/benchmark.md`

## Purpose

This is the live truth record for the strict executable projection slice. It
distinguishes safe existing surfaces from stale, unsafe, missing, and
future-unproven surfaces.

## Freshness / Refresh Rules

P0 is the fresh baseline. After P1-A and P1-B, append refresh rows and update only
affected statuses; preserve the P0 classifications as history.

## Scope

Target scope:

- exact upstream identity and security audit;
- bounded execution adapter;
- existing P2P registry/router/selective projection metadata;
- future Thiên Hạ character/asset protocols and canonical bootstrap discovery.

Out of scope:

- Thiên Hạ repository, Golden Character, Golden Weapon implementation, visual browser
  runtime, release/deploy/push/promotion, full upstream vendoring, P2P architecture.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `tests/test_p2p_game_toolchain_02a.py` | `E0-P0A-GRAPH1` | 3 outbound / 30 local | registry, vendor routing, workflow helper consumers | high scope warning; focused test edits only |
| `.p2p/system/p2p_capabilities/capabilities.json` | `E0-P0A-GRAPH1` (Anvien excludes ignored `.p2p` file surface) | UNKNOWN | JSON source of capability manifests consumed by registry/router | data contract; validate with `load_registry` |
| `.p2p/vendor/provenance/p2p-game-toolchain-02a.json` | `E0-P0A-GRAPH1` (ignored data surface) | UNKNOWN | historical/external provenance source | data contract; preserve old record |
| `docs/p2p-development/P2P-PROJECT-BOOTSTRAP.md` | `E0-P0A-GRAPH1` | 0 | provider-neutral bootstrap documentation | low; add optional read-order hook only |
| new `img2threejs_adapter.py` | not indexed before creation | N/A | new execution boundary | review as security-critical new module |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| upstream v1.5.1 source | exact release fetched and audited; unsafe CS2 URL and region path routes remain | exact immutable source identity with P2P deny boundary | unsafe upstream routes contained at adapter boundary | source audit | E0-P0A-SRC2, E0-P0A-SEC1, E0-P0A-SEC2, E1-P1A-SEC1..SEC4 | preserve external source; deny unsafe routes |
| old img2threejs provenance | 02A record exists at old pin; no code vendored | preserve history and add current exact audited record | correct / preserve-only | UNKNOWN | E0-P0A-SRC3, E1-P1B-REG2 | do not mutate predecessor |
| P2P img2threejs capability | noncanonical registry entry with explicit adapter/protocol snapshot | selected capability with explicit adapter/projection | correct / noncanonical | UNKNOWN | E1-P1B-REG1, E1-P1B-PROJ1 | exact-subject review |
| safe execution adapter | exact source/clean tree/allowlist/workspace enforcement implemented | exact source/clean tree/allowlist/workspace enforcement | correct | N/A | E1-P1A-SEC1..SEC5, E1-P1A-TEST1 | preserve narrow boundary |
| existing vendor/JIT projector | local vendor/projection machinery exists and is non-executing/pure | reuse without launcher behavior | correct / preserve-only | E0-P0A-SRC4 | preserve P1-B |
| character protocol | P2P-authored future Golden Character contract with six-view/quality boundaries | minimal future contract and honest maturity limits | protocol-ready / visual unproven | N/A | E1-P1B-PROJ1 | preserve future gate |
| asset-forge protocol | separate P2P-authored Golden Weapon / Asset Forge contract | separate bounded hard-surface route | protocol-ready / visual unproven | N/A | E1-P1B-PROJ1 | preserve separate maturity |
| Arena bootstrap discovery | canonical project bootstrap now has optional capability read-order hook | discover WHEN/NOT/PIN/SAFETY/ENTRYPOINT/QA fields | correct / optional | 0 docs edges | E1-P1B-PROJ2 | preserve P2P_REQUIRED |
| visual browser proof | no current Thiên Hạ runtime in scope | future actual-browser evidence before visual acceptance | unbound / future | N/A | E0-P0A-BOUNDARY1 | preserve as future gate |
| canonical quorum | 8 identities, denominator 8 | unchanged | correct / preserve-only | registry data | E0-P0A-SRC3 | do not touch |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-29 | fresh P2P origin/main and fresh upstream refs | all target surfaces | baseline classifications above | E0-P0A-SRC1..E0-P0A-BOUNDARY1 | P1-A first; P1-B after refresh |
| R1 | 2026-08-30 | after P1-A implementation | adapter/security | missing -> correct; unsafe upstream routes -> contained | E1-P1A-SEC1..SEC5, E1-P1A-TEST1 | P1-B allowed |
| R2 | 2026-08-30 | after P1-B implementation | registry/projection/bootstrap | missing -> registered/selective; protocols missing -> protocol-ready; browser remains future | E1-P1B-REG1..E1-P1B-TEST1 | final Anvien/doctor/supervisor |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| new adapter | upstream audited scripts | dependency boundary | P1-A | edit | E0-P0A-SEC1..SEC2 | exact allowlist only |
| `capabilities.json` | `vendor_skill.py`, router | source-of-truth / consumer | P1-B | edit | E0-P0A-SRC3, E0-P0A-GRAPH1 | preserve 8/8 and single router |
| provenance/external manifest | 02A tests | source-of-truth / test | P1-B | edit | E0-P0A-SRC3 | preserve predecessor record |
| contract/skill snapshot | host projection | source-of-truth / projected data | P1-B | edit | E0-P0A-SRC4 | no full runtime/vendor tree |
| bootstrap doc | future Arena reader | bootstrap documentation | P1-B | edit | E0-P0A-GRAPH1 | optional hook, no runtime requirement change |
| existing vendor skills | new route | unrelated consumer | P1-B | validate-only | E0-P0A-SRC4 | no regression |
| Thiên Hạ project | target consumer | external project | all | do-not-touch | E0-P0A-BOUNDARY1 | no checkout or mutation |

## Detailed Findings

### Upstream security

Current state: exact v1.5.1 is available, but the two reported unsafe routes are
still present. Apache-2.0 proves license provenance only. The adapter now
contains them by deny-only dispatch and does not rewrite upstream.

Required state:

```text
arbitrary network DENIED; CS2 route DISABLED; identifiers and output paths bounded;
only five explicitly audited local/control-plane entrypoints from an exact clean
checkout may execute.
```

Evidence:

- `E0-P0A-SEC1`: direct `urlopen`/`urlretrieve` path remains.
- `E0-P0A-SEC2`: region-derived output path remains insufficiently sanitized.

Classification: wrong upstream safety, correctable at P2P boundary without upstream
rewrite. Allowed next action: P1-A adapter only. Forbidden next action: expose or patch
the unsafe routes implicitly.

### Existing P2P projection

Current state: existing vendor discovery is metadata-only and host projection is pure;
the old img2threejs candidate is not registered.

Required state: selective operational contract projection plus separate explicit adapter
availability. Classification: correct at this slice. The projector remains pure and
the upstream repository remains external; no full repository copy is allowed.

### Future visual pipeline

Current state: no Thiên Hạ project or browser lab is in scope. Classification:
unbound/future. Allowed next action: document acceptance protocol only. Forbidden next
action: claim Golden Character/Weapon visual quality from code or metadata.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | unsafe external routes are applicable but are denied by a narrow adapter; focused smoke is PASS | complete; preserve five-entrypoint allowlist |
| P1-B | registry/projection/protocol/bootstrap surfaces are present and existing projector remains pure | complete; run final closure checks and exact-subject supervisor |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Existing target relationship evidence is recorded where Anvien can resolve it;
  ignored `.p2p` data surfaces are explicitly marked UNKNOWN.
- [x] Phase Touch Map defines touch mode.
- [x] Correct parts are preserve-only.
- [x] Partial, missing, and wrong parts have exact next actions.
- [x] No unresolved authority blocker remains for the bounded implementation.
- [x] Status Refresh Log has an R0 baseline row.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase status, next action, and work steps are set from fresh
  evidence; P1-A can proceed.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

The safe boundary is not in upstream itself, but can be contained without architecture
expansion by an exact-clean-checkout adapter with a five-entrypoint allowlist. This is
enough to enable bounded local workflow/spec/codegen execution and future selective
project projection; visual reconstruction remains explicitly unproven and future-gated.

## P1 completion decision

- [x] P1-A adapter and focused security execution evidence complete.
- [x] P1-B registry, provenance, selective contract, and bootstrap hook complete.
- [ ] Final closure checks and independent exact-subject supervisor report complete.
