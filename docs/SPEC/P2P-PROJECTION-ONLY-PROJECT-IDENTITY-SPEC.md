# P2P Projection-Only Project Identity, Readiness and Materialization Specification

Status: CANDIDATE — OWNER GATE PENDING
Date: 2026-08-29
Scope: P2P development source only

Parent authority:

- `P2P-HOST-SKILL-PROJECTION-SPEC.md`
- `P2P-CAPABILITY-CONTEXT-POINTER-SPEC.md`
- `P2P-CAPABILITY-ROUTING-READINESS-SPEC.md`
- `P2P-CAPABILITY-TRUST-DATA-INSTRUCTIONS-SPEC.md`

This is the reconciled 01C candidate contract. It is not promoted runtime
authority and does not authorize release, merge, deployment, production
project mutation, remote push, or inference of Owner approval.

## Purpose

Define one truthful adoption extension for a target project that receives
selected P2P project-consumable instructions without receiving the P2P
runtime. The extension reuses the existing project pin, project context,
capability registry, single router, C18/C19 context flow, and pure host
projection plan. It adds no registry, router, context engine, council, quorum,
or deployment subsystem.

The contract is:

```text
validated selection
    -> pure host projection plan
    -> bounded controlled materialization
    -> source/plan/file/policy/context binding
    -> project pin written last
    -> mode-aware readiness validation
```

## Authority and compatibility

The capability registry remains authoritative for capability identity, class,
provenance, invocation policy, trust, and capability-specific readiness. The
host projection specification remains authoritative for host vocabulary,
project-relative targets, progressive disclosure, ownership classes, and pure
plan behavior. This document defines only the adoption and binding seam.

The legacy `p2p-project-pin/1` contract remains the packaged-runtime path. It
continues to require installed metadata, artifact binding, rollback source,
permission envelope, and strict Doctor health. A v1 pin is never reinterpreted
as projection-only, and existing v1 projects are not migrated by this
candidate.

The v2 schema has two explicit closed modes:

| Mode | Meaning of `READY` | Runtime requirement |
| --- | --- | --- |
| `PACKAGED_RUNTIME` | Existing packaged identity and Doctor-backed runtime are valid | `.p2p/system`, candidate metadata, exact artifact, and healthy Doctor |
| `PROJECTION_ONLY` | Selected projection and durable bindings are valid | No P2P runtime, artifact, or packaged Doctor is required or claimed |

Unknown schema versions, unknown modes, missing modes, and packaged fields in
the projection-only branch fail closed.

## Canonical projection-only identity

A projection-only pin is project-local, deterministic, and composed of these
semantic groups. Values are never inferred from file presence.

### Project identity

- `schema`: `p2p-project-pin/2`.
- `mode`: `PROJECTION_ONLY`.
- `project_id`: stable non-secret project identifier; never a filesystem path.
- `project_name` and optional `project_version`.
- `project_fingerprint`: SHA-256 fingerprint of project-owned files under the
  existing exclusion boundary.

### Exact P2P source binding

`source_binding` is required and contains:

- `schema`: `p2p-project-source-binding/1`;
- the exact HTTPS repository identity;
- exact 40-hex commit and tree objects;
- `status: VERIFIED`, only when the caller supplied the exact binding.

The repository, commit, and tree are identity evidence, not permission to
fetch or execute. Validation is offline and does not resolve a remote. Local
developer paths, credential-bearing URLs, and unverified objects are invalid.

### Selected capability evidence

`selected_capabilities` is non-empty and duplicate-free. Each entry binds the
existing capability ID, observed state, observed readiness or `UNKNOWN`,
source/snapshot SHA-256, selected entrypoint SHA-256, and runtime-readiness
facts. It is a selective projection, not a copy of the registry.

Selection remains the responsibility of the existing router. This contract
does not select, rank, install, or make a capability executable. Metadata
presence never upgrades readiness. `img2threejs` must retain
`executable_registered=false`; Tripo-related metadata must retain inactive and
non-executable state. Missing evidence remains `UNKNOWN`.

### Projection binding

`projection` is required and contains:

- `schema`: `p2p-project-projection-binding/1`;
- `materialization_version`: `p2p-project-materialization/1`;
- the validated host kind;
- SHA-256 of canonical pure-plan data and the exact plan snapshot;
- ordered managed-file records;
- optional bindings for the existing project policy and context-map files.

