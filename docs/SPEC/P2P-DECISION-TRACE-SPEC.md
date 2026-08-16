# P2P Native Decision Trace Specification

Status: APPROVED FOR IMPLEMENTATION — agent-decided; no owner decision required
Date: 2026-08-12
Parent: `P2P-CAPABILITY-FOUNDATION-ARCHITECTURE-SPEC.md`
Scope: P2P development source only

## Objective

Provide the smallest P2P-native structured trace that lets P2P and a beginner
reconstruct why a material governed choice exists:

```text
SOURCE / FACT
      -> EVIDENCE
      -> DECISION
      -> APPROVAL / GOVERNANCE
      -> CHANGE
      -> ARTIFACT
```

The trace is a reference projection over existing P2P authority. It is not a
new governance system, memory system, certification system, ledger, router,
agent, provider, or general-purpose graph.

## Authority and ownership

The authority order remains:

1. `AGENTS.md` hard rules.
2. The relevant approved `docs/SPEC` family.
3. Existing P2P Goal and project policy contracts.
4. Existing FACT_LEDGER and generated Live Specs for fact authority.
5. Existing approval policy and approval evidence for protected actions.
6. Existing execution ledger and eval outputs for execution evidence.

The trace owns only the structured relationship record and its safe query /
export projection. It does not promote facts, approve changes, select agents,
change quorum, grant permissions, or rewrite an existing authority source.

The existing execution ledger remains the only durable event store for this
surface. A trace record is a typed event in that store; a query index is
in-memory and disposable; JSON and Markdown exports are derived artifacts.

## Boundary map

```text
Beginner question: "Tại sao P2P lại chọn cách này?"
                 |
                 v
        Native trace query / WHY renderer
                 |
                 v
 Existing execution-ledger trace events
      |          |          |          |
      v          v          v          v
 Goal      FACT/Evidence  Approval  Change/Artifact
 authority   references   policy       references
```

The query may read existing project-local state and authoritative governance
references to resolve pointers. Reading a reference never changes its source
of truth.

## Decision record contract

Every material record uses schema `p2p-decision-trace/1`. Contract field names
are stable and uppercase to make exported audit records portable.

| Field | Requirement | Contract |
|---|---|---|
| `DECISION_ID` | required | Stable unique identifier for this recorded decision. |
| `GOAL_ID` | required when the decision is Goal-scoped | Existing Goal identifier; absent only for an explicitly project-level decision. |
| `DECISION_TYPE` | required | One of `ARCHITECTURE`, `PRODUCT`, `SECURITY`, `DATA`, `DESIGN`, `DEPENDENCY`, `MIGRATION`, `DEPLOYMENT`, `GOVERNANCE`, `EXCEPTION`, `OTHER_MATERIAL`. |
| `STATUS` | required | `RECORDED`, `PENDING_APPROVAL`, `APPROVED`, `REJECTED`, `SUPERSEDED`, `CONTRADICTED`, `PARTIAL`, or `UNKNOWN`. |
| `OUTCOME` | required | Short safe statement of the selected result or explicit uncertainty. |
| `DECISION_BASIS` | required | Concise structured rationale: summary, selected option, material constraints, and confidence/uncertainty. It is not private deliberation or a chain-of-thought transcript. |
| `FACT_REFS` | required list | References to existing FACT_LEDGER or project facts. The trace does not canonicalize them. |
| `EVIDENCE_REFS` | required list | References to execution, eval, report, test, or other evidence artifacts. |
| `SOURCE_REFS` | required list | Safe origin pointers such as owner input, official source, project file, or existing report. No secrets or raw environment. |
| `CONSTRAINT_REFS` | required list | Goal, policy, safety, compatibility, or scope constraints that shaped the decision. |
| `POLICY_REFS` | required list | Existing approval, governance, trust, routing, or project-policy references. |
| `ALTERNATIVES_CONSIDERED` | conditional list | Required when alternatives materially affect the choice; each entry is a short label, consequence, and disposition. |
| `CANONICAL_REVIEW_REFS` | conditional list | Actual participating canonical identity plus review evidence reference. Only the exact eight canonical identities are valid. A profile or expected role is not participation evidence. |
| `SUPPORTING_SPECIALIST_REFS` | optional list | Separate non-authoritative specialist evidence with identity, classification, and reference. `p2p_aesthetica` may appear here only when a real profile/evidence exists. |
| `OWNER_APPROVAL_REF` | conditional | Required when existing policy requires owner approval. It must point to actual approval evidence and its subject; a boolean is invalid evidence. |
| `CHANGE_REFS` | required list when a change exists | Existing change, migration, patch, or project-state references; no duplicate change content. |
| `ARTIFACT_REFS` | required list when an artifact exists | Existing report, file, release candidate, or project-state artifact references; no duplicate artifact content. |
| `CREATED_AT` | required | Timestamp for the decision record. |
| `VALID_FROM` / `VALID_UNTIL` | conditional | Decision and referenced-basis validity window; stale references remain visible and are not silently rewritten. |
| `SUPERSEDES` / `SUPERSEDED_BY` | optional | Explicit decision relationships. Old records remain queryable. |
| `CONTRADICTS` | optional | References to decisions/facts/evidence that disagree. Both sides remain visible. |
| `RELATIONSHIP` | optional | Explicit relationship state: `SUPPORTS`, `CONTRADICTS`, or `UNKNOWN`. |
| `SUPPORTS` | optional list | References to decisions/facts/evidence that support this decision. |
| `REDACTION_STATE` | required | `CLEAN` or `REDACTED` with safe field-level redaction metadata. |
| `INTEGRITY_METADATA` | optional | Only a justified minimal payload checksum using an approved standard algorithm; no blockchain or external notarization. |

