# Concierge validation protocol — logistics quote comparison

This protocol converts an opted-in design partner into observed market evidence without pretending a product exists.

## 1. Consent and intake

- Only accept a quote/rate-card set after the participant explicitly opts in.
- Ask the participant to remove customer names, booking numbers, account numbers, personal contact details, and other unnecessary sensitive/commercial identifiers before sharing.
- Do not require suppliers/carriers to change their existing file format.
- Record source type, quote id, route, equipment, currency, validity, every extracted charge, and a source reference for each field/charge.

## 2. Normalization

The concierge engine normalizes charge names and pricing bases but does not invent values.

Supported pricing bases:

- `PER_SHIPMENT`
- `PER_CONTAINER`
- `PER_BL`
- `PER_KG`
- `PER_CBM`
- `INCLUDED`
- `UNKNOWN`

A missing source reference, missing amount, unknown basis, or cross-currency charge is marked uncertain/incomplete. Uncertain quotes may be shown for review but must not silently enter the cheapest-price ranking.

## 3. Comparison boundary

No silent foreign-exchange conversion is allowed. Quotes are rankable only when they share the same route, equipment, and quote currency and all priced line items have enough context to compute a total.

The output must preserve an audit trail from every priced line item back to `source_ref` so a participant can challenge the extraction.

The system must prefer `INSUFFICIENT_COMPLETE_COMPARABLE_QUOTES` over a fake winner when fewer than two complete comparable quotes remain.

## 4. What we measure

For every participant, capture observed rather than inferred signals where possible:

- opted in or declined;
- submitted a real anonymized quote set;
- elapsed concierge processing time;
- extraction/normalization corrections made by the participant;
- uncertain fields and missed surcharge/charge categories;
- whether the returned comparison was trusted enough to use;
- whether the participant requested a second run;
- explicit willingness-to-pay amount/range, if volunteered or directly tested;
- actual payment, if a later authorized paid experiment is run.

## 5. Evidence semantics

`CONTACTED`, `OPTED_IN`, `SUBMITTED`, and `COMPLETED` are behavior signals, not payment evidence.

`REPEAT_REQUEST` is stronger retention intent but still not payment.

`WTP_SIGNAL` requires an explicit participant statement about willingness to pay; never infer it from praise or repeat use.

`PAID` requires an observed transaction in an Owner-authorized paid experiment.

## 6. Market gate

The existing Opportunity Lab gate remains authoritative:

- public pain or prospect discovery alone cannot produce `BUILD`;
- one successful concierge result alone cannot produce `BUILD`;
- failed real-world thresholds may produce `KILL`;
- `BUILD` requires the configured experiment success threshold plus observed payment/WTP evidence;
- `BUILD` is still not merge, deploy, spend, or promotion authority.

## 7. Current outreach batch

Batch 01 is bounded to the first three approved public-signal prospects. Do not expand the batch without a new Owner authorization. The current runtime cannot post to Reddit, so prepared outreach remains unsent until an authenticated Reddit write surface exists.
