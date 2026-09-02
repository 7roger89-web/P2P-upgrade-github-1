---
name: creative.social.voice_profile
description: Build a bounded author voice profile from user-supplied writing samples and context.
version: 1.0.0
---

# Social voice profile

## Purpose

Build a reusable description of who the author is and how the author writes.
This is a context-producing capability. It is not a memory platform, a
provider, a content publisher, or a replacement for prose polishing.

## Selection and inputs

- Run only after the existing P2P route selects this capability for a voice
  profile request.
- Require at least three non-empty writing samples supplied by the user for a
  complete profile. The samples may be provided in one message or several
  messages.
- Accept optional user context about role, audience, topic pillars, point of
  view, brand promise, and off-limits topics.
- A user correction or a new user sample takes precedence over an earlier
  descriptive context item within the same scope.
- Never load a starter corpus or infer the user's identity from the upstream
  author. If required sample evidence is missing, return `INCOMPLETE` with the
  missing evidence and do not fabricate a profile.

## Analysis contract

Read all supplied samples as one bounded evidence set. Extract only patterns
supported by the samples:

- audience, recurring topic pillars, point of view, and brand promise;
- tone, sentence length, sentence rhythm, paragraph rhythm, and pacing;
- opening and closing moves, hook patterns, transitions, and calls to action;
- recurring words or signature phrases;
- topic and structural patterns that appear across samples;
- absence signals and prohibited constructions only when the absence is
  observable across the required evidence set.

Contradictory samples remain visible as a conflict or mixed signal. Do not
average away a contradiction and do not turn a generic style preference into a
sample-derived fact.

## Output contract

Return two logical context outputs named `about-me` and `voice-profile`.
Their bounded serialized fields are:

- `about_me`: audience, topic pillars, point of view, brand promise, and
  off-limits topics;
- `voice_profile`: tone, sentence rhythm, hook patterns, opening patterns,
  closing patterns, signature phrases, absence signals, and prohibited
  constructions.

Attach sample identifiers, sample count, scope, source hashes, and freshness
through the existing P2P context-pointer machinery. Do not attach full sample
text to registry metadata, provenance, diagnostics, or capability identity.

## Context and privacy boundary

The result is a bounded context payload for downstream selected capabilities.
It is not durable user memory and does not create project files by default.
The existing context resolver decides whether the pointer is fresh, permitted,
scope-matched, and selected. Private sample text stays in the caller's
protected input boundary.

## Failure and forbidden behavior

- Missing, blank, stale, or scope-mismatched evidence returns `INCOMPLETE` or
  `UNKNOWN`; never invent a voice profile.
- Do not require a named host, named provider, external service, network,
  account, browser, interactive-form engine, or second router.
- Do not publish, save, or overwrite user files as an implicit side effect.
- Do not invoke `creative.prose.humanize` automatically. It is an independent
  optional downstream prose-polishing capability when separately selected.
- Do not make a private sample, an upstream author's style, or a model's guess
  the user's default voice.

## Determinism

For identical samples, context, scope, and selection snapshot, emit the same
field ordering, evidence ordering, and canonical context representation.
