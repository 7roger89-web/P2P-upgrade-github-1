# Logistics quote-comparison validation status

## External lane

- Owner authorization: APPROVED for exactly the first three shortlisted prospects.
- Outreach delivery: READY_BUT_NOT_SENT.
- Durable counters: `sent=0`, `reply=0`, `opt_in=0`.
- Delivery blocker: no authenticated Reddit write/post surface is available in the current ChatGPT session.
- Reply watch: ACTIVE, every 6 hours, notify only on new direct reply or clear opt-in.
- Latest observed watch run produced no reply/opt-in notification; because outreach is still unsent, no direct reply can exist yet.

## Internal lane

- Market gate remains `VALIDATE`.
- Quote intake requires provenance and anonymization confirmation.
- No silent FX conversion.
- Route/equipment/currency mismatches are excluded.
- Missing/uncertain charge data blocks ranking rather than creating a fake cheapest quote.
- Charge-coverage parity prevents a quote winning by omission; evidenced `INCLUDED` / `NOT_APPLICABLE` resolutions are allowed.
- Explicit `as_of_date` excludes expired/not-yet-valid quotes and malformed validity cannot silently rank.
- `minimum_amount` is now supported for pricing bases such as per-kg/per-cbm charges. The engine calculates `max(rate × quantity, minimum_amount)` and preserves raw contribution, minimum, whether the floor applied, and source reference in the audit trail.
- Negative minimums and `INCLUDED + minimum_amount` contradictions are rejected.
- Concierge engine exact regression: **15/15 PASS**; representative synthetic fixture: **PASS**.
- Experiment tracker separates `CONTACTED`, `SUBMITTED`, `REPEAT_REQUEST`, `WTP_SIGNAL`, and `PAID`; praise/repeat use cannot become money evidence.

## Promotion boundary

Do not build production UI/login/billing/deployment from this checkpoint. Continue validation infrastructure and representative real-world semantics until observed user behavior changes the market gate.
