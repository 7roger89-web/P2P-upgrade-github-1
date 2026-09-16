# Validation test matrix

Current committed regression inventory:

- market gate: 5 tests;
- prospect bridge: 5 tests;
- concierge engine: 20 tests;
- route-alias provenance: 2 tests;
- conditional commercial terms: 3 tests;
- charge semantics guard: 9 tests;
- multi-equipment FCL portfolio semantics: 10 tests;
- percentage surcharge resolver: 5 core tests + 2 optional-percentage delegation tests;
- explicit FX resolver: 6 tests;
- atomic validated pipeline: 2 percentage integration contracts + 2 FX-first integration contracts;
- validated FCL portfolio pipeline: 3 percentage integration contracts + 2 FX-first integration contracts;
- experiment tracker: 5 tests;
- legacy synthetic quote fixture: 1 deterministic core-engine fixture test;
- validated golden quote fixture: 2 top-level tests (end-to-end evidence/ranking + input-order invariance);
- dirty quote adversarial lane: 4 top-level validated-pipeline tests;
- dirty commercial/validity adversarial lane: 4 top-level validated-pipeline tests;
- design-partner shortlist fixture: 4 tests exercising 6 evidence-backed candidates against qualification/stage/score/no-money-signal invariants.

**Exact collected total: 96 tests.**

Coverage regressions prove that a quote cannot win by silently omitting charges; unresolved omissions block ranking, and a missing charge is resolved only by evidenced `INCLUDED` or `NOT_APPLICABLE` status.

Validity regressions prove that expired/not-yet-valid quotes are excluded when an explicit comparison date is supplied; malformed quote dates are excluded and a malformed comparison date fails loudly.

Minimum-charge regressions prove that `rate × quantity` is floored by an evidenced `minimum_amount`, the floor is not applied when usage pricing already exceeds it, and invalid negative minimums are rejected.

Conditional-term regressions prove that unresolved `subject to` / conditional commercial terms block ranking, an evidenced resolution restores rankability, and merely claiming a term is resolved without a resolution source does not.

Comparison-group regressions prove that a first-position outlier cannot become the baseline, ambiguous equal groups require an explicit target, equivalent equipment aliases normalize together, and materially different equipment remains separate.

Route-alias regressions require an explicit alias plus non-empty source evidence before routes may be merged. Applied aliases are exposed through `route_alias_audit`.

Charge-semantics regressions cover scoped charge identity, duplicate blocking, all-in bundle expansion, bundle/component double-count blocking, and explicit optional/add-on selection.

Multi-equipment FCL regressions cover required-equipment completeness, canonical equipment aliases, shared-charge single application, apples-to-apples charge coverage, evidenced coverage resolutions, bundle coverage, conditions, and validity at equipment-offer level.

Percentage-surcharge contracts cover named bases, quantity-adjusted bases, multiple bases, missing-base refusal, percentage-on-percentage refusal, and delegation of unselected/ambiguous optional percentage lines to the downstream optional-service guard.

FX contracts cover direct evidenced conversion, minimum-amount conversion, missing-rate refusal, missing-source refusal, future-rate refusal, and skipping unnecessary FX for an explicitly unselected optional add-on.

Top-level atomic pipeline order is:

`FX -> percentage -> charge semantics -> core comparison`

Top-level FCL portfolio pipeline applies the same order independently to every required equipment offer and shared provider bucket.

## Validated golden fixture

`pilots/logistics-quote-comparison/fixtures/synthetic-validated-quote-set-02.json` is the top-level integration fixture. It exercises the real atomic entrypoint with one scenario containing:

- evidenced `CNY -> USD` conversion;
- `BAF = 5% of FREIGHT` using an explicit named base line;
- an evidenced all-in bundle covering freight + THC;
- an unselected optional insurance add-on that must not contaminate price or required coverage;
- evidence-backed `CNSHA -> SHANGHAI` route aliasing;
- canonical `40HQ -> 40HC` equipment normalization;
- apples-to-apples scoped coverage and final ranking.

Expected deterministic ranking is `VAL-B USD 1940 < VAL-A USD 2028`. The primary golden test asserts FX audit, percentage audit, route-alias audit, optional exclusion, no unresolved coverage gaps and final ranking.

A second adversarial golden test reverses both the quote order and every quote's charge-line order. Ranking, required coverage, FX application and the core evidence resolutions must remain identical. This protects the validated pipeline from accidental first-seen/order-dependent behavior.

## Dirty quote adversarial contracts

`tests/test_dirty_quote_adversarial.py` mutates the validated golden quote set at the top-level entrypoint rather than testing isolated helpers.

The four contracts prove:

- deleting a required `DOC` charge cannot manufacture a false cheapest quote; the incomplete quote is not rankable and the result warns that fewer than two complete comparable quotes remain;
- adding `Sea Freight` beside `Ocean Freight` in the same scope/basis/currency is canonicalized to the same `FREIGHT` identity and blocked as `DUPLICATE_PRICED_CHARGE` before ranking;
- supplying two evidenced direct `CNY -> USD` rates for the same comparison context is treated as `AMBIGUOUS_FX_RATE`; the pipeline does not pick one arbitrarily;
- removing provenance from the freight line used as the named base for BAF prevents percentage resolution and produces `UNRESOLVED_PERCENTAGE_SEMANTICS` rather than pricing from an unproven base.

## Dirty commercial and validity contracts

`tests/test_dirty_commercial_adversarial.py` drives the same top-level validated entrypoint with commercially unsafe quote state.

The four contracts prove:

- a quote whose `valid_to` is before the comparison date is excluded as `EXPIRED` and cannot be ranked as a current offer;
- a malformed validity date such as `30/09/2026` is excluded as `INVALID_VALIDITY_DATE` instead of being guessed or locale-parsed;
- an unresolved `Subject to carrier space and final approval` term makes that quote incomplete and therefore unrankable;
- setting `resolved=true` without a non-empty `resolution_source_ref` does not manufacture a resolution; the term remains unresolved.

These adversarial lanes intentionally reward refusal when evidence is incomplete, contradictory, stale, malformed or conditionally unresolved. A safe `no decision` is preferable to a fabricated winner.

## Focused CI acceptance surface

Workflow: `.github/workflows/p2p-opportunity-lab-focused.yml`.

The workflow intentionally uses only the Python standard library test runner:

`python -m unittest discover -s tests -p 'test_*.py' -v`

No external pytest installation is required. This reduces network/supply-chain drift while preserving the deterministic contract inventory.

Every substantive branch mutation must obtain fresh exact-head focused-CI evidence plus P2P Shield evidence before the new head inherits PASS status. Exact accepted head/run IDs are maintained in PR #180 and Issue #181 rather than committed here, avoiding a self-referential commit loop.

Synthetic, shortlist, and regression fixtures are not market evidence; they protect deterministic behavior before real participant data arrives.