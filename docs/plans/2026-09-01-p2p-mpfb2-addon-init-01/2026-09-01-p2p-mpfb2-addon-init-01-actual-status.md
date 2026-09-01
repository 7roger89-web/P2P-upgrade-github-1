# P2P MPFB2 Addon Init 01 Actual Status

Title: P2P MPFB2 Addon Init 01
Date: 2026-09-01
Status: P1-B implementation in progress
Companion plan: `docs/plans/2026-09-01-p2p-mpfb2-addon-init-01/2026-09-01-p2p-mpfb2-addon-init-01-plan.md`
Companion evidence: `docs/plans/2026-09-01-p2p-mpfb2-addon-init-01/2026-09-01-p2p-mpfb2-addon-init-01-evidence.md`
Companion benchmark: `docs/plans/2026-09-01-p2p-mpfb2-addon-init-01/2026-09-01-p2p-mpfb2-addon-init-01-benchmark.md`

## Purpose

Classify the current subject and keep status truthful after each bounded slice.

## Freshness / Refresh Rules

P0 is the pre-edit baseline. Refresh affected rows after every slice and update
next-phase assumptions before continuing. Detailed proof remains in evidence.

## Scope

Target scope:

- canonical child MPFB2 loading boundary;
- existing Blender/MPFB2 runtime;
- one real addon proof and one neutral character smoke;
- firewall/adapter/output/provenance preservation.

Out of scope:

- Owner checkout, upstream source, reinstall/download, Game Truyen,
  release/promotion/deployment/merge, and firewall/adapter redesign.

## Relationship / Impact Evidence

Fresh Anvien graph has 1109 scanned files, 199 parsed code files, and 0 parse
failures. The hidden `.p2p` entrypoint is not a file node; file-detail/impact
is UNKNOWN for that file. The focused test file has 143 local relationships.

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `.p2p/system/p2p_capabilities/mpfb_blender_entrypoint.py` | E0-P0A-IMPACT1/E1-P1B-IMPACT1 | unavailable: hidden source | dedicated Blender child | high/UNKNOWN warning |
| `.p2p/system/p2p_capabilities/mpfb_adapter.py` | E0-P0A-IMPACT1 | unavailable: hidden source | parent/Popen/output/isolation | preserve-only |
| `.p2p/system/p2p_capabilities/windows_network_isolation.py` | E0-P0A-IMPACT1 | unavailable: hidden source | firewall lifecycle | preserve-only |
| `tests/test_p2p_game_truyen_mpfb_adapter_01.py` | E0-P0A-IMPACT1 | 143 local relationships | focused contracts/validators | validate-only |
| existing MPFB2 archive/source | E0-P0A-MPFB1 | N/A external | runtime dependency | do-not-touch |
| Blender executable | E0-P0A-RUNTIME1 | N/A | native child | preserve-only |
| Game Truyen | E0-P0A-LOG1 | N/A | protected downstream | do-not-touch |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Required boundary holds. | Preserve. |
| `partial` | Required behavior has a bounded gap. | Change only the gap. |
| `wrong` | Behavior conflicts with contract. | Replace narrowly. |
| `unbound` | Surface is not connected to real flow. | Bind real flow only. |
| `blocked` | Authority/evidence unavailable. | Stop. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| canonical subject | clean branch at `b65948b...`, tree `6553b9...` | exact isolated subject | correct | N/A | E0-P0A-GIT1 | preserve |
| parent adapter | canonical firewall-before-Popen and output/provenance route | unchanged | correct/preserve-only | hidden/UNKNOWN | E0-P0A-SRC1 | no edit |
| firewall helper | canonical profiles/DisplayName/rule/cleanup path | unchanged | correct/preserve-only | hidden/UNKNOWN | E0-P0A-SRC1 | no edit |
| child entrypoint | bare import `mpfb` + explicit register without Blender addon identity | extension identity before service access | partial/wrong/unbound | hidden/UNKNOWN | E0-P0A-SRC1, E1-P1A-RUNTIME1 | P1-B edit |
| MPFB2 source | exact 2810/2810 archive bytes; cache now quarantined | exact source/root hash | correct after cache reconciliation | N/A | E0-P0A-MPFB1, E1-P1B-CACHE1 | preserve |
| Blender runtime | 4.2.23 LTS exact binary hash | same | correct/preserve-only | N/A | E0-P0A-RUNTIME1 | reuse |
| extension contract | `bl_ext.src.mpfb`, addon key, preference, register all PASS | canonical child uses it | correct/unbound | N/A | E1-P1A-RUNTIME2 | wire P1-B |
| output/provenance | existing exact downstream validators | unchanged | correct/preserve-only | hidden/UNKNOWN | E0-P0A-SRC1 | validate-only |
| Game Truyen | not accessed | no mutation | correct/do-not-touch | N/A | E0-P0A-LOG1 | fingerprint before/after |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-09-01 | fresh clone before source edit | all target surfaces | entrypoint partial/wrong; cache partial; security/pins correct | E0-P0A-GIT1, E0-P0A-RUNTIME1, E0-P0A-MPFB1, E0-P0A-SRC1 | P1-A required |
| R1 | 2026-09-01 | real bare/extension probes and cache quarantine | addon/runtime | extension correct but canonical unbound; cache partial -> correct; decision=BOUNDED_SOURCE_FIX | E1-P1A-RUNTIME1, E1-P1A-RUNTIME2, E1-P1A-DECISION1, E1-P1B-CACHE1 | start P1-B |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| child entrypoint | focused adapter test | contract consumer | P1-B | edit only bounded fix | E1-P1B-IMPACT1 | no fallback |
| child entrypoint | MPFB2 source | external dependency | P1-A/P2-A | inspect-only | E0-P0A-MPFB1 | no upstream edit |
| adapter | firewall helper | spawn/isolation | P2-B | preserve-only | E0-P0A-SRC1 | no firewall edit |
| adapter | output/provenance | post-child validation | P2-B | preserve/validate-only | E0-P0A-SRC1 | exact two outputs |
| runtime | source/cache/portable | provisioned runtime | P1-A/P2-A | bounded local | E1-P1B-CACHE1 | no reinstall |
| Game Truyen | none | protected downstream | all | do-not-touch | E0-P0A-LOG1 | mutation NO |

