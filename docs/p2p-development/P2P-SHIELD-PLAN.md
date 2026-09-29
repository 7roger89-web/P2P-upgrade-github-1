# P2P SHIELD PLAN

Status: `CANDIDATE_PROMOTED`

Purpose: durable development plan for a reusable, replaceable, evidence-based
security layer for P2P-managed projects.

This document is a development plan, not a promoted Supreme Law, not a live
security certification, and not permission to deploy or change production.
Promotion into canonical operating law or a default live P2P security profile
requires separate evidence and Owner approval.

---

## 0. Why P2P Shield exists

P2P-managed projects may expose code, private corpora, user data, AI/RAG
systems, CI/CD, deployment credentials, cloud resources, and production
services to different levels of risk.

The purpose of P2P Shield is not to promise that a project is "unhackable".
That is not a credible engineering target.

The target is:

```text
ASSUME_ONE_LAYER_CAN_EVENTUALLY_FAIL
NO_SINGLE_FAILURE_SHALL_AUTOMATICALLY_CAUSE_TOTAL_COMPROMISE
NO_SINGLE_PROVIDER_OR_VENDOR_IS_A_PERMANENT_SECURITY_DEPENDENCY
SECURITY_CLAIMS_REQUIRE_SCOPE-APPROPRIATE_EVIDENCE
```

P2P Shield therefore protects outcomes and trust boundaries rather than
locking P2P to a fixed toolchain.

---

## 1. Final design decision

P2P Shield SHALL NOT be defined as a bundle of tools such as Gitleaks,
CodeQL, ZAP, OPA, Trivy, promptfoo, CyberStrikeAI, or any future product.

P2P Shield owns:

1. security outcomes;
2. security invariants;
3. control contracts;
4. evidence contracts;
5. security profiles;
6. provider qualification rules;
7. provider replacement rules;
8. project-specific override/extension points;
9. review and retirement rules.

Tools and services are replaceable providers.

```text
SECURITY_OUTCOME
      ↓
CONTROL_CONTRACT
      ↓
PROVIDER_IMPLEMENTATION
      ↓
EVIDENCE
      ↓
PROJECT_SECURITY_VERDICT
```

The control remains stable when a provider changes, unless the threat model or
required outcome itself changes.

---

## 2. External design anchors

P2P Shield is intentionally aligned with concepts already proven useful by
security standards instead of inventing an isolated P2P-only theory.

### NIST CSF 2.0

NIST CSF 2.0 defines high-level cybersecurity outcomes and explicitly does not
prescribe one implementation for achieving them. P2P Shield follows the same
separation between outcome and mechanism.

Reference:
https://www.nist.gov/publications/nist-cybersecurity-framework-csf-20

### NIST OSCAL

OSCAL separates control definition, implementation, and assessment, and its
component model allows different components or combinations of components to
support the same control. P2P Shield borrows this mental model but does not
adopt the full OSCAL data model unless future evidence shows that doing so is
worth the complexity.

References:
https://pages.nist.gov/OSCAL/learn/concepts/terminology/
https://pages.nist.gov/OSCAL/learn/concepts/layer/implementation/component-definition/

### OpenSSF Security Baseline

OpenSSF maintains machine-readable YAML security controls with explicit
objectives and assessment requirements. P2P Shield similarly prefers small,
human-readable and machine-readable control definitions.

Reference:
https://github.com/ossf/security-baseline

### OWASP Secure by Design

OWASP Secure by Design emphasizes simplicity, minimized attack surface,
versioned contracts, automation, and repeatable verification. P2P Shield must
not increase security complexity faster than it reduces real risk.

Reference:
https://owasp.org/www-project-secure-by-design-framework/

---

## 3. Threat-model assumption

P2P Shield assumes a capable attacker will usually avoid "breaking the shield"
directly. The attacker will search for whichever actor, component, workflow,
session, dependency, runtime, or recovery mechanism already has legitimate
capability.

Therefore every protected project should be reasoned about as a capability
and data-flow graph:

```text
ACTOR
  ↓
IDENTITY
  ↓
CAPABILITY
  ↓
RESOURCE
  ↓
DATA
  ↓
OUTPUT / SINK
```

The primary review question is:

```text
WHO can use WHAT CAPABILITY
on WHICH RESOURCE
and send WHAT DATA to WHICH SINK
under WHICH CONDITIONS?
```

