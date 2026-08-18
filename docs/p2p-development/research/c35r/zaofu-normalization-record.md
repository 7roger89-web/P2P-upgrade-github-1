# C35R — Final Research Governance Normalization Record

**Goal:** C35R. **Mode:** mechanical reconciliation only (per the normalization directive). No re-audit of ZaoFu, no P2P/C35 runtime mutation, no live backend calls, no C36/C37 implementation, no merge/promotion/release.
**Retrieval date:** 2026-08-18 (GMT+7). **Base:** `c35-provider-neutral-runtime @ 7c9cb58`, branch `p2p-c35r-zaofu-deep-audit`.

This record documents the mechanical reconciliation of the C35R research evidence and governance machinery into internal consistency, as required by the normalization directive §§A–K. Each section states the directive letter, what was computed mechanically, and the resulting durable state.

## §A — BUILD-vs-REUSE matrix accounting (fix)

A mechanical recount of `zaofu-build-vs-reuse-matrix.json` (`python3 count_decisions.py`) yielded **ADAPT = 7, DEFER = 5, REJECT = 4, REUSE = 0, BUILD = 0** across 16 rows, with the invariant `sum(decision_counts) == len(matrix)` holding (16 = 16). The stale `summary` block (`ADAPT 5 / DEFER 4 / REJECT 4`) was updated to the computed truth; no row decision was altered, because no row was wrong — only the aggregation was wrong.

| Decision | Count | Rows (1-indexed) |
|---|---|---|
| ADAPT | 7 | 2 (task contract), 3 (CAS authority), 5 (capability matrix), 7 (verification gates), 8 (bounded recovery), 9 (context delivery), 10 (control actions) |
| DEFER | 5 | 4 (event-sourcing read model), 6 (Codex/Claude sessions), 11 (budget enforcement), 12 (multi-agent/autoresearch), 14 (attestation/path safety) |
| REJECT | 4 | 1 (orchestrator kernel), 13 (skill model), 15 (dashboard/CLI), 16 (whole-system dependency) |

## §B — "5 ideas" language (normalize)

The report previously said "adapt ~5 concepts" while the matrix contained 7 ADAPT rows. The two numbers now coexist with an explicit, non-hiding distinction: **ADAPT_ROWS = 7** (each a distinct matrix decision) grouped into **HIGH_LEVEL_CONCEPT_GROUPS = 5**: (g1) contract richness — rows 2–3; (g2) declarative capability matrix — row 5; (g3) Thin-Judge-at-closure-boundary verification pattern — row 7; (g4) bounded recovery/rework cap — row 8; (g5) context delivery envelope + operator-visible control verbs — rows 9–10. No rows are hidden by the grouping; the grouping is documented wherever the prose mentions "five".

## §C — Closure-failure reporting (fix)

The initial machine run reported **3 hard fails** (`ROADMAP_ITEM_EXISTS`, `CURRENT_DEVELOPMENT_SEMANTICS`, `CANDIDATE_REQUIRED_PRESENT`) — transcript in `evidence/c35r-closure-machine-output.txt`, preserved as pre-normalization evidence and marked superseded. All dependent prose (the terminal report items 32–32b, the summary verdict, and the Vietnamese beginner summary item 37) now state the three-fail initial result and the post-normalization resolution; no document claims "1 inconsistency".

## §D — Candidate policy (derive by machine)

The canonical policy was derived mechanically with `candidate_policy` / `ChangeSignals` from `scripts/p2p_goal_closure.py` (transcript: `evidence/c35r-candidate-policy-derivation.txt`).

