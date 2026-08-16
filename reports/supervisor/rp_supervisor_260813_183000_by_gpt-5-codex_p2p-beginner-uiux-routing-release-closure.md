# Supervisor Report: P2P Beginner UI/UX Routing and Native AESTHETICA Closure

Verdict: `REJECT`

## Metadata

- Report file: `reports/supervisor/rp_supervisor_260813_183000_by_gpt-5-codex_p2p-beginner-uiux-routing-release-closure.md`
- Review time: `2026-08-13 18:30 Asia/Saigon`; amended after the exact fresh acceptance task completed.
- Reviewer: `gpt-5-codex`
- Repo/project: `D:\\AI\\P2P_dev\\P2P-8.4.6-C-Codex-Edition-v4`
- Scope reviewed: attached request, `.12` source correction, package, lifecycle evidence, project eval suite, gate report, coder report, and current repository state.
- Claim reviewed: the beginner UI/UX routing correction and native AESTHETICA release candidate are ready to close.
- Authority used: attached user request; repo `AGENTS.md`; project policy; planner/coder/supervisor requirements; source contracts; runtime registry; package and gate contracts.
- Related artifacts: coder report `reports/coder/rp_coder_260813_182800_by_gpt-5-codex_p2p-beginner-uiux-routing-release-closure.md`; technical report `.tmp/gates/p2p-beginner-uiux-closure-final/technical-gate-report.json`; candidate `.12` ZIP; plan/evidence/benchmark/status files.

## Executive Summary

- Problem: generic beginner wording could route a concrete UI/UX request to the idea workflow; the task also requires truthful release-gate closure.
- Decision: the source correction is present and the implementation evidence is strong, but the release claim is not acceptable because the mandatory technical gates fail, the exact fresh task initially planned the idea workflow before self-correcting to UI/UX, and no native child receipt was produced by the fresh Desktop behavior session.
- Required outcome: keep the candidate blocked; complete the legitimate evaluation and governance prerequisites, then re-run the bound technical gate before any approval request.

## Blocking Findings

### [BLOCKER] Mandatory release technical gates fail

File: `.tmp/gates/p2p-beginner-uiux-closure-final/technical-gate-report.json`

Issue: `p2p_gate.py prepare` returned `BLOCKED_TECHNICAL_GATES` for `drift gate failed` and `project eval gate failed`. The report is bound to subject SHA-256
`7250b5864ecc06afaf360ba72a44da674ea58c8acce643f8f5915a04f2437cfb` and rollback `.11` SHA-256
`08f988e1a2d61cdedb8aa0b80c9aa38efad2d99e611ebe9bcd02fcf41e91db75`.

Evidence: the current drift report lists unledgered volatile claims in unrelated active-runtime MCP/payment/supervisor/UI-taste material. The schema-v2 project suite validates with five cases but has zero baseline and zero P2P trials for every case; `p2p_eval.py gate` fails the minimum two trials per variant, pass-rate, and regression requirements.

Why this blocks acceptance: project policy requires drift PASS and eval PASS before release; user approval cannot override failed technical gates.

Fix direction: perform the authorized two-trial baseline/P2P evaluation using a real runner and immutable evidence, separately resolve or ledger the volatile claims with valid FACT_REF data and regenerated governed artifacts, then re-run `p2p_gate.py prepare` against the unchanged candidate hash.

Re-review evidence required: fresh drift PASS, fresh project-eval PASS with at least two trials per variant and no regressions, and a new technical report bound to the same or newly recorded subject/rollback hashes.

### [HIGH] Fresh native child receipt was not observed

File: N/A; behavior evidence is in fresh Desktop tasks `019ffacf-0ac5-73b0-be8d-07407d98f8d5` and `019ffacf-ca61-78f1-971b-821660b3f602`.

Issue: both uncorrected fresh requests produced plain UI/UX guidance without an idea-route response or internal capability names, but neither task emitted a new official host child receipt. Existing receipt authority remains valid for the previously verified path; it does not prove a new child ran in these two sessions.

