# Percentage surcharge semantics

Percentage pricing is resolved before ordinary charge semantics and before ranking.

## Required evidence

A percentage charge must carry:

- `line_id` — stable identifier for the percentage line;
- `percentage_rate` — numeric percent, e.g. `5` means 5%;
- `percentage_of_line_ids` — one or more named base lines;
- `source_ref` — provenance for the percentage rule.

The system never guesses a percentage base from charge names or commercial convention.

Example:

```json
{
  "line_id": "BAF",
  "name": "BAF",
  "percentage_rate": 5,
  "percentage_of_line_ids": ["FREIGHT"],
  "source_ref": "quote:p2:r14"
}
```

## Calculation

Each named base line is converted to its effective contribution using the same quantity semantics used by the comparison:

`effective base = max(rate × applicable quantity, minimum_amount when present)`

Then:

`percentage total = sum(effective named bases) × percentage_rate / 100`

For atomic comparisons the resolved percentage becomes a deterministic per-shipment amount before passing to the charge-semantics guard.

For a multi-equipment FCL offer, the resolver first uses the required equipment quantity to calculate the percentage total, then the portfolio validation pipeline rebases that resolved total back to a `PER_CONTAINER` amount for that equipment bucket so the existing portfolio engine reconstructs exactly the same total.

Provider-level shared percentage charges are resolved once against shared lines and are not multiplied by the number of equipment rows.

## Refusals

Resolution is blocked when:

- the base line ID does not exist;
- the percentage line references itself;
- a percentage line is used as another percentage line's base;
- a bundled line is used as a percentage base before bundle resolution;
- an optional base line is unselected or lacks explicit selection;
- the base line uses another currency and no explicit FX layer exists;
- the percentage line also contains a manually supplied fixed amount;
- the percentage rule lacks source evidence.

Atomic failure returns `UNRESOLVED_PERCENTAGE_SEMANTICS` before ranking. In FCL portfolios, a provider with unresolved percentage semantics is excluded; remaining complete providers may still be compared.

## Audit

Every resolved percentage records:

- percentage line ID;
- rate;
- named base line IDs;
- effective base total;
- resolved surcharge total;
- source reference.

This is calculation evidence, not market evidence and not willingness-to-pay evidence.