A private repository, encryption, MFA, a WAF, a proxy, or a PASS from a
scanner is not by itself a proof that protected data cannot cross an
unauthorized trust boundary.

---

## 4. Security invariants

These invariants are intended to outlive individual tools.

### SHIELD-I01 — No client master secret

No public/client component may hold a master secret or administrative
credential.

### SHIELD-I02 — No unrestricted data + unrestricted authority

No ordinary runtime workload should simultaneously have unrestricted protected
data access and unrestricted administrative authority.

### SHIELD-I03 — No single identity owns the entire blast radius

No single routine identity should automatically control source, production,
encryption keys, and independent recovery deletion.

### SHIELD-I04 — Authorization before retrieval

Authorization must be enforced before protected data is retrieved or exposed,
not merely after a model, query, or application has already received it.

### SHIELD-I05 — Bounded sinks

Protected data must not be able to reach arbitrary sinks. Network requests,
Git commits, pull requests, logs, build artifacts, browser output, model
output, email, webhooks, and similar channels are all potential sinks.

### SHIELD-I06 — Untrusted data cannot grant authority

Untrusted data from users, the web, files, emails, issues, retrieved documents,
tool results, or other external sources must not be able to grant itself
privileged authority.

### SHIELD-I07 — Minimum agent/tool capability

AI agents and automation receive only the minimum capabilities required for the
bounded task.

### SHIELD-I08 — Recovery isolation

Compromise of production must not automatically imply compromise or deletion of
independent recovery.

### SHIELD-I09 — Critical privilege is bounded

High-impact privilege should be short-lived, narrowly scoped, explicitly
elevated, or otherwise bounded by the platform's practical capabilities.

### SHIELD-I10 — High-value paths have evidence

Security claims for high-value data paths require evidence appropriate to the
claim.

### SHIELD-I11 — Tool PASS is never sufficient alone

A scanner PASS never substitutes for business authorization tests, real system
state, threat-model reasoning, or project-specific validation.

### SHIELD-I12 — Proprietary AI/RAG output is bounded

Projects containing proprietary knowledge should reduce systematic extraction
risk through scoped retrieval, bounded output, rate/behavior controls where
justified, and project-specific adversarial testing.

---

## 5. Core architectural rule: control != provider

A P2P Shield control defines:

- what security outcome is required;
- where it applies;
- what evidence is required;
- what constitutes PASS, FAIL, or BLOCKED;
- what failure mode is unacceptable.

A provider defines one concrete implementation of that control.

Example:

```yaml
control:
  id: SHIELD-SECRET-01
  objective: >-
    Repository source and history contain no exposed live credentials.
  profiles: [PRIVATE, VAULT]
  required_evidence:
    - working_tree_scan
    - git_history_scan
  pass_condition:
    confirmed_live_secret_count: 0
```

A current implementation may be:

```yaml
provider:
  control: SHIELD-SECRET-01
  name: gitleaks
  status: ACTIVE
```

A later implementation may be a different tool without changing the control.

---

## 6. Critical correction: providers with the same label are NOT automatically equivalent

This is a mandatory design safeguard.

Two tools can claim to implement `SECRET_SCAN`, `SAST`, `SCA`, `DAST`,
`AUTHZ`, `AI_REDTEAM`, or another capability while covering materially
different failure classes.

Therefore P2P Shield MUST NOT normalize providers into a simple boolean
interface such as:

```text
provider_passed=true
```

and then assume interchangeability.

Every qualified provider must carry enough semantics to explain what was
actually tested.

Minimum provider metadata:

```yaml
provider:
  control_id: SHIELD-SECRET-01
  name: example-provider
  version: x.y.z
  status: CANDIDATE
  coverage:
    - working_tree
    - git_history
  known_exclusions:
    - runtime_secret_store
  failure_mode: fail_closed
  last_reviewed: YYYY-MM-DD
```

A provider replacement is valid only if the replacement satisfies the required
control semantics and required coverage for the target profile/project.

---

## 7. Evidence contract

P2P Shield must normalize evidence without erasing its meaning.

Minimum evidence shape:

