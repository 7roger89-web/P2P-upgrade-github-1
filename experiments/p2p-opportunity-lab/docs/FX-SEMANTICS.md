# FX semantics

FX conversion is explicit, evidence-backed preprocessing. It runs before percentage-surcharge resolution, charge semantics, coverage checks and ranking.

## Top-level order

Atomic quote validation:

`FX -> percentage -> charge semantics -> core comparison`

Multi-equipment FCL validation:

`FX per required offer/shared bucket -> percentage -> portfolio semantics -> ranking`

## Required rate evidence

Every direct conversion rate must provide:

- `from` currency;
- `to` currency;
- positive `rate`;
- non-empty `source_ref`;
- `as_of_date`.

Only the explicitly supplied direction is valid. The resolver does not infer an inverse rate and does not triangulate through a third currency.

When a comparison `as_of_date` exists, an FX rate dated after that comparison date is rejected. The current slice records older rate dates but does not invent a universal staleness threshold; any future freshness threshold must be explicit and evidence-driven.

## Conversion

For a fixed charge whose currency differs from the quote currency:

`converted amount = original amount × direct rate`

The same rate is applied to `minimum_amount` when present. The original currency, amount and minimum remain attached to the transformed line and the FX audit records the rate, source and rate date.

Included lines require no monetary conversion. Unselected optional add-ons do not require FX because they are removed by the later optional-service guard. An optional add-on whose selection remains ambiguous is left for the semantic guard to reject rather than forcing an unnecessary conversion.

## Percentage interaction

FX runs before percentage resolution. This permits an evidenced percentage surcharge to reference a fixed base line that originally appeared in another currency after that base has been explicitly converted to the quote currency.

A percentage line that itself declares a different output currency without a fixed amount is rejected; the resolver will not guess how a percentage result should be denominated.

## Refusals

The FX layer blocks on:

- missing direct rate;
- invalid/non-positive rate;
- missing rate source;
- missing/invalid rate date;
- rate from the future relative to the explicit comparison date;
- multiple direct rates for the same pair in one context;
- unsupported cross-currency percentage output.

No silent FX is ever performed.

## Evidence boundary

FX audit evidence proves only how a monetary line was normalized for a comparison. It is not market demand, willingness-to-pay, or permission to transact at that rate.
