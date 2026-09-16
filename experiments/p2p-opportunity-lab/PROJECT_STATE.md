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

## Current checkpoint

`VALIDATE — OUTREACH_BATCH_01_AUTHORIZED_READY`

The first three design-partner contacts are authorized. No message has been sent yet because the current ChatGPT tool surface has no authenticated Reddit write/post action: web access is read-only and plugin discovery found no Reddit messaging/posting connector.

This delivery limitation does not reopen the Owner Gate; authorization is already recorded. Once an authenticated Reddit write surface is available, send only the three preserved public replies in `outreach-batch-01.json`, then record observed replies and opt-ins. Do not expand the batch without a new authorization.

## Next bounded step

Deliver the three authorized public research replies through an authenticated Reddit account. On any opt-in, request anonymized quote/ratecard data through a mutually agreed safe channel, execute the existing concierge test, and record observed submission, repeat-use, accuracy objections, and payment/WTP signals. Do not broaden into generic lead generation and do not build the product before the market gate changes on real evidence.
