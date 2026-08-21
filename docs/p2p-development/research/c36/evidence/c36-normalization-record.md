# C36 FINAL MECHANICAL NORMALIZATION RECORD

Mode: documentation / governance-evidence reconciliation only. No runtime mutation, no new candidate, no backend call, no C37 start, no merge/promotion/release, no force-push. All findings below were recovered mechanically (actual scripts, actual files, actual machine output) — no inference by prose.

## §A. Final Git truth (verified against the repository, not assumed)

Branch `p2p-c36-evidence-bound-context-efficiency` is clean (0 uncommitted changes at verification time). HEAD equals the expected value: **64d4387** (full: `64d4387e73fa1451ba527adeb44c2dd1ff52a9f9`), matching `origin/p2p-c36-evidence-bound-context-efficiency`. Base `9dc0811` (`p2p-c35r-zaofu-deep-audit`) is a valid ancestor of HEAD; `7c9cb58` is also an ancestor. Semantic anchors:

| Anchor | SHA | Rationale |
|---|---|---|
| IMPLEMENTATION_HEAD | `64d4387` | Single C36 commit carrying all implementation, tests, evidence, candidate zip, and report |
| CLOSURE_MACHINE_HEAD | `64d4387` | Closure machine evidence was written against this surface; the final amend only inserted the measured FINAL HEAD line and `GOAL_END_SHA` into two already-correct files |
| FINAL_GOVERNANCE/DOCS_HEAD | `64d4387` | Same single commit; governance metadata was applied in the working tree at verification time and is committed by this normalization (see §E) |

No self-referential SHA loop occurred: the report's `GOAL_END_SHA` records the final HEAD as a measurement taken once after the last code change, and no further edits were made to make prose chase the SHA.

## §B. Regression count discrepancy — RESOLVED, neither number was a typo

The two durable counts measure two different suite sizes, both truthful:

| Measure | failed | passed | skipped | collected |
|---|---|---|---|---|
| BASELINE at `9dc0811` (CP0 run, before the C36 test file existed) | 30 | **766** | 19 | **815** |
| FINAL at `64d4387` (full C36 surface) | 30 | **835** | 19 | **884** |
| Difference | 0 | +69 | 0 | +69 = exactly the 69 C36 tests |

Arithmetic verified: 30+766+19 = 815; 30+835+19 = 884; 884−815 = 69 (current suite collects exactly 884 tests — measured by `pytest --collect-only`). The CP0 evidence's 766-pass number is **correct for the 815-test baseline suite**; the terminal report's 835-pass number is **correct for the 884-test final suite**. The 835 number was never a misstatement of the baseline — it is the count the full surface returns.

The primary invariant holds by direct evidence, not by assumption: the preserved raw failure list at CP0 (`analysis/c36_baseline_failures.txt`, 30 lines, all unique) is byte-identical in identity to the final-surface failure list (`/tmp/c36_fail_base.txt`, comm -23 = 0, comm -13 = 0). **FAILURE_IDENTITY_DELTA = 0 — PROVEN.** The terminal report items 46–48 have been normalized to state baseline as 30 failed / 766 passed (815 collected) and final as 30 failed / 835 passed (884 collected), retaining the delta=0 proof.

## §C. Validator count — measured once on the current surface

A single canonical run of the current framework validator at `64d4387` produced **69/69 checks passed, 0 failed** (raw output preserved in this normalization's evidence). The historical 67/67 figure was the C35R-era state; two additional registry checks grew the count when the C36 modules and C36 test file joined the capability registry. **No validator check was modified to reach 69** — the growth is evidence of the registry expanding, not of checks being weakened.

## §D. CURRENT_DEVELOPMENT_SEMANTICS — canonical severity semantics recovered, not relabeled

From `scripts/p2p_goal_closure.py` (the canonical machinery itself): `ClosureFinding` carries `severity` defaulting to `"hard"` with the machine's own documentation — *"hard" = genuine inconsistency; "explained" = durable snapshot drift accounted for by a later packaged goal* (line 291); line 389 marks the finding `severity="explained"`; line 667 defines `consistent = all(f.ok or f.severity == "explained" for f in findings)` — explained findings do not break consistency; only hard failures do.

| Field | Value |
|---|---|
| CURRENT_DEVELOPMENT_SEMANTICS_STATUS | FAIL (the snapshot field is not-ok — printed `[FAIL]` in the transcript) |
| CURRENT_DEVELOPMENT_SEMANTICS_SEVERITY | explained (set by the machine itself) |
| HARD_FINDING | NO |
| EFFECT ON VERDICT | none — `Goal C36: CONSISTENT` stands |

The transcript's visual `[FAIL] … explained` line is the machine's own output: the `[FAIL]` token labels the "not ok" status while the severity annotation carries "explained". This is the designed exception for durable snapshot drift (identical semantics to the C35R normalization), not a weakness and not a relabel.

## §E. Final-surface candidate-policy sanity check (no duplicate mint)

The committed surface `9dc0811..64d4387` contains 13 files; `ChangeSignals.detect` over that list yields `runtime_changed=True`, `governance_changed=False`, `release_artifact_changed=False` — the governance metadata sync was still in the working tree at that snapshot, which is why the committed diff shows no `governance/` change. Over the working surface (sync applied), `governance_changed=True`, `runtime_changed=True` still. On both surfaces:

- `candidate_policy(PASS, None, final_signals) = YES` (priority-2 rule — PASS terminal with a durable runtime change mandates a candidate);
- `candidate_policy(PASS, "YES", final_signals) = YES` (declared path agrees);
- **The final surface cannot reverse the existing lane.** `runtime_changed=True` is monotonic; a governance change can only add obligations, never remove the candidate mandate. No duplicate candidate was minted; the lane remains bound to the single existing artifact.

Mechanical recovery also exposed one stale field that the earlier closure record carried: the uncommitted governance record's `candidate_sha256` held `828df9a0…`, which is the **manifest-in-zip** sha256 (`unzip -p … c36-candidate-manifest.json | sha256sum` = `828df9a0…`), not the zip. The record has been corrected to the zip sha256 `c8915363462d12cde7e3a3db398bbd7a2457755bacb1a0f64274d8559fe354c5` — identical to the terminal report's `CANDIDATE_SHA256` metadata field — and `source_commit` set to the final normalization HEAD. This commit is the minimum metadata-integrity sync required for the governance file to truthfully record the already-minted candidate (same category as the C35R roadmap-integrity commit).

## §F. C36 technical truth preserved

All accepted findings in the prompt's §F list remain intact; no evidence was found to contradict them. Re-verification performed during this normalization: the six modules contain no provider/model routing code, no `requests`/`httpx`/`socket`/`urllib` imports (zero live backend calls); `git diff` confirms zero bytes changed in every C34/C35 module; `git show 9dc0811:reports/candidates/` contains no C36 zip, and the working-tree zip's sha256 equals the committed one (`c8915363…`) — the candidate is untouched; no C37 implementation exists (design boundary, not debt).

## §G. Verification performed (narrowly necessary only)

Current framework validator 69/69 PASS; final-surface ChangeSignals + candidate-policy sanity check (actual machinery, transcripts saved); goal-closure machine already durable at `docs/p2p-development/research/c36/evidence/c36-closure-machine-output.txt` (CONSISTENT, 0 hard findings); secret scan clean over this normalization record and the governance/governance-related edits; no external backends called; no runtime rewritten.

## §H. Git

Stayed on `p2p-c36-evidence-bound-context-efficiency`; normal push only; Draft PR #13 updates automatically; no merge, no promotion, no release.
