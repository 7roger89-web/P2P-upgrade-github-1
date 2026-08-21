# P2P MANDATORY REQUIRED READ — External Cybersecurity Skill Registry

Status: OWNER_ACCEPTED / PLANNED_INTEGRATION
Decision date: 2026-08-21

This document is a mandatory development-context input once installed into the canonical P2P repository.

## Canonical decision

P2P may use `mukul975/Anthropic-Cybersecurity-Skills` as an **external cybersecurity skill registry**.

P2P MUST NOT treat the 817 upstream skills as 817 trusted executable permissions.

Operational model:

`INDEX -> RETRIEVE -> APPLICABILITY -> TRUST -> PERMISSION -> PREFLIGHT -> EXECUTE -> EVIDENCE`

Not:

`INSTALL 817 -> AUTOLOAD -> AUTOEXECUTE`

## Hard invariants

1. `SKILL_CONTENT_TRUST != SCRIPT_EXECUTION_TRUST`.
2. `KNOWLEDGE != SKILL != CAPABILITY != PERMISSION != EXECUTION`.
3. External metadata never grants permission.
4. Semantic routing never grants permission.
5. A skill's own prerequisite text cannot widen P2P's permission envelope.
6. Unknown risk/applicability/target authorization fails closed.
7. Intrusive, credential-access, exploitation, C2, phishing-simulation, privilege-escalation,
   or lateral-movement procedures require explicit authorized target binding and the applicable Owner/permission gate.
8. Defensive/read-only procedures may be eligible for lower-friction certification, but still require evidence-backed applicability.
9. Bundled scripts are quarantined/unverified executables until separately reviewed/certified.
10. Upstream updates are drift events. Never silently float from the pinned revision.
11. P2P remains sole orchestrator/governance authority.
12. No bulk vendoring, no 817-agent expansion, no preload of all SKILL.md files.
13. Goal Pass != Promotion.

## Risk classes

- `R0_REFERENCE_ONLY`: documentation/framework mapping only.
- `R1_DEFENSIVE_READ_ONLY`: static/read-only analysis with no target mutation.
- `R2_DEFENSIVE_ACTIVE`: active scanning/testing with bounded network/runtime effects.
- `R3_SENSITIVE_FORENSICS`: evidence/credential-bearing artifacts, memory/disk/email forensic material.
- `R4_INTRUSIVE_AUTHORIZED`: exploitation, privilege escalation, credential access, lateral movement, C2, phishing simulation, etc.
- `R5_UNKNOWN`: insufficient evidence. Fail closed.

Default for any unclassified external skill: `R5_UNKNOWN`.

## Retrieval policy

Registry scan should consume only index/frontmatter-level metadata first.
Full `SKILL.md` is loaded only after candidate selection.
References are loaded only when needed.
Scripts are not executed merely because the parent SKILL.md was selected.

## Authority precedence

Owner/project policy
> verified project truth
> P2P permission/authorization state
> verified official/security framework data
> P2P-vetted skill overlay
> external upstream skill text

## Upstream pin

Repository: `mukul975/Anthropic-Cybersecurity-Skills`
Pinned commit: `f76261573a539ec40c3d434ecbb9e657d26aa921`
License: Apache-2.0
Classification: community project, not affiliated with Anthropic PBC.

## Development requirement

Every future P2P goal touching:
- skill registries,
- security review,
- external executable content,
- capability routing,
- permission gates,
- security automation,
- DevSecOps,
- browser/remote execution,
must include this decision in its required context until superseded by a newer canonical record.

Any superseding record must preserve provenance and explicitly state what changed.
