# Validation test matrix

Current isolated regression groups:

- market gate: 5 tests;
- prospect bridge: 5 tests;
- concierge engine: 15 tests;
- conditional commercial terms: 3 tests;
- experiment tracker: 5 tests;
- synthetic quote fixture: 1 deterministic fixture test;
- design-partner shortlist fixture: 6 candidates re-qualified against expected stage/score/no-money-signal invariants.

Coverage regressions prove that a quote cannot win by silently omitting charges; unresolved omissions block ranking, and a missing charge is resolved only by evidenced `INCLUDED` or `NOT_APPLICABLE` status.

Validity regressions prove that expired/not-yet-valid quotes are excluded when an explicit comparison date is supplied; malformed quote dates are excluded and a malformed comparison date fails loudly.

Minimum-charge regressions prove that `rate × quantity` is floored by an evidenced `minimum_amount`, the floor is not applied when usage pricing already exceeds it, and invalid negative minimums are rejected.

Conditional-term regressions prove that unresolved `subject to` / conditional commercial terms block ranking, an evidenced resolution restores rankability, and merely claiming a term is resolved without a resolution source does not.

Verification for this slice: base concierge engine **15/15 PASS**, conditional-term probes **3/3 PASS**, representative synthetic fixture **PASS**.

Synthetic and shortlist fixtures are not market evidence. They only protect deterministic behavior before real participant data arrives.
