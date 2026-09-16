# Validation test matrix

Current regression groups:

- market gate: 5 tests;
- prospect bridge: 5 tests;
- concierge engine: 20 committed tests;
- route-alias provenance: 2 committed tests;
- conditional commercial terms: 3 tests;
- charge semantics guard: 9 committed tests;
- multi-equipment FCL portfolio semantics: 5 committed tests;
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

Charge-semantics regressions prove that:

- origin/main/destination scope is preserved in coverage keys rather than conflated;
- exact duplicate priced charge signatures are blocked before ranking;
- the same code in different scopes is not misclassified as a duplicate;
- an evidenced all-in bundle expands into traceable included component coverage without charging those components again;
- a priced bundle plus a separately priced overlapping component is blocked as a double-count risk;
- an unselected optional add-on is removed from both price and required coverage while remaining visible in semantic audit;
- a selected optional add-on remains in the quote;
- an optional add-on without explicit `selected=true|false` blocks the quote instead of guessing;
- unresolved semantic errors return an empty ranking and `UNRESOLVED_CHARGE_SEMANTICS`.

Multi-equipment FCL portfolio regressions prove that:

- one provider total can be built from multiple required equipment types plus shared per-shipment/per-BL charges;
- a provider missing required equipment is excluded;
- multiple offers for one canonical required equipment type are treated as ambiguous rather than guessed;
- per-shipment charges placed inside an equipment-level offer are blocked to avoid multiplying them across containers/equipment rows;
- equivalent requirement labels such as `40HQ` and `40HC` combine into one canonical equipment quantity.

Fresh isolated harness results for this slice:

- charge semantics guard: **9/9 PASS** using the repo-style `src.*` import layout;
- multi-equipment FCL portfolio semantics: **5/5 PASS** against focused dependency stubs that preserve the pricing/basis contracts exercised by this module.

These focused results do not claim that the entire repository regression inventory was rerun in one local harness. GitHub Shield remains a separate exact-head acceptance surface.

The representative synthetic quote fixture remains the deterministic acceptance case. Synthetic and shortlist fixtures are not market evidence; they only protect deterministic behavior before real participant data arrives.
