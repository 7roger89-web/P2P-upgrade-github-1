---
name: creative.social.hook
description: Generate six bounded social-post hook variations from supplied topic context.
version: 1.0.0
---

# Social hook generator

## Purpose

Generate six distinct opening options for a social post. This is a narrow
idea-generation capability, not advertising copy, a post writer, a scorer, or
a publishing integration.

## Selection and inputs

- Run only after the existing P2P route selects this capability.
- Require a topic or supplied context. Missing topic/context returns
  `INCOMPLETE` rather than a generic set of hooks.
- Use numbers, metrics, names, tools, brands, and outcomes only when the user
  supplied them or a selected, permitted context pointer contains them.
- If a requested angle needs an unsupported fact, mark the gap `UNKNOWN` or
  choose a fact-free angle. Never fabricate authority or performance.

## Output contract

Return exactly six variations. Each variation has two short lines:

- line one is an unexpected, specific, or punchy opening and is at most 40
  characters;
- line two is a contrast or reframe and is at most 40 characters;
- the opening is not a question;
- a digit or metric is used only when supported by input evidence.

Cover these angles in order when the supplied topic supports them:

1. number-led;
2. contrarian;
3. personal transformation;
4. supplied-authority reference;
5. admission or loss;
6. future change.

If an angle is unsupported, keep the slot but use a truthful bounded variant.
Do not reuse one idea six times.

## Boundary rules

- `creative.copywriting` owns advertising, brand, and double-semantic copy.
  This capability owns general social hooks and personal content openers.
- Do not add unsupported metrics, names, citations, urgency, results, or
  platform claims.
- Do not require a named host, external service, network, account, browser,
  provider, new router, or content orchestrator.
- Do not publish, schedule, save, or automatically hand off to another
  capability. A later post draft or format operation requires separate
  selection.
- Do not invoke `creative.prose.humanize` automatically.

## Failure and determinism

Missing topic, stale context, or unsupported source evidence returns a visible
`INCOMPLETE` or `UNKNOWN` result. Identical selected input and context produce
the same angle order, variation order, and bounded output envelope.
