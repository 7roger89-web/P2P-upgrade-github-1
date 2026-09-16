# PROJECT STATE — P2P Opportunity Lab

TASK_ID: P2P_MARKET_VALIDATION_PILOT_01
STATUS: EXPERIMENTAL
CANONICAL_CAPABILITY: NO
PROMOTION: UNPROMOTED
MARKET_GATE: VALIDATE

## Goal

Prove or falsify that P2P can turn a rough opportunity into an evidence-grounded market decision before full product implementation.

## First pilot

Logistics quote comparison: normalize and compare inconsistent freight quotations/rate sheets without requiring suppliers to adopt a new input format.

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

## Market-validation capability

- Evidence ledger and Opportunity Packet contracts implemented.
- Deterministic market gate implemented; anti-confirmation-bias suite 5/5 PASS.
- First logistics desk-evidence packet resolves to `VALIDATE`; competitors are explicit counterevidence and the broad feature is not treated as unique.
- `Kappaemme-git/codex-first-customer-finder-skill` reviewed at pinned commit `943c455bdfc40da46265b01b3c1f41e4bb386f27` and integrated as `REUSE_WITH_THIN_ADAPTER`.
- Prospect bridge 5/5 PASS; public direct evidence required, sensitive/private enrichment forbidden, outreach remains draft-only, and prospect pain cannot become money evidence.
- Six evidence-backed design-partner candidates preserved; competitor/peer records are excluded from the customer shortlist.

## External validation lane

Owner authorized contact for exactly the first three shortlisted prospects on 2026-09-16 09:27 +07:00.

Durable batch: `pilots/logistics-quote-comparison/outreach-batch-01.json`.

Current delivery state:
- `sent_count=0`
- `reply_count=0`
- `opt_in_count=0`
- `READY_BUT_NOT_SENT`
- blocker: current ChatGPT surface has no authenticated Reddit write/post action.

A six-hour reply watch is active, but an unsent outreach comment cannot receive a direct reply. Authorization does not need to be requested again when a valid Reddit write surface appears.

## Atomic quote validation pipeline

Raw real-world quote comparison entrypoint:

`src.validation_pipeline.compare_quotes_validated`

Pipeline order:

1. evidenced percentage-surcharge resolution;
2. scoped/bundle/duplicate/optional charge semantics via `src.charge_semantics.compare_quotes_guarded`;
3. deterministic core comparison.

Implemented atomic protections include:
- route/equipment/currency grouping with no first-input baseline bias;
- no silent FX conversion;
- charge-coverage parity;
- validity window using explicit `as_of_date`;
- minimum charge floors;
- unresolved conditional-term blocking;
- conservative equipment aliases;
- evidence-backed route aliases;
- scoped charges (`ORIGIN | MAIN | DESTINATION | OTHER | UNSPECIFIED`);
- duplicate priced-charge blocking;
- evidenced all-in bundle expansion and bundle/component double-count blocking;
- explicit optional/add-on selection;
- named-base percentage surcharges using `line_id`, `percentage_rate`, `percentage_of_line_ids`, and source provenance.

Percentage rules are never guessed. Missing/invalid base references, self-reference, percentage-on-percentage, cross-currency bases without an explicit FX layer, or a manually supplied fixed amount conflicting with percentage pricing block resolution before ranking.

## Multi-equipment FCL validation

Base portfolio engine:

`src.portfolio_semantics.compare_fcl_portfolios`

Raw percentage-aware portfolio entrypoint:

`src.portfolio_validation_pipeline.compare_fcl_portfolios_validated`

Implemented:
- one RFQ may require multiple equipment types and quantities;
- equivalent equipment aliases combine quantities, e.g. `40HQ -> 40HC`;
- each provider must cover every required equipment type exactly once;
- apples-to-apples coverage is checked per equipment bucket and shared bucket;
- shared `PER_SHIPMENT | PER_BL` charges are priced once per provider;
- equipment-level pricing remains conservative and quantity-aware;
- percentage surcharges on an equipment offer are resolved against that equipment's required quantity, then rebased to a `PER_CONTAINER` amount that reconstructs the same total in the existing portfolio engine;
- provider-level shared percentage surcharges are resolved once and are not multiplied by equipment rows;
- unresolved percentage semantics exclude that provider while other complete providers may remain rankable.

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
- percentage resolver: 5/5 PASS in isolated deterministic harness;
- original FCL portfolio focused slice: 5/5 PASS;
- experiment tracker: 5/5 PASS.

Committed acceptance inventory now also includes expanded portfolio semantics, atomic validation-pipeline integration tests, and percentage-aware FCL portfolio integration tests. Those newer committed contracts are not falsely promoted to full source-tree PASS without an actual runner executing them. GitHub Shield remains a separate exact-head acceptance surface.

## Current checkpoint

`VALIDATE — OUTREACH_AUTHORIZED + ATOMIC_VALIDATION_PIPELINE_READY + GUARDED_CHARGE_SEMANTICS_READY + PERCENTAGE_SURCHARGE_READY + OPTIONAL_ADDON_GUARD_READY + MULTI_EQUIPMENT_FCL_PIPELINE_READY + EXPERIMENT_TRACKER_READY`

The external lane is blocked only on Reddit delivery capability. The internal lane can reject or explicitly normalize many common false-comparison traps without manufacturing a cheapest option.

## Next bounded step

1. Deliver only the three already-authorized Reddit research replies when an authenticated write surface exists.
2. Add explicit FX resolution with provenance/date before percentage semantics so mixed-currency quote lines can be compared without silent conversion.
3. On opt-in, run the real concierge test through the top-level validated entrypoint, record corrections/trust objections/repeat use and explicit WTP/payment signals.
4. Feed only observed experiment output into the market gate and re-evaluate `VALIDATE | BUILD | KILL`.
