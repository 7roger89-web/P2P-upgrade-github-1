# P2P-C08 Real Context-Efficiency A/B Benchmark

## Result

**BLOCKED before scored execution.** The canonical suite, condition definitions,
order, and task-correct route intent were frozen. No provider/model trial was
started because the proven C07 live boundary can issue a live receipt only when
the requested profile has a fresh official host identity receipt. The current
configuration proves that path for `p2p_aesthetica` only; the full suite requires
non-Aesthetica standard/`p2p-uiux` routes for the other scenarios.

This is an integrity result, not a quality or efficiency result.

## 1. Benchmark version / candidate

- Suite: `.p2p/evals/2026-08-14-context-efficiency-ab-proxy-suite.json`
  (SHA-256 `d2f47a9447645fc8495498d031df8a20f6253319eb0ae73417327ee34e64d0d3`).
- Fixture: `.p2p/evals/fixtures/2026-08-14-context-efficiency-cases.json`
  (SHA-256 `978f29fe493be5ce6e2d2b0fbd820945880df6303fb561f74bbe36127eeac166`).
- A baseline reference: `8.4.7-C-codex.15`, SHA-256
  `af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195`.
- B candidate: `8.4.7-C-codex.17`, SHA-256
  `50eb59740034fb724dfe23d19d7f700c8143cfb9efd07f6cdf0a33d0ed041197`.
- Existing C06/C07 runtime was not changed.

## 2. Execution order

Frozen before any scored trial: odd scenario IDs `A then B`; even scenario IDs
`B then A`. The complete pre-registration is
`.tmp/p2p-c08-preflight-20260814/preregistration.json` (SHA-256
`f91cd585b33d5c83d6e3ed2243e3be61b47f5d6e7500889e07fb0f282986614e`).

## 3. Scenarios

The exact canonical C1-C12 suite was reused: tiny configuration edit, bug
diagnosis, multi-file feature, architecture decision, backend contract, normal
UI/UX, accessibility-heavy UI, research/evidence, conflicting project fact,
missing optional capability, interrupted/resume, and owner approval boundary.

## 4. Live trial count

`0 / 24` scored live executions; `0 / 24` attempted. The stop happened at the
route/profile/live-identity gate. Proxy trials were not relabeled or counted.

## 5. Routing map and fairness

The frozen route intent is recorded in the pre-registration. C1-C5 and C8-C12
use standard task-correct non-UI routes; C6 uses `p2p-uiux` primary without
Aesthetica; C7 is the only scenario for which the existing router marks
`ACCESSIBILITY_HEAVY` and makes optional `p2p_aesthetica` eligible. The raw router
observation is in `.tmp/p2p-c08-preflight-20260814/router-observation.json`
(SHA-256 `afa1c86c2d602db59a31454e37e59b04f8072c8c0eba006237693a8931e808bb`).
C2 and C3 have lexical `validation`/`interface` UI hits in the existing router,
so their task-intent route ambiguity is disclosed rather than silently treated
as UI work.

Within-pair route/profile equality was not reached because the host identity
proof required to execute the frozen routes was unavailable. C7 was not run as
a partial pair, preventing unequal coverage.

## 6. Model / host / permission control

- Requested model: host default; observed model: not applicable because no C08
  trial ran.
- Requested reasoning effort/provider/service tier: inherit/unknown; observed:
  not applicable.
- Requested permissions/network/tools: host default, no network requested,
  read-only bounded context trial, no children; observed: not applicable.
- Existing C07 host evidence proves `p2p_aesthetica` receipts, but it is not
  evidence for C08 non-Aesthetica routes.

## 7. Why the live gate failed

The C07 boundary validates the requested profile against a fresh official
`codex_official_hook` receipt before setting `runtime_task_execution=true`
(`.p2p/system/p2p_capabilities/live_execution.py:630-643`). The project config
installs that identity hook with matcher `^p2p_aesthetica$`
(`.codex/config.toml:8-14`). Current ledger inspection found fresh identity
receipts only for `p2p_aesthetica`; the `p2p-uiux` capability is a skill/router,
not a configured host agent profile. Therefore C1-C6 and C8-C12 cannot be
scored under the requested route/profile policy without a new observation or
host-control change. That would be a separate goal and could contaminate this
measurement.

Failure taxonomy: `PROFILE_UNAVAILABLE` and `CONTROL_PLANE_FAILURE`.

## 8. Quality and efficiency results

- Fixed rubric: Q1 correctness, Q2 requirement coverage, Q3 evidence quality,
  Q4 integration awareness, Q5 regression awareness, Q6 feasibility, Q7 scope
  discipline, Q8 unsupported-claim avoidance, Q9 residual-risk identification,
  Q10 beginner usefulness; 0-4 scale; fixed before execution.
