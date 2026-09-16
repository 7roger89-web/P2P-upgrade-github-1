# PROJECT STATE — P2P Opportunity Lab

TASK_ID: P2P_MARKET_VALIDATION_PILOT_01
STATUS: EXPERIMENTAL
CANONICAL_CAPABILITY: NO
PROMOTION: UNPROMOTED
MARKET_GATE: VALIDATE

## Goal

Prove or falsify that P2P can turn a rough opportunity into an evidence-grounded market decision before full product implementation.

## Authority and guardrails

- BUILDABLE != VIABLE.
- GOAL PASS != MARKET PASS.
- Desk research alone cannot produce BUILD.
- Owner preference is not evidence.
- Contradicting evidence is preserved.
- BUILD requires an observed real-world experiment plus observed payment/WTP evidence.
- Public pain/prospect evidence cannot be promoted into PAYMENT/WTP.
- No private contact enrichment, automatic spend, production deploy, secrets, or infrastructure changes.
- Canonical P2P law remains the authority; this lab maintains only a binding/reference, not a hand-edited law copy.

## First pilot

Logistics quote comparison: normalize and compare inconsistent freight quotations/rate sheets without requiring suppliers to adopt a new input format.

## External validation lane

Owner authorized contact for exactly the first three shortlisted prospects on 2026-09-16 09:27 +07:00.

Durable batch: `pilots/logistics-quote-comparison/outreach-batch-01.json`.

Current delivery state remains:
- `sent_count=0`
- `reply_count=0`
- `opt_in_count=0`
- `READY_BUT_NOT_SENT`
- blocker: current ChatGPT surface has no authenticated Reddit write/post action.

A six-hour reply watch is active, but an unsent outreach comment cannot receive a direct reply. Authorization does not need to be requested again when a valid Reddit write surface appears.

## Atomic quote validation pipeline

Raw real-world atomic comparison entrypoint:

`src.validation_pipeline.compare_quotes_validated`

Pipeline order:

`explicit FX -> named-base percentage -> charge semantics -> deterministic core comparison`

Implemented protections include:
- evidence-backed direct FX only; no inferred inverse/triangulation;
- FX rate requires positive rate, source reference and date;
- future-dated FX relative to explicit comparison date is rejected;
- original cross-currency amount/minimum are preserved in audit;
- percentage resolution occurs after FX so converted named bases are calculated in quote currency;
- named-base percentage rules never guess their base;
- scoped charges distinguish `ORIGIN | MAIN | DESTINATION | OTHER | UNSPECIFIED`;
- exact duplicate priced charges block ranking;
- evidenced all-in bundles expand to included coverage while blocking bundle/component double counting;
- optional/add-on selection is explicit; unselected items leave price/coverage but remain auditable;
- optional percentage charges that are unselected or still selection-ambiguous are deferred to the optional-service guard instead of triggering unnecessary percentage resolution;
- route/equipment/currency grouping, charge coverage, validity, minimum charge, conditional terms, equipment aliases and evidence-backed route aliases remain active.

## Multi-equipment FCL validation pipeline

Raw provider-portfolio entrypoint:

`src.portfolio_validation_pipeline.compare_fcl_portfolios_validated`

Base portfolio engine remains:

`src.portfolio_semantics.compare_fcl_portfolios`

The validated portfolio pipeline now:
- resolves FX independently for every required equipment offer and shared provider bucket;
- resolves percentage surcharges only after FX;
- uses the required equipment quantity when resolving an offer-level percentage;
- rebases the resolved percentage total to a `PER_CONTAINER` amount that reconstructs the same offer total in the existing engine;
- resolves shared FX/percentage charges once at provider level, not once per equipment row;
- excludes a provider whose FX or percentage semantics are unresolved while allowing other complete providers to remain rankable;
- preserves apples-to-apples coverage per equipment bucket and shared bucket;
- rejects missing or ambiguous required equipment rather than guessing.

## Schemas and documentation

- quote intake carries charge scope, bundle fields, optional selection, stable `line_id`, percentage rate and named base line IDs;
- comparison context carries explicit direct `fx_rates` with `from`, `to`, positive `rate`, `source_ref` and `as_of_date`;
- `docs/CHARGE-SEMANTICS.md`, `docs/PERCENTAGE-SEMANTICS.md`, and `docs/FX-SEMANTICS.md` define the entrypoint hierarchy and evidence boundaries.

## Verification state

Verified focused harness evidence preserved:
- market gate: 5/5 PASS;
- prospect bridge: 5/5 PASS;
- shortlist fixture: 6/6 PASS;
- prior base concierge suite: 15/15 PASS before later grouping additions;
- group/equipment probes: 5/5 PASS;
- route-alias helper probes: 4/4 PASS;
- conditional-term probes: 3/3 PASS;
- charge semantics: 9/9 PASS using repo-style `src.*` imports;
- percentage core resolver: 5/5 PASS in isolated deterministic harness;
- original FCL portfolio focused slice: 5/5 PASS;
- experiment tracker: 5/5 PASS.

Committed acceptance contracts additionally cover FX, optional-percentage delegation, atomic FX/percentage pipelines, expanded portfolio semantics, and FX/percentage-aware portfolio validation. Those newer tests are not falsely labeled full source-tree PASS without an actual runner executing them. GitHub Shield is verified separately on exact heads.

## Current checkpoint

`VALIDATE — OUTREACH_AUTHORIZED + FX_NORMALIZATION_READY + ATOMIC_VALIDATION_PIPELINE_READY + PERCENTAGE_SURCHARGE_READY + GUARDED_CHARGE_SEMANTICS_READY + MULTI_EQUIPMENT_FCL_PIPELINE_READY + EXPERIMENT_TRACKER_READY`

The external lane is blocked only on Reddit delivery capability. Internal validation can now normalize explicitly evidenced mixed-currency fixed charges before percentage and comparison semantics instead of either silently converting or rejecting every mixed-currency quote.

## Next bounded step

1. Deliver only the three already-authorized Reddit research replies when an authenticated write surface exists.
2. Continue validation-only hardening where representative freight quote semantics justify it; candidate next slice is tiered/bracket pricing, but do not implement speculative breadth before checking the exact-head state and acceptance evidence.
3. On opt-in, run the real concierge test through the top-level validated entrypoint, record corrections/trust objections/repeat use and explicit WTP/payment signals.
4. Feed only observed experiment output into the market gate and re-evaluate `VALIDATE | BUILD | KILL`.
