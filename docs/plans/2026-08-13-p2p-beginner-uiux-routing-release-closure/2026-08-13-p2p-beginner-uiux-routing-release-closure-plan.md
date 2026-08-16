# P2P Beginner UI/UX Routing and Native AESTHETICA Release Closure Plan

## Metadata

- Date: `2026-08-13`
- Status: `BLOCKED`
- Plan: `docs/plans/2026-08-13-p2p-beginner-uiux-routing-release-closure/2026-08-13-p2p-beginner-uiux-routing-release-closure-plan.md`
- Evidence: `docs/plans/2026-08-13-p2p-beginner-uiux-routing-release-closure/2026-08-13-p2p-beginner-uiux-routing-release-closure-evidence.md`
- Benchmark: `docs/plans/2026-08-13-p2p-beginner-uiux-routing-release-closure/2026-08-13-p2p-beginner-uiux-routing-release-closure-benchmark.md`
- Actual status: `docs/plans/2026-08-13-p2p-beginner-uiux-routing-release-closure/2026-08-13-p2p-beginner-uiux-routing-release-closure-actual-status.md`

## Goal

Close the first-try beginner UI/UX routing defect identified in the attached
request, preserve the existing single P2P router and host-owned native
`p2p_aesthetica` path, and determine whether a new patch candidate can pass
the technical release gates. The result must be truthful: `PASS`, `BLOCKED`,
or `REJECT`; no simulated specialist execution, hidden model claim, or
approval self-action is allowed.

## Rules and boundaries

- Primary intent is determined by the requested outcome, not by beginner tone,
  language, or one keyword.
- A concrete interface, usability, accessibility, responsive, navigation,
  interaction, or visual-design outcome routes to `p2p-uiux` first, even when
  the user says they do not know design or calls it an idea.
- Undeveloped product/feature ideation with no concrete interface outcome
  routes to `p2p-idea` first. Mixed requests may retain a secondary route and
  must be decided by the requested deliverable.
- Trivial mechanical UI changes remain UI/UX/direct work and do not invoke
  AESTHETICA by default. Material hierarchy, flow, accessibility, responsive
  redesign, visual direction, or design-system work may use the real optional
  specialist only when host proof is available.
- Keep exactly eight canonical identities and denominator `8`; keep
  `p2p_aesthetica` optional/supporting and excluded from quorum.
- Keep `p2p_uiux.router` as the only router. Do not add a second classifier,
  meta-agent, quorum, ledger, or certification system.
- Preserve `.10`, `.9`, v5, the immutable baseline, App Game Truyện,
  Logistics, and all user projects. A changed candidate, if required, is
  `.11` and `.12`; never overwrite `.10` or `.9`.
- Do not repeat the already verified host-identity research or use private
  AgentControl/app-server named-selector research. A fresh first-try session
  may test routing; accept only the existing official receipt authority.
- Temporary paths remain under repository `.tmp`; no network, connectors,
  hooks, proxy, dependency installation, or external communication is enabled.
- This checkout has no Git metadata. Do not claim a commit; record the exact
  limitation and use Anvien change detection where available.

## Current scope

In scope:

1. P0 actual-status and root-cause evidence for the first-try misroute.
2. A narrow instruction-boundary correction in the existing P2P dispatcher,
   `p2p-idea`, and `p2p-uiux` contracts.
3. A reviewed 30+ case Vietnamese/English routing fixture covering clear UI,
   clear idea, mixed, accessibility, responsive, backend-negative, trivial,
   greenfield design, and ambiguous beginner wording.
4. Project eval-suite generation and release-gate/drift investigation.
5. Applicable full build, regression, package, lifecycle, canonical/quorum,
   security, and native first-try evidence.

Out of scope:

- AESTHETICA final behavioral-value certification.
- Context Economics, Code-Impact, App Game, Logistics, or broad framework work.
- Host identity re-research, private APIs, manual spawn substitution, or
  specialist simulation.
- Release promotion, deployment, merge, publish, or approval execution.

## Phase plan

### P0 — Actual status and implementation gate

- Refresh the current-root drift report and reproduce the `.10` technical
  gate without asking for approval.
- Record Anvien graph refresh, file-detail/impact limits for hidden skill and
  runtime paths, current package hashes, existing native receipt evidence,
  and the missing project eval suite.
- Establish the invariant family map: one router; primary outcome boundary;
  optional AESTHETICA; canonical eight; official receipt authority; fallback.
- Exit only when actual-status rows identify `correct`, `partial`, `wrong`,
  `missing`, or `blocked` and the exact next action.

### P1 — Bounded routing correction

- Add explicit precedence language to `.agents/skills/p2p/SKILL.md`.
- Add the negative boundary to `.agents/skills/p2p-idea/SKILL.md`.
- Add beginner outcome examples and the mixed/trivial/AESTHETICA boundary to
  `.agents/skills/p2p-uiux/SKILL.md`.
