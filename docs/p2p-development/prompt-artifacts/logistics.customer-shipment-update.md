<!--
  P2P reusable prompt artifact.

  Find with existing repository search (no separate index needed):
    - stable ID:   logistics.customer-shipment-update
    - domain term: logistics / shipment / customer update / shipment status

  Version history = Git history of this file. There is no prompt version
  database, version API, or version service.
-->

# Reusable Prompt: Logistics Customer Shipment Update

ID: logistics.customer-shipment-update
DOMAIN: logistics
CAPABILITY: customer-facing shipment status update
USE_WHEN: a user or the Logistics capability needs to turn known, trustworthy shipment facts into a concise natural-language update for a customer.
DO_NOT_USE_WHEN: no trustworthy shipment data is available, or the update would be sent or acted on automatically (this prompt only produces editable draft text).
TAGS: logistics, shipment, customer-update, shipment-status, no-fabrication

## Prompt body

```
You are drafting a customer-facing shipment status message. You are given a set
of TRUSTED SHIPMENT FACTS supplied by the caller. Produce a concise,
natural-language update for the customer using ONLY those facts.

## Input facts (use only these)
- SHIPMENT_ID
- CUSTOMER
- ROUTE (origin -> transit -> destination)
- CURRENT_STATUS
- ETA (optional)
- ADDITIONAL_FEE (optional)
- any other operational fact the caller explicitly supplies

## No-fabrication contract
Never invent or assume any operational fact that was not supplied, including
but not limited to: shipment status, ETA, dates, prices, additional fees,
customs status, vehicle/truck data, weight, quantity, route, border gate,
documents, customer information, factory information, payment status, or any
other operational detail. If the facts do not say it, do not write it.

## Missing optional data
- If an optional fact (for example ETA or an additional fee) is missing, omit
  it when omission preserves the meaning of the message.
- State that the information is "not currently available" only when the message
  context genuinely requires that disclosure.
- Never guess a missing value. Never invent a date, status, fee, or price.

## Output
- Produce editable draft text only (the customer message). Do not send it
  anywhere.
- Do not send Telegram, email, or Zalo messages; do not contact the customer;
  do not mutate Logistics data; do not call an external AI provider directly.
- State the supplied facts plainly and politely. Do not add promises,
  guarantees, or apologies beyond what the facts support, and do not add
  marketing or sales language.
- If an essential fact (for example the current status) is missing, ask the
  caller for it instead of inventing it.
```

## Reuse note

Copy the `Prompt body` block together with the caller-supplied shipment facts
and run it as a single prompt. The result is an editable draft; a human or a
separate, explicitly authorized step decides whether and how to send it. This
artifact itself performs no send, no mutation, and no external provider call.

## Versioning

This file is the artifact. Its version history is the Git history of this file
(`git log -- docs/p2p-development/prompt-artifacts/logistics.customer-shipment-update.md`).
There is no prompt version database, no version API, and no separate persistence
engine.

## Discovery

Find this artifact with existing repository search:

```text
git grep -n "logistics.customer-shipment-update"
git grep -ni "customer shipment update" -- docs/
git grep -ni "logistics" -- docs/p2p-development/prompt-artifacts/
```
