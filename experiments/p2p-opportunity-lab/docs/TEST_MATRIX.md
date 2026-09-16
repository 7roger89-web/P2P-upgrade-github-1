# Validation test matrix

Current isolated regression groups:

- market gate: 5 tests;
- prospect bridge: 5 tests;
- concierge engine: 20 tests;
- route-alias provenance: 2 committed tests;
- conditional commercial terms: 3 tests;
- experiment tracker: 5 tests;
- synthetic quote fixture: 1 deterministic fixture test;
- design-partner shortlist fixture: 6 candidates re-qualified against expected stage/score/no-money-signal invariants.

Coverage regressions prove that a quote cannot win by silently omitting charges; unresolved omissions block ranking, and a missing charge is resolved only by evidenced `INCLUDED` or `NOT_APPLICABLE` status.

Validity regressions prove that expired/not-yet-valid quotes are excluded when an explicit comparison date is supplied; malformed quote dates are excluded and a malformed comparison date fails loudly.

Minimum-charge regressions prove that `rate × quantity` is floored by an evidenced `minimum_amount`, the floor is not applied when usage pricing already exceeds it, and invalid negative minimums are rejected.

Conditional-term regressions prove that unresolved `subject to` / conditional commercial terms block ranking, an evidenced resolution restores rankability, and merely claiming a term is resolved without a resolution source does not.

Comparison-group regressions prove that:

- a first-position outlier cannot become the baseline merely because it was first;
- the unique largest route/equipment/currency group is selected automatically;
- equal multi-quote groups refuse to guess and require an explicit comparison target;
- an explicit target selects only the matching comparison group;
- equivalent equipment forms such as `40HQ` and `40HC` normalize together;
- materially different equipment types such as `40GP` and `40HC` remain separate.

Route-alias regressions prove that an explicit alias such as `CNSHA -> SHANGHAI` restores comparability only when it carries a non-empty source reference; an unproven alias is ignored and cannot silently merge routes. Applied alias evidence is exposed through `route_alias_audit`.

Fresh targeted probes for the new grouping/equipment slice are 5/5 PASS; route-alias provenance helper probes are 4/4 PASS. These targeted probes do not pretend the entire committed regression inventory was rerun in the same local harness.

The representative synthetic quote fixture remains the deterministic acceptance case. Synthetic and shortlist fixtures are not market evidence; they only protect deterministic behavior before real participant data arrives.
