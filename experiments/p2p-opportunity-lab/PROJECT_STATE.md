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
- blocker: the current ChatGPT surface has no authenticated Reddit write/post action.

The outreach copy is research-first, public, low-volume, no sales pitch, no private enrichment, and requires opt-in before data exchange. A six-hour reply watch is active, but an unsent outreach comment cannot receive a direct reply.

## Concierge validation engine

Implemented:

- anonymized quote-intake contract with provenance;
- deterministic quote normalization and audit trail;
- route/equipment/currency comparability checks;
- no silent FX conversion;
- unknown/uncertain pricing basis blocks ranking;
- charge-coverage parity: a quote cannot win by silently omitting a charge present in another otherwise-comparable quote;
- coverage gaps require evidenced `INCLUDED` or `NOT_APPLICABLE` resolution;
- validity-window guard using explicit `as_of_date`; expired/not-yet-valid quotes are excluded and malformed dates cannot silently rank;
- minimum-charge support: contribution is `max(rate × quantity, minimum_amount)` with raw calculation, floor application, and source reference preserved in audit output;
- negative minimums and `INCLUDED + minimum_amount` contradictions are rejected.

Verification at this slice:

- concierge engine: 15/15 PASS in exact local regression;
- representative synthetic fixture: PASS (`SYN-B USD 2010 < SYN-A USD 2060`; CNY quote excluded without FX);
- experiment tracker: 5/5 PASS;
- experiment stages remain distinct: `CONTACTED`, `SUBMITTED`, `REPEAT_REQUEST`, `WTP_SIGNAL`, `PAID`.

## Current checkpoint

`VALIDATE — OUTREACH_AUTHORIZED + CONCIERGE_ENGINE_READY + EXPERIMENT_TRACKER_READY + CHARGE_COVERAGE_GUARD_READY + VALIDITY_GUARD_READY + MINIMUM_CHARGE_READY`

The external lane is blocked only on Reddit delivery capability. The internal lane continues independently and is ready to accept anonymized opted-in quote sets.

## Next bounded step

1. Deliver only the three already-authorized Reddit research replies when an authenticated write surface exists.
2. Continue validation-only hardening for real quote semantics: conditional/subject-to exclusions and ambiguous pricing bases. Do not build product UI/login/billing/deployment.
3. On opt-in, run the real concierge test and record corrections, trust objections, repeat use and explicit WTP/payment signals.
4. Feed only observed experiment output into the market gate and re-evaluate `VALIDATE | BUILD | KILL`.