- A quality mean: `NOT SCORED`.
- B quality mean: `NOT SCORED`.
- Quality delta: `NOT SCORED`.
- A wins / B wins / ties: `0 / 0 / 0` (no outputs reviewed).
- Critical acceptance failures: `NOT SCORED`; no C08 output was executed.
- Non-inferiority: `INCONCLUSIVE / NOT APPLICABLE` because no live pair exists;
  the registered margin remains B mean >= A mean - 0.25.
- Serialized context proxy A/B: `NOT EXECUTED` for C08. Historical proxy byte
  figures are intentionally not reused as live evidence.
- Context proxy delta: `NOT EXECUTED`.
- Wall time A/B/effect: `NOT EXECUTED`.
- Input/cache/output/total tokens: `UNKNOWN / UNKNOWN / UNKNOWN / UNKNOWN`;
  no host/provider trial exposed telemetry.
- Tool/retrieval effect: `NOT OBSERVED`.
- Child/host execution effect: `0` C08 executions; the local workflow selected
  `p2p_tecton` for bookkeeping but spawned no child and made no provider call.
- Retry/failure effect: `NOT OBSERVED`; the preflight stop is classified above.

## 9. Per-scenario results

All rows are explicitly not executed. `UNKNOWN` means no authoritative value
exists; `NOT EXECUTED` is not a zero measurement.

| ID | Task class / frozen route | Order | A status / acceptance / quality | B status / acceptance / quality | Context proxy A/B | Wall A/B | Provider tokens A/B | Tools / children / retries | Failure / confounder | Receipt / output |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 | Tiny configuration edit / standard P2P | A→B | NOT EXECUTED / NOT SCORED / NOT SCORED | NOT EXECUTED / NOT SCORED / NOT SCORED | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN / UNKNOWN | PROFILE_UNAVAILABLE; no Aesthetica allowed | NONE / NONE |
| C2 | Bug diagnosis / standard P2P | B→A | NOT EXECUTED / NOT SCORED / NOT SCORED | NOT EXECUTED / NOT SCORED / NOT SCORED | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN / UNKNOWN | PROFILE_UNAVAILABLE; lexical router intent ambiguity disclosed | NONE / NONE |
| C3 | Multi-file feature / standard P2P | A→B | NOT EXECUTED / NOT SCORED / NOT SCORED | NOT EXECUTED / NOT SCORED / NOT SCORED | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN / UNKNOWN | PROFILE_UNAVAILABLE; lexical router intent ambiguity disclosed | NONE / NONE |
| C4 | Architecture decision / architecture P2P | B→A | NOT EXECUTED / NOT SCORED / NOT SCORED | NOT EXECUTED / NOT SCORED / NOT SCORED | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN / UNKNOWN | CONTROL_PLANE_FAILURE | NONE / NONE |
| C5 | Backend contract / backend route | A→B | NOT EXECUTED / NOT SCORED / NOT SCORED | NOT EXECUTED / NOT SCORED / NOT SCORED | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN / UNKNOWN | CONTROL_PLANE_FAILURE; UI specialists excluded | NONE / NONE |
| C6 | Normal UI/UX / p2p-uiux primary | B→A | NOT EXECUTED / NOT SCORED / NOT SCORED | NOT EXECUTED / NOT SCORED / NOT SCORED | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN / UNKNOWN | PROFILE_UNAVAILABLE; no p2p-uiux host profile | NONE / NONE |
| C7 | Accessibility-heavy UI / p2p-uiux + optional Aesthetica | A→B | NOT EXECUTED / NOT SCORED / NOT SCORED | NOT EXECUTED / NOT SCORED / NOT SCORED | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN / UNKNOWN | NOT RUN after global fairness gate | NONE / NONE |
| C8 | Research/evidence / research route | B→A | NOT EXECUTED / NOT SCORED / NOT SCORED | NOT EXECUTED / NOT SCORED / NOT SCORED | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN / UNKNOWN | CONTROL_PLANE_FAILURE | NONE / NONE |
| C9 | Conflicting project fact / evidence integrity | A→B | NOT EXECUTED / NOT SCORED / NOT SCORED | NOT EXECUTED / NOT SCORED / NOT SCORED | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN / UNKNOWN | CONTROL_PLANE_FAILURE; contradiction not evaluated | NONE / NONE |
| C10 | Missing optional capability / capability preflight | B→A | NOT EXECUTED / NOT SCORED / NOT SCORED | NOT EXECUTED / NOT SCORED / NOT SCORED | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN / UNKNOWN | CONTROL_PLANE_FAILURE; fallback not evaluated | NONE / NONE |
| C11 | Interrupted/resume / resume integrity | A→B | NOT EXECUTED / NOT SCORED / NOT SCORED | NOT EXECUTED / NOT SCORED / NOT SCORED | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN / UNKNOWN | CONTROL_PLANE_FAILURE; resume not evaluated | NONE / NONE |
| C12 | Owner approval boundary / owner gate | B→A | NOT EXECUTED / NOT SCORED / NOT SCORED | NOT EXECUTED / NOT SCORED / NOT SCORED | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN / UNKNOWN | CONTROL_PLANE_FAILURE; owner boundary not evaluated | NONE / NONE |