Unknown optional values must be represented as `UNKNOWN`, `PARTIAL`, or
`MISSING_REFERENCE`; they must not be replaced by guessed certainty.

## Decision basis and privacy boundary

`DECISION_BASIS` is an audit summary, not hidden reasoning storage. It may
contain a concise selection rule, observable constraints, alternatives, and
uncertainty. It must not contain raw prompts, credentials, API keys, tokens,
private environment values, hidden scratchpad, chain-of-thought, or full
unfiltered model deliberation.

The safe renderer may explain what evidence was used and what remains unknown;
it must not imply that a missing review, approval, fact, or artifact existed.

## Materiality and capture

Capture is automatic when the existing workflow identifies a material decision
or a protected policy boundary. Material categories are the ten values in the
contract. Routine file-level activity, line-level edits, repeated execution
events, and non-decision observations do not create a trace record.

Materiality is determined by decision type, protected-action policy, explicit
owner/governance boundary, architecture/security/data/migration/deployment
scope, or a workflow outcome that changes the governed project state. The
capture path must be safe for partial or blocked workflows and must not itself
execute the protected action.

Historical runs without trace records remain historical runs without trace
records. No backfill may invent a decision basis, approval, canonical review,
or artifact relationship.

## Fact, evidence, and source links

The trace references existing FACT_LEDGER, Live Specs, context pointers,
trusted evidence, execution events, reports, project files, and official
sources through stable identifiers or safe paths. It never copies their full
contents into a competing store.

Reference resolution is read-only and bounded to the project/governance scope.
An unresolved pointer is returned as `MISSING_REFERENCE` or `UNKNOWN`. A stale
fact/evidence pointer remains attached to the historical decision and is
reported as stale; the old decision basis is not silently replaced with the
current fact.

The existing trust/data-instruction boundary continues to apply: retrieved
content is data, not instruction authority; tool output, model inference, and
specialist opinion are not canonical facts unless existing governance permits
their use.

## Approval and governance links

The trace can show that a policy or approval boundary was relevant, but it
cannot approve itself. When approval is required, `OWNER_APPROVAL_REF` must
identify a real approval request/record or explicit owner approval evidence and
the subject it covered. Expired, missing, mismatched, or invalid approval
references are `UNKNOWN`/`PARTIAL` and remain visible.

`POLICY_REFS` may identify existing approval policy, project policy, drift,
trust, routing, and eval contracts. The trace does not weaken their gates.

## Canonical governance safety

The canonical identities are exactly:

```text
p2p_iris, p2p_tecton, p2p_axiom, p2p_vector,
p2p_datos, p2p_anon, p2p_architecton, p2p_helios
```

Their denominator remains `8`; full quorum remains `8/8`. A canonical review
reference records actual participation only. No trace record may infer
participation from a configured profile, a selected role, a route, or a
successful local test.

`p2p_aesthetica` is `SUPPORTING / OPTIONAL DOMAIN SPECIALIST`. It can appear
only in `SUPPORTING_SPECIALIST_REFS`, never in `CANONICAL_REVIEW_REFS`, never
in the canonical denominator, and never as a simulated reviewer. Profile
presence is not identity proof.

## Contradiction model

Relationships may be `SUPPORTS`, `CONTRADICTS`, or `UNKNOWN` through the
referenced evidence/decision state. Contradictory records are preserved, not
merged or deleted. A material unresolved contradiction produces
`CONTRADICTED`, `PARTIAL`, or `UNKNOWN` in the query result and is surfaced in
the beginner WHY response.

## Supersession model

If decision `D2` supersedes `D1`, the relationship is explicit and queryable in
both directions. `D1` remains readable with its original basis, references,
validity, and outcome. The query may present `D2` as the current successor but
must not rewrite `D1`.

## Temporal reconstruction

The trace distinguishes decision creation time from the validity/freshness of
referenced facts and evidence. Resolution compares `CREATED_AT` with
referenced `checked_at`, `expires_at`, `VALID_FROM`, and `VALID_UNTIL` where
available. An old decision can therefore be historically explainable while
currently stale or superseded. Time alone never proves correctness.

