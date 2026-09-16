# Validation test matrix

Current isolated regression groups:

- market gate: 5 tests;
- prospect bridge: 5 tests;
- concierge engine: 8 tests;
- experiment tracker: 5 tests;
- synthetic quote fixture: 1 deterministic fixture test;
- design-partner shortlist fixture: 6 candidates re-qualified against expected stage/score/no-money-signal invariants.

Concierge-engine coverage regressions now prove:

- a quote missing a charge code seen in another otherwise-comparable quote is not allowed to win merely because the omitted charge makes its visible total lower;
- an unresolved coverage gap marks that quote incomplete and removes it from ranking;
- a missing charge can be resolved only with an explicit `INCLUDED` or `NOT_APPLICABLE` resolution carrying a non-empty source reference;
- an unevidenced waiver does not restore comparability.

The synthetic and shortlist fixtures are not market evidence. They only protect deterministic behavior before real participant data arrives.
