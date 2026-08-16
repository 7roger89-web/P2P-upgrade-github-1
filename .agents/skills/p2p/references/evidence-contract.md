# P2P evidence contract

## Evidence precedence

1. Current official primary source for the exact product, surface, plan, region, client, and
   version.
2. Reproducible benchmark or issue with the same setup and a preserved fixture.
3. Several genuinely independent observations, used only to monitor or warn.
4. Community post, model report, legacy table, or rumor, kept as a hypothesis only.

Multiple AI research reports that cite the same page are one evidence path, not multiple votes.
Never average exact prices. Never combine benchmark scores unless model version, harness,
settings, date, and data are comparable.

## FACT_LEDGER fields

Every volatile claim needs: claim ID, kind, statement/value, exact scope, source URL/type,
evidence level, checked date, expiry date, route action, runtime eligibility, provenance note,
risk tier, affected components, and a repeatable verification method.
Derive lifecycle as `current`, `expiring`, or `stale`; do not type it by hand.

`block` requires exact official evidence level A. Reproducible evidence may warn or prefer.
Community and legacy evidence may monitor or remain ignored, but cannot silently control routing.

Distinguish `CONFIRMED_ACTIVE`, `NOT_RECHECKED`, `NO_EVIDENCE_OF_FIX`, `DISPUTED`, and
`RETIRED`. “No update found” never proves a problem remains active.

## Synchronization

Edit `governance/fact-ledger.json`, run `prepare-live` to validate it and hash the deterministic
Live Specs candidate, then create a `promote_live_specs` request bound to both the ledger and
technical-preview SHA-256. Only after the user's decision may `build-live` generate
`governance/live-specs.json`. Rebuild the protected-runtime lock and run drift. Runtime files
refer to the generated artifact instead of copying model IDs, limits, prices, or bug rules. A
later ledger, preview, approval, or generated-target change invalidates the chain.

For important changes, search for deltas without showing the previous conclusion first, verify old
issues in a second pass, and run an adversarial pass that tries to disprove the riskiest claims.
