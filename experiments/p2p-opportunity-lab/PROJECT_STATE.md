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

Real-world atomic comparison entrypoint:

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

Real-world provider-portfolio entrypoint:

`src.portfolio_validation_pipeline.compare_fcl_portfolios_validated`

The validated portfolio pipeline:
- resolves FX independently for every required equipment offer and shared provider bucket;
- resolves percentage surcharges only after FX;
- uses required equipment quantity when resolving offer-level percentage charges;
- rebases resolved percentage totals to `PER_CONTAINER` without changing the total contribution;
- resolves shared FX/percentage charges once at provider level, not once per equipment row;
- excludes only providers with unresolved FX or percentage semantics while allowing other complete providers to remain rankable;
- preserves apples-to-apples coverage per equipment bucket and shared bucket;
- rejects missing or ambiguous required equipment rather than guessing.

## Validated golden fixture

Golden integration fixture:

`pilots/logistics-quote-comparison/fixtures/synthetic-validated-quote-set-02.json`

It exercises the top-level atomic pipeline end to end with evidenced FX, named-base percentage surcharge, all-in bundle coverage, optional exclusion, route alias provenance and equipment alias normalization in one deterministic quote set.

Expected ranking:

`VAL-B USD 1940 < VAL-A USD 2028`

The golden suite includes a normal end-to-end assertion and an adversarial permutation assertion that reverses both quote order and charge-line order. Ranking, scoped coverage, FX application, percentage resolution and relevant audits must remain invariant under that reordering.

## Schemas and documentation

- quote intake carries charge scope, bundle fields, optional selection, stable `line_id`, percentage rate and named base line IDs;
- comparison context carries explicit direct `fx_rates` with `from`, `to`, positive `rate`, `source_ref` and `as_of_date`;
- `docs/CHARGE-SEMANTICS.md`, `docs/PERCENTAGE-SEMANTICS.md`, `docs/FX-SEMANTICS.md`, and `docs/TEST_MATRIX.md` define the evidence boundaries and deterministic acceptance contracts.

## Verification state

Full source-tree deterministic acceptance is provided by `.github/workflows/p2p-opportunity-lab-focused.yml` using Python stdlib `unittest` only; it does not install pytest or another external test runner.

The committed regression inventory is now **88 tests**, including two top-level validated golden tests. Exact accepted branch SHA, current-main merge ref, focused workflow run ID and Shield run ID are maintained in PR #180 and Issue #181 after each final mutation so this file does not create a self-referential SHA-update loop.

A branch mutation does not inherit prior PASS automatically. Fresh focused CI plus P2P Shield are required for the new exact head.

## Current checkpoint

`VALIDATE — OUTREACH_AUTHORIZED + FX_NORMALIZATION_READY + ATOMIC_VALIDATION_PIPELINE_READY + PERCENTAGE_SURCHARGE_READY + GUARDED_CHARGE_SEMANTICS_READY + MULTI_EQUIPMENT_FCL_PIPELINE_READY + FULL_DOMAIN_CI_READY + VALIDATED_GOLDEN_FIXTURE_READY + ORDER_INVARIANCE_READY + EXPERIMENT_TRACKER_READY`

The external lane remains blocked only on Reddit delivery capability. Internal validation now has full source-tree CI, a realistic top-level golden fixture, and an adversarial order-invariance contract proving that input ordering does not change the economic decision.

## Next bounded step

1. Deliver only the three already-authorized Reddit research replies when an authenticated write surface exists.
2. Prefer adversarial/realistic fixture hardening over speculative pricing breadth until real quote data justifies a new semantic.
3. On opt-in, run the real concierge test through the top-level validated entrypoint, record corrections/trust objections/repeat use and explicit WTP/payment signals.
4. Feed only observed experiment output into the market gate and re-evaluate `VALIDATE | BUILD | KILL`.
