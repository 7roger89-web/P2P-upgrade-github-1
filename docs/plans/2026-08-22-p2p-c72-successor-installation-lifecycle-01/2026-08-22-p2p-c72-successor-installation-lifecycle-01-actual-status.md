# P2P C72 Successor Installation Lifecycle 01 Actual Status

Title: P2P C72 Successor Installation Lifecycle 01  
Date: 2026-08-22  
Status: PASS_WITH_DISCLOSURES / P2P_INSTALLATION_LIFECYCLE_SUCCESSOR_CANDIDATE_VERIFIED

Companion plan: `docs/plans/2026-08-22-p2p-c72-successor-installation-lifecycle-01/2026-08-22-p2p-c72-successor-installation-lifecycle-01-plan.md`  
Companion evidence: `docs/plans/2026-08-22-p2p-c72-successor-installation-lifecycle-01/2026-08-22-p2p-c72-successor-installation-lifecycle-01-evidence.md`  
Companion benchmark: `docs/plans/2026-08-22-p2p-c72-successor-installation-lifecycle-01/2026-08-22-p2p-c72-successor-installation-lifecycle-01-benchmark.md`

## Purpose

Record the real state of the clean canonical-reconciliation lineage before implementation. This file is a living status record and must be refreshed after every implementation slice.

## Scope

Target scope:

- canonical repaired lineage and `.72` preservation;
- project pin contract and normal packaged producer;
- project-eval lifecycle;
- installer/adoption/Doctor/MAP-BEFORE-WORK sibling surfaces;
- derived governance, packaging, seal, fresh gate, and branch delivery.

Out of scope:

- Manus C43 branch and Controlled Execution Hardening;
- AERG, Large Goal, new framework/router;
- official promotion, main merge, deployment;
- authoritative Game Truyện/Gia Phả/Logistics mutation or installation.

## Relationship / Impact Evidence

