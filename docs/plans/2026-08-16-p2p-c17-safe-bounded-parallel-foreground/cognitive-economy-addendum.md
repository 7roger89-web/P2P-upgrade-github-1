# P2P-C17 Cognitive Economy / Spawn Economy Addendum

Date: `2026-08-16`  
Chat: `P2P-C17 / Làm nhiều việc độc lập cùng lúc an toàn`  
Mode: `CONTINUE CURRENT CHAT`

## Result

`PASS / COGNITIVE_ECONOMY_PARALLEL_ORCHESTRATION_EVALUATED`

The existing C17 safety result remains unchanged:

`PASS / PARALLEL_EXECUTION_FOUNDATION_READY`

This addendum evaluates bounded orchestration economy. It does not claim that
parallel execution is always faster, cheaper, or universally optimal. The
runtime uses quality-adjusted gate signals and deterministic rejection reasons;
it does not introduce a numeric optimizer, scheduler, worker pool, background
execution, remote execution, or adaptive quorum.

## Requirement classification

| Requirement | Classification | Evidence / decision |
|---|---|---|
| Existing C17 max-two foreground safety | `ALREADY_PROVEN` | C17 focused suite, group receipts, no background/pool/grandchild, C08/C09/canonical preservation |
| C15 tiny/no-material-value delegation gate | `ALREADY_PROVEN` | Existing C15 decision surface and C17 sequential fallback |
| Progressive disclosure and local context serialization proxy | `ALREADY_PROVEN` | C06 context modes, pointers, stale binding rejection, `LOCAL_SERIALIZATION_PROXY` |
| Parent/worker separation and parent verification | `ALREADY_PROVEN` | C15 handoff/result contracts, parent verification, output-not-evidence invariant |
| Explicit large duplicated-context gate | `PARTIALLY_PROVEN` → `ALREADY_PROVEN` for this bounded slice | New `ParallelEconomyProfile` and deterministic `DUPLICATED_CONTEXT_OVERHEAD` rejection |
| Explicit handoff/verification overhead gate | `PARTIALLY_PROVEN` → `ALREADY_PROVEN` for this bounded slice | Fixed work/coordination signals; no universal score or performance claim |
| Result-context dependency and insufficient-context escalation | `PARTIALLY_PROVEN` → `ALREADY_PROVEN` for this bounded slice | `CONTEXT_INSUFFICIENT` and `RESULT_CONTEXT_DEPENDENCY` reject parallel selection |
| SEQUENTIAL_DIRECT / SEQUENTIAL_DELEGATED / PARALLEL_BOUNDED comparison | `NOT_PROVEN` → `ALREADY_PROVEN` for deterministic fixtures | CE1–CE10 and 0/1/2-worker tests |
| Universal minimum-context/minimum-worker optimum | `NOT_PROVEN` | Deliberately not inferred from synthetic fixtures |
| Token, price, provider, or wall-clock optimization | `NOT_PROVEN` | Local byte proxy is not converted into those claims |
| Live native-host parallel certification | `NOT_PROVEN` | Remains separately `NOT_CERTIFIED`; no host surface was simulated |
| External networking, cloud memory, model routing, or provider selection | `NOT_APPLICABLE` | Out of this offline bounded runtime slice |

## Economy gate

`ParallelEconomyProfile` is optional and backward-compatible. Without a profile,
the controller derives a small deterministic work-unit default from the
existing C15 task size. A supplied profile can record:

- expected work units;
- handoff and verification units;
- context bytes only as an explicitly labelled local serialization proxy;
- source/context fingerprints for duplicate detection;
- `CONTEXT_INSUFFICIENT`, result-context dependency, owner-interruption risk,
  and material-evidence-delta signals.

The controller rejects a pair when a safety/quality boundary is not reliable,
when the same large context is duplicated, when coordination is not justified
by the declared quality value, or when owner interruption would add ceremony
without material value. A quality reason such as independent review can keep a
small pair eligible even when raw work units do not dominate ceremony. This is
the quality-adjusted policy boundary; it is not a universal cost equation.

The gate preserves valid Spawn Economy outcomes:

| Candidate workers | Runtime result |
|---:|---|
| 0 | `BLOCKED` / no worker start; direct control remains with the parent |
| 1 | `SEQUENTIAL` through the existing direct/delegated C15 path |
| 2 | `PARALLEL` only after the existing independence, permission, budget, and economy gates |

