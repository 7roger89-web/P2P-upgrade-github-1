# PROJECT STATE — P2P Opportunity Lab

TASK_ID: P2P_MARKET_VALIDATION_PILOT_01
STATUS: EXPERIMENTAL
CANONICAL_CAPABILITY: NO
PROMOTION: UNPROMOTED

## Goal

Prove or falsify that P2P can turn a rough opportunity into an evidence-grounded market decision before full implementation.

## First pilot

Logistics quote-comparison: normalize and compare inconsistent freight quotations/rate sheets without requiring suppliers to adopt a new input format.

## Guardrails

- BUILDABLE != VIABLE.
- GOAL PASS != MARKET PASS.
- Desk research alone cannot produce BUILD.
- Owner preference is not evidence.
- Contradicting evidence must be preserved, not averaged away.
- BUILD requires an observed real-world experiment plus an observed payment or willingness-to-pay signal.
- Public prospect discovery is not payment/WTP evidence by itself.
- External outreach is bounded by explicit Owner authorization and community rules.
- No private contact enrichment, automatic spending, production deployment, secrets, or infrastructure changes.

## Verified progress

- Core market gate implemented.
- Evidence ledger schema implemented.
- Opportunity Packet schema implemented.
- Anti-confirmation-bias market-gate regression suite: 5/5 PASS in isolated local execution.
- First desk-evidence Opportunity Packet completed for logistics quote comparison.
- Deterministic gate result for the pilot packet: `VALIDATE`.
- Existing competitors are explicit counterevidence; the broad feature idea is not treated as unique.
- No observed payment/WTP signal exists yet, therefore `BUILD` is prohibited by the current gate.
- Reviewed `Kappaemme-git/codex-first-customer-finder-skill` as an upstream candidate and pinned commit `943c455bdfc40da46265b01b3c1f41e4bb386f27`.
- Integration mode: `REUSE_WITH_THIN_ADAPTER`; no fork and no unpinned `@latest` install.
- Prospect bridge regression suite: 5/5 PASS in isolated local execution.
- Prospect bridge forbids private/sensitive enrichment, requires a public source and direct signal, keeps outreach `DRAFT_ONLY`, and never upgrades pain into payment/WTP.
- Public design-partner research completed for the first pilot.
- Six primary candidates are preserved in `pilots/logistics-quote-comparison/design-partner-shortlist.json` with direct public evidence, weighted qualification dimensions, source-grounded draft openers, and no money-signal promotion.
- Competitor/peer records such as QuoteFast are explicitly excluded from the primary customer shortlist.
- Shortlist fixture verification: 6/6 candidates match expected score/stage and no-money-signal invariants.
- Owner authorized external contact for exactly the first three candidates on 2026-09-16 at 09:27 +07:00.
- Authorized batch is durable at `pilots/logistics-quote-comparison/outreach-batch-01.json`.
- Outreach wording was adapted to r/freightforwarding's No Promoting culture: research-first, public, low-volume, opt-in before any data exchange, and no request to post files publicly.
- A reply watch is active for the three source threads every 6 hours and notifies only on a new direct reply or clear opt-in; an unsent outreach comment cannot produce a reply.
- Real quote intake contract added at `schemas/quote-intake.schema.json`; intake requires anonymization confirmation and per-field/charge provenance.
- Concierge validation observation contract added at `schemas/experiment-observation.schema.json`.
- Deterministic quote normalization/comparison engine added at `src/concierge_engine.py`.
- Engine refuses silent FX conversion, excludes route/equipment/currency mismatches from ranking, preserves source references, and refuses to rank incomplete/uncertain quotes as a fake winner.
- Charge-coverage parity guard added: a quote cannot win by omitting a charge code that appears in another otherwise-comparable quote.
- Coverage gaps block ranking until resolved as `INCLUDED` or `NOT_APPLICABLE` with a non-empty source reference.
- Comparison output now exposes required charge codes, a per-quote coverage matrix, unresolved omissions, and evidenced resolutions.
- Concierge engine regression suite: 8/8 PASS in isolated local execution.
- Representative synthetic quote fixture remains deterministic: Carrier B = USD 2010, Carrier A = USD 2060, CNY quote excluded without FX; Carrier A now explicitly records PSS as included so the comparison does not rely on silent omission.
- Synthetic fixture behavior re-run locally together with concierge tests: 9/9 PASS.
- Observed experiment tracker added at `src/experiment_tracker.py`.
- Tracker regression suite: 5/5 PASS; contact/praise/repeat-use cannot create money evidence, `WTP_SIGNAL` requires an explicit amount, and failure is not declared until the configured contact target is actually reached.
- Validation procedure is durable at `docs/CONCIERGE-VALIDATION-PROTOCOL.md`.
- Parallel internal/external development boundaries are durable at `docs/DEVELOPMENT_LANES.md`.
- Live pilot status is durable at `pilots/logistics-quote-comparison/VALIDATION_STATUS.md`.

## Current checkpoint

`VALIDATE — OUTREACH_AUTHORIZED + CONCIERGE_ENGINE_READY + EXPERIMENT_TRACKER_READY + CHARGE_COVERAGE_GUARD_READY`

The first three design-partner contacts remain authorized. No message has been sent yet because the current ChatGPT tool surface has no authenticated Reddit write/post action: web access is read-only and plugin discovery found no Reddit messaging/posting connector.

This delivery limitation does not reopen the Owner Gate and does not stop internal validation development. Authorization is already recorded. Once an authenticated Reddit write surface is available, send only the three preserved public replies in `outreach-batch-01.json`; the reply watch then surfaces direct responses/opt-ins without requiring the Owner to manually poll Reddit.

The internal validation lane is ready to accept an opted-in participant's anonymized real quote set, normalize charges with provenance, compare only charge-complete/evidenced quote sets, compute comparable totals only when the comparison basis is valid, surface uncertainty rather than hiding it, and record observed experiment behavior separately from payment/WTP evidence.

## Next bounded step

1. Deliver the three authorized public research replies through an authenticated Reddit account when a write surface is available.
2. Continue validation-only hardening around real-world quote semantics, especially validity windows, exclusions, minimum charges, and ambiguous pricing bases; do not build product UI/login/billing/deployment.
3. On any opt-in, request anonymized quote/ratecard data through a mutually agreed safe channel, run the concierge engine, return an auditable comparison, and record corrections, trust objections, repeat-use, and explicit payment/WTP signals.
4. Feed only observed tracker output into the market gate and re-evaluate `VALIDATE | BUILD | KILL`; do not broaden into generic lead generation and do not build the product before the market gate changes on real evidence.
