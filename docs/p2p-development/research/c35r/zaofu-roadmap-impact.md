# C35R — Roadmap Impact Assessment

**Goal:** C35R (research only). **Reference points:** ZaoFu upstream main `@ b5e569dd` (v0.0.5, Apache-2.0); P2P at `c35-provider-neutral-runtime @ 7c9cb58`.
**Scale used:** `NO_CHANGE` / `MINOR_REFINEMENT` / `MATERIAL_REDESIGN_REQUIRED`, reported separately for C36 and C37.

## C36 — Context / Cache / Token / Cost Intelligence

**Verdict: MINOR_REFINEMENT**

The audit found that ZaoFu already implements, at the implementation level, most of what the C36 lane plans at the specification level. This is net-positive: it validates the C36 scope and supplies concrete design artifacts to borrow, rather than forcing a redesign.

Exact deltas identified (all additive, none destructive):

1. **Context manifest + delivery envelope.** ZaoFu's `src/zf/runtime/context_delivery.py` models context as an *immutable source manifest* turned into a sectioned envelope (`required` / `delta_allowed` flags) bound to workflow, task, contract, session, and permission identity, with a delivery receipt that deliberately does not claim reads. `task_context_manifest.py` adds a four-facet manifest (`implement`/`check`/`research`/`closeout`) with `missing_required_refs` and `read_receipt_gaps`. C36 should adopt the manifest-then-delivery split: P2P's context truth stays in P2P's own format, but a durable "what was delivered, with which digests" envelope materially strengthens the beginner-first promise (the operator can see exactly what the agent received).
2. **Read-receipt accounting.** "What the agent was *told* to read vs what it *actually* read" is a gap C36 currently does not model. ZaoFu's receipt pattern closes it without any new runtime dependency.
3. **Cost telemetry shape.** `cost/tracker.py` (active+archive JSONL), `BillingAdapter` pluggability, and `check_budget` → halt give C36's cost-intelligence layer a proven reference shape. P2P should keep its evidence-first posture (record usage per receipt) and add an optional enforced budget only if C36's design calls for it.
4. **Briefing metrics.** Soft budgets on briefing size (`briefing_metrics`) are a cheap, concrete C36 addition with no authority impact.

No C36 component needs redesign: the cache and token aspects of C36 remain untouched by the audit, and P2P's deterministic verification standard is not challenged by ZaoFu's judge patterns (the judge is deferred to C37-relevant closure work, not C36).

## C37 — Adaptive Target / Model / Effort Selection

**Verdict: MINOR_REFINEMENT**

Two borrowings sharpen the C37 design without changing its foundations:

1. **Declarative capability matrix.** ZaoFu's `BackendCapabilities` dataclass (hooks, resume, usage reading, stream-json, nested-agent, child-lineage, multi-agent…) demonstrates a clean way to prevent `if backend == …` branching across the codebase. P2P already has `BackendCapabilityCertification` (claim-based, auditable); the refinement is to give C37's adaptive selector a *declarative* capability view alongside the certification view. This is a presentation/selection-layer addition, not a redesign of the selection policy (C21 minimum-sufficient selection remains P2P's ground truth).
2. **Operator-visible control actions.** ZaoFu's `control_actions_*` mixins (plan-approve/reject, recovery verbs, replay/resume with `checkpoint_id`) show how an adaptive layer can expose a small, audited verb set to the operator. C37's adaptive execution policy (C18) can adopt the "small deterministic verb set" discipline; P2P's Owner Gates remain the authority, exactly as they are today.

Additionally, C37 gains an optional recovery refinement: ZaoFu's `RecoverySeries`/rework-cap/quarantine pattern (evidence-based rework messages, cap exhaustion → formal bug candidate instead of silent drops) fills a known gap in P2P's recovery story and is pure, event-driven, provider-neutral logic P2P can adapt in its own recovery lane without touching C35's receipt/quorum surfaces.

No C37 component requires redesign; both refinements are additive and authority-preserving.

## Cross-lane observations (no roadmap action required)

| Observation | Consequence |
|---|---|
| ZaoFu multi-agent fanout/autoresearch is outside P2P's current lane | No C-lane change; if a future lane ever targets autonomous self-repair, ZaoFu's autoresearch module is the best known prior art to audit first |
| ZaoFu dashboard/CLI is operator-tooling oriented, P2P is certification-machine oriented | Confirms the beginner-first UX divergence; no merge point |
| C35 architecture validated | No change to C35; the receipt/quorum model and ZaoFu's CAS/event model are complementary, not conflicting |