```yaml
evidence:
  control_id: SHIELD-SECRET-01
  provider: example-provider
  provider_version: x.y.z
  project_ref: <repo/ref/head>
  timestamp: <time>
  status: PASS|FAIL|BLOCKED
  scope:
    - working_tree
    - git_history
  findings:
    count: 0
  limitations:
    - runtime secret stores not assessed
  artifact_or_reference: <durable evidence reference>
```

Evidence must be scoped and fresh enough for the claim being made.

`OLD_PASS != CURRENT_PASS` when relevant project state, dependency state,
configuration, deployment, threat assumptions, or provider behavior has
changed materially.

P2P Shield should not invent a universal fixed evidence TTL. Freshness depends
on the control and project state.

---

## 8. Security profiles

Profiles define required outcomes, not fixed products.

### SHIELD-BASE

Use for public/demo projects with little or no protected user data.

Typical controls:

- secret protection;
- dependency vulnerability checks;
- source security checks proportional to the stack;
- CI/workflow safety where CI exists;
- basic authentication/authorization if private functions exist;
- deployment exposure checks;
- recovery appropriate to business value.

### SHIELD-PRIVATE

Use for projects such as Bazi, Logistics, Gia Pha, internal business tools, or
applications containing proprietary corpora or ordinary private user data.

Adds or strengthens:

- explicit asset map;
- authorization tests;
- data minimization;
- server-side data boundary;
- data-flow/sink review;
- stronger identity controls;
- scoped runtime credentials;
- audit evidence;
- protected backups and restore tests;
- AI/RAG security controls when applicable.

### SHIELD-VAULT

Use only for projects where compromise would create high legal, financial,
privacy, safety, or commercial impact.

Possible additions based on threat model:

- stronger key separation/KMS;
- field/object-level encryption where justified;
- more isolated recovery trust domain;
- stricter egress controls;
- stronger administrative step-up authentication;
- higher-assurance audit and restore evidence;
- separate privileged execution boundaries;
- confidential-computing or similar mechanisms only if the threat model and
  economics justify them.

VAULT is not "install every security product" mode.

---

## 9. Control families for the first Shield version

The initial control catalog should stay small.

### A. ASSET_AND_DATA

- asset classification;
- sensitive-data minimization;
- protected-data location;
- approved sinks;
- backup/recovery classification.

### B. IDENTITY_AND_AUTHORIZATION

- authentication appropriate to risk;
- deny-by-default authorization;
- object/resource ownership checks;
- administrative privilege boundaries;
- project-specific authorization evidence.

### C. SOURCE_AND_SECRETS

- repository secret protection;
- source security scanning where useful;
- no client-side master secret;
- protected configuration/secrets handling.

### D. DEPENDENCY_AND_SUPPLY_CHAIN

- dependency vulnerability checks;
- CI workflow checks;
- bounded CI permissions;
- immutable/pinned references where appropriate;
- scoped workload identity/OIDC trust if used.

### E. RUNTIME_AND_EGRESS

- least-privilege runtime identity;
- bounded network/service access where practical;
- no unnecessary administrative capability;
- sink-aware data-flow review.

### F. AI_AND_RAG

Applicable only when AI/RAG exists:

- retrieval authorization before model exposure;
- corpus provenance/approval;
- untrusted-data authority separation;
- prompt-injection/adversarial tests;
- extraction/data-exfiltration tests;
- bounded AI tools/capabilities.

### G. OBSERVABILITY_AND_RECOVERY

- security-relevant audit events;
- no secret/sensitive payloads in logs unless explicitly required and
  protected;
- independent backup path;
- restore evidence;
- incident containment/rotation path proportional to risk.

### H. ADVERSARIAL_VERIFICATION

- staging DAST where applicable;
- project-specific negative authorization tests;
- AI red-team where applicable;
- deeper pentest only when risk justifies it.

---

## 10. Project-specific controls are mandatory where business semantics matter

P2P Shield global providers cannot prove domain-specific authorization.

Example Bazi:

```text
user_A -> chart_A = ALLOW
user_A -> chart_B = DENY
anonymous -> chart_A = DENY
```

Example legal system:

```text
org_A -> org_A_private_case = ALLOW
org_A -> org_B_private_case = DENY
public_law_text -> public = ALLOW
```

These checks remain project-owned evidence.

A global scanner cannot replace them.

---

## 11. Provider lifecycle

Providers use a simple lifecycle:

```text
DISCOVERED
   ↓
CANDIDATE
   ↓
QUALIFIED
   ↓
ACTIVE
   ↓
DEPRECATED
   ↓
RETIRED
```

No automatic provider promotion solely because a new tool is popular, newer,
AI-powered, or has more GitHub stars.

A provider may remain ACTIVE while a candidate is evaluated.

---

## 12. Provider replacement gate

A proposed replacement must be evaluated against the SAME control contract and
the actual profile/project needs.

Minimum comparison dimensions:

1. required coverage;
2. true-positive detection on known fixtures where available;
3. false-positive burden;
4. known blind spots;
5. failure behavior (fail-open/fail-closed/unknown);
6. maintenance health;
7. supply-chain/security risk of the provider itself;
8. operational complexity;
9. runtime/resource cost when material;
10. evidence quality and reproducibility;
11. portability/integration cost;
12. rollback feasibility.

Decision rule:

```text
NEW_PROVIDER_PASS != DEFAULT_PROVIDER_PROMOTED
```

Promotion requires evidence that it is at least sufficiently equivalent for
the required semantics and is materially better overall, or that the current
provider is no longer acceptable.

Replacement must be reversible when practical.

---

## 13. No premature plugin framework

P2P Shield MUST NOT initially build a generic plugin framework, provider
registry service, central security daemon, new database, or dedicated security
platform.

Initial implementation should be simple files/config plus narrow adapters only
where a real second provider or migration creates demonstrated need.

Default rule:

```text
ONE_PROVIDER_FOR_A_CONTROL
    ↓
CONFIG_ONLY

SECOND_REAL_PROVIDER_OR_REAL_MIGRATION_NEED
    ↓
CONSIDER_THIN_ADAPTER
```

Do not invent a `UniversalSecurityProviderFactoryAdapterManager` merely to prove
that future replacement is theoretically possible.

---

## 14. Shield itself must not become a new single point of compromise

P2P Shield should primarily be a policy/control/evidence layer, not a privileged
runtime service sitting in the middle of every project request.

If future implementation proposes a central Shield service with broad access
to projects, secrets, deployment, logs, or production data, it must be treated
as a high-risk architecture change and separately threat-modeled.

Default preference:

```text
DISTRIBUTED_ENFORCEMENT
+
STANDARDIZED_CONTROL_AND_EVIDENCE
```

rather than:

```text
ONE_SUPER_PRIVILEGED_SHIELD_SERVICE
```

---

## 15. Control evolution and versioning

Provider replaceability is not enough. Controls themselves can become stale
when threats change.

Therefore controls are versioned when their semantics materially change.

Example:

```text
SHIELD-AI-03/v1
↓ threat evidence changes required semantics
SHIELD-AI-03/v2
```

Do not silently reinterpret an old PASS under a materially different control.

Security invariants should change rarely, but they are not metaphysically
immutable. A future threat or design lesson may justify revision through normal
P2P governance and evidence.

---

## 16. Current and target profiles

Each project may maintain a lightweight Current vs Target view:

```yaml
shield_profile: PRIVATE
current:
  secret_scan: gitleaks
  dependency_scan: osv-scanner
  authz: project-native

target:
  secret_scan: current
  dependency_scan: candidate-under-evaluation
  authz: current
```

This supports evolution without treating every new security release as an
emergency migration.

---

## 17. Composition rule: individual PASS does not imply system PASS

P2P Shield explicitly rejects the composition fallacy:

```text
SECRET_SCAN=PASS
SAST=PASS
SCA=PASS
AUTHN=PASS
```

does not imply:

```text
SYSTEM_SECURITY=PASS
```

The system verdict must additionally consider:

- business authorization;
- trust boundaries;
- combined capability graph;
- protected-data paths;
- production configuration;
- project-specific threat model;
- recovery path;
- relevant AI/RAG paths.

Security is a system property, not the sum of scanner badges.

---

## 18. Failure behavior

Critical controls should define what happens when the provider is unavailable,
misconfigured, unsupported, or produces indeterminate evidence.

Typical states:

```text
PASS
FAIL
BLOCKED
NOT_APPLICABLE
```

For a mandatory control, provider failure SHOULD NOT silently become PASS.

Where the safest behavior is to block promotion, use `BLOCKED` rather than
bypassing the control.

Risk-proportional emergency exceptions, if ever needed, must be explicit,
scoped, documented, and separately authorized.

