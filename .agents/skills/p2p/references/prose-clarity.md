# P2P Prose Clarity Guard

Use this reference after the content is already correct.

The goal is smaller, clearer prose without changing the task contract. This is
an editing guard, not a new router, agent, state machine, or authority layer.

## Apply when

Apply one bounded pass to prose that P2P writes or rewrites, including:

- executor prompts and handoff prose;
- documentation, runbooks, README material, and explanations;
- reports and user-facing summaries.

Do not apply sentence-shaping rules to code, commands, paths, hashes, IDs,
schemas, JSON/YAML, exact quotations, evidence payloads, or other
machine-readable content.

## Clarity rules

1. Give each sentence one main idea whenever accuracy permits.
2. Prefer short or medium sentences. Treat roughly 8-20 words as a useful
   default band, not a hard validator.
3. Review prose sentences above 25 words. Split them when the relationship
   between ideas stays clear.
4. Avoid nested qualifications. Put secondary conditions in another sentence,
   bullet, note, or table when that is easier to parse.
5. Remove filler, ceremonial transitions, repeated framing, and generic claims
   of importance.
6. Keep technical terms when they carry meaning. Plain language must not erase
   precision.
7. Stop after one useful pass. Do not create a rewrite loop for style alone.

## Protected meaning

Concision must never weaken or delete:

- objective or acceptance criteria;
- authority and Owner Gates;
- scope, exclusions, and permissions;
- evidence status, uncertainty, provenance, or limitations;
- safety warnings, destructive-action boundaries, rollback, or recovery;
- material exceptions and decision points;
- exact commands, paths, identifiers, hashes, status names, or schema fields.

If shortening conflicts with protected meaning, keep the meaning.

## Documentation-only Diataxis use

For an actual documentation task, classify the reader's immediate job only
when the classification helps structure the page:

- learning through a guided example;
- completing a known task;
- looking up precise facts;
- understanding concepts or tradeoffs.

Choose one dominant job per page when practical. Split or link material that
serves a different job.

Do not force this taxonomy onto executor prompts, Control Tower packets,
schemas, acceptance contracts, or short operational messages. Those surfaces
already have their own contracts.

## Evaluation contract

For a prose-clarity A/B check, compare the same semantic content before and
after one pass.

Measure:

- total word count;
- count of prose sentences above 25 words;
- preservation of protected tokens and required facts;
- added or removed claims;
- whether the result is easier to act on.

A shorter output is not a PASS if it loses protected meaning. Do not encode a
target percentage reduction as a universal requirement.

## Provenance

Research reference only:

- upstream: `tronghieu/agent-skills`
- upstream path: `skills/diataxis-writer`
- observed upstream commit: `d9177f2ae6feb6fe61c01b63a236680395b3d025`
- observed `SKILL.md` blob: `df6a99e3062d0f35e16e1bf481c5695008cf7a40`
- observed repository license metadata: not declared
- integration mode: `REFERENCE_ONLY`

P2P does not vendor or copy the upstream skill while a reusable license is not
declared. The concepts above are an original P2P adaptation aligned with the
existing legacy writing rules. Upstream installation commands, automatic
Humanizer chaining, shell helpers, and output templates are not imported.

The reported "30-60% fewer words" figure is not a P2P fact. The inspected
upstream evals are qualitative task checks, not an independent quantitative
benchmark for that percentage.
