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
- No automatic spending, outreach, production deployment, secrets, or infrastructure changes.

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
- Six primary candidates are preserved in `pilots/logistics-quote-comparison/design-partner-shortlist.json` with direct public evidence, weighted qualification dimensions, source-grounded draft openers, and `send_authorized=false`.
- Competitor/peer records such as QuoteFast are explicitly excluded from the primary customer shortlist.
- The shortlist does not alter the market-gate result: prospect discovery remains validation input, not proof of payment/WTP.

## Current checkpoint

`VALIDATE — DESIGN_PARTNER_SHORTLIST_READY`

The first-customer capability has now produced a bounded, evidence-backed design-partner shortlist. The project still lacks observed behavior from the concierge experiment and observed payment/WTP evidence, so `BUILD` remains prohibited.

## Next bounded step

External contact is now the blocking boundary. Under the current project law it requires Owner authorization. Once authorized, contact only a small initial batch of the strongest public-signal candidates, ask for one real quote/rate-card set, execute the existing concierge test, and record observed submission, repeat-use, accuracy objections, and payment/WTP signals. Do not broaden into generic lead generation and do not build the product before the market gate changes on real evidence.
