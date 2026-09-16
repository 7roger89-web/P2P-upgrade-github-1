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

## Current checkpoint

`VALIDATE` — evidence supports a cheap real-world experiment, not product implementation.

The new first-customer capability may be used to identify evidence-backed design
partners for that experiment, but prospect discovery alone cannot change the
market-gate decision.

## Next bounded step

Use the pinned first-customer-finder workflow plus the local prospect bridge to
produce a small evidence-backed shortlist of candidate design partners for the
logistics quote-comparison concierge test. External contact remains an Owner
Gate. Until real target-user behavior and money/WTP evidence are observed, do
not build the product.
