# Logistics quote-comparison pilot

Current market decision: `VALIDATE`.

This pilot tests whether small/mid logistics teams and freight forwarders will repeatedly use and pay for an auditable workflow that normalizes inconsistent carrier/forwarder quotations without forcing suppliers to change format.

## External validation lane

- Six evidence-backed design-partner candidates have been shortlisted.
- Owner authorized outreach to exactly ranks 1-3.
- Outreach is public, research-first, opt-in, and non-promotional.
- Current runtime cannot post to Reddit, so the three authorized messages are prepared but unsent.
- A 6-hour condition watch monitors the three source threads and notifies only after a direct reply or clear opt-in appears.

## Internal validation lane

While external replies are pending, development continues only on validation infrastructure:

- quote intake + anonymization/provenance contract;
- deterministic normalization/comparison engine;
- explicit uncertainty and audit trail;
- synthetic quote fixtures;
- experiment observation schema;
- experiment tracker that separates behavior, repeat-use, WTP, and actual payment.

No production UI/login/billing/deployment is authorized from this checkpoint.

## Core files

- `opportunity-packet.json`
- `design-partner-shortlist.json`
- `outreach-batch-01.json`
- `VALIDATION_STATUS.md`
- `fixtures/synthetic-quote-set-01.json`

## Real-data entry condition

A participant must explicitly opt in before sharing an anonymized quote/rate-card set. The concierge workflow then returns a traceable comparison; participant corrections, trust objections, repeat-use, and explicit WTP/payment signals are recorded as observed evidence.
