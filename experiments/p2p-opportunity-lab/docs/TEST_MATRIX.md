# Validation test matrix

Current committed regression inventory:

- market gate: 5 tests;
- prospect bridge: 5 tests;
- concierge engine: 20 tests;
- route-alias provenance: 2 tests;
- conditional commercial terms: 3 tests;
- charge semantics guard: 9 tests;
- multi-equipment FCL portfolio semantics: 10 tests;
- percentage surcharge resolver: 5 tests;
- atomic validated pipeline: 2 integration-contract tests;
- percentage-aware FCL portfolio pipeline: 3 integration-contract tests;
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

Percentage-surcharge regressions cover:

- percentage of one named freight line;
- quantity-adjusted named bases;
- multiple named bases;
- missing named base refusal;
- percentage-on-percentage refusal.

Atomic validation-pipeline contracts require percentage resolution to occur before the scoped/bundle/duplicate/optional charge guard. A bad percentage reference must block ranking as `UNRESOLVED_PERCENTAGE_SEMANTICS`.

Percentage-aware FCL portfolio contracts require:

- equipment-level percentage surcharges to use the required equipment quantity and preserve the same resolved total after rebasing to `PER_CONTAINER`;
- shared percentage surcharges to be priced once at provider level rather than once per equipment row;
- a provider with an unresolved named percentage base to be excluded while other complete providers may remain rankable.

Verified focused harness evidence currently preserved:

- charge semantics guard: **9/9 PASS** using repo-style `src.*` imports;
- percentage surcharge resolver: **5/5 PASS** in its isolated deterministic harness;
- original multi-equipment FCL focused slice: **5/5 PASS**;
- group-selection/equipment probes: **5/5 PASS**;
- route-alias helper probes: **4/4 PASS**;
- conditional-term probes: **3/3 PASS**.

The newer atomic pipeline tests, expanded portfolio regression inventory, and percentage-aware portfolio pipeline tests are committed acceptance contracts but have not been claimed as full source-tree PASS in this tool session. GitHub Shield is a separate exact-head acceptance surface and does not substitute for domain regression execution.

The representative synthetic quote fixture remains the deterministic acceptance case. Synthetic, shortlist, and regression fixtures are not market evidence; they protect deterministic behavior before real participant data arrives.
