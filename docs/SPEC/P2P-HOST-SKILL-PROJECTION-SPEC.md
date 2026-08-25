# P2P Host Skill Projection Specification

Status: APPROVED — OWNER ARCHITECTURE DECISION
Date: 2026-08-25
Scope: P2P development source only
Parent authority:
- `docs/SPEC/P2P-CAPABILITY-FOUNDATION-ARCHITECTURE-SPEC.md`
- `docs/SPEC/P2P-CAPABILITY-MANIFEST-SPEC.md`
- `docs/SPEC/P2P-CAPABILITY-CONTEXT-POINTER-SPEC.md`
- `docs/SPEC/P2P-CAPABILITY-ROUTING-READINESS-SPEC.md`
- `docs/SPEC/P2P-CAPABILITY-TRUST-DATA-INSTRUCTION-SPEC.md`
- `docs/SPEC/P2P-PROVIDER-ABSTRACTION-SPEC.md`
- `docs/SPEC/P2P-CAPABILITY-EXECUTION-EVIDENCE-SPEC.md`

This document is the approved architecture contract for this scope. It does not
authorize production implementation, host deployment, user configuration
mutation, release, promotion, or any runtime certification. The owner approval
covers architecture and terminology only; all implementation, deployment,
runtime, release, and promotion gates remain separate.

## Purpose

Define the smallest deterministic, host-neutral boundary that converts an
already-selected P2P capability and its resolved canonical context into a
host-native projection plan. The plan is pure data. It describes what a future
controlled writer could materialize; it does not materialize it.

The canonical direction is:

```text
P2P capability registry
        -> existing single router selects capability
        -> existing context resolver resolves permitted canonical content
        -> Host Skill Projector builds pure-data plan
        -> separate owner-authorized deployment boundary
        -> separate host runtime
```

P2P remains canonical. A host projection is a derived view and never becomes a
second source of truth.

## Non-goals

- No router, skill engine, executor, provider selector, model selector,
  package manager, deployment system, task-state system, approval system, or
  host launcher.
- No host runtime attestation, host account management, authentication,
  permission grant, quorum change, evidence acceptance, or task-state write.
- No copy of the `cc-use-exp` source, scripts, rules, profiles, installer,
  patcher, or user-configuration mutation logic.
- No user/global host path, including `~/.codex`, `~/.claude`, `~/.gemini`,
  `~/.cursor`, or equivalent, in a projection target.
- No full vendor-tree replication. References, assets, and scripts remain
  separately addressable and are not loaded or copied by discovery.
- No host support claim based only on a vendored folder or a stale host opinion.

## Authority and ownership

The capability registry, current P2P manifest validation, context-pointer
contract, and existing router are authoritative for capability identity,
description, invocation class, provenance, trust, scope, readiness, and
approval boundary. The projector may validate and transform those values but
may not amend them.

The host owns the semantics of its native metadata and runtime. The projector
may emit a host-native representation only when the mapping and serialization
contract are current and unambiguous. Host-native output is never authority
for P2P routing, governance, provenance, or evidence.

Only a future controlled writer may own files explicitly classified as
`P2P_PROJECT_MANAGED`. Existing host-owned files, user-level files, and
unmanaged project files are preserve-only or blocked. This SPEC defines no
writer.

## Layer boundary

The projector accepts a selected capability and an explicit host target. It
does not choose either one. It may reject a request when the selected
capability, resolved context, host mapping, provenance, or target scope is
unsafe. Rejection is a data result with a stable reason code.

The projector cannot:

- invoke or rank capabilities;
- select or change a provider, model, harness, protocol, tool set, workspace,
  authentication state, or permission envelope;
- turn retrieved content into instruction authority;
- create or update Goal, task state, execution ledger, approval, quorum, or
  decision-trace records;
- launch a process, execute a script, install a dependency, use a credential,
  call a network service, or write a file.

## Canonical input contract

The normalized input is `p2p-host-skill-projection-input/1`. It is derived from
existing P2P structures and an explicit projection request. The minimum fields
are listed below. `skill_id` is the normalized input name for the existing canonical
`CAPABILITY_ID`; no second identity is created:

| Field | Source / rule |
|---|---|
| `skill_id` | Existing validated `CAPABILITY_ID`; never host-generated. |
| `display_name` | Deterministic label derived from the validated ID and P2P `DESCRIPTION`; no upstream host label is authoritative. |
| `description` | Existing P2P `DESCRIPTION`; whitespace-normalized only for host serialization. |
| `invocation_class` | Existing `INVOCATION_CLASS`. |
| `invocation_policy` | Derived from P2P invocation policy and host capability; it is never defaulted to implicit. |
| `context_entrypoint` | Existing vendor integration entrypoint or validated context pointer. |
| `context_refs` | Existing `CONTEXT_POINTERS` plus explicitly declared references; not a full tree. |
| `provenance` | Existing `UPSTREAM_PROVENANCE`, registry hash, source class, license, and verification state. |
| `source_hash` | Existing immutable source/snapshot hash. |
| `entrypoint_hash` | Existing exact entrypoint hash. |
| `host_kind` | Explicit request value from the closed host vocabulary. |
| `host_scope` | Explicit project-relative target scope; user/global scope is invalid here. |
| `approval_boundary` | Existing `APPROVAL_BOUNDARY`; transformed, never weakened. |
| `trust_level` | Existing manifest trust level; it does not grant authority. |
| `load_stage` | One of `DISCOVERY`, `MATCH`, `LOAD`, or `DEEP_LOAD`. |

No new registry field is required by this contract for the current two vendor
skills. `display_name`, `invocation_policy`, and `host_scope` are derived or
request-scoped. A future registry change is justified only if an actual
validated capability cannot supply a safe value without guessing.

### Invocation policy

The mapping is explicit:

| P2P policy | Host projection meaning |
|---|---|
| `USER_REQUESTED` | Explicit invocation only. |
| `MODEL_ROUTABLE` | Implicit invocation is eligible only where the host mapping explicitly supports it and the P2P route has selected the capability. |
| `GOVERNANCE_MANDATED` | Explicit policy-bound representation only; never a general implicit skill trigger. |

The Codex `allow_implicit_invocation` value, when the Codex mapping is
supported, is the result of this policy plus host validation. It must not
default to `true` because an upstream skill or host tree uses that value.

## Projection output contract

The output is `p2p-host-skill-projection-plan/1` and contains no write result.
The minimum shape is:

```text
HostProjectionPlan {
  schema
  status: READY | BLOCKED
  host_kind
  capability_id
  source_hash
  entrypoint_hash
  load_stage
  files[]
  warnings[]
  blocked_reason
  content_loaded: bool
  writes_performed: false
  provider_mutated: false
  model_mutated: false
  auth_mutated: false
  permission_mutated: false
  task_state_mutated: false
}

HostProjectionFile {
  relative_target
  format
  content_hash
  content_or_template
  ownership_class: P2P_PROJECT_MANAGED | HOST_OWNED_PRESERVE | OWNER_REVIEW_REQUIRED
}
```

`relative_target` is relative to the project root and must not contain an
absolute path, drive, home-directory marker, traversal, or user-specific
location. `content_or_template` is absent during metadata-only discovery. It
contains only the entrypoint-derived host content after an explicit `LOAD`.
References, assets, and scripts appear only after an explicit `DEEP_LOAD` and
must retain their source hashes and relative paths. Scripts are pointers/data,
not executable work.

OWNER_REVIEW_REQUIRED means that an ownership decision is still required; it
does not authorize a write. If unresolved ownership is required for deployment,
the result must fail closed with P2P_OWNERSHIP_REVIEW_REQUIRED. Projection
performs no writes in any status.

The output is deterministic and idempotent: identical validated input,
source bytes, host mapping, and load stage produce byte-equivalent canonical
JSON and the same ordered file list. The plan contains no nondeterministic
timestamp, random ID, host secret, or environment dump.

## Progressive disclosure invariant

The projector preserves four stages:

