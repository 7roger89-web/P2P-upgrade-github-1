# P2P-DOCUMENT-MARKER-CONVERT-01 — TERMINAL REPORT

**GOAL_ID:** P2P-DOCUMENT-MARKER-CONVERT-01
**CAPABILITY_ID:** `document.marker.convert`
**GOAL_TERMINAL_STATUS:** **BLOCKED / WRONG_REPOSITORY_OR_PROJECTION**

## 1. Assignment received

Task instructions asserted the following architecture as "already
approved" and "already existing" in this repository:

```text
Owner / Control Tower
  -> GitHub durable job/request
  -> GitHub Actions existing control plane
  -> existing Google Colab execution lane
  -> ephemeral Colab GPU runtime
  -> bounded Marker worker
  -> output/evidence artifacts
  -> GitHub durable return
  -> Control Tower validation/review
```

The task explicitly forbade redesigning this architecture and required
locating the *actual existing* implementation files for the GitHub
Actions control plane, Colab dispatch, Colab worker, artifact-return
path, capability registry/router, execution ledger, and evidence
contract — "do not invent filenames."

## 2. Phase 0 fresh-truth findings

| Field | Value |
| --- | --- |
| REPO | `7roger89-web/P2P-upgrade-github-1` |
| CURRENT_BRANCH | `arena/01a079c0-p2p-upgrade-github-1` |
| CURRENT_HEAD | `c1ddc4fdbc3bf6639a5f3e3f171a7fb5c1df6352` |
| DEFAULT_BRANCH | `main` |
| WORKTREE_STATUS | clean, no local mutations |

Search performed (working tree, full history, and **all 86 remote
branches** fetched and `git grep`'d, including archived/experimental
branches such as `p2p-c*`, `codex/*`, `control-tower/*`):

- No `.github/` directory exists anywhere in the working tree, in git
  history (`git log --all --diff-filter=A --name-only | grep
  .github/workflows` returns nothing), or on any of the 86 remote
  branches.
- No case-insensitive occurrence of the string `colab` exists anywhere
  in the repository (working tree or any of the 86 branches).
- No occurrence of `marker-pdf`, `marker_pdf`, or `surya` (the OCR
  engine Marker depends on) exists anywhere in the repository.
- No `workflow_dispatch`, `repository_dispatch`, `runs-on:`, or
  `actions/checkout@` pattern exists outside vendored *reference*
  documentation under `.agents/skills/*/references/*.md` (generic
  DevOps/CI teaching material, not a P2P control plane).
- `governance/development-control.json` (the canonical roadmap/decision
  record) contains no reference to `marker`, `colab`, `GitHub Actions`,
  `OCR`, `GPU`, or `PDF`.
- `.p2p/system/p2p_capabilities/capabilities.json` (the actual single
  capability registry, 72 entries) contains no `document.marker.convert`
  entry and no Colab/Actions-based `BACKEND_PROVIDER`.
- The repository's own governance explicitly registers the opposite
  decision as **REJECTED, permanently preserved**:
  - `docs/RESEARCH-ADOPTION-LEDGER.md:85` — *"Scraping as core
    infrastructure / **GitHub Actions as control plane** | Core
    infrastructure is self-contained and evidence-verified"*
  - `docs/p2p-development/P2P-DEVELOPMENT-CHARTER.md` §7 — the
    permanent "must never be reintroduced" register, backed by
    `docs/p2p-development/reports/P2P-C30-terminal-report.md:68`:
    *"Rejected-as-P2P-core list durably preserved: ... **GitHub Actions
    as P2P brain** ..."*
  - `docs/P2P-DEVELOPMENT-ROADMAP.md:99` (Vietnamese) also lists
    *"GitHub Actions làm bộ não"* ("GitHub Actions as the brain") in the
    same permanently-rejected register.
- `gh issue list` / `gh pr list` search across the live repository found
  no open or historical issue/PR proposing a Colab/Marker execution
  lane. The one closest related open issue, **#70
  `P2P-EXECUTOR-01: prove generic upstream execution path`**, is itself
  still unstarted/unproven and proposes a *different* candidate
  (DeepSeek Harness, not GitHub Actions + Colab).

## 3. Verdict

