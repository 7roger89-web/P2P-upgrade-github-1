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

Authorization does not need to be requested again when a valid Reddit write surface appears.

## Atomic quote validation pipeline

Real-world atomic comparison entrypoint:

`src.validation_pipeline.compare_quotes_validated`

Pipeline order:

`explicit FX -> named-base percentage -> charge semantics -> deterministic core comparison`

Implemented protections include evidenced direct FX, percentage-base provenance, scoped charge identity, duplicate blocking, bundle/double-count guards, explicit optional selection, coverage parity, quote validity, minimum charges, conditional commercial terms, equipment aliases and evidence-backed route aliases.

## Multi-equipment FCL validation pipeline

Real-world provider-portfolio entrypoint:

`src.portfolio_validation_pipeline.compare_fcl_portfolios_validated`

The validated portfolio pipeline resolves FX/percentage semantics per required equipment/shared bucket, preserves apples-to-apples coverage, applies shared charges once and refuses missing or ambiguous required equipment.

## Validated golden fixture

`pilots/logistics-quote-comparison/fixtures/synthetic-validated-quote-set-02.json`

Expected ranking:

`VAL-B USD 1940 < VAL-A USD 2028`

The golden suite verifies full top-level composition plus quote/charge-order invariance.

## Adversarial refusal lanes

Dirty quote contracts prove refusal for missing required coverage, alias-equivalent duplicate freight, contradictory direct FX evidence and missing provenance on a percentage base.

Dirty commercial/validity contracts prove expired and malformed-dated quotes are excluded, unresolved `subject to` terms remain incomplete, and `resolved=true` without resolution evidence does not manufacture certainty.

## Identity integrity

Fresh review found a real identity gap: quote IDs were required but not unique, while downstream coverage resolution and grouping use `quote_id` as identity.

The gap is now closed in both layers:
- `src.concierge_engine.compare_quotes` rejects duplicate non-empty `quote_id` values before normalization/grouping;
- `src.validation_pipeline.compare_quotes_validated` rejects the same ambiguity before FX/percentage resolution.

Duplicate quote identity now fails loudly instead of allowing separate quotations to share audit, coverage or ranking identity. Duplicate non-empty charge `line_id` was already guarded by percentage semantics, so no redundant parallel line-ID mechanism was added.

## Schemas and documentation

- quote intake carries charge scope, bundle fields, optional selection, stable `line_id`, percentage rate and named base line IDs;
- comparison context carries explicit direct `fx_rates` with `from`, `to`, positive `rate`, `source_ref` and `as_of_date`;
- `docs/CHARGE-SEMANTICS.md`, `docs/PERCENTAGE-SEMANTICS.md`, `docs/FX-SEMANTICS.md`, and `docs/TEST_MATRIX.md` define evidence boundaries and deterministic acceptance contracts.

## Verification state

Full source-tree deterministic acceptance is provided by `.github/workflows/p2p-opportunity-lab-focused.yml` using Python stdlib `unittest` only.

The committed regression inventory is now **98 tests**: two validated golden tests, four dirty-quote tests, four dirty commercial/validity tests, two quote-identity integrity tests, plus the earlier deterministic contracts.

Exact accepted branch SHA, current-main merge ref, focused workflow run ID and Shield run ID are maintained in PR #180 and Issue #181 after each final mutation. A branch mutation never inherits prior PASS automatically.

## Current checkpoint

`VALIDATE — OUTREACH_AUTHORIZED + FX_NORMALIZATION_READY + ATOMIC_VALIDATION_PIPELINE_READY + PERCENTAGE_SURCHARGE_READY + GUARDED_CHARGE_SEMANTICS_READY + MULTI_EQUIPMENT_FCL_PIPELINE_READY + FULL_DOMAIN_CI_READY + VALIDATED_GOLDEN_FIXTURE_READY + ORDER_INVARIANCE_READY + DIRTY_QUOTE_ADVERSARIAL_READY + DIRTY_COMMERCIAL_VALIDITY_READY + IDENTITY_INTEGRITY_READY + EXPERIMENT_TRACKER_READY`

The external lane remains blocked only on Reddit delivery capability. Internal deterministic hardening is now sufficiently broad for the pilot: full source-tree CI, golden integration, order invariance, dirty-data refusal, commercial/validity refusal and unique quote identity are all covered.

## Next bounded step

1. Deliver only the three already-authorized Reddit research replies when an authenticated write surface exists.
2. Stop speculative deterministic expansion unless real participant/quote data reveals a concrete missing semantic. Do not add pricing breadth merely to grow the suite.
3. On opt-in, run real concierge comparisons through the top-level validated entrypoint and record corrections, trust objections, repeat use and explicit WTP/payment signals.
4. Feed only observed experiment output into the market gate and re-evaluate `VALIDATE | BUILD | KILL`.