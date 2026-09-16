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

Full source-tree deterministic acceptance now exists through `.github/workflows/p2p-opportunity-lab-focused.yml`.

Exact accepted evidence on head `4dfd6ba5168bac14e1bafc3ad70ef22f41192a05`:
- source compile: **PASS**;
- full Opportunity Lab pytest suite: **86/86 PASS** (`86 passed in 0.08s`);
- focused workflow run `35072232369`: **SUCCESS**;
- P2P Shield run `35072232306`: **SUCCESS**.

The 86-test total is reconciled with `docs/TEST_MATRIX.md`; the design-partner fixture is 4 tests exercising 6 candidates, not 6 tests.

Focused historical harness evidence remains useful for diagnosis, but the exact-head GitHub Actions run above is now the authoritative deterministic regression evidence for that head. Any later branch mutation requires fresh focused-CI evidence before the new head inherits PASS status.

## Current checkpoint

`VALIDATE — OUTREACH_AUTHORIZED + FX_NORMALIZATION_READY + ATOMIC_VALIDATION_PIPELINE_READY + PERCENTAGE_SURCHARGE_READY + GUARDED_CHARGE_SEMANTICS_READY + MULTI_EQUIPMENT_FCL_PIPELINE_READY + FULL_DOMAIN_CI_READY + EXPERIMENT_TRACKER_READY`

The external lane is blocked only on Reddit delivery capability. Internal validation now has a reproducible exact-head domain-test surface rather than fragmented local probe evidence.

## Next bounded step

1. Deliver only the three already-authorized Reddit research replies when an authenticated write surface exists.
2. Before adding pricing breadth, use the full focused CI as the gate for any internal hardening; prefer fixing integration/bypass inconsistencies over speculative new semantics.
3. On opt-in, run the real concierge test through the top-level validated entrypoint, record corrections/trust objections/repeat use and explicit WTP/payment signals.
4. Feed only observed experiment output into the market gate and re-evaluate `VALIDATE | BUILD | KILL`.