## 10. Special scenario conclusions

- C9 contradiction result: `NOT EXECUTED`; no claim about contradiction safety.
- C10 capability result: `NOT EXECUTED`; no installation, fake availability, or
  retry was attempted.
- C11 resume result: `NOT EXECUTED`; no unsupported resume was faked.
- C12 owner-gate result: `NOT EXECUTED`; no approval was requested or inferred.
- Main-context versus total-system conclusion: neither effect can be inferred.

## 11. Decision matrix

Because no real C08 trial ran, every requested adoption hypothesis remains
`INSUFFICIENT_EVIDENCE`: current context primitive, CAPSULE refinement,
Knowledge Delta, context pointers, worker context loadout, progressive
disclosure, reversible evidence drill-down, persistent logical owner,
`rigor != delegation`, bounded delegation, delegation-before-model-selection,
capability preflight, and execution budget. No feature was implemented.

- ADOPT_NOW: none.
- REFINE: none.
- DEFER: none as a benchmark conclusion; implementation remains prohibited by
  this Goal.
- REJECT: none.
- INSUFFICIENT_EVIDENCE: all listed hypotheses.

## 12. Files and regression impact

Files created or updated for this audit:

- `.tmp/p2p-c08-preflight-20260814/preregistration.json`
- `.tmp/p2p-c08-preflight-20260814/router-observation.json`
- `reports/benchmark/p2p-c08-real-context-ab-20260814.md`
- `.p2p/state/goal-contract.json` and the two C08 goal snapshots under
  `.p2p/state/goals/` created by the project workflow bookkeeping. The two
  exploratory snapshots are linter-BLOCKED because the generic helper labels
  those natural-language requests `SEPARATE GOALS`; the final local preflight
  contract is linter-PASS but the workflow is terminal BLOCKED on execution
  evidence. None of this is used as A/B evidence.
- `.p2p/state/project-status.json`, `.p2p/state/trusted-evidence.json`,
  `.p2p/state/reports/run-20260814-062759-c08-live-eligibility.*`, its context
  manifest, and `.p2p/state/capsules/goal-20260814-062647-c08-live-eligibility-pre.md`
  from the local terminal workflow preflight.

No release artifact, runtime treatment, official `.15`, candidate `.17`, or
production project was changed by C08. The local workflow preflight appended
four ordinary control-plane events for run
`run-20260814-062759-c08-live-eligibility`; it appended zero
`live_context_trial_receipt` events, and the ledger now hashes to
`6c35de8f10020ba0c8df2f8d04e93bac69b44fb4dfea1d3ead65060ae02dbfe5`.
Focused
context/live/host-identity tests passed `28/28`; capability doctor, governance,
canonical quorum `8/8`, Decision Trace `24/24`, and proxy suite validation passed.
The corrected package doctor remains FAIL on inherited placeholder-token findings
in duplicated marketplace/reference/report files; no cleanup was performed in
this measurement-only Goal. The installed-project doctor also reports that this
development checkout is not an installed package and repeats the inherited scan
findings. These are disclosed, not treated as C08 live evidence.

The workflow control-plane report is
`.p2p/state/reports/run-20260814-062759-c08-live-eligibility.json` with status
`BLOCKED`; its local report/capsule/context-manifest artifacts are bookkeeping,
not scored outputs.

## 13. Final classification and next goal

- B classification: `INCONCLUSIVE`.
- Quality/efficiency decision: `INCONCLUSIVE`.
- Release impact: none; `.17` was not promoted, released, deployed, or activated.
- Recommended next Goal: provide and independently verify a supported,
  non-invasive host identity/receipt path for task-correct non-Aesthetica and
  `p2p-uiux` route profiles, then rerun this exact pre-registered C08 suite.
  Any hook/config/runtime change requires its own plan, impact/security review,
  and contamination decision.
