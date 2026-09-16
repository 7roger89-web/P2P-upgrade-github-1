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
- route/location aliases such as `CNSHA -> SHANGHAI` are accepted only when an explicit alias mapping carries a non-empty source reference; applied aliases are preserved in `route_alias_audit`;
- `src.charge_semantics.compare_quotes_guarded` is now the required real-validation entrypoint before the core comparison engine;
- scoped charge coverage distinguishes `ORIGIN`, `MAIN`, `DESTINATION`, `OTHER`, and `UNSPECIFIED` instead of conflating identical charge labels across commercial stages;
- exact duplicate priced charge signatures are blocked before ranking;
- evidenced all-in/bundled charges may expand into zero-contribution included coverage rows while one primary component carries the bundle price;
- priced standalone components that overlap the same priced bundle are blocked as a double-count risk;
- quote-intake schema now carries `scope`, `bundle_includes`, and `bundle_primary_code` explicitly.

## Multi-equipment FCL validation

Implemented:
- `src.portfolio_semantics.compare_fcl_portfolios` for one RFQ requiring multiple container equipment types;
- requirements canonicalize aliases such as `40HQ -> 40HC` and combine quantities;
- provider quote sets must cover every required equipment type exactly once; missing or ambiguous equipment offers are excluded rather than guessed;
- equipment-level offers are deliberately restricted to `PER_CONTAINER` / `INCLUDED` in this pilot slice;
- `PER_SHIPMENT` / `PER_BL` charges live at provider shared-charge level and are priced once, preventing accidental multiplication across equipment rows;
- portfolio total is the sum of complete required equipment offers plus complete shared charges in one currency/route;
- incomplete provider portfolios are excluded from ranking.

Verification at this slice:
- prior base concierge engine suite: 15/15 PASS before the group-selection slice;
- group-selection/equipment-alias probes: 5/5 PASS;
- route-alias provenance probes: 4/4 PASS;
- conditional commercial terms: 3/3 PASS from the prior slice;
- charge semantics isolated harness: 6/6 PASS using repo-style `src.*` imports;
- multi-equipment FCL portfolio focused harness: 5/5 PASS;
- current committed inventory includes 20 concierge-engine tests, 2 route-alias tests, 6 charge-semantics tests and 5 portfolio-semantics tests;
- representative synthetic fixture remains the deterministic acceptance fixture (`SYN-B USD 2010 < SYN-A USD 2060`; CNY excluded without FX);
- experiment tracker: 5/5 PASS;
- experiment states remain distinct: `CONTACTED`, `SUBMITTED`, `REPEAT_REQUEST`, `WTP_SIGNAL`, `PAID`.

Focused harnesses prove only their stated slices. They do not claim that the entire repository regression inventory was rerun together on one local source-tree runner. GitHub Shield is verified separately on exact heads.

## Current checkpoint

`VALIDATE — OUTREACH_AUTHORIZED + GUARDED_CHARGE_SEMANTICS_READY + MULTI_EQUIPMENT_FCL_READY + EXPERIMENT_TRACKER_READY`

The external lane is blocked only on Reddit delivery capability. The internal lane can now reject stale, incomplete, conditionally priced, duplicate, double-counted, scope-confused, comparison-incompatible, and incomplete multi-equipment provider quote sets rather than manufacturing a false cheapest option.

## Next bounded step

1. Deliver only the three already-authorized Reddit research replies when an authenticated write surface exists.
2. Continue validation-only hardening only where representative FCL quote semantics justify it. The next useful candidates are explicit provider-level surcharges expressed as percentages/tier rules and evidence-safe handling of optional/add-on services; do not drift into product UI/login/billing/deployment.
3. On opt-in, run the real concierge test through guarded semantics, record corrections/trust objections/repeat use and explicit WTP/payment signals.
4. Feed only observed experiment output into the market gate and re-evaluate `VALIDATE | BUILD | KILL`.
