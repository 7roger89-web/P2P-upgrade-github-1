# Synthetic fixture purpose

Synthetic fixtures exercise the concierge comparison logic before any real participant data is available.

They are not market evidence and must never be copied into the Opportunity Packet as if they came from users.

`synthetic-quote-set-01.json` verifies:

- `PER_CONTAINER`, `PER_SHIPMENT`, and `PER_BL` arithmetic;
- charge-name normalization (`Ocean Freight` / `Sea Freight` -> `FREIGHT`, documentation aliases -> `DOC`);
- included-charge handling;
- stable audit references;
- deterministic ranking when quotes are comparable;
- exclusion of a different quote currency instead of silent FX conversion.

Expected result for the first fixture:

1. `SYN-B` — USD 2010
2. `SYN-A` — USD 2060
3. `SYN-C` — excluded (`CURRENCY_MISMATCH`)
