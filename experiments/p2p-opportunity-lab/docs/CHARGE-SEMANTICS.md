# Charge semantics guard

## Entrypoint hierarchy

Raw atomic quote comparison MUST enter through:

`src.validation_pipeline.compare_quotes_validated`

That pipeline resolves evidenced percentage surcharges first, then calls:

`src.charge_semantics.compare_quotes_guarded`

which applies scope, duplicate, bundle and optional-service semantics before the existing deterministic core comparison engine.

Raw multi-equipment FCL provider quote sets MUST enter through:

`src.portfolio_validation_pipeline.compare_fcl_portfolios_validated`

which resolves percentage semantics for each required equipment offer and provider-level shared charges before delegating to `src.portfolio_semantics.compare_fcl_portfolios`.

Calling lower-level engines directly is appropriate only for their isolated regression/unit contracts, not for real concierge-validation intake.

## Scope

Each charge may declare one of:

- `UNSPECIFIED`
- `ORIGIN`
- `MAIN`
- `DESTINATION`
- `OTHER`

A scoped charge is encoded into the coverage key, e.g. `ORIGIN::THC` and `DESTINATION::THC` are intentionally different. The guard never infers scope from price, carrier, port name, or prose.

## Duplicate guard

Two non-included priced lines with the same normalized `scope + charge code + basis + currency` are treated as an unresolved duplicate risk. The quote is blocked before ranking.

This is deliberately conservative. A real quote may contain legitimately distinct charges with similar labels, but that distinction must first be represented explicitly rather than silently double-counted.

## Bundled / all-in charges

A priced bundle may declare:

- `bundle_includes`: the component charge codes covered by the bundle;
- optional `bundle_primary_code`: which covered component carries the bundle price in the existing engine;
- `source_ref`: mandatory evidence for the bundle statement.

The guard keeps exactly one priced bundle line and derives zero-contribution `INCLUDED` coverage rows for the remaining bundled components. This lets an evidenced all-in rate compare against an itemized quote without inventing missing surcharges.

If a priced standalone component overlaps a priced bundle in the same scope, the quote is blocked as `BUNDLE_COMPONENT_DOUBLE_COUNT_RISK`.

## Optional / add-on services

A charge with `optional: true` must also state `selected: true` or `selected: false` explicitly.

- `selected: false` removes the add-on from both price and required coverage while preserving it in the semantic audit as `optional_excluded`.
- `selected: true` keeps the charge as an ordinary priced/included line.
- omitted selection blocks the quote as `OPTIONAL_SELECTION_REQUIRED`.

The guard never infers selection from wording, price, or presence in one provider's rate sheet. This prevents optional insurance, trucking, customs, or other add-ons from making one provider look falsely expensive or from being silently added to a customer's requested scope.

## Evidence boundary

Bundle expansion is a deterministic representation of supplied evidence. It does not infer that a fee is included merely because a quote says `all-in` in casual prose. The component list must be explicit in structured intake and must preserve a source reference.

Likewise, optional selection is an explicit experiment/comparison input, not an inference made by the model.

## Failure behavior

Any unresolved semantic error yields:

`decision_warning = UNRESOLVED_CHARGE_SEMANTICS`

and an empty ranking. The semantic audit is returned with per-quote errors. The system prefers no winner over a winner produced by duplicate charges, scope conflation, bundle double counting, or guessed optional-service selection.
