# Charge semantics guard

The real concierge-validation entrypoint is `src.charge_semantics.compare_quotes_guarded`, not a direct call to `src.concierge_engine.compare_quotes`.

This is a validation guard, not a new pricing engine. It transforms evidence-preserving charge semantics into the existing deterministic comparison engine and refuses ranking when the input can create a false total.

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

## Evidence boundary

Bundle expansion is a deterministic representation of supplied evidence. It does not infer that a fee is included merely because a quote says `all-in` in casual prose. The component list must be explicit in structured intake and must preserve a source reference.

## Failure behavior

Any unresolved semantic error yields:

`decision_warning = UNRESOLVED_CHARGE_SEMANTICS`

and an empty ranking. The semantic audit is returned with per-quote errors. The system prefers no winner over a winner produced by duplicate charges, scope conflation, or bundle double counting.
