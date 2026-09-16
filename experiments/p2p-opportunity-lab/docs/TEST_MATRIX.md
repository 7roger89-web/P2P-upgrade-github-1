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
- synthetic quote fixture: 1 deterministic fixture test;
- design-partner shortlist fixture: 6 candidates re-qualified against expected stage/score/no-money-signal invariants.

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

Top-level atomic pipeline order is now:

`FX -> percentage -> charge semantics -> core comparison`

A missing FX rate must block before percentage resolution or ranking. A bad percentage reference must block before charge semantics or ranking.

Top-level FCL portfolio pipeline applies the same order independently to every required equipment offer and shared provider bucket. Equipment-level percentage totals are quantity-aware and rebased to `PER_CONTAINER`; provider-level shared percentage/FX adjustments are applied once.

Verified focused harness evidence currently preserved:

- charge semantics guard: **9/9 PASS** using repo-style `src.*` imports;
- percentage surcharge core resolver: **5/5 PASS** in its isolated deterministic harness;
- original multi-equipment FCL focused slice: **5/5 PASS**;
- group-selection/equipment probes: **5/5 PASS**;
- route-alias helper probes: **4/4 PASS**;
- conditional-term probes: **3/3 PASS**.

The new FX tests, optional-percentage delegation tests, atomic pipeline integration tests, expanded portfolio inventory, and percentage/FX-aware portfolio pipeline tests are committed acceptance contracts but have not been promoted to full source-tree PASS in this tool session. GitHub Shield is a separate exact-head acceptance surface and does not substitute for domain regression execution.

The representative synthetic quote fixture remains the deterministic acceptance case. Synthetic, shortlist, and regression fixtures are not market evidence; they protect deterministic behavior before real participant data arrives.
