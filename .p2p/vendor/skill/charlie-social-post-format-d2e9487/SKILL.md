---
name: creative.social.post_format
description: Format supplied social-post content with one explicitly selected writing framework.
version: 1.0.0
---

# Social post formatter

## Purpose

Turn a supplied topic, draft, or context dump into a bounded framework-based
social post for review. Supported frameworks are PAS, AIDA, BAB, STAR, and
SLAY. This capability formats content; it does not freeform-write by default,
humanize automatically, score a draft, or publish.

## Selection and inputs

- Run only after the existing P2P route selects this capability.
- Require a topic or non-empty source context and one explicit framework. If
  either is missing, return `INCOMPLETE` and identify the missing input.
- A selected, fresh voice pointer may tune tone and rhythm when the user asks
  for the author's voice. Missing requested voice context is `INCOMPLETE`, not
  a reason to invent a style.
- Use only facts, numbers, names, dates, quotes, and claims in the supplied
  source or selected permitted context.

## Formatting contract

- Maximum 20 lines and 200 to 250 words unless the caller supplies a different
  bounded length.
- Put a blank line between logical lines where the target surface needs it.
- Keep the hook and contrast concise, then apply the selected framework's
  stages in order.
- Use no question unless the supplied hook or requested format requires it.
- Use a list of exactly three items only when the source and framework call for
  a list; never pad a list to create a rhetorical trio.
- End with a reviewable action that is supported by the source. Do not invent a
  call to action, result, or platform behavior.

Framework maps:

- PAS: Problem, Agitation, Solution;
- AIDA: Attention, Interest, Desire, Action;
- BAB: Before, After, Bridge;
- STAR: Situation, Task, Action, Result;
- SLAY: Story, Lesson, Actionable advice, You.

## Boundary rules

- Return a reviewable text result. Do not save, schedule, publish, or claim
  delivery as an implicit side effect.
- Do not research externally, call a provider, access a social account, scrape
  a platform, or require a browser, account, named host, new router, or
  content orchestrator.
- `creative.social.post` owns freeform social drafting. This capability owns
  strict framework formatting. `creative.copywriting` owns marketing and
  double-semantic brand copy.
- `creative.prose.humanize` remains an independent optional downstream
  capability and is not loaded automatically.

## Failure and determinism

Missing source, framework, selected context, or factual support returns
`INCOMPLETE` or `UNKNOWN`. Identical source, framework, selected context, and
constraints produce the same framework order and canonical output envelope.
