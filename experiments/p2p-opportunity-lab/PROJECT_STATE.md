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

## Concierge validation engine

Implemented:
- anonymized quote-intake contract with provenance;
- comparison-context schema covering quantities, explicit target, coverage resolutions and evidence-backed location aliases;
- deterministic quote normalization and audit trail;
- route/equipment/currency comparability checks;
- no silent FX conversion;
- unknown/uncertain pricing basis blocks ranking;
- charge-coverage parity so a quote cannot win by silently omitting charges;
- evidenced `INCLUDED` / `NOT_APPLICABLE` resolution for coverage gaps;
- validity-window guard using explicit `as_of_date`;
- minimum-charge support: `max(rate × quantity, minimum_amount)` with raw calculation, floor application and provenance preserved;
- conditional-commercial-term guard: unresolved `subject to` / exclusion / confirmation terms make a quote incomplete and non-rankable; resolution requires independent source evidence;
- comparison-group selection no longer trusts the first input quote as the baseline: eligible quotes are grouped by normalized route + equipment + currency and the unique largest group is selected automatically;
- equal multi-quote groups are treated as ambiguous and produce no ranking until an explicit `comparison_target` is supplied;
- conservative equipment aliases normalize equivalent forms such as `40HQ` / `40HC` while keeping materially different types such as `40GP` separate;
- route/location aliases such as `CNSHA -> SHANGHAI` are accepted only when an explicit alias mapping carries a non-empty source reference; applied aliases are preserved in `route_alias_audit`.

Verification at this slice:
- prior base concierge engine suite: 15/15 PASS before the group-selection slice;
- new group-selection/equipment-alias probes: 5/5 PASS;
- route-alias provenance probes: 4/4 PASS;
- conditional commercial terms: 3/3 PASS from the prior slice;
- current committed regression inventory: 20 concierge-engine tests + 2 route-alias tests;
- representative synthetic fixture remains the deterministic acceptance fixture (`SYN-B USD 2010 < SYN-A USD 2060`; CNY excluded without FX);
- experiment tracker: 5/5 PASS;
- experiment states remain distinct: `CONTACTED`, `SUBMITTED`, `REPEAT_REQUEST`, `WTP_SIGNAL`, `PAID`.

## Current checkpoint

`VALIDATE — OUTREACH_AUTHORIZED + CONCIERGE_ENGINE_READY + EXPERIMENT_TRACKER_READY + CHARGE_COVERAGE_GUARD_READY + VALIDITY_GUARD_READY + MINIMUM_CHARGE_READY + CONDITIONAL_TERMS_READY + UNBIASED_GROUP_SELECTION_READY + ROUTE_ALIAS_PROVENANCE_READY`

The external lane is blocked only on Reddit delivery capability. The internal lane continues independently and is ready to reject stale, incomplete, conditionally priced, or comparison-incompatible quote groups rather than manufacturing a false cheapest option.

## Next bounded step

1. Deliver only the three already-authorized Reddit research replies when an authenticated write surface exists.
2. Continue validation-only hardening only where representative quote semantics justify it; next useful candidates are tiered/percentage pricing and LCL/air chargeable-weight semantics. Do not drift into product UI/login/billing/deployment.
3. On opt-in, run the real concierge test and record corrections, trust objections, repeat use and explicit WTP/payment signals.
4. Feed only observed experiment output into the market gate and re-evaluate `VALIDATE | BUILD | KILL`.
