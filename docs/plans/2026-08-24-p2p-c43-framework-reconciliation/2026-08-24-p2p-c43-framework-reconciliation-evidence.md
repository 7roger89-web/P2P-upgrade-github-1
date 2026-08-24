# P2P C43 Framework Reconciliation Evidence Ledger

## Metadata

- Date: `2026-08-24`
- Plan: `docs/plans/2026-08-24-p2p-c43-framework-reconciliation/2026-08-24-p2p-c43-framework-reconciliation-plan.md`
- Evidence: `docs/plans/2026-08-24-p2p-c43-framework-reconciliation/2026-08-24-p2p-c43-framework-reconciliation-evidence.md`
- Benchmark: `docs/plans/2026-08-24-p2p-c43-framework-reconciliation/2026-08-24-p2p-c43-framework-reconciliation-benchmark.md`
- Actual status: `docs/plans/2026-08-24-p2p-c43-framework-reconciliation/2026-08-24-p2p-c43-framework-reconciliation-actual-status.md`

## Evidence Rules

- Evidence is tied to exact paths, commands, hashes, exit codes, and source authority.
- Reports and repeated research claims are evidence pointers, not authority by themselves.
- A pass is not inferred from logs that omit the checked contract. Negative fixtures must observe the failure surface and exit code.
- `NEW_FAILURE`, `INHERITED_FAILURE`, and `RESOLVED_INHERITED_FAILURE` remain separate throughout the ledger.
- No evidence in this file authorizes promotion, release, deployment, remote mutation, or changes to `.19`/`.74`.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-SRC1`: Current target is `D:\AI\P2P_dev\P2P-upgrade-github\.tmp\p2p-post74-development-01`, branch `codex/p2p-post74-development-01`, HEAD `583ed32bb306f36edfa537344a19d761627a7697`.
- `E0-P0A-SRC2`: Capability SPEC family and `docs/p2p-development/capability-ledger/capability-ledger.schema.json` were read as the authority for required fields, status vocabulary, ID pattern, origin types, and fail-closed boundaries.
- `E0-P0A-SRC3`: `capability-index.json` currently contains 176 entries, 12 registered families, and the schema vocabulary `VERIFIED_IMPLEMENTED`, `FOUNDATION_READY`, `PARTIAL`, `PLANNED`, `DEFERRED`, `REJECTED`, `OBSOLETE`, `UNKNOWN`.
- `E0-P0A-DRIFT1`: Tail entries at current indices 172-175 are compact `family`/`id`/`status` objects without required `capability_id` and other required fields; this is malformed data and a historical migration defect.
- `E0-P0A-DRIFT2`: `SYMBOL_AWARE_RETRIEVAL` has a duplicate compact lineage and an existing full record using `SHIPPED`, which is outside capability-index vocabulary; classification pending final authority decision is stale vocabulary/projection versus implementation upgrade.
- `E0-P0A-DRIFT3`: `CONTEXTUAL_RULE_INTELLIGENCE` has a full record and a compact duplicate with invalid `origin_type`, invalid dependency forms, and unsupported `SHIPPED`; classification is duplicate plus historical migration defect, with authority binding still to be checked.
- `E0-P0A-DRIFT4`: `ROADMAP_AWARE_DEVELOPMENT_PLANNER_PLANNED` uses `VERIFIED`, outside the declared capability vocabulary; current full record has evidence/implementation references. Classification is stale vocabulary/historical migration defect.
- `E0-P0A-DRIFT5`: `current-roadmap.md` declares a 159-record capability snapshot while the current source ledger has 176 entries. The file explicitly identifies itself as a derived projection; classification is stale projection.
- `E0-P0A-DRIFT6`: Additional pre-existing schema errors include unregistered family labels, missing `origin_type`/required fields, non-array `do_not_duplicate_with`, and malformed nullable fields. They are outside the four named drift items unless a focused gate proves otherwise and remain residual candidates.
- `E0-P0A-HISTORY1`: Git history shows the RM-CONTEXT line appended four compact tail records, later changed their statuses, while a full CRI record existed separately. This is provenance for a migration defect, not permission to delete or merge without membership evidence.
- `E0-P0A-BOUNDARY1`: RF01 independent-verification evidence and `.74` sealed artifact/hash proof were inspected. RF01 orientation remains development-only and `.74` is preserved; no C43 action touches canonical `.19`, release, promotion, or host enforcement.
- `E0-P0A-GRAPH1`: `anvien analyze --force` completed at the current HEAD with 875 files scanned, 163 parsed code files, 0 parse failures, 37,058 graph nodes, 42,835 relationships, and a fresh graph.
- `E0-P0A-GRAPH2`: Anvien file-detail/impact was run for the validator, charter tests, capability index, current roadmap, and schema. The validator and charter test files are high-risk source surfaces; the JSON/Markdown sources have low direct graph blast radius. The validator must be edited surgically.
- `E0-P0A-STATUS1`: P0 decision: complete for implementation of the bounded C43 scope, with an explicit authority blocker if CRI/membership cannot be resolved from current source and direct evidence.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-BEFORE1`: Before C43 ledger state at HEAD blob SHA-256 `63bf9c43558e7236438b0be821b1d355a06af966a46d965a0fe608b6a7011976`; 176 capability entries; 54 schema errors; invalid statuses were `SYMBOL_AWARE_RETRIEVAL=SHIPPED`, `CONTEXTUAL_RULE_INTELLIGENCE=SHIPPED`, and `ROADMAP_AWARE_DEVELOPMENT_PLANNER_PLANNED=VERIFIED`; compact tail carried four `id` records.
- `E1-P1A-PROV1`: Git history `4407e0d` introduced the compact RM-CONTEXT tail, `1a914f13` changed the full CRI record to `SHIPPED`, `b8e15a17` changed compact statuses to `VERIFIED_IMPLEMENTED`, and later lineage retained the malformed append. This supports `F HISTORICAL_MIGRATION_DEFECT` and `D DUPLICATED_RECORD`, not silent deletion.
- `E1-P1A-DEC1`: Authority decisions: `SYMBOL_AWARE_RETRIEVAL` remains `PLANNED` because its canonical owner-accepted record explicitly says intent-only; `CONTEXTUAL_RULE_INTELLIGENCE` remains `PLANNED` because RI-007 explicitly says `PLANNED / NOT_IMPLEMENTED / NOT_CERTIFIED`; `TOKEN_BOUNDED_PROJECT_MAP` and `ADAPTIVE_CONTEXT_BUDGET` are reconstructed as `PARTIAL` with existing source refs but no verified promotion; the planner alias `VERIFIED` is reconciled to `VERIFIED_IMPLEMENTED` because the record has implementation/evidence refs.
- `E1-P1A-AFTER1`: After repair the ledger has 174 entries, zero duplicate canonical IDs, zero unsupported statuses, and all four original compact capability IDs remain exactly once. `TOKEN_BOUNDED_PROJECT_MAP` and `ADAPTIVE_CONTEXT_BUDGET` are now full records; the duplicate symbol/CRI compact records are merged into their canonical records with historical claims retained in notes/provenance.
- `E1-P1A-AFTER2`: Schema validation now reports 17 errors, down from 54; the 37 resolved errors are the targeted compact/status/origin/duplicate-lineage drift. The remaining 17 are pre-existing unrelated legacy defects: one non-array `do_not_duplicate_with`, five missing names plus one nullable rejection reason, and ten missing `origin_type` fields on other appended records. They remain `INHERITED_FAILURE`, not silently relabeled.
- `E1-P1A-NODISCARD1`: Membership preservation check confirms `SYMBOL_AWARE_RETRIEVAL`, `TOKEN_BOUNDED_PROJECT_MAP`, `ADAPTIVE_CONTEXT_BUDGET`, and `CONTEXTUAL_RULE_INTELLIGENCE` each occur once after reconciliation; the historical compact `VERIFIED_IMPLEMENTED`/`SHIPPED` assertions are represented in the canonical records' notes and history references.
- `E1-P1B-AFTER1`: The derived roadmap snapshot now declares 174 total records, 171 in the 12 registered families, and three visible residual records under unregistered legacy family labels. Its count matches the final ledger exactly; its canonical-source declaration remains intact.
- `E1-P1-DIFF1`: Intended P1 diff is limited to `capability-index.json` (87 additions/27 deletions) and `current-roadmap.md` (9 additions/7 deletions); `git diff --check` reports no whitespace errors. No source module, `.19`, `.74`, RF01, release, or promotion path was edited.
- `E1-P1-HASH1`: Current worktree SHA-256 values are `capability-index.json=59828e29fec45fb6aa05b271ff761da4c8cb43a57cb13186468b8381b97aee18` and `current-roadmap.md=ab7a6559589f1f46ff04cf030ff2f1220f826c0bcd683fbb7b5586a2d2860d3e`.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-CODE1`: The validator now normalizes record shape before field access through `_record_entries`, `_record_label`, and `_record_diagnostics`; duplicate IDs, missing IDs, unsupported status values, malformed dependency shapes, and stale roadmap counts are surfaced as explicit failed checks. No malformed record is filtered into a passing path, and the existing valid-record checks remain in place.
- `E2-P2A-NEG1`: Missing `capability_id` fixture fails closed with an explicit missing-ID diagnostic; focused test PASS.
- `E2-P2A-NEG2`: Duplicate canonical `capability_id` fixture fails closed with a duplicate-ID diagnostic; focused test PASS.
- `E2-P2A-NEG3`: Unsupported `SHIPPED` capability lifecycle fixture fails closed against the declared vocabulary; focused test PASS.
- `E2-P2A-NEG4`: Stale roadmap fixture (`159` against ledger `174`) is detected; focused test PASS.
- `E2-P2A-NEG5`: Non-object record plus malformed dependency fixture returns a bounded nonzero validator result without `KeyError`, `TypeError`, traceback, or silent discard; focused test PASS.
- `E2-P2A-NEG6`: No-silent-discard fixture retains the original entry count and reports the missing ID; focused test PASS.
- `E2-P2A-NEG7`: RF01 orientation fixture remains `ACTIVE_NONCANONICAL_NO_PROMOTION`, with `development_plane.goal_id=RF01` and promotion disabled; focused test PASS.
- `E2-P2A-NEG8`: Sealed `.74` boundary fixture preserves version `8.4.6-C-codex.74`, `SEALED_UNPROMOTED`, the recorded artifact SHA-256, closure SHA, and `promotion.allowed=false`; focused test PASS.
- `E2-P2A-NEG9`: Current validator invocation exits `1` with `52/59 checks passed` and `7` named inherited failures, but no uncontrolled exception or traceback; focused boundary test PASS. This is an honest residual failure result, not a green-by-default assertion.
- `E2-P2A-TEST1`: `py -X utf8 tests/test_p2p_c43_framework_reconciliation.py` ran 9 tests and exited `0` (`OK`). Classification: `NEW_FAILURE=0`; all new C43 checks pass.
- `E2-P2A-SYNTAX1`: `py -X utf8 -B -m py_compile scripts/validate_p2p_development_framework.py tests/test_p2p_c43_framework_reconciliation.py` exited `0`. Classification: no syntax regression.
- `E2-P2B-VALIDATOR1`: The real current framework validator remains intentionally nonzero: `52/59` passed, `7` failed. The residual categories are the first schema error at ledger index `170` (`origin_type` missing), three unregistered legacy families, broken dependency references, freshness-vocabulary drift, the charter competitor-pattern check, invalid/missing origin-type checks on legacy records, and missing governance `pr_lineage`. These are `INHERITED_FAILURE`, not C43-created failures.
- `E2-P2B-REG1`: Regression commands exited `0`: C36 evidence-bound context `69/69`; targeted context `19/19`; targeted-context comparison `1/1`; C35 provider-neutral runtime `57/57`. The direct C36-as-script form has an existing import-path harness failure, so the correct module invocation was used; no product source was changed for that harness issue. The comparison test reported its existing metrics without treating them as C43 proof.
- `E2-P2B-CHARTER1`: A read-only harness executed all 40 `test_` functions in `tests/test_p2p_development_charter.py`: `38` passed and `2` failed. The two failures are inherited (`MANUS_EXECUTION_TARGET` depends on missing `BACKEND_ADAPTER_REGISTRY`; schema still rejects ledger index `170` for missing `origin_type`). No pytest installation was performed; a zero-discovery or unavailable-run result was not counted as proof.
- `E2-P2B-ANVIEN1`: After the C43 edits, `anvien analyze --force` refreshed the graph with `880` files scanned, `164` parsed code files, `0` parse failures, `37,294` nodes, and `43,109` relationships. Refreshed file detail reports the validator as parsed/high-risk with `91` symbols, `8` inbound refs, `286` unresolved analyzer gaps, and `3` linked flows; the focused test file has `25` symbols and no upstream impacted files. File impact remains a scope warning only; the edit is surgical and confined to the validator normalization path.
- `E2-P2B-BOUNDARY1`: RF01 orientation and the `.74` sealed candidate remain unchanged. The official `.19` artifact SHA-256 remains `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`; the sealed `.74` artifact SHA-256 remains `2b82dea10695abb1c99253be1205728335a114df42cececde2fcca5c1727fd12`; no `.19`/`.74` source, artifact, release, promotion, or host state was edited.
- `E2-P2B-SMOKE1`: Direct context-module probing did not justify status promotion: the target worktree's parent `.tmp` path is rejected by the existing path-safety filter, so fresh implementation proof for the context primitives remains unavailable. `TOKEN_BOUNDED_PROJECT_MAP` and `ADAPTIVE_CONTEXT_BUDGET` therefore remain `PARTIAL`, and CRI/SYMBOL remain `PLANNED` under owner authority. This is an evidence limitation, not a fabricated PASS.
- `E2-P2B-CLASSIFY1`: C43 result classification is `NEW_FAILURE=0`, `RESOLVED_INHERITED_FAILURE=37` targeted ledger/schema defects, and remaining `INHERITED_FAILURE` for the 17 unrelated schema errors plus the seven validator/charter residual categories. No unrelated owner-worktree failure was absorbed into C43.

## Closure Evidence

- `E3-P2B-COMMIT1`: Targeted implementation commit `2b2c104` contains exactly the nine intended C43 paths; `git diff --check 583ed32..2b2c104` exited `0`, and the intended paths are clean after commit. Unrelated owner changes remain outside the commit.
- `E3-P2B-REVIEW1`: Supervisor report `reports/supervisor/rp_supervisor_260824_115808_by_gpt-5-codex_p2p-c43-framework-reconciliation.md` independently reviewed the commit, fresh graph, tests, residuals, and protected boundaries and recorded `P2P_C43_PASS_FOR_INDEPENDENT_REVIEW_HANDOFF`.
- `E3-P2B-REVIEW-HASH1`: Supervisor report SHA-256 is `20b22754f540bde4d40acfae1725d8bc54eb4c6b4c70d9154ebaf7d0527faee2` (7,873 bytes) before closure-document commit.
- `E3-P2B-BOUNDARY1`: Fresh governance and direct artifact hashes confirm `.19` remains official/promoted with SHA `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`, `.74` remains sealed/unpromoted with SHA `2b82dea10695abb1c99253be1205728335a114df42cececde2fcca5c1727fd12`, RF01 remains `ACTIVE_NONCANONICAL_NO_PROMOTION`, CPT01-R2 remains `EXTERNAL_HOST_CAPABILITY_LIMITATION`, and `promotion.allowed=false`.
- `E3-P2B-CLOSE1`: C43 terminal classification is `NEW_FAILURE=0`, `RESOLVED_INHERITED_FAILURE=37`, with residual inherited schema/validator/charter failures explicitly retained. No promotion, release, deployment, host mutation, AERG start, or authority mutation occurred.

The C43 hard stop is now active after supervisor review. Any future work must be
a separately authorized Goal; it must not be started as an automatic C43
continuation.
