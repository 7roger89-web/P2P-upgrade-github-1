# Logistics quote-comparison validation status

## External lane

- Owner authorization: APPROVED for exactly the first three shortlisted prospects.
- Outreach delivery: READY_BUT_NOT_SENT.
- Delivery blocker: no authenticated Reddit write/post surface is available in the current ChatGPT session.
- Reply watch: ACTIVE, every 6 hours, notify only on new direct reply or clear opt-in.
- Reply watch limitation: it cannot observe a direct reply until the authorized outreach comment is actually posted.

## Internal lane

- Market gate remains `VALIDATE`.
- Concierge engine is ready for anonymized real quote sets.
- Quote intake requires provenance and anonymization confirmation.
- No silent FX conversion.
- Route/equipment/currency mismatches are excluded from comparable ranking.
- Missing source references, unknown pricing bases, missing amounts, and cross-currency line items make a quote incomplete rather than silently rankable.
- Synthetic fixture verifies a deterministic example: `SYN-B USD 2010 < SYN-A USD 2060`; `SYN-C CNY` is excluded without FX.

## Promotion boundary

Do not build production UI/login/billing/deployment from this checkpoint. Continue only validation infrastructure and representative fixtures until observed real-user behavior changes the market gate.