Every managed-file record contains a normalized project-relative POSIX path,
ownership `P2P_MANAGED_PROJECTED_FILE`, exact on-disk content SHA-256, and a
previous state of `ABSENT` or `PRESENT` plus its exact previous hash. Ownership
is a recoverable refresh record, not permission to alter ordinary project
files. A refresh is valid only when the prior pin proves ownership and the
current bytes still equal the last managed hash.

Policy and context bindings, when present, bind the canonical relative path,
schema where applicable, and exact current bytes. Drift invalidates readiness;
stale bytes are not silently refreshed.

### Atomic multi-capability projection bundle

When one project selects more than one already-validated host projection plan,
the plans are aggregated before any target write. The aggregate is one
project projection state, not a sequence of independent installations. The
v2 pin remains the identity envelope; its projection contains either the
legacy singular plan snapshot shape or a bundle with schema
p2p-project-projection-bundle/1. No p2p-project-pin/3 is introduced.

The bundle binds, in canonical order:

- exact source repository, commit, and tree;
- project identity, projection-only mode, and project fingerprint;
- sorted selected capability evidence;
- one wrapper per capability containing its exact plan SHA and plan snapshot;
- the sorted union of every target path and its content hash; and
- existing policy/context bindings when present.

The bundle hash is computed from that canonical representation, so incidental
input ordering cannot change identity. Constituent plans retain capability
identity, host, provenance-derived source/entrypoint hashes, and declared
files. All plans in one bundle use one supported host kind; mixed-host
materialization remains outside this bounded contract.

For each union path, one owner is accepted, identical content from multiple
plans is deterministically deduplicated, and differing content fails closed
with both capability IDs and hashes. Parent/child target paths also fail
closed. The complete union is the only managed-file set written into the
single resulting pin.

Bundle refresh is one transaction. Preflight classifies every desired path as
UNCHANGED, ADD, or UPDATE, and prior managed paths absent from the desired
union as REMOVE_MANAGED. Removal or update is allowed only when the prior
valid pin proves P2P ownership and the on-disk hash still matches. Unmanaged
collisions, missing or tampered managed paths, stale pins, and cross-plan
conflicts stop before mutation. The materializer writes the whole union,
verifies every resulting hash, writes one pin last, and validates
projection-only readiness only after the complete transaction succeeds.
Failure rolls back the whole attempted bundle using only proven prior bytes,
ownership, and created directories; it cannot produce a partial READY state.

### Runtime and rollback truth

Projection-only pins contain exactly the truthful runtime boundary:

- `runtime_claim: {"installed": false, "status": "NOT_INSTALLED"}`;
- `rollback: {"scope": "PROJECTED_FILES_ONLY", "prior_state_recorded": true}`.

They must not contain or require a packaged artifact hash, installed runtime
location, installation mode implying installation, Doctor health, or package
rollback artifact. Omitted values are not replaced with null, placeholders, or
synthetic claims. A projection pin is not a packaged-runtime certificate.

## Readiness contract

One existing project-context gate has two mode-aware validation branches:

1. `PACKAGED_RUNTIME` preserves the v1-equivalent installed metadata, project
   fingerprint, source, artifact, permission, rollback, release marker, and
   healthy Doctor checks.
2. `PROJECTION_ONLY` validates the v2 identity, exact HTTPS source/commit/tree,
   selected evidence, canonical plan snapshot/hash, managed ownership and
   current file hashes, policy/context bindings, project fingerprint, and
   explicit `NOT_INSTALLED` runtime claim.

The projection branch does not load or invoke packaged Doctor and does not
require `.p2p/system`. A valid result means only that the projection is
complete and internally bound. It does not mean a capability is executable,
a provider is available, a host is certified, or a P2P runtime is installed.

Project maps remain derived context, not project truth. C18/C19 retain bounded,
selective retrieval semantics; projection never materializes the full P2P
catalog. `MINIMAL` context must retrieve only directly required camera
references in the reference fixture.

## Pure-plan and controlled-materialization boundary

The host projection plan is pure, deterministic, read-only, and free of
filesystem mutation, network calls, subprocess execution, credentials, and
task-state changes. It describes candidate outputs only.

One controlled materializer may consume an already-`READY` plan. It may:

- validate source, selection evidence, plan, ownership, and target roots before
  writing;
- write only plan-declared project-relative files;
- create missing parent directories beneath the target root;
- write exact bytes atomically;
- return resulting hashes and prior states to the pin builder;
- restore only bytes changed by this operation if a later write fails.