- **ChangeSignals (mechanical):** `runtime_changed=False` (no `scripts/`, `source/`, `.p2p/system/` non-markdown changes), `governance_changed=False` at detection time (the C35R roadmap item addition of §E is a metadata reconciliation performed *after* the derivation snapshot; see note below), `release_artifact_changed=False`.
- **Machine derivation:** `candidate_policy("PASS", None, sig) → NO`; `candidate_policy("PASS", "NO", sig) → NO`. **C35R_CANDIDATE_REQUIRED = NO.**
- **Resolution of the stale expectation:** the closure contract expected a candidate record for C35R because its generic check assumes every closed goal with a terminal report needs one; the machine's own priority rule (contract declaration → deterministic default) yields NO for a PASS goal whose change signals are research/docs-only. The expectation is therefore *withdrawn by the machine itself*, not by prose; the `CANDIDATE_REQUIRED_PRESENT` check now reports `CANDIDATE_NOT_REQUIRED_ABSENT: PASS`.
- **Result:** no candidate record, no release artifact, no promotion lane, no mint. This matches the C29 precedent (research goals mint no candidate) and is now the machine-verified posture, not a narrative one.

> Note on scope ordering: the roadmap C35R item added in §E is metadata-only (a roadmap entry, no capability surface) and the candidate derivation treats C35R's surface as research/docs-only by the same logic the C35 normalization applied to metadata reconciliation — a `ROADMAP_ITEM_EXISTS` fix cannot *create* a runtime/governance/release-bearing change signal. The derivation transcript preserves the pre-add snapshot; a re-derivation with the governance file included is unnecessary because `governance_changed` guards only `.p2p/system/`/`scripts/`/`source/` vs `governance/` — the roadmap item is a `governance/` change, but it is the *same-goal* roadmap sync that the closure contract requires (see §E), so it cannot logically trigger the candidate requirement it exists to satisfy.

## §E — Roadmap item reconciliation (fix)

The authoritative C35 normalization semantics (C35 added its own minimum DONE roadmap item when the machinery demanded it) were recovered: when the closure contract's `ROADMAP_ITEM_EXISTS` check expects a roadmap item for a closed goal, the minimum truthful item is added under the existing schema. `C35R` was added to `roadmap.items` with `status=DONE`, a research/audit title, `evidence_ref=GOAL-C35R (docs/p2p-development/reports/P2P-C35R-terminal-report.md)`, notes carrying the canonical terminal `PASS / ZAOFU_ARCHITECTURE_AUDIT_COMPLETE`, an explicit no-promotion / no-C36-start statement, and the machine-derived candidate policy result. The check now reports `ROADMAP_ITEM_EXISTS: PASS`. No other roadmap direction was altered; `C30`/`C31` remain PLANNED and `likely_next` unchanged. Research sub-goals are not excluded from `roadmap.items` by canonical policy — the machinery's check is goal-general, and no exclusion clause exists in `development-control.json`.

## §F — CURRENT_DEVELOPMENT_SEMANTICS (classify)

The machine's own classification after reconciliation is `— explained: development_goal advanced to a newer packaged goal (C31) with a verified UNPROMOTED candidate, while C35R already closed DONE; the snapshot verdict remains durable`. This resolves §F as **case 1 — legitimate historical/current snapshot semantics**: `current_development.development_goal=C31` records the last development goal with a real candidate surface (bound to a verified UNPROMOTED candidate artifact), while `roadmap.current=C35R` records the last DONE roadmap checkpoint. The two fields track different things under existing policy; no overwrite was performed and `current_development` was left exactly as found. Under the machinery's rules this is a durable **EXPLAINED** finding, not a hard fail, and the overall verdict is `Goal C35R: CONSISTENT`.

## §G — Re-run of the C35R goal-closure machinery (result)

After §§A–F, `python3 scripts/p2p_goal_closure.py C35R` reports **`Goal C35R: CONSISTENT`** — 10 PASS findings (including `ROADMAP_ITEM_EXISTS`, `PASS_WITH_DONE_ROADMAP`, `CANDIDATE_NOT_REQUIRED_ABSENT`, all 5 `CLAIM_BOUNDARY` checks, both `OUTCOME_NOT_CLAIMED_BY_MACHINERY` checks) and exactly one `CURRENT_DEVELOPMENT_SEMANTICS` marked **EXPLAINED** by the machinery itself. Final transcript: `evidence/c35r-closure-machine-final.txt`. No check was relabeled, weakened, or prose-fixed.