Anvien graph refresh completed in this worktree: 36,412 nodes, 42,097 relationships, 0 parse failures, stale=false. The checkout's initial tracked-file changes were Windows line-ending noise only; this disposable worktree was normalized and is now clean apart from the four untracked plan files.

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|---|---|---:|---|---|
| `install.ps1` / `install.sh` | `E0-P0A-IMPACT1` | 0 direct graph symbols; entrypoint callers inspected mechanically | package install entrypoints | high scope warning; fresh package proof required later |
| `scripts/p2p_safe_installer.py` | `E0-P0A-IMPACT1` | 38 symbols; 3 flows; high risk | source pin producer candidate | high scope warning |
| `scripts/p2p_install_release.py` | `E0-P0A-IMPACT1` | 84 symbols; 11 flows; high risk | legacy release/adoption candidate, no current pin writer | preserve as legacy input |
| `.p2p/system/p2p_capabilities/project_context.py` | `E0-P0A-IMPACT1` | source inspected; ignored by Anvien file-detail, runtime reader confirmed | pin reader and context gate | fail-closed reader must bind canonical validator |
| `scripts/p2p_gate.py` | `E0-P0A-IMPACT1` | 52 symbols; 1 flow; high risk | drift/eval/approval technical prepare | add pin + strict Doctor technical gates |
| `scripts/p2p_governance.py` | `E0-P0A-IMPACT1` | 113 symbols; 16 flows; high risk | current derived governance generator | preserve historical records; regenerate derived state only |
| `scripts/package_release.py` | `E0-P0A-IMPACT1` | 92 symbols; 7 flows; high risk | distribution include/exclude contract | add only required producer/context surfaces |
| `.72` artifact | `E0-P0A-SUBJECT1` | SHA `70613080d2ddbb92a52d2d79186e125439ec7f5ba8a6fa87bda9208d1b39d872`; 491 members; 2,899,774 bytes | immutable historical candidate | do-not-touch |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|---|---|---|---|---:|---|---|
| Canonical lineage | branch created from `origin/codex/p2p-canonical-lineage-repair-01` at `4ce6a85f5991b6d6c464fb4b59e177114698947e` | clean successor source base | verified | source unchanged before P1 | `E0-P0A-REF1`, `E0-P0A-IMPACT1` | preserve and inspect |
| Official authority | `origin/main` governance says `.19`, SHA `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8` | unchanged `.19`/SHA | verified | 1 authority record | `E0-P0A-REF1` | preserve-only |
| `.72` candidate | immutable SHA known | no byte/remint change | verified preserve-only | 491 members | `E0-P0A-SUBJECT1` | do-not-touch |
| Project pin schema | lifecycle doc requires `.p2p/project-pin.json`; source safe installer defines `p2p-project-pin/1` but is not packaged | one producer/validator using that schema | partial, contract recovered | 1 current writer plus fixture writers | `E0-P0A-CONTRACT1` | P1-A |
| Project pin producer | source `p2p_safe_installer.py` creates a pin; `.72` omitted the producer and entrypoint call | packaged normal lifecycle producer | missing/unbound in `.72` | 1 source candidate | `E0-P0A-CONTRACT1` | P1-A |
| Pin validation/readers | `project_context.py` trusts only two fields; tests hand-write pins | canonical validator bound to context/Doctor/gate | partial | 3 consumer families | `E0-P0A-CONTRACT1` | P1-B after P1-A |
| Project eval lifecycle | installer creates no `.p2p/evals/suite.json`; Doctor warns, `p2p_gate prepare` fails closed | classify as project-owned setup and prove normal setup | project-owned, not installer-created | 2 gates | `E0-P0A-CONTRACT1` | P2-A classification |
| Doctor/install | `.72` package install Doctor passed but no pin was produced | package and strict Doctor HEALTHY after normal pin | partial | install + Doctor + gate | `E0-P0A-CONTRACT1` | producer first |
| Governance derived state | `.72` review recorded drift failures | successor-bound current drift PASS | pending source changes | 1 generator + derived locks | `E0-P0A-CONTRACT1` | regenerate after source freeze |
| Distribution contract | builder excludes producer and Project Context surfaces from runtime | producer/context surfaces included without repository dump | partial | package include rules | `E0-P0A-CONTRACT1` | P3-A |
| Manus C43 lane | separate branch explicitly excluded | zero imported material | correct/preserve-only | pending | `E0-P0A-REF1` | do not touch |
| AERG | planned, not part of scope | accepted planned/not implemented | correct/preserve-only | pending | `E0-P0A-REF1` | do not touch |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---|---|---|---|---|---|---|
| R0 | 2026-08-22 | new branch `codex/p2p-c72-successor-installation-lifecycle-01` at `4ce6a85f5991b6d6c464fb4b59e177114698947e` | initial successor scope | lineage/base correct; pin producer missing from `.72` inherited | `E0-P0A-REF1` | recover contracts before edits |
| R1 | 2026-08-22 | same branch after Anvien refresh and mechanical contract recovery | P0 evidence closure | EOL-only checkout noise normalized; `.19` and `.72` independently rechecked; `.73` is the smallest unused immediate successor candidate | `E0-P0A-REF1`, `E0-P0A-SUBJECT1`, `E0-P0A-CONTRACT1`, `E0-P0A-IMPACT1`, `E0-P0A-VERSION1` | proceed to P1 minimal implementation |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|---|---|---|---|---|---|---|
| `scripts/p2p_safe_installer.py` | `governance/project-adoption-lifecycle.md` | producer/contract | P1-A | inspect then edit minimally | `E0-P0A-CONTRACT1` | canonical schema only |
| `scripts/p2p_install_release.py` | `install.ps1`, `install.sh` | lifecycle/entrypoint | P1-A | inspect then edit minimally | `E0-P0A-CONTRACT1` | packaged distribution required |
| `project_context.py` | MAP-BEFORE-WORK readers | validation/consumer | P1-B | inspect/edit only if required | `E0-P0A-CONTRACT1` | fail closed |
| `scripts/p2p_eval.py` | `governance/project-eval.template.json` | eval producer/validator | P2-A | inspect then edit only if contract requires | `E0-P0A-CONTRACT1` | no synthetic suite |
| `scripts/package_release.py` | package manifests/tests | distribution contract | P3-A | edit include rules only as required | `E0-P0A-CONTRACT1` | no repository dump |
| `governance/live-specs.json` and locks | FACT_LEDGER/governance commands | generated current state | P2-B | regenerate | `E0-P0A-CONTRACT1` | no historical rewrite |
| `.72` ZIP | seal/release reports | immutable candidate | all | do-not-touch | `E0-P0A-SUBJECT1` | byte identity fixed |