```text
DISCOVERY  -> metadata only; no SKILL.md, refs, assets, or scripts read
MATCH      -> selected capability and canonical entrypoint pointer
LOAD       -> exact SKILL.md only, after selection
DEEP_LOAD  -> explicitly requested, declared refs/assets/scripts only
```

An unrelated request must produce no projected skill content. The projector
must never inject a full vendor tree or silently expand a reference set.

## Host-kind vocabulary and current mapping status

The closed design vocabulary is `codex`, `claude`, `gemini`, `cursor`,
`copilot`, and `antigravity`. An unlisted host has mapping status
`HOST_UNKNOWN` and blocks.

Host mapping status is one of `MAPPING_SUPPORTED`, `MAPPING_PLANNED`,
`HOST_UNKNOWN`, or `BLOCKED_HOST_DRIFT`. `MAPPING_SUPPORTED` means only that a
projection mapping is defined; `MAPPING_SUPPORTED` is not
`HOST_RUNTIME_CERTIFIED`.

| Host kind | Current status | Project-relative native target | Required metadata / transform |
|---|---|---|---|
| `codex` | `MAPPING_SUPPORTED` | `.agents/skills/<capability_id>/SKILL.md` and `.agents/skills/<capability_id>/agents/openai.yaml` | `interface.display_name`, P2P `DESCRIPTION` as `interface.short_description`, and policy-derived `allow_implicit_invocation`; no `.codex/config.toml` mutation. |
| `claude` | `MAPPING_PLANNED` | `.claude/skills/<capability_id>/SKILL.md` | Native skill frontmatter with P2P display/description; no `CLAUDE.md`, rules, commands, or global config injection. |
| `gemini` | `MAPPING_PLANNED` | `.gemini/skills/<capability_id>/SKILL.md` | Native skill metadata from P2P fields; `GEMINI.md`, rules, policies, and settings remain untouched. |
| `cursor` | `MAPPING_PLANNED` | `.cursor/rules/<capability_id>.mdc` | Native rule metadata with explicit non-global scope; no unbounded glob and no implicit always-apply default. |
| `copilot` | `MAPPING_PLANNED` | `.github/instructions/<capability_id>.instructions.md` | `applyTo` must come from an explicit safe P2P scope; `**` is never a default. |
| `antigravity` | `HOST_UNKNOWN` | No target emitted until current native format evidence exists | Host folder presence is not evidence; block on missing or drifted format. |

`MAPPING_SUPPORTED` means the plan can define the mapping from current P2P
project paths and known native format evidence. It does not mean the host
runtime has been independently certified. `MAPPING_PLANNED` means a mapping is
defined but not currently wired. `HOST_UNKNOWN` means no safe mapping may
be emitted. If current host evidence changes or conflicts, the result becomes
`BLOCKED_HOST_DRIFT`.

## Provenance, freshness, and trust

The source hash and entrypoint hash must be present, valid, and equal to the
current bytes at the requested load stage. A stale or mismatched hash blocks;
it is never refreshed silently. Provenance must identify a safe source class,
source path/reference, license state, and verification state. The projector
does not relicense vendor material or treat a host projection as new source
authority.

Retrieved content and upstream skill prose remain data at this boundary. They
cannot grant tools, permissions, approval, owner authority, or a quorum vote.
Diagnostics may include IDs, reason codes, hashes, safe relative paths, and
freshness states, but never secrets or hidden reasoning.

## Fail-closed semantics

The following conditions must return `BLOCKED` with exactly one stable canonical
reason code; no best-effort file plan is allowed:

| Condition | Required result |
|---|---|
| Unknown host | `HOST_KIND_UNKNOWN` |
| Missing provenance | `PROVENANCE_MISSING` |
| Stale source hash | `SOURCE_HASH_STALE` |
| Entrypoint mismatch | `ENTRYPOINT_HASH_MISMATCH` |
| Path traversal | `PATH_TRAVERSAL` |
| Absolute target | `ABSOLUTE_TARGET_PATH` |
| Unsupported invocation policy | `INVOCATION_POLICY_UNSUPPORTED` |
| Ambiguous host format | `HOST_FORMAT_AMBIGUOUS` |
| Current host evidence conflicts with the mapping | `BLOCKED_HOST_DRIFT` |
| Invalid serialization | `SERIALIZATION_INVALID` |
| Conflicting P2P ownership | `P2P_OWNERSHIP_CONFLICT` |
| Unselected capability at `LOAD` | `CAPABILITY_NOT_SELECTED` |
| Implicit full-tree or undeclared deep load | `CONTEXT_EXPANSION_UNAUTHORIZED` |
| Missing explicit Copilot scope | `COPILOT_SCOPE_REQUIRED` |
| Unresolved ownership required for deployment | `P2P_OWNERSHIP_REVIEW_REQUIRED` |
| Missing approval boundary | `MISSING_APPROVAL_BOUNDARY` |
| Host scope does not match the requested host | `HOST_SCOPE_MISMATCH` |

An unavailable optional dependency is a blocked optional operation; it is not
converted to a successful projection and it must not make core P2P appear
unavailable.

These reason codes are the only public vocabulary for these semantic
conditions. No alternate or alias reason code is accepted.

## Deployment and runtime separation

Projection is offline, pure, read-only, deterministic, and side-effect free.
Deployment is a future separate contract requiring a controlled writer,
explicit owner authorization, exact subject/source hashes, managed-path
ownership, conflict detection, rollback, and independent verification. An
OWNER_REVIEW_REQUIRED classification does not authorize that writer; unresolved
deployment ownership must fail closed. That writer must preserve host
authentication, history, logs, cache, default provider/model, base URL, and all
unmanaged config. No user-level writer is defined in this SPEC.

## Compatibility and forbidden abstractions

The projector reuses the existing registry, manifest, vendor adapter, context
pointer, routing, trust, evidence, and host-selection vocabulary. It must not
introduce a second registry, provenance ledger, state store, router, executor,
or deployment orchestrator. The following names are explicitly rejected as
new architecture: `HostProjectionEngine`, `SkillCompilerFramework`,
`ProjectionRegistryV2`, `HostCapabilityRouter`, and
`SkillDeploymentOrchestrator`.

Existing provider/model/auth/execution-target, task-state, host-execution, and
approval semantics remain unchanged. A projection plan is not an execution
target, host attestation, task checkpoint, evidence PASS, release candidate,
or promotion decision.

## Evidence and evaluation contract

Future implementation evidence must prove behavior rather than file existence:

1. deterministic output for identical inputs;
2. idempotent canonical serialization;
3. no entrypoint read during discovery;
4. source and entrypoint hashes preserved;
5. provenance and approval boundary preserved;
6. Codex metadata serializes correctly;
7. implicit invocation is derived from P2P policy;
8. Claude is a target and never canonical;
9. Copilot never receives silent wildcard scope;
10. unknown/unsupported host fails closed;
11. stale source and mismatched entrypoint fail closed;
12. malformed metadata, traversal, and absolute targets fail closed;
13. provider/model/auth/permission/task state remain unchanged;
14. the two existing vendor skills simulate correctly for Codex, Claude, and Gemini;
15. unrelated requests load no skill content;
16. the one-router invariant and canonical 8/8 semantics remain unchanged.

Evidence must use existing P2P evidence/ledger/report surfaces. No second
projection ledger or automatic task-state event is introduced.
Future tests must assert the exact canonical reason codes above; aliases are
not equivalent evidence.

## Architecture / SPEC rule versus implementation suggestion

Architecture / SPEC rule: the authority, input/output boundary, host vocabulary,
progressive-disclosure, provenance, fail-closed, determinism, ownership, and
deployment-separation clauses above are binding if this SPEC is approved.

Implementation suggestion: one standard-library module under
`.p2p/system/p2p_capabilities/` may build the plan, and one focused test file
may exercise the contract. These are implementation choices, not additional
architecture authority. No registry or router edit should be made unless a
test proves an existing field cannot express the approved contract safely.

## Done when

This SPEC is marked APPROVED by the applicable architecture/owner authority,
the future implementation plan is hash-bound to the approved text, and later
behavior evidence proves the evaluation contract without host deployment or
user-config mutation.
