# Upstream evaluation — Codex First Customer Finder

Status: `EXPERIMENTAL_UPSTREAM_CANDIDATE`

## Provenance

- Repository: `Kappaemme-git/codex-first-customer-finder-skill`
- License: MIT
- Pinned upstream commit: `943c455bdfc40da46265b01b3c1f41e4bb386f27`
- Upstream author: Francesco Mistero (`Kappaemme-git`)
- Attribution note: public secondary references indicate Greg Brockman reshared the project; he is not the repository author.

## Why it fits Opportunity Lab

This upstream covers the gap between a `VALIDATE` market decision and a real-world
experiment: identify plausible first customers/design partners from recent public
pain, demand, workaround, switching, and timing signals.

The useful upstream primitives are:

- explicit primary and adjacent ICPs plus disqualifiers;
- multi-angle search buckets for demand, pain, workaround, switching, and timing;
- evidence-backed prospect qualification;
- a 0–5 weighted score across pain strength, product fit, timing, public
  reachability, and evidence quality;
- public-source provenance for every primary prospect;
- source-grounded outreach drafts;
- manual outreach by default.

## P2P integration decision

`REUSE_WITH_THIN_ADAPTER`.

Do not fork or rewrite the upstream skill. Do not install `@latest` into a
governed P2P runtime. Pin the reviewed upstream commit and adapt its prospect
records into the Opportunity Lab evidence model.

The local bridge is `src/prospect_bridge.py`.

## P2P boundary additions

P2P is intentionally stricter than the upstream prospecting workflow:

1. A public prospect signal is evidence about pain/demand/timing, not proof of a
   buyer.
2. A public pain or demand signal MUST NOT be converted into `PAYMENT` or
   `WILLINGNESS_TO_PAY`.
3. Industry/role fit without a cited public pain/need/timing signal is rejected
   from the primary shortlist.
4. Private contact enrichment, data brokers, sensitive traits, personal phone
   numbers, home addresses, and private email discovery are forbidden.
5. Outreach output is `DRAFT_ONLY`; no message, follow, comment, form submission,
   CRM mutation, or other external contact action is authorized by this
   capability.
6. Real outreach remains an Owner Gate under the current pilot state.
7. A prospect shortlist may help execute a validation experiment; it cannot
   promote the Opportunity Packet from `VALIDATE` to `BUILD` by itself.

## Adoption gate

Promote this upstream from candidate only after a representative pilot proves:

- source links remain valid and materially support each prospect;
- false-positive/industry-only prospects are rejected;
- no money signal is hallucinated from public pain;
- no private/sensitive enrichment occurs;
- P2P preserves manual outreach authority;
- the shortlist improves the real-world validation experiment rather than
  becoming a generic lead-generation side project.