Evidence: `codex_app__read_thread` showed only user/assistant messages for the two fresh sessions. The current capability doctor correctly reports AESTHETICA as resolved but not executable/health/identity verified in the development root. No identity is claimed from response prose.

Why this blocks acceptance: the requested closure includes a truthful native specialist boundary. The implementation contract is correct and fallback is safe, but a current first-try native execution claim cannot be accepted from these sessions.

Fix direction: use one supported host-coordinator run that emits the official receipt, or explicitly close this as fallback-only behavior and remove any claim of fresh native execution. Do not manually spawn, infer identity, or simulate.

Re-review evidence required: official receipt with exact `agent_type=p2p_aesthetica` and host authority, or an explicit owner decision accepting the verified UI/UX fallback without a current specialist execution claim.

### [HIGH] Strict first-try planning criterion is only partial

File: N/A; exact fresh task `019ffaea-1c46-7293-9b55-913045ed7038`, inspected with `codex_app__read_thread`.

Issue: the user-facing final answer selected the UI/UX path without owner correction, but the first planning message said it would use the idea workflow. The next message self-corrected to UI/UX after recognizing the concrete interface outcome.

Evidence: the completed thread records reasoning summary `Planning UI analysis with p2p-idea`, followed by an assistant message saying it would use `p2p-idea`, then a later assistant message switching `p2p-uiux` to primary. The final answer is materially UI/UX-specific, but this is not a clean first-planning-step proof.

Why this blocks acceptance: BR11 requires correct first-try routing; the strict evidence shows a residual precedence leak even though no owner correction was needed.

Fix direction: strengthen the executable/native dispatcher precedence so concrete interface outcomes are selected before beginner/idea cues, then validate with a fresh uncorrected session. Do not rely on response self-correction as first-try proof.

Re-review evidence required: a fresh exact request whose first recorded planning route is UI/UX, with no owner correction, plus the same official receipt/fallback evidence requirements.

## Source-Level Clearance Notes

- `.agents/skills/p2p/SKILL.md:120-151`: clear. The direct contract now chooses by requested outcome and explicitly separates concrete UI/UX from undeveloped idea work.
- `.agents/skills/p2p-idea/SKILL.md:1-13,78-95`: clear. Concrete interface/usability/accessibility/responsive/visual outcomes are excluded from idea-primary routing.
- `.agents/skills/p2p-uiux/SKILL.md:1-63`: clear. UIUX precedence, mixed deliverables, trivial cosmetic restraint, exact official receipt authority, and fallback are explicit.
- `.p2p/system/p2p_uiux/router.py:103-160`: clear for the implemented runtime boundary. Vietnamese terms classify as `UI_UX`; unavailable-specialist smoke returns `PROFILE_UNAVAILABLE` with `call_aesthetica=false`; cosmetic wording sets `trivial_cosmetic=true`; the router remains singular.
- `.p2p/system/p2p_capabilities/capabilities.json:169-192`: clear. Trigger metadata is bilingual, canonical identities remain eight, AESTHETICA remains optional/noncanonical, and version is `.12`.
- `tests/fixtures/p2p-beginner-routing.json` and `tests/test_p2p_beginner_routing.py:17-100`: clear supporting/behavioral boundary evidence; 40 cases and six tests pass.
- `tests/test_p2p_release_packaging.py:14-17`: clear. The current candidate constant is `.12`; the historical fixture remains isolated.
- `reports/coder/...`: clear as an implementation record; it does not override failed release gates.

## Evidence Checked

Passed:

- Fresh source inspection of all touched production contract/runtime groups listed above.
- `python -m unittest -v tests.test_p2p_beginner_routing tests.test_p2p_capability_foundation`: 31/31 PASS.
- `python -m unittest -v tests.test_p2p_release_packaging`: 2/2 PASS.
- `python -m unittest discover -s tests -p 'test_*.py' -q`: 64/64 PASS, 68.003 seconds.
- Clean `.12` package verify: PASS; 398 payload files and 399 checksums.
- Package doctor: PASS; source inventory 152/152, canonical 8/8, UIUX runtime `.12`.
- Fresh, upgrade, and same-version reinstall evidence: PASS; UIUX DW1-DW18 are 18/18.
- Project doctor, capability doctor, decision-trace doctor, secret scan, and focused compile checks: PASS.
- `anvien analyze --skip-git --force ...`: current graph refresh PASS with 232 files, 9,474 nodes, 10,823 relationships.
- Direct runtime smoke using ASCII-escaped Vietnamese inputs: material UI request -> `UI_UX` with safe fallback when specialist unavailable; product idea without interface -> `NON_UI`; trivial cosmetic -> `UI_UX` and `trivial_cosmetic=true`; backend -> `NON_UI`.
- Exact fresh Desktop acceptance task `019ffaea-1c46-7293-9b55-913045ed7038`: final answer is UI/UX-correct, but first planning route is `p2p-idea` then self-correction to UI/UX; strict first-try result is `PARTIAL`.

Failed:

- `python scripts/p2p_eval.py gate --suite .p2p/evals/suite.json`: FAIL because every baseline/P2P run list is empty and policy thresholds cannot be computed.
- `python scripts/p2p_governance.py drift --root . --governance governance ...`: FAIL because unledgered volatile claims remain.
- `python scripts/p2p_gate.py prepare ...`: `BLOCKED_TECHNICAL_GATES` for exactly the two failures above.
- `anvien detect-changes --repo P2P-8.4.6-C-Codex-Edition-v4 --scope all`: Git diff exit 129 because the checkout has no `.git` metadata; this is an environment limitation, not a hidden PASS.

Not run:

- `p2p_gate.py finalize`: correctly not run because no technical PASS or user approval exists.
- Any approval, Live Spec promotion, release/deployment, publish, or commit: intentionally not run.

## Invariant Closure

- Affected invariant: outcome-based primary routing with one runtime router, optional receipt-backed specialist handoff, fail-closed fallback, canonical governance, and protected release evidence.
- Sibling surfaces checked: dispatcher contract; idea/UIUX skill boundaries; runtime UIUX router; capability registry and readiness; canonical quorum; host receipt tests/ledger; fixture/tests; package metadata; installer/lifecycle; project eval and drift gates.
- Residual unverified same-invariant surfaces: a fresh official native child receipt for the new Desktop session; strict first-planning-step UIUX routing for the exact beginner request; legitimate project baseline/P2P trials; active-runtime volatile-claim governance cleanup. These are explicitly disclosed and prevent acceptance.

## Required Fix List For Resubmission

1. Produce the real minimum two baseline and two P2P trials per project-eval case through an authorized evaluation path; preserve frozen fixture/evidence hashes and re-run `validate` and `gate`.
2. Resolve the active-runtime drift using valid FACT_REF/FACT_LEDGER evidence and the governed Live Specs/lock workflow; do not suppress findings or edit unrelated claims opportunistically.
3. Decide whether current native specialist execution is required for closure. If yes, obtain the official host receipt through the supported coordinator. If no, state that closure is fallback-only and keep the no-identity-claim boundary.
4. Close the strict first-try precedence leak in the executable/native dispatcher, then run the exact fresh request once and record the first planning route.
5. Re-run package, lifecycle, regression, drift, eval, and `p2p_gate.py prepare`; only then prepare (but do not self-execute) the required approval request.

## Overall Evaluation

Implementation quality is acceptable for the bounded routing correction: the
source boundary is explicit, the runtime change is narrow, package/lifecycle
behavior is verified, and the canonical/fallback invariants remain intact.
Evidence quality is insufficient for release acceptance because mandatory
technical gates fail and a fresh native child receipt was not observed. The
candidate remains a truthful, reproducible `.12` implementation candidate, not
a releasable artifact.
