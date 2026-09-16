# P2P Opportunity Lab

Experimental market-validation capability for P2P.

The lab answers a narrower question than a normal coding agent: **should we build this at all?** It separates evidence from inference, searches for counterevidence, designs the cheapest falsification test, and prevents desk research from being mislabeled as market validation.

## Decision path

`DISCOVER -> HYPOTHESIS -> CHEAP TEST -> REAL SIGNAL -> KILL | RESEARCH_MORE | VALIDATE | BUILD`

`BUILD` is not deployment authority. It means only that market evidence is sufficient to hand the opportunity to the normal P2P implementation lifecycle, where all existing governance and Owner Gates still apply.

## Initial files

- `schemas/evidence-ledger.schema.json` — evidence classification contract.
- `schemas/opportunity-packet.schema.json` — durable handoff artifact.
- `src/market_gate.py` — deterministic evidence gate.
- `tests/test_market_gate.py` — anti-confirmation-bias regression cases.
- `docs/P2P-LAW-BINDING.md` — binding to canonical P2P law without duplicating it.
- `PROJECT_STATE.md` — durable pilot checkpoint.

## Non-goals for v0

No UI, database, autonomous outreach, paid data providers, agent swarm, production deployment, or generic scoring dashboard. Those are deferred until a real pilot proves they are needed.

## Run regression tests

```bash
python -m unittest discover -s tests -v
```
