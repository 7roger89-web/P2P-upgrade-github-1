# Development lanes during market validation

Opportunity Lab does not stop engineering while waiting for human responses. It separates work into two lanes.

## External lane

`OUTREACH -> REPLY -> OPT_IN -> REAL_DATA -> CONCIERGE_RUN -> REPEAT/WTP`

Only observed external behavior can change market confidence. The first outreach batch is already Owner-authorized but remains unsent until an authenticated Reddit write surface is available.

## Internal lane

Allowed while waiting:

- evidence/provenance contracts;
- quote intake and anonymization contracts;
- deterministic normalization/comparison logic;
- uncertainty handling and audit trail;
- synthetic/representative fixtures;
- experiment observation tracking;
- regression tests and falsification cases.

Not allowed from the current `VALIDATE` checkpoint:

- production product UI;
- login/account system;
- billing/subscription system;
- production deployment;
- autonomous lead generation/outreach expansion;
- claims of market pass based on synthetic fixtures.

The point is to make the real test cheap and fast when a participant opts in, without accidentally building the full product before the test says it deserves to exist.