For a multi-capability bundle, this same materializer consumes the complete
canonical aggregate once. It validates cross-plan conflicts and computes the
full union before the first write; it does not invoke the single-plan seam
once per constituent plan. The resulting v2 projection binding records every
managed path from that union.

It may not select capabilities, expand context, install dependencies, copy the
runtime, invoke Doctor, call a network service, execute a script, change
provider/model/auth/permission state, or write an undeclared path.

## Path, ownership, and recovery safety

The materializer rejects empty, absolute, drive-qualified, home-qualified, or
traversal paths; normalized parent traversal; final or parent symlink/reparse
escapes; undeclared paths; non-managed plan ownership; unmanaged differing
collisions; and prior managed files whose ownership or last hash no longer
matches disk.

An identical existing file is a no-op. A differing Owner file is never
overwritten. All preflight checks occur before the first write. Each changed
file is re-hashed. If any write or post-write binding step fails, changed files
and created directories are restored and no new valid `READY` pin is left.

The pin is never a pre-write permission grant. Pin-last sequencing is:

1. validate exact source identity;
2. validate selected capability evidence;
3. validate pure plan and canonical plan hash;
4. validate paths, symlinks, ownership, and conflicts;
5. materialize declared files;
6. hash resulting bytes;
7. validate policy/context bindings;
8. write the v2 pin last;
9. validate fresh project readiness.

Rollback is projection-only, not package rollback. A newly created file may be
removed only when its current hash and P2P ownership are proven. Earlier bytes
may be restored only when available and hash-bound. Hash-only evidence cannot
reconstruct Owner content. Unmanaged files are never deleted or restored.

## Target boundary and selective projection

Supported targets inherit the current host projection contract: project-scoped
`.agents`, `.claude`, `.gemini`, `.cursor`, or `.github` instruction surfaces.
No user/global host path is valid.

A projection-only target may contain the v2 pin, selected existing policy and
context bindings, and selected host files declared by the plan. Adoption must
not copy `.p2p/system`, the full capability registry, vendor trees, councils,
quorum infrastructure, unrelated tests, report archives, credentials, or
external binaries.

## Security and evidence boundary

Validation is offline-safe and uses local bytes and metadata only. Canonical
JSON and exact UTF-8/file bytes are hashed with SHA-256. Secrets, credentials,
machine paths, hidden prompts, and environment dumps are not identity
evidence.

Focused evidence must cover v1 compatibility; projection readiness without
`.p2p/system`; unknown/malformed schema and mode; source/tree/plan/file/policy/
context drift; traversal/absolute/symlink escape; unmanaged collision and
tamper; partial failure and pin-last; idempotent rerun and owned update; C18,
C19, and FASTPATH boundaries; `img2threejs=false`; Tripo inactive; and absence
of runtime/registry/vendor/report copying. Multi-capability evidence must also
cover deterministic bundle identity, duplicate-path deduplication, differing
path conflict, complete union ownership, add/remove transitions, stale prior
state, and whole-bundle rollback.

The current C18 bridge must classify authoritative architecture replacement as
`HIGH_RISK`, `CRITICAL`, and `OWNER_GATE_REQUIRED`; it must return `BLOCKED`
until the Owner gate is separately resolved. Technical projection PASS never
supplies that gate.

## Lifecycle boundary

This candidate adds no second CLI or command framework. Existing packaged
installation and rollback continue on their current path and retain v1
semantics. Projection-only adoption is a separate lifecycle branch:

```text
PROJECTION_PLAN
  -> CONTROLLED_MATERIALIZATION
  -> PROJECTION_ONLY_PIN
  -> PROJECTION_VERIFY
```

It remains separate from host discovery, live host certification, task
dispatch, receipt verification, release, deployment, promotion, and Owner
approval.

The candidate is technically complete only when source, implementation,
focused tests, security evidence, exact candidate SHA/tree, and an independent
focused Supervisor review are recorded. Owner promotion remains a separate
decision bound to the unchanged technical subject.

## Architecture rule versus implementation suggestion

The authority, mode, binding, readiness, path, ownership, sequencing,
rollback, and forbidden-runtime-copy clauses above are binding. A
standard-library module beside existing project pin/context code may own the
materialization seam, and disposable fixtures may exercise it; those are
implementation choices, not a second architecture or registry.