## Detailed Findings

### Canonical lineage and `.72`

Current state: new successor branch is based on remote canonical-reconciliation head `4ce6a85f5991b6d6c464fb4b59e177114698947e`; `.72` is inherited and must remain immutable.

Required state:

```text
C72_BYTES_CHANGED = FALSE
C72_REMINTED = FALSE
SUCCESSOR_BRANCH_BASE = origin/codex/p2p-canonical-lineage-repair-01
```

Evidence:

- `E0-P0A-REF1`: fresh fetch and new branch creation.
- `E0-P0A-SUBJECT1`: fresh `.72` hash/member inspection pending.

Relationship and impact:

- Related file count: 491 archive members; source graph count pending.
- Relationship summary: immutable candidate and source-bound release evidence.
- Impact note: preserve-only.

Classification: `correct / preserve-only`.

Allowed next action: inspect and build a new version only.

Forbidden next action: modify/remint/overwrite `.72` or merge main.

### Project pin lifecycle

Current state: `.72` failed because its packaged distribution did not provide a normal pin writer; successor will package the existing `p2p-project-pin/1` contract through one shared runtime producer and call it from both supported install entrypoints. The source-only safe installer will delegate to the same producer; no second pin schema will be introduced.

Required state:

```text
PROJECT_PIN_PRODUCER = packaged normal lifecycle
PROJECT_PIN_SCHEMA = existing canonical schema
FAIL_CLOSED = TRUE
```

Evidence: `E0-P0A-CONTRACT1` pending mechanical reads.

Classification: `missing/unbound`.

Allowed next action: inspect all producers/readers, then edit only the minimal invariant family.

Forbidden next action: handwritten pin, test-injected pin, new competing schema, or source-only proof.

### Project eval lifecycle

Current state: `.72` included an eval template/helper but fresh installation lacked a project suite. The repository contract makes the project eval suite project-owned: Doctor warns when it is absent, while `p2p_gate.py prepare` correctly fails closed. The successor will document and exercise normal project setup; it will not manufacture a synthetic suite inside the installer.

Required state: `PROJECT_EVAL_NORMAL_LIFECYCLE = VERIFIED`.

Evidence: `E0-P0A-CONTRACT1` pending.

Classification: `partial/unknown`.

Allowed next action: classify project-owned versus distribution/adoption-initialized and follow only repository-defined setup.

Forbidden next action: arbitrary synthetic eval suite or hidden source-repo dependency.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|---|---|---|
| P1-A | producer is missing from `.72`, schema/creation/update semantics not yet freshly recovered | keep P1-A; inspect exact contract before editing |
| P1-B | fail-closed readers exist but sibling coverage not yet proven | keep P1-B after P1-A |
| P2-A | eval suite absence is known; ownership unresolved | classify before any eval code change |
| P2-B | prior governance drift existed; successor-bound source not yet changed | defer until source freeze |
| P3-A/P3-B | no version selected or candidate minted | defer until all source/gates pass |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a provisional status.
- [x] Each status has evidence IDs or explicitly pending P0 evidence.
- [x] Correct parts are marked preserve-only.
- [x] Partial/missing/unbound parts have exact next actions.
- [x] Blockers and forbidden actions are recorded.
- [x] Status Refresh Log has an R0 baseline row.
- [x] Fresh source/contract/Anvien evidence complete.
- [x] P0 final decision updated after fresh commands.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [ ] P0 complete. Next phase can proceed unchanged.
- [ ] P0 complete. Next phase status, next action, or work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

P0 is closed. Fresh reads establish one existing pin schema (`p2p-project-pin/1`), a source-only producer omitted from `.72`, project-owned eval initialization, and the exact package/runtime surfaces that must be added. The Anvien graph is fresh and the affected files have high-scope warnings recorded. The smallest unused immediate successor is `.73`; this is a candidate identity only and does not change official `.19`.

