# CLAUDE_SEO_LOGISTICS_01 — Logistics SEO Capability Evaluation

Status: `PENDING`

This file is a **detail record for one approved backlog item**, not a parallel backlog and not runtime authority. The durable backlog/index remains `docs/p2p-development/P2P-APPROVED-IDEAS-BACKLOG.md` / PR41. This record exists so the idea cannot be lost before consolidation.

## Owner direction

Evaluate and, if fit is proven, integrate the Claude SEO methodology/capability family for the Logistics project profile / Logistics-facing public web surfaces.

Do not install or activate it globally merely because it is available.

## Upstream verified at intake

Primary upstream: `AgriciDaniel/claude-seo`

```text
UPSTREAM_SHA=a1480c7e590b16001bd9dc1627eacdcd44d580f9
UPSTREAM_TREE=9215d385ce6b6cd950b58dd243cb2b4f7c32feaa
ROOT_LICENSE=MIT
OBSERVED_STARS≈15965
```

Observed upstream shape at intake:

- 25 sub-skills;
- 18 specialist agents;
- full-site audits can fan out to up to 15 specialist agents;
- 32 user-invocable `/seo` commands across core/sub-skills/extensions;
- technical SEO, content/E-E-A-T, Schema.org, GEO/AEO, local/maps, backlinks, e-commerce and international SEO;
- recommendations are explicitly falsifiable: each should carry the first-principle observation, dependency relationship, a `how would we know this failed?` check, and a leading indicator;
- core can start without paid third-party SEO extensions; Google integrations use tiered credentials when the owner chooses to add them;
- upstream includes an explicit limitations section and security-oriented installer guidance.

The upstream README also points to `AgriciDaniel/codex-seo`, a Codex-first port. At intake, GitHub metadata for that port reported a Codex-first SEO suite, but its repository license metadata was `NOASSERTION`; therefore it is **REFERENCE_ONLY_PENDING_LICENSE_VERIFICATION** and must not be vendored/installed merely because it is a convenient Codex transport.

## Approved P2P role

Treat the useful part as a **provider-neutral SEO capability family**, not as a Claude-only authority and not as a replacement for P2P governance.

Target projection for Logistics:

```text
LOGISTICS PROJECT PROFILE
  -> public website / landing page / content / service-page SEO task
  -> minimum relevant SEO capability selection
  -> evidence-led audit/recommendation
  -> explicit falsifiability + leading indicator
  -> implementation only when authorized
  -> post-change verification / drift check
```

High-value candidate capabilities:

```text
marketing.seo.audit
marketing.seo.technical
marketing.seo.content
marketing.seo.schema
marketing.seo.local
marketing.seo.international
marketing.seo.geo_aeo
marketing.seo.images
marketing.seo.drift
```

Do **not** bind these capabilities to internal Logistics business workflow, database/payment logic, shipment operations, or production mutations unless a specific task genuinely concerns a public-facing SEO surface.

## Why this is especially valuable

The strongest concept to adapt is not the 18-agent fan-out. It is the recommendation contract:

```text
RECOMMENDATION
  -> SOURCE OBSERVATION
  -> DEPENDENCIES
  -> FAILURE / FALSIFICATION CHECK
  -> LEADING INDICATOR
```

This maps well to P2P evidence discipline and should be preferred over generic SEO advice that cannot be independently tested.

## Constraints

```text
GLOBAL_INSTALL=NO
BULK_AGENT_FANOUT_BY_DEFAULT=NO
SEO_CAPABILITY_LOADED_ONLY_WHEN_RELEVANT=YES
P2P_AUTHORITY_REPLACEMENT=NO
THIRD_PARTY_CREDENTIALS_OPTIONAL=YES
SECRET_VALUES_IN_REPO=NO
CODEX_PORT_LICENSE_VERIFICATION_REQUIRED=YES
```

- Do not automatically spawn 15 agents; use risk/task-proportional concurrency and the minimum sufficient set.
- Do not turn 25 skills into default Logistics context.
- Free/no-key analysis does not authorize crawling arbitrary third-party sites; scope must remain user/project-authorized.
- Any Google/Search Console/GA4/Ads/DataForSEO/Firecrawl/Ahrefs/etc. credential path requires the existing P2P secret-reference / Owner-Gate rules.
- SEO recommendations must remain advisory/evidence-bound until the target site is known and post-change measurement is available.

## Future bounded acceptance test

A later P2P workstream should:

1. fresh-pin and security/license-review the selected upstream surfaces;
2. compare Claude SEO and the Codex port by **capability semantics**, not brand;
3. project only the minimum relevant Logistics SEO capabilities;
4. prove a no-key/read-only audit against an Owner-authorized public test surface;
5. verify every material recommendation contains observation + dependency + falsification check + leading indicator;
6. demonstrate no global skill/context loading and no unnecessary multi-agent fan-out;
7. if credentials are later desired, validate reference-only secret handling separately;
8. run independent Supervisor verification before any canonical activation.

## Terminal boundary

```text
CLAUDE_SEO_LOGISTICS_01=PENDING
IMPLEMENTED=NO
INSTALLED=NO
AUTHORIZED_FOR_RUNTIME=NO
```

Current img2threejs/PR40 work remains the active priority; this item is intentionally deferred.