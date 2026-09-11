# Upstream finding — `tamnd/luatdo`

Reviewed: `2026-09-11`
Upstream head reviewed: `42cd4817b41ae9bbe4c889e79d892a02160a0c5f`
License: `MIT`
Provisional verdict: `ADAPT`

## Why it matters

`luatdo` is not merely another RAG demo. Its core model directly attacks the difficult part of Vietnamese legal retrieval: a structural provision keeps its identity while its wording and force change over time.

The repository explicitly separates:

- deterministic document/citation structure from model-generated semantics;
- stable `Component` identity from wording/version state;
- raw amendment evidence from interpreted temporal events;
- trusted on-disk state from Neo4j, which is treated as a rebuildable projection.

This is closely aligned with P2P Legal VN's desired truth layer.

## High-value patterns to adapt

### 1. Stable provision identity + temporal wording

`law/component.go` and the README model a structural provision separately from its wording. A provision can therefore survive an amendment without inventing a new legal identity for the Article/Clause/Point itself.

For P2P Legal VN, preserve this distinction:

```text
ProvisionIdentity != TextVersion
```

### 2. Amendment operation is not automatically trusted mutation

`temporal/temporal.go` separates an extracted `Operation` from an applied `Event`. The target is resolved outside the model and the version graph/text transformation is built in deterministic code.

This is the right safety boundary for legal data:

```text
instruction reading -> resolve/validate -> event -> version transition
```

not:

```text
LLM reads amendment -> LLM rewrites corpus
```

### 3. Quarantine rather than guess

The temporal package has explicit quarantine reasons for unresolved targets, missing text, missing dates, phrase-not-found, compound targets and other ambiguous states. A quarantined operation remains inspectable but does not alter the version graph.

P2P should adapt this behavior, not necessarily its exact enum.

### 4. Effective dates are never guessed

An operation uses its own effective date where stated, otherwise the instrument's commencement date. If neither exists, it remains undated and is excluded from point-in-time answers.

This is a mandatory legal-truth invariant for our implementation.

### 5. Half-open validity intervals

A version covers `[from, to)`, avoiding two simultaneously valid answers on the successor's start date. This is simple and correct enough for the Phase-1 model.

### 6. Suspension is distinct from repeal

The temporal model carries `in_force` and `suspended` separately and also models resume. P2P should preserve the conceptual distinction even if the TT39 first slice does not exercise it.

### 7. Consolidated text as external ground truth

`temporal/consolidated.go` compares the computed point-in-time text against a published `văn bản hợp nhất`. It matches by structural path and reports divergence instead of silently repairing derived text.

This is one of the strongest patterns in the repository and should be adapted directly at the design level.

## What not to adopt yet

- Neo4j as a required runtime dependency. `luatdo` itself says Neo4j is a projection; Phase 1 can use plain JSON/SQLite/PostgreSQL structures.
- the full ontology/concept/norm extraction pipeline;
- corpus-wide LLM campaigns;
- eight-million-node graph deployment;
- every event kind before a real P2P test needs it.

Those are later capabilities, not prerequisites for proving TT39 amendment history.

## Evidence inspected

- `README.md`
- `law/component.go` references via code search
- `temporal/temporal.go`
- `temporal/consolidated.go`
- `temporal/*` package surface via repository code search
- upstream main commit metadata

Not yet executed locally: the current tool shell could not resolve `github.com`, so no clone/build/test result is claimed in this record.

## Phase-1 decision

Use `luatdo` as the primary reference implementation for **data semantics and failure discipline**, not as a dependency to install wholesale.

Next falsification test: run the P2P TT39 concrete slice against its temporal/parser behavior. If it cannot correctly represent the `06/2023/TT-NHNN` amend + supplement + repeal operations, downgrade this verdict instead of building around it.