## Final Status Refresh — R2

Fresh remote-derived evidence supersedes the provisional pending labels above:

| Area | Final state | Evidence |
|---|---|---|
| Canonical authority | `origin/main`; official `.19` and SHA unchanged | `E0-CLOSE-AUTHORITY1` |
| Historical `.72` | exact bytes preserved; no remint | `E0-CLOSE-HISTORY1` |
| Successor identity | `.73`, one candidate only, unpromoted | `E3-CLOSE-ARTIFACT1` |
| Pin producer | one packaged canonical producer, schema `p2p-project-pin/1` | `E1-CLOSE-PIN1` |
| Pin validation | version/SHA/project/source/Doctor binding verified; malformed and stale cases fail closed | `E1-CLOSE-TEST1`, `E3-CLOSE-PILOT1` |
| MAP-BEFORE-WORK | fresh allowed; stale/missing/permission denied blocked | `E1-CLOSE-MAP1` |
| Project eval | project-owned suite, 5/5 case pairs, baseline/p2p 1.0/1.0, zero regressions | `E2-CLOSE-EVAL1` |
| Governance | derived drift `PASS`; historical approvals not rewritten | `E2-CLOSE-DRIFT1` |
| Package | 493/493 accounted; inventory/checksum/safety all pass | `E3-CLOSE-PACKAGE1` |
| Source provenance | clean at mint; commit/tree/object binding verified | `E3-CLOSE-PROVENANCE1` |
| Installed Doctor | strict `ok=true`, project pin and runtime checks `PASS` | `E3-CLOSE-DOCTOR1` |
| Technical prepare | `PASS`; approval request `PENDING`; no approve/finalize | `E3-CLOSE-GATE1` |
| Manus sentinel | `NOT_RUN / NO_LIVE_TRANSPORT_OR_CREDENTIALS`; no result fabricated | `E3-CLOSE-MANUS1` |
| C43/AERG | C43 not merged; AERG/Large Goal completeness planned/not implemented | `E0-CLOSE-SCOPE1` |
| Authoritative projects | Game Truyện `0`, Gia Phả `0`, Logistics `0/NO`, auto-upgrade `NO` | `E3-CLOSE-SAFETY1` |

### Final exact identity

```text
CANONICAL_AUTHORITY_REF = origin/main
CURRENT_OFFICIAL_BASELINE = 8.4.7-C-codex.19
CURRENT_OFFICIAL_ARTIFACT_SHA256 = 3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8
NEW_SUCCESSOR_VERSION = 8.4.7-C-codex.73
NEW_SUCCESSOR_ARTIFACT_PATH = reports/candidates/P2P-8.4.7-C-Codex-Edition-v73.zip
NEW_SUCCESSOR_ARTIFACT_SHA256 = 72bfbef935a41b68ebe3c7fc5464d99d2a47e849cb77e85507ceb90cdf19ef1a
NEW_SUCCESSOR_SOURCE_COMMIT = 4fba15e47f8c7290d71992dc0f44356321080c1b
NEW_SUCCESSOR_SOURCE_TREE = dff1ccbbcab439f806c4f391e3a62ac857a1e1d3
TOTAL_MEMBERS = 493
INVENTORY_MATCH = TRUE
CHECKSUM_MATCH = TRUE
PROJECT_LOCAL_DOCTOR = HEALTHY
MAP_BEFORE_WORK_GATE_RUNTIME_ENFORCED = VERIFIED
MANUS_BACKEND_TASK_ID = NOT_RUN / no live transport or credentials available
NEGATIVE_MATRIX = 26/26
NEW_UNEXPLAINED_FAILURES = 0
AUTHORITATIVE_PROJECT_MUTATION = 0
OFFICIAL_BASELINE_CHANGED = NO
PROMOTION_PERFORMED = NO
```

Disclosure: live Manus was unavailable; the whole-source secret scan reports two pre-existing token-shaped strings outside the candidate package; FW05 has one unrelated absent-shadow-project skip. Candidate-scope secret scans are clean. These are disclosed limitations, not new successor failures.