## Detailed Findings

### Child addon identity

Current state:

Bare `mpfb` is not a Blender extension identity. The fresh bare probe fails
inside MPFB2's location service because `__package__` is not an extension and
the addon preference key is absent. The extension probe passes using
`bl_ext.src.mpfb` and a local repo.

Required state:

```text
The canonical child must use Blender's local extension repository and enable
the existing pinned `mpfb` package before preference/service access.
```

Evidence:

- E0-P0A-SRC1: old child sequence.
- E1-P1A-RUNTIME1: exact bare failure.
- E1-P1A-RUNTIME2: exact extension PASS.

Relationship and impact:

- Related file count: unavailable for hidden source; focused test has 143 local
  relationships.
- Relationship summary: adapter -> entrypoint -> MPFB2 -> services -> outputs.
- Impact note: high/UNKNOWN warning; sibling security surfaces are preserve-only.

Classification:

`partial / wrong / unbound`

Allowed next action:

Apply the one P1-B source fix proven by P1-A.

Forbidden next action:

No addon registry injection, bare fallback, upstream edit, or adapter redesign.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-B | source fix is required and not yet committed | edit only the child entrypoint; preserve siblings |
| P2-A | probe gates pass but final canonical child not rerun | rerun after P1-B commit |
| P2-B | not run | blocked until P2-A PASS |

## Implementation Gate

- [x] Target scope and statuses listed.
- [x] Evidence IDs assigned.
- [x] Relationship counts/hidden-source limitation recorded.
- [x] Touch map and preserve-only surfaces recorded.
- [x] P0/P1-A status refreshes recorded.
- [x] P1-B gate is based on fresh real proof.
- [ ] P1-B source commit and post-edit refresh complete.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [ ] P0 complete. Next phase can proceed unchanged.
- [x] P0 complete. Next phase status, next action, or work steps must be
  updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

The real extension path is proven. Because the canonical source remains
unbound, the only authorized remediation is a bounded source fix in the child
entrypoint; no firewall or adapter change is justified.