---

## 19. Candidate implementation shape

Do not implement this entire structure at once.

Target repository shape when justified:

```text
shield/
  controls.yaml
  profiles/
    base.yaml
    private.yaml
    vault.yaml
  providers/
    mapping.yaml
  schemas/
    evidence.schema.json        # only when schema validation is justified
  fixtures/                     # only for controls with useful test fixtures

docs/p2p-development/
  P2P-SHIELD-PLAN.md
```

Project repositories should hold only the minimum project-specific overlay or
evidence hooks they actually need.

---

## 20. Proposed implementation sequence

### Slice 0 — plan only

This document.

Acceptance:

- architecture is understandable;
- no production behavior changes;
- no new framework/service/database exists;
- Owner can reject or revise the direction before implementation.

### Slice 1 — one control end-to-end

Implement one real control contract and one provider, preferably a low-risk,
high-value control such as repository secret scanning.

Acceptance:

```text
CONTROL_DEFINED
PROVIDER_EXECUTES
EVIDENCE_RECORDED
PASS_FAIL_BLOCKED_WORKS
NO_GENERIC_PLUGIN_FRAMEWORK
```

### Slice 2 — small BASE profile

Add only the minimum useful cross-project controls supported by actual P2P
projects.

Candidate areas:

- secrets;
- dependencies;
- CI workflow safety;
- narrow source checks.

### Slice 3 — PRIVATE vertical slice on real projects

Pilot on Bazi and VNLAW or another pair selected by Owner.

Add only controls needed by their real data and application architecture:

- asset/data classification;
- authorization evidence;
- server-side/private data boundary;
- backup/restore;
- AI/RAG controls where actually used.

### Slice 4 — first real provider replacement exercise

Only after a real alternative exists, evaluate one provider migration using the
replacement gate.

This is the point where a thin adapter may become justified.

### Slice 5 — VAULT only if a real high-impact project requires it

Do not prebuild enterprise controls without a real requirement.

---

## 21. Candidate provider examples, NOT constitutional dependencies

The following are examples to evaluate during implementation, not required
permanent choices:

```text
Secrets           -> Gitleaks / TruffleHog / future qualified provider
SAST              -> CodeQL / future qualified provider
Dependencies      -> OSV-Scanner / Trivy / future qualified provider
GitHub workflows  -> zizmor / future qualified provider
CI runtime/egress -> Harden-Runner or platform-native equivalent
Web/API DAST      -> ZAP / Nuclei / deeper bounded pentest
AI/RAG red-team   -> promptfoo / garak / PyRIT / future qualified provider
Deep staging test -> CyberStrikeAI when justified
Authorization     -> project-native first; policy engine only when complexity proves need
```

The provider list belongs in operations/profile data, not in Supreme Law.

---

## 22. Security verdict packet

A future Shield run may emit a compact packet such as:

```text
P2P_SHIELD_VERSION=<version>
PROFILE=BASE|PRIVATE|VAULT
PROJECT=<repo/ref/head>

ASSET_MAP=PASS|FAIL|BLOCKED|NA
SECRET_PROTECTION=PASS|FAIL|BLOCKED|NA
DEPENDENCY_SECURITY=PASS|FAIL|BLOCKED|NA
SOURCE_SECURITY=PASS|FAIL|BLOCKED|NA
CI_SECURITY=PASS|FAIL|BLOCKED|NA
AUTHN=PASS|FAIL|BLOCKED|NA
AUTHZ=PASS|FAIL|BLOCKED|NA
DATA_FLOW=PASS|FAIL|BLOCKED|NA
RECOVERY=PASS|FAIL|BLOCKED|NA
AI_RAG_SECURITY=PASS|FAIL|BLOCKED|NA
ADVERSARIAL_VERIFICATION=PASS|FAIL|BLOCKED|NA

SYSTEM_SECURITY_VERDICT=PASS|FAIL|BLOCKED
EVIDENCE=<durable references>
LIMITATIONS=<explicit scope limits>
```

The packet must not falsely imply that `PASS` means "unhackable".
It means the required Shield controls for the declared profile and scope have
sufficient current evidence.

---

## 23. Final red-team objections and resolution

### Objection A — Replaceability can become fake portability

If P2P reduces every provider to the same boolean, meaningful coverage
differences disappear.