## Context and handoff seams

The parent receives structured Knowledge Delta fields and durable references,
not a copied worker narrative. C15 continues to emit a compact proposal with
summary, work performed, artifact references, self-checks, unresolved items,
risks, next step, candidate binding, and `output_is_evidence=false`. The C17
group receipt stores economy profiles beside handoff/result/verification and
combined-verification references. The existing `p2p-capsule/2` continuation
seam remains a pointer/index to authoritative state; large context remains in
the project state, manifests, ledger, and referenced artifacts.

`LOCAL_SERIALIZATION_PROXY` records measured local serialized bytes only. It
does not claim token usage, API cost, wall-clock savings, throughput, or worker
quality improvement.

## CE1–CE10 controlled evaluations

| Case | Fixture | Result |
|---|---|---|
| CE1 | Two tiny independent tasks | `SEQUENTIAL`; C15 selects direct/low-overhead path |
| CE2 | Two meaningful independent moderate tasks | `PARALLEL`; bounded economy profile is accepted |
| CE3 | Two tasks with the same large context fingerprint | `SEQUENTIAL`; `DUPLICATED_CONTEXT_OVERHEAD` |
| CE4 | One candidate has reduced acceptance context | `SEQUENTIAL`; `CONTEXT_INSUFFICIENT`, never parallel PASS |
| CE5 | Worker supplies verbose narrative plus structured result fields | Structured compact delta is retained; oversized unsafe narrative is rejected, never silently accepted |
| CE6 | One extensive task plus one tiny task | `SEQUENTIAL`; readiness alone does not justify a second worker |
| CE7 | Independent-review value is explicit | `PARALLEL` may remain justified even without a raw speed claim |
| CE8 | Deterministic verification answer | `SEQUENTIAL`/direct; no worker is spawned for no-value work |
| CE9 | Equivalent baseline vs efficient context proxy | Lower local proxy path avoids the duplicated-large-context rejection |
| CE10 | Lower context but result depends on missing context | `SEQUENTIAL`; `RESULT_CONTEXT_DEPENDENCY` |

The fixtures are deterministic and isolated under repo-local `.tmp` roots. They
are evidence for policy behavior, not a benchmark proving a universal optimum.

## Research preservation and roadmap seams

The existing external research registry remains unchanged and non-vendored:
Superlearn, TencentDB Agent Memory, Semantica, Zimster, Agent TaskGraph
Protocol, DeepSeek Harness, Nolane UI Intelligence/NUI, and Comp AI CRM. The
adapted principles remain research-before-plan, explicit coverage checklist,
one bounded subtask per worker, filesystem/context offloading, durable evidence
trail, parent review of worker artifacts, and deterministic validation before
completion.

Older directions remain preserved as research-only/unknown where exact runtime
status is not established: FAST_TRIO, CODE_QUAD, SECURITY_QUAD, ARCH_PENTA,
Budget Declaration, Spawn Economy, Dynamic Weighting, MASPO, PXPIPE, adaptive
worker/agent count, adaptive quorum/rigor, adaptive reasoning, provider
selection, task-targeted retrieval, cache-aware context, and project/repo maps.
This slice adds only the bounded seam needed to evaluate current C17 economy;
adaptive orchestration remains a future roadmap item.

## Candidate and governance boundary

- Official `.19` remains immutable and its SHA-256 remains
  `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`.
- Existing C17 final2 candidate remains historical and unpromoted after the
  runtime economy extension.
- A new `.20` candidate is required because source behavior changed; it is
  built and verified separately as
  `P2P-8.4.7-C-Codex-Edition-v20-c17-cognitive-economy-candidate.zip` with
  SHA-256 `d4b4966716da6b06e3211b57f2e9df6649d99c840272a988e287d5c36ba99983`;
  it remains unpromoted.
- `LIVE_PARALLEL_EXECUTION_CERTIFIED` remains `NO / NOT_CERTIFIED`.
- C08 remains `DEFERRED`, C09 remains `BLOCKED / EVENT_EVIDENCE_UNAVAILABLE`,
  and the canonical capability set remains exactly 8 with quorum 8/8.

## Decision

The bounded cognitive-economy slice is `PASS`. It is sufficient to preserve
quality, evidence, safety, and regression boundaries for the current C17
foreground foundation. Broader adaptive worker count, model/provider choice,
token/cost measurement, quorum adaptation, and live-host certification remain
future work and are not implied by this result.
