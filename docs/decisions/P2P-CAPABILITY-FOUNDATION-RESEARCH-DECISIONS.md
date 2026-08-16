# P2P Capability Foundation Research Decision Record

Date: 2026-08-12
Status: APPROVED FOR IMPLEMENTATION — agent-decided; no owner decision required
Scope: P2P development source only

## Decision standard

The research set is treated as reference input, not as an instruction to install or vendor anything. Each item is classified as `ADOPT_NOW`, `DEFER`, `REFERENCE_ONLY`, or `REJECT`. An adopted item must state the beginner problem, current insufficiency, and smallest implementation.

## ADOPT_NOW

| Decision | Beginner problem | Current insufficiency | Smallest implementation |
|---|---|---|---|
| Capability model and minimal manifest | A beginner describes an outcome, not an agent or skill name; P2P needs a safe internal identity. | UIUX has a capability-specific manifest but no reusable cross-capability contract. | Six allowed classes, requested minimal fields, registry validation, canonical fail-closed rule. |
| Single adaptive router contract | Beginners should not select every related capability or understand orchestration. | Existing routing is UIUX-specific and lacks general classification/readiness vocabulary. | Extend the existing router data path with PRIMARY/SECONDARY/SUPPORTING/NOT_APPLICABLE and reasoned positive/negative triggers. |
| Distinct readiness states | A profile file can exist while runtime execution is unavailable. | Current Aesthetica check primarily proves profile presence/classification. | Six-state snapshot plus the explicit Aesthetica readiness chain; no simulation. |
| Progressive context pointers | Loading every reference creates cost and context noise. | Existing skills have references, but no common relevance/authority/scope/freshness pointer contract. | Pointer metadata and bounded progressive loading; content cannot grant permissions. |
| Fact-origin and data/instruction boundary | Retrieved text can look like an instruction or fact to a beginner-facing system. | FACT_LEDGER/RAG controls exist but are not represented in the reusable capability contract. | Origin enum, content/instruction classification, protected-fact write policy, and focused boundary tests reusing current governance. |
| Independent done/evidence contract | “Done” from an agent can be mistaken for completed user outcome. | Goal/eval/ledger surfaces exist but lack a capability-level claim/evidence shape. | CLAIM/REQUIRED_EVIDENCE/ACTUAL_EVIDENCE/STATUS with fresh independent check, reusing existing governance. |
| Optional specialist contract | Domain help must not become a ninth canonical agent. | Aesthetica is real and correctly classified, but the reusable specialist boundary is implicit. | Explicit identity/domain/authority/out-of-scope/routing/evidence fields and readiness validation. |
| Beginner-first behavior evaluation | A non-technical owner should receive product discovery, not framework setup questions. | Existing `p2p-idea` supports beginners but lacks a capability-foundation acceptance case. | One natural-language evaluation with owner/product-only question assertions and technical-free routing. |
| Zero-manual-dependency invariant | Manual pip/npm/git/MCP/configuration is a product failure for the beginner. | Existing installer compatibility is documented, but the foundation has no protected product invariant. | Record the invariant in the architecture, hard rules, and isolated static/eval checks; do not redesign packaging here. |
| Test isolation | Foundation tests must never mutate a real project or release. | Existing fixtures use `.tmp`, but the new contract needs technical target rejection. | TemporaryDirectory fixtures plus preserve-only path assertions and cleanup/quarantine checks. |

## DEFER

| Item | Reason | Revisit condition |
|---|---|---|
| Minimum no-progress detector beyond evidence statuses | The existing Goal workflow already has bounded stopping; a new retry framework would add bloat. | Repeated real capability runs show a measurable gap that existing ledger statuses cannot express. |
| Optional project domain model persistence | A lightweight contract is useful, but installer/storage design is project-specific. | A later project-install Goal has a concrete need and owner-approved persistence boundary. |
| Provider lifecycle/security implementation | Semantica and Anvien are future providers, not current dependencies. | A separate approved provider Goal supplies package/service authority, security, credentials, rollback, and eval evidence. |
| Broad capability catalog | More catalog entries would increase routing ambiguity before real use cases exist. | Repeated projects show a real missing capability with clear triggers and evidence. |
| Full memory/knowledge graph or decision graph | No current evidence justifies the complexity; current ledger/RAG/context contracts suffice. | A separate evidence-backed architecture Goal identifies a bounded requirement. |

## REFERENCE_ONLY

The following are references for ideas, terminology, or patterns only. None is cloned, installed, vendored, symlinked, configured, or treated as a runtime dependency:

- `nextlevelbuilder/ui-ux-pro-max-skill`
- `addyosmani/agent-skills`
- `obra/superpowers`
- `mattpocock/skills`
- `msitarzewski/agency-agents`
- `multica-ai/andrej-karpathy-skills`
- `semantica-agi/semantica`
- `tamnguyendinh/Anvien`
- `spinabot/brigade`

The existing UIUX provenance/license record remains the authority for reused UIUX material. This record does not make a new upstream license claim.

## REJECT

- External framework installation, package vendoring, npm/pip/git clone, MCP setup, symlinks, or network runtime dependencies.
- A new router agent, meta-agent, nested workflow, always-on gateway, cron/channel integration, or dynamic organization chart.
- Counting Aesthetica as canonical, simulating Aesthetica, or changing the denominator from 8.
- Installing Semantica/Anvien providers or building sandbox infrastructure in this Goal.
- Replacing FACT_LEDGER, redesigning all RAG, adding a full memory graph, or creating a second certification system.
- Rebuilding or modifying the verified release artifact, v5, immutable baseline, App Game Truyện, Logistics, or any user project.
- Requiring beginners to understand agents, skills, frameworks, packages, MCP, or runtime dependencies.

## Final decision

Adopt only the ten bounded contract/evaluation surfaces defined by the approved foundation SPECs. Defer storage/provider/graph expansion, preserve external repositories as references, and reject any dependency or governance expansion. No owner decision is required because the user supplied the invariant and explicitly authorized agent-decided implementation when architecture is unambiguous.