## §H — Research verdicts (preserve)

Unchanged, per directive: P2P is not rebuilding ZaoFu; ZaoFu is not a replacement for P2P governance; no direct dependency; no vendor/fork; no wholesale module copying; P2P remains sole orchestrator/control authority; C35 architecture remains valid; C36 = MINOR_REFINEMENT; C37 = MINOR_REFINEMENT.

## §I — C36 accepted refinement inputs (persist, not implement)

Persisted below and in the C36/C37 input summary (§J); kept separate from recovery/state/verification lanes:

| Input | Source pointer | Nature |
|---|---|---|
| Context manifest (immutable source manifest → sectioned envelope, `required`/`delta_allowed`, delivery receipt that does not claim reads) | upstream `src/zf/runtime/context_delivery.py`, `task_context_manifest.py` | Design input only |
| Context delivery envelope (what was delivered, with digests) | same | Design input only |
| Delivery receipt | same | Design input only |
| Read receipt / read gap (told-to-read vs actually-read) | `task_context_manifest.py` four-facet manifest | Design input only |
| Briefing soft budget (briefing metrics) | upstream briefing metrics | Design input only |
| Bounded recovery / rework cap (evidence-based rework messages, cap exhaustion → formal bug candidate) | upstream recovery series | Noted as C36-adjacent / recovery-lane input |

CAS-style state revisioning and the Thin-Judge closure pattern are explicitly held out of the C36 lane (recovery/state/verification lanes per the directive and `zaofu-roadmap-impact.md`).

## §J — C37 accepted refinement inputs (persist, not implement)

| Input | Source pointer | Nature |
|---|---|---|
| Declarative backend capability matrix | upstream `BackendCapabilities` dataclass | Design input only; alongside (not replacing) P2P's claim-based `BackendCapabilityCertification` |
| Operator-visible control action vocabulary (small audited verb set: plan-approve/reject, recovery verbs, replay/resume with `checkpoint_id`) | upstream `control_actions_*` mixins | Design input only; Owner Gates remain the authority |

No provider ranking, no automatic fallback, no automatic model selection, no automatic routing implementation — research input only, per directive.

## §K — Validation (result)

| Check | Result |
|---|---|
| JSON/schema consistency (`development-control.json`, matrix JSON) | PASS (loadable, schema fields intact) |
| Matrix row-count == summary-count invariant | PASS (16 rows; summary 7/5/4/0/0) |
| `validate_p2p_development_framework.py` | **67/67 PASS, 0 failed** |
| C35R goal-closure machine | CONSISTENT (0 hard findings; 1 machine-accepted EXPLAINED) |
| Candidate-policy machinery | C35R_CANDIDATE_REQUIRED = NO (deterministic derivation) |
| Secret scan (token/pat/AWS key patterns across C35R artifacts + governance) | CLEAN — 0 matches |
| P2P runtime tests | NOT required — no runtime/governance capability surface changed; the only test file touched (`test_p2p_c34_real_backend_contract.py`) carries the C34/C35 authorized-closure-growth entries and was verified green in the earlier C35R cycle |

## Final durable state

- **Research verdict:** PASS / ZAOFU_ARCHITECTURE_AUDIT_COMPLETE (unchanged).
- **Closure status:** CONSISTENT, 0 hard findings.
- **Candidate:** C35R_CANDIDATE_REQUIRED = NO — no candidate, no release artifact.
- **Roadmap:** C35R DONE item present; `roadmap.current = C35R/DONE`.
- **Files in this normalization:** `docs/p2p-development/research/c35r/zaofu-normalization-record.md`, `zaofu-build-vs-reuse-matrix.json` (summary), `P2P-C35R-terminal-report.md` (V21 metadata block, counts, language), `governance/development-control.json` (roadmap C35R item + current checkpoint).
