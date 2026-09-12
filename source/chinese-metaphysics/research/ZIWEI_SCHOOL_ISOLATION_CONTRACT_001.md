# Ziwei school isolation contract 001

TASK_ID=ZIWEI_SCHOOL_ISOLATION_CONTRACT_001  
DOMAIN=ZIWEI_DOUSHU  
STATUS=RESEARCH_PRODUCT_CONTRACT_ONLY  
Date: 2026-09-12

## Outcome and boundary

One website may contain many Chinese metaphysics domains and multiple Ziwei
schools/conventions. Every interpretation remains in its explicitly selected
school/source lane. No best combined school exists in this contract.

```text
DETERMINISTIC CHART FACTS
        ↓
EXPLICIT SCHOOL PROFILE
        ↓
ISOLATED SCHOOL INTERPRETER
        ↓
SCHOOL-TAGGED RESULT
```

“Deterministic” means reproducible under declared inputs and calculation settings,
not historically authoritative or predictively valid. Convention-dependent 四化
is not a school-neutral fact. Share a chart skeleton only where the chosen
calculation profiles actually establish compatibility; never assume all schools
share every placement, calendar boundary, or time convention.

## Minimum profile identity

All fields below are required. Unknown evidence must be explicit, not fabricated.
A research candidate may use `UNVERIFIED`/`NOT_CONFIGURED`; that does not authorize
interpretation when required calculation or method inputs are missing.

| Field | Minimum meaning |
|---|---|
| DOMAIN | `ZIWEI_DOUSHU`; do not inherit rules from another domain |
| SCHOOL_PROFILE_ID | Stable, versioned identity for this exact evidence/settings lane |
| DECLARED_SCHOOL | Verbatim declared label and who declares it; not inferred from repo name |
| SCHOOL_ATTRIBUTION | `UNVERIFIED` unless historical attribution has claim-specific evidence |
| CONVENTION_ID | Explicit versioned convention, including actual applicable 四化 rows; a 庚 variant alone is not a complete school |
| CALCULATION_ENGINE | Engine identity and immutable version/pin, or explicit external-chart origin |
| CALCULATION_PROFILE | Input/calendar/time-boundary/placement settings, transformation convention, required chart fields and reproducibility limits |
| SOURCE_OR_EDITION | Actual repo pin and named work/edition; distinguish declared book from directly inspected edition |
| SOURCE_LOCATOR | Claim-level pinned path/lines or verified edition/page; absent page proof stays absent |
| SOURCE_CLASS | Evidence quality, using the existing provenance ladder; not a credibility vote |
| PROVENANCE_STATUS | Repo verification, direct textual proof, supplement and attribution status separately |
| ENGINEERING_STATUS | What structure or behavior was actually inspected/tested |
| PREDICTIVE_STATUS | Independent empirical status; default `NOT_TESTED` |
| KNOWN_CONFLICTS | Conflicting rows, editions, terminology, calendar settings, missing inputs and unresolved attribution; explicit `NONE_KNOWN` only after scoped review |

Each applied rule/conclusion must carry the profile ID, rule/method identifier,
source locator, source class, provenance/method layer, and input/calculation
profile reference. A top-level school label alone is insufficient when the rules
have mixed source layers. A changed source, convention or material setting must
produce a distinguishable profile revision, not silently change past results.

Method layers are `DIRECT_CLAIMED_SOURCE`, `AUTHORIZED_SUPPLEMENT`,
`SPECIALIST_SECONDARY`, `MODERN_REPO_DERIVED`, `ENGINEERING_HEURISTIC`, `UNVERIFIED`.
They describe rule origin, separately from the P0–P5 source-quality ladder.
`DIRECT_CLAIMED_SOURCE` means an explicit textual claim, not independently proven
authenticity. `AUTHORIZED_SUPPLEMENT` requires positive authorization evidence;
a repository's “verified”, “standard”, A-grade, or multi-source agreement is not enough.

## Isolation invariants