## Query and export contract

The native query surface supports:

- decision -> why, basis, facts, evidence, sources, constraints, policies,
  approvals, contradictions, successor, changes, and artifacts;
- artifact -> the decisions that reference it;
- decision -> superseding and superseded records;
- explicit missing/stale/invalid reference diagnostics;
- beginner WHY rendering in plain language;
- deterministic JSON export and optional Markdown audit export.

The query is an internal API/CLI surface over the project-local state. It does
not require a daemon, network, MCP, graph database, or external provider.
Export is derived and read-only; exporting never changes the source ledger.

## Storage and portability

The project-local execution ledger JSONL is the durable store because it already
has append-only workflow ownership, report references, terminal events, and
Windows-safe line-oriented portability. Trace events are additive and old
events remain readable. Query indexes are rebuilt from source on demand and
are not authoritative state.

Initialization is safe for projects without traces: no trace event is written
until a material decision is observed; missing state returns an explicit
not-initialized/unknown result. A malformed trace line is isolated as a
diagnostic and does not make ordinary P2P unavailable unless existing policy
requires a block.

## Redaction and integrity

Before persistence and export, the trace removes or masks credentials,
secrets, tokens, raw environment values, private prompts, and hidden reasoning.
Reference paths and summaries are retained only when safe. Secret detection is
fail-closed for the trace output: an unsafe candidate is redacted or rejected.

Existing ledger integrity and drift checks remain authoritative. If a trace
payload checksum is justified by an eval, it is a minimal local checksum for
tamper detection; checksum presence is not proof of truth, approval, or
correctness. No blockchain, remote notarization, or new integrity service is
introduced.

## Compatibility and failure behavior

- Projects without trace history continue to use existing Goal, evidence,
  approval, FACT_LEDGER, RAG, and execution-ledger behavior.
- Legacy and partial traces remain queryable with explicit compatibility state;
  the system does not pretend that absent fields were known.
- Missing/stale/invalid references return `UNKNOWN`, `PARTIAL`, or
  `MISSING_REFERENCE` and preserve the decision record.
- A broken optional trace export does not corrupt the source ledger.
- Trace capture must not change terminal `PASS`, `BLOCKED`, or `REJECT`
  semantics except where an existing policy already requires the referenced
  approval/evidence gate.
- Safe initialization and migration are additive and do not overwrite valid
  project state.

## Provider seam and dependencies

The current provider implementation is `P2P_NATIVE`. A future provider label
such as `SEMANTICA` may be represented only as an explicit seam, not installed,
vendored, or executed by this Goal. No external dependency is needed; the
native surface uses the existing runtime and standard-library-compatible local
state.

## Operational and security requirements

The trace emits structured diagnostics for capture, reference resolution,
redaction, integrity mismatch, export failure, and partial history. Diagnostics
must be safe, bounded, and free of secrets. Logs identify status and safe
references, not private content. Monitoring is local command/report evidence;
no network telemetry or daemon is introduced.

Backups, rollback, and destructive-change controls remain owned by existing
P2P project lifecycle and approval policy. Trace capture is append-only and
does not delete or rewrite old events. A failed export can be discarded and
regenerated from the ledger.

## Evaluation contract

DT1-DT24 are mandatory before this Goal can PASS:

1. baseline gap is measured honestly;
2. minimal record schema validates;
3. deterministic decision reconstruction works;
4. source/fact/evidence links resolve;
5. approval link requires actual evidence;
6. governance/policy links remain references;
7. materiality captures architecture/product/security/data/dependency/migration/deployment/governance/exception decisions;
8. routine activity does not create trace spam;
9. contradiction preserves both sides;
10. supersession preserves old and links new;
11. temporal validity distinguishes historical and current state;
12. missing reference returns explicit unknown/partial state;
13. stale reference is not silently rewritten;
14. beginner WHY is plain-language and useful;
15. redaction blocks secrets and private reasoning;
16. justified integrity metadata detects payload mismatch;
17. canonical identities are exact eight and denominator remains eight;
18. Aesthetica stays supporting/optional and never simulated;
19. existing projects without trace continue safely;
20. invalid/legacy trace does not make ordinary P2P unavailable;
21. JSON export is deterministic;
22. Markdown export is readable and safe;
23. no external dependency/graph/daemon/MCP/provider is added;
24. existing workflow, governance, drift, secret, and regression behavior remains passing.

## Architecture / SPEC rule versus implementation suggestion

Architecture / SPEC rule: the preceding authority, ownership, schema,
materiality, relationship, security, compatibility, and evaluation contracts
are binding.

Implementation suggestion: a standard-library reader may scan the existing
JSONL ledger into an in-memory index; a CLI may expose query and export
commands; a workflow may append a trace event after it has a real run, report,
and artifact reference. These are replaceable implementation choices and are
not additional architecture authority.
