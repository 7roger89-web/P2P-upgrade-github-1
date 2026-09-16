# P2P Opportunity Lab

Experimental market-validation capability for P2P.

The lab answers a narrower question than a normal coding agent: **should we build this at all?** It separates evidence from inference, searches for counterevidence, designs the cheapest falsification test, and prevents desk research from being mislabeled as market validation.

## Decision path

`DISCOVER -> HYPOTHESIS -> CHEAP TEST -> REAL SIGNAL -> KILL | RESEARCH_MORE | VALIDATE | BUILD`

`BUILD` is not deployment authority. It means only that market evidence is sufficient to hand the opportunity to the normal P2P implementation lifecycle, where all existing governance and Owner Gates still apply.

## Current v0 components

- `schemas/evidence-ledger.schema.json` — evidence classification contract.
- `schemas/opportunity-packet.schema.json` — durable market handoff artifact.
- `schemas/quote-intake.schema.json` — anonymized real-quote intake contract with provenance.
- `schemas/experiment-observation.schema.json` — observed validation behavior / WTP ledger contract.
- `src/market_gate.py` — deterministic `KILL | RESEARCH_MORE | VALIDATE | BUILD` evidence gate.
- `src/prospect_bridge.py` — thin adapter for evidence-backed first-customer/design-partner discovery.
- `src/concierge_engine.py` — deterministic quote normalization, pricing, audit trail, and safe comparison boundary.
- `tests/` — anti-confirmation-bias, prospect, concierge, and fixture regressions.
- `docs/P2P-LAW-BINDING.md` — binding to canonical P2P law without duplicating it.
- `docs/CONCIERGE-VALIDATION-PROTOCOL.md` — real-user validation procedure.
- `pilots/logistics-quote-comparison/` — first real market-validation pilot, shortlist, outreach batch, and synthetic quote fixture.
- `PROJECT_STATE.md` — durable checkpoint.

## Comparison safety

The concierge engine does not silently convert currencies or fabricate missing charge semantics. A route/equipment/currency mismatch is excluded from the comparable ranking. Missing provenance, unknown pricing basis, missing amount, or cross-currency line item marks a quote incomplete. If fewer than two complete quotes remain, the engine returns `INSUFFICIENT_COMPLETE_COMPARABLE_QUOTES` instead of inventing a winner.

## Non-goals for v0

No production UI, login, billing, autonomous outreach, paid data providers, agent swarm, production deployment, or generic lead-generation dashboard. Those are deferred until a real pilot proves they are needed.

## Run regression tests

From this directory:

```bash
python -m unittest discover -s tests -v
```