- Extend the existing Python router only for the demonstrated Vietnamese
  natural-language boundary and trivial-cosmetic specialist restraint; keep
  `p2p_uiux.router` as the only router and do not change canonical identity
  behavior.
- Refresh the source metadata only when the package evidence shows it is the
  actual cause of drift; never rewrite historical installed evidence.

### P2 — Routing eval and project gate inputs

- Add the deterministic 30+ case fixture and focused evaluator/test surface.
- Test runtime UI/technical boundary, trivial AESTHETICA restraint, source
  contract precedence, coverage, language, negative boundaries, and absence
  of internal agent/capability names in user examples.
- Generate the current project `.p2p/evals/suite.json` through the canonical
  project-eval helper; do not copy a temporary suite or invent passing cases.
- Validate and gate the suite; classify any drift as expected development
  change, protected fact/ledger issue, installed metadata issue, or real
  unexpected drift.

### P3 — Candidate and lifecycle evidence

- If the source correction is required, prepare `.12` using the repository
  packaging path and preserve `.11`/`.10`/`.9` hashes.
- Run package doctor, source/manifest/lock checks, UIUX DW1–DW18, capability
  foundation, decision trace, canonical/quorum, secret scan, and full
  regression.
- Run meaningful fresh-install, the preserved `.9`/`.10` lifecycle chains,
  `.11` to `.12`, and same-version reinstall checks in repo-local temporary
  roots.
- Run one fresh native Desktop-coordinator first-try beginner UI/UX request
  without correcting the model. Record the actual child and official receipt
  only if the host produces them; otherwise report the precise blocker.

### P4 — Supervisor closure

- Refresh plan evidence, benchmark, actual-status, notes/decision log, and
  coder report after each completed slice.
- Run Anvien `detect-changes` before closure; record no-Git behavior.
- Apply the supervisor skill as an independent acceptance review. It must
  inspect source/diff, test outputs, gate reports, package hashes, and scope
  boundaries. Final status is `PASS`, `BLOCKED`, or `REJECT`.

## Acceptance criteria

- The first-try boundary is explicit and outcome-based in the existing skill
  contracts; generic beginner wording no longer masks concrete UI intent.
- The 30+ case fixture passes coverage and deterministic runtime/contract
  checks, with clear UI, clear idea, mixed, and negative decisions reported.
- The existing native AESTHETICA receipt path and unavailable fallback remain
  unchanged and truthful.
- The current project eval suite is real and validated, or the exact gate
  blocker is retained rather than bypassed.
- Any `.11` candidate is reproducible, hash-recorded, lifecycle-tested, and
  not promoted without the required technical and user approvals.
- Supervisor accepts the result, or the task ends `BLOCKED`/`REJECT` with the
  concrete evidence and one actionable user decision.

## Current closure result

The source correction and verification work completed, but release closure is
blocked. Candidate `.12` is reproducible and package/lifecycle checks pass:

- Candidate: `D:\\AI\\P2P_dev\\P2P-8.4.7-C-Codex-Edition-v12.zip`
- Subject SHA-256: `7250b5864ecc06afaf360ba72a44da674ea58c8acce643f8f5915a04f2437cfb`
- Rollback `.11` SHA-256: `08f988e1a2d61cdedb8aa0b80c9aa38efad2d99e611ebe9bcd02fcf41e91db75`
- Technical report: `.tmp/gates/p2p-beginner-uiux-closure-final/technical-gate-report.json`
- Gate result: `BLOCKED_TECHNICAL_GATES` (`drift gate failed`, `project eval gate failed`).
- Drift blocker: existing unledgered volatile claims in unrelated MCP/payment/supervisor/UI-taste material.
- Eval blocker: the real schema-v2 suite has five cases but zero recorded trials for both variants; no trials were invented.
- Native first-try observation: the exact fresh Desktop task `019ffaea-1c46-7293-9b55-913045ed7038` ended with correct plain UI/UX guidance and no owner correction, but its first planning step selected the idea workflow before self-correcting to UI/UX. No fresh official child receipt appeared; existing receipt authority remains reused only for the previously verified native path.
- No approval, Live Spec promotion, release promotion, deployment, or commit was performed. This checkout has no `.git` metadata.

## Checklist

- [x] P0 actual status started before implementation.
- [x] P0 actual status refreshed after baseline gate/drift commands.
- [x] P1 routing boundary implemented narrowly.
- [x] P2 30+ routing fixture and focused evaluation pass.
- [x] P2 project eval suite generated and schema-validated; gate blocker retained.
- [x] P3 `.12` candidate/package/lifecycle evidence completed; native receipt limit recorded.
- [x] P4 full regression and Anvien change detection completed; no-Git limitation recorded.
- [x] P4 independent supervisor report written; verdict `REJECT` because release gates remain blocked.