The task's Phase 0 premise — "the existing P2P GitHub→Actions→Colab
execution lane" — does not exist in this repository, in any branch, or
in this repository's governance/roadmap intent. It is not a case of the
files being named differently; the specific pattern (GitHub Actions as
control/dispatch plane) is affirmatively and durably registered as a
**rejected pattern** that must not be reintroduced without a fresh,
explicit Owner approval reopening that specific rejection (per Charter
§7: *"a future goal that touches any of these patterns must reopen it
explicitly with Owner approval"*).

Per the task's own Phase 0 stop condition:

```text
BLOCKER=WRONG_REPOSITORY_OR_PROJECTION
```

Per `NO_OVER_ENGINEERING` / `REUSE_EXISTING_ARCHITECTURE` / `NO_NEW_INFRASTRUCTURE`
and the explicit instruction "Do not create a replacement architecture,"
no GitHub Actions workflow, Colab notebook, dispatch script, or Marker
worker was created in this session. Building any of these now would
either (a) invent a brand-new execution lane in violation of
`REUSE_EXISTING_ARCHITECTURE`/`MINIMUM_DELTA`/`NO_NEW_INFRASTRUCTURE`, or
(b) knowingly reintroduce a permanently-registered rejected pattern
without the required Owner re-approval. Both are out of bounds for a
bounded implementation executor.

## 4. What *does* exist and is available for a corrected next goal

If the Owner wants to proceed with `document.marker.convert`, the
closest real, reusable seams already in this repository are:

- **Capability registry (single source of truth):**
  `.p2p/system/p2p_capabilities/capabilities.json` — flat list of 72
  manifest records; new capabilities are added here with
  `TYPE=BACKEND_PROVIDER`, `STATUS=DISCOVERED` (never auto-`ACTIVE`).
- **Adapter precedent for "external tool wrapped as bounded backend
  provider":** `android.protection.detect` →
  `.p2p/system/p2p_capabilities/apkid_adapter.py` (local CLI tool,
  `install_mode: DISABLED`, `network_runtime: false`,
  `EXECUTION_STATUS: ADAPTER_TESTED_ONLY`).
- **Adapter precedent for a bounded, non-executed external-process
  orchestrator:** `game.three.asset.static_glb_standardize` →
  `.p2p/system/p2p_capabilities/static_glb_standardizer.py`, and
  `mpfb_adapter.py` (bounded parent/orchestrator pattern for one pinned
  external job, `EXECUTION_AUTHORIZED: False` until an Owner Gate).
- **Provider-neutral host/executor contract layer (no launcher):**
  `.p2p/system/p2p_capabilities/host_executor.py`,
  `host_selection.py`, `backend_contract.py`,
  `backend_execution_bridge.py` — these define
  `PortableExecutionRequest`/`Receipt`/`Handoff`, adapter conformance,
  and normalized error classes, but explicitly do **not** launch a
  host, select a provider, or create background workers.
- **Durable session/evidence handoff:**
  `.p2p/system/p2p_capabilities/control_tower_handoff.py` and
  `docs/p2p-development/CONTROL-TOWER-SESSION-HANDOFF.md` — the actual
  GitHub-connected Arena session ↔ Control Tower packet contract
  (`docs/ARENA_AGENT_MODE_PROTOCOL.md`), which is provider/host-neutral
  and does not assume GitHub Actions or Colab.
- **Provider abstraction seam for a future external execution
  provider:** `docs/SPEC/P2P-PROVIDER-ABSTRACTION-SPEC.md` — defines
  how a new provider role would be declared (trust level, evidence
  contract, failure states) without adding infrastructure in the same
  goal.

None of these constitute a GitHub Actions or Colab dispatch lane. They
are the actual reusable primitives a correctly-scoped
`document.marker.convert` goal would build on top of, using whichever
concrete execution host the Owner actually approves (which the
`P2P-EXECUTOR-01` issue #70 suggests is still an open, unresolved
question for this project — the Owner has not yet selected/proven any
generic external execution harness, let alone Colab specifically).

## 5. No mutation performed

- No `.github/workflows/*` created.
- No Colab notebook, dispatch script, or Marker/Surya dependency added.
- No capability registered in `capabilities.json`.
- No test added (nothing exists yet to test).
- No secrets, credentials, or tokens referenced or requested.
- No merge, promotion, or production mutation performed.
- Working tree is unchanged except for this one durable evidence file.

## 6. Recommended next action for the Owner

Open a new, correctly-scoped goal that either:

1. **Resolves issue #70 first** (`P2P-EXECUTOR-01`), proving one
   generic external execution path (the issue itself proposes DeepSeek
   Harness, not Colab) before any document-conversion capability is
   layered on top of it; or
2. **Explicitly reopens the rejected `GitHub Actions as control plane`
   pattern** with a stated, bounded rationale and re-approves it as an
   exception (per Charter §7's own reopening procedure) before any
   Colab/Actions-based `document.marker.convert` design is attempted in
   this repository.

Either path is an Owner architecture decision, not something this
bounded implementation session may resolve unilaterally.