1. Select an explicit profile before interpretation. Missing profile, missing
   required 四化, or incompatible chart/profile means pause that lane and request
   clarification. Never borrow another school's method to complete a result.
2. Keep inputs, derived transformations, rules and results bound to their profile.
   Configuration/state/results from one lane must not contaminate another.
3. A user's chart/table discrepancy is a visible conflict, not permission to
   overwrite their convention. Any profile change is explicit and requires a new
   labeled result. “Use the user's school” is not an untracked fallback.
4. Supplements remain visibly identified per rule. Same row does not prove same
   doctrine; same author does not prove same edition or source layer.
5. AI may explain a lane's sourced reasoning; it may not blend contradictory
   schools into an untraceable conclusion. Unsupported claims stay unsupported.

Explicitly forbidden:

```text
MASTER_SIHUA_TABLE
UNIVERSAL_ZIWEI_INTERPRETER
PROFILE=COMBINED_BEST
MAJORITY_VOTE
WINNER_LOGIC
AUTO_CONFLICT_RESOLVER
SILENT_SCHOOL_FALLBACK
AI_SYNTHESIS_WITHOUT_SOURCE_TAGS
```

For multiple requested schools, the only permitted comparison shape is:

```text
SCHOOL_A_RESULT
SOURCE_A
PROVENANCE_A

SCHOOL_B_RESULT
SOURCE_B
PROVENANCE_B

CONFLICTS
NO_WINNER_SELECTED
```

A result may be `INSUFFICIENT_INPUT_OR_EVIDENCE` independently of other lanes.
Agreement can be reported but never treated as a vote or proof of validity.

## Existing evidence retained, not rerun

- [School profile probe](iztro/SCHOOL_PROFILE_PROBE_001.md): same pinned iztro,
  input and construction with only convention changed preserved the skeleton,
  changed explicit 四化, and prevented profile contamination in that bounded test.
  This is not a test of a future interpreter.
- [庚 provenance](iztro/GENG_SIHUA_PROVENANCE_002.md): retain all observed variants
  A=陽武陰同, B=陽武同相, C=陽武同陰, D=陽武府同, E=陽武府相, with
  their separate source/edition conflicts. This list is an evidence index, not a
  master table or exhaustive school taxonomy.
- [Qintian audit](qintian-sihua/AUDIT_2026-09-12.md): declared school verified as a
  repo declaration only; 庚 A is supplemented, not direct Xu Quanren proof.
- Existing iztro, xu-quanren, Linden, wuandyA/ziwei and ziwei-chart lanes remain
  separate. No dossiers or upstreams are modified by this contract.

## Minimum website consequence and acceptance examples

```text
SCHOOL_PROFILE_REQUIRED_FOR_INTERPRETATION=YES
CROSS_SCHOOL_OUTPUT_MODE=SIDE_BY_SIDE_ONLY
SCHOOL_SOURCE_VISIBLE_TO_USER=YES
CONFLICT_VISIBLE_TO_USER=YES
DEFAULT_CONFLICT_WINNER=NONE
```

Documentation-level acceptance: an absent profile stops interpretation; a qintian
chart without required 四化 stops that lane; A versus any B/C/D/E result keeps
both tags and the disagreement; a supplemented 庚 A rule never displays “direct
Xu Quanren text verified”; selecting another profile never mutates an earlier
result. These are future acceptance requirements, not tests executed here.

## Không bị over engineering chứ?

1. Simpler sufficient path? One Markdown contract plus one repo audit.
2. Real information? Yes: explicit isolation and supplemented-source boundaries.
3. Omit it? Future multi-school Ziwei would lack this minimum isolation contract.
4. Method boundary or premature runtime? Method boundary only.
5. Smaller independently verifiable slice? Two documents suffice; no registry.
6. Master-engine drift? Explicitly forbidden; no runtime, API, database, router,
   plugin framework, frontend, ontology, resolver or agent council.

OE_GATE=PASS — one contract + one repo audit + no runtime.
