# Diataxis Writer intake — 2026-09-18

## Decision

`REFERENCE_ONLY + ADAPT_SMALL_PRINCIPLES`.

P2P will not vendor `tronghieu/agent-skills/skills/diataxis-writer` at this
checkpoint. The upstream repository exposes no declared license in GitHub
metadata and no root `LICENSE`, `LICENSE.md`, or `LICENSE.txt` was found
during intake. Copying the skill into P2P would therefore add avoidable
licensing ambiguity.

## Evidence inspected

- Repository: `tronghieu/agent-skills`
- Path: `skills/diataxis-writer`
- Upstream main commit:
  `d9177f2ae6feb6fe61c01b63a236680395b3d025`
- `SKILL.md` blob:
  `df6a99e3062d0f35e16e1bf481c5695008cf7a40`
- Supporting material inspected: README, evals, prose-tell reference,
  Diataxis-pattern reference, classifier shell script.
- Repository license metadata: `null` at intake time.

## What P2P adopts

P2P already had related ideas in the legacy `writing_suite.md`, including
technical constraint prompting and a 25-word sentence review boundary. This
intake makes the useful part live instead of creating a second writing system.

Adopted:

- one bounded prose-polish pass after semantic correctness;
- one main idea per sentence where practical;
- short/medium sentence preference with review above 25 words;
- removal of filler and nested qualifications;
- strict preservation of contracts, evidence, authority, warnings, exceptions,
  rollback, and exact machine tokens;
- optional reader-job classification for real documentation only.

Not adopted:

- vendored upstream source;
- automatic installation of another writing/humanizer skill;
- shell execution or network use;
- a new router, agent, daemon, registry, or control plane;
- mandatory Diataxis classification for prompts or packets;
- the claimed 30-60% reduction as a verified P2P metric.

## Acceptance

The live P2P skill points to
`.agents/skills/p2p/references/prose-clarity.md`.
Regression coverage must prove that:

1. only one bounded clarity pass is requested;
2. protected meaning outranks brevity;
3. Diataxis remains documentation-only and optional;
4. upstream stays reference-only while licensing is undeclared;
5. a deterministic A/B fixture becomes shorter without losing protected
   tokens.

This intake does not modify Supreme Law and therefore does not invalidate
portable-law projections in managed project repositories.