Resolution:

- provider contract includes coverage, exclusions, version, failure mode, and
  limitations;
- replacement gate compares semantics, not labels.

### Objection B — Normalized evidence can create false assurance

A standardized PASS can hide that two providers assessed different things.

Resolution:

- evidence always carries scope and limitations;
- system verdict cannot infer claims broader than the evidence scope.

### Objection C — Stable controls can ossify old threat assumptions

A control contract written today can become wrong tomorrow.

Resolution:

- controls are versioned;
- Current/Target profiles support planned evolution;
- threat evidence may revise the catalog.

### Objection D — A central Shield can become the most dangerous system in P2P

A universal service holding all permissions would create a new catastrophic
blast radius.

Resolution:

- Shield defaults to distributed enforcement plus standardized controls and
  evidence;
- central privileged runtime is not part of v1.

### Objection E — Security tools themselves are supply-chain dependencies

A new provider can introduce its own compromise path.

Resolution:

- provider qualification includes maintenance, provenance, permissions,
  integration surface, and rollback;
- security tools receive minimum required permissions.

### Objection F — Security automation may create compliance theater

More scanners and dashboards can increase noise without reducing risk.

Resolution:

- measure controls proven, not tools installed;
- no provider is added without a distinct required outcome;
- stop when sufficient evidence exists.

### Objection G — Project semantics cannot be generalized away

Global Shield cannot know whether one Bazi chart, logistics shipment, family
record, or legal matter belongs to a particular user.

Resolution:

- project-specific authorization/data-flow tests remain mandatory where
  applicable;
- global controls request evidence, not domain ownership.

Final verdict:

```text
P2P_SHIELD_DIRECTION=ACCEPT_WITH_GUARDS
IMPLEMENTATION_STATUS=NOT_STARTED
PROMOTION_STATUS=UNPROMOTED
```

No unresolved architectural objection currently justifies abandoning the
control/provider/evidence separation. The main risk is overengineering the
abstraction before a second real provider or migration exists, so the first
implementation must remain a small vertical slice.

---

## 24. Anti-overengineering gate

Before each Shield implementation increment ask:

`Không bị over engineering chứ?`

1. Có cách đơn giản hơn đạt cùng mục tiêu không?
2. Bước này có tạo thêm thông tin, capability, hoặc tiến triển đáng kể không?
3. Nếu bỏ bước này, điều kiện thành công có thực sự bị thiếu không?
4. Chúng ta đang giải capability chính hay tối ưu hạ tầng phụ trước capability?
5. Có thể thu nhỏ thành vertical slice độc lập kiểm chứng nhỏ hơn không?

Interpret the questions directionally: YES on questions 1 and 5 is a
reduction signal, while NO may mean the current path is already minimal.
Questions 2–4 require YES to proceed; NO means reduce, remove, or defer.
Do not treat every literal negative answer as failure.

Explicitly deferred until evidence creates need:

- central Shield service;
- generic plugin marketplace;
- provider registry database;
- SIEM/SOC stack;
- Kubernetes/service mesh just for Shield;
- custom cryptography;
- dedicated Vault cluster by default;
- HSM/confidential computing by default;
- broad security data lake;
- permanent multi-agent security council.

---

## 25. Recommended first implementation goal

When implementation is approved, the first bounded goal should be:

```text
P2P_SHIELD_V0_1_SECRET_CONTROL_VERTICAL_SLICE
```

Scope:

1. define one control contract (`SHIELD-SECRET-01`);
2. map one existing provider;
3. execute against one safe P2P test repository/fixture;
4. emit scoped evidence with PASS/FAIL/BLOCKED;
5. prove that changing provider mapping does not require changing the control;
6. stop.

Do not build the broader Shield framework during this slice.

Only after this vertical slice proves useful should the next control family be
added.

---

## 26. Owner-facing interpretation

For a beginner Owner, P2P Shield should be understandable as:

```text
P2P decides WHAT must be protected.
A control says WHAT must be proven.
A provider/tool performs ONE way of proving or enforcing it.
Evidence says WHAT actually happened.
The project decides whether the required protection is sufficient.

If a better tool appears later:
compare -> test -> candidate -> qualify -> promote -> replace.

Do not rewrite the whole Shield.
```

That is the intended long-term design contract for P2P Shield.
