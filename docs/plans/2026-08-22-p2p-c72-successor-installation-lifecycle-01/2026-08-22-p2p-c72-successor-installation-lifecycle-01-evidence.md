# P2P C72 Successor Installation Lifecycle 01 Evidence Ledger

## Metadata

- Date: `2026-08-22`
- Plan: `docs/plans/2026-08-22-p2p-c72-successor-installation-lifecycle-01/2026-08-22-p2p-c72-successor-installation-lifecycle-01-plan.md`
- Evidence: `docs/plans/2026-08-22-p2p-c72-successor-installation-lifecycle-01/2026-08-22-p2p-c72-successor-installation-lifecycle-01-evidence.md`
- Benchmark: `docs/plans/2026-08-22-p2p-c72-successor-installation-lifecycle-01/2026-08-22-p2p-c72-successor-installation-lifecycle-01-benchmark.md`
- Actual status: `docs/plans/2026-08-22-p2p-c72-successor-installation-lifecycle-01/2026-08-22-p2p-c72-successor-installation-lifecycle-01-actual-status.md`

## Evidence Rules

- Fresh evidence must come from this successor worktree or repo-local disposable pilots.
- `.72`, origin/main, historical approvals, and authoritative projects are preserve-only.
- Source-tree-only helpers are not evidence for installed distribution capability.
- Every implementation slice records source, behavior, cleanup, Anvien, tests, and commit evidence.
- Approval state may be pending only; no approval, promotion, merge, or deployment is performed.

## E0 - P0 Evidence

Matching plan item: `P0-A`.

- `E0-P0A-REF1`: fresh fetch; successor branch starts at `4ce6a85f5991b6d6c464fb4b59e177114698947e`; `origin/main` official governance remains `.19` with SHA `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`.
- `E0-P0A-SUBJECT1`: exact `.72` ZIP rechecked at SHA `70613080d2ddbb92a52d2d79186e125439ec7f5ba8a6fa87bda9208d1b39d872`, size `2899774`, 491 members; no source edit targets the ZIP.
- `E0-P0A-CONTRACT1`: lifecycle doc, installer entrypoints, safe installer, legacy installer, Project Context, Doctor, gate, eval helper, and package builder mechanically inspected. `.72` has no packaged safe-installer producer; project eval suite is project-owned setup.
- `E0-P0A-IMPACT1`: Anvien refreshed successfully (36,412 nodes, 42,097 relationships, 0 parse failures, stale=false); affected Python surfaces were file-detailed and high-scope impact warnings recorded.
- `E0-P0A-VERSION1`: active source is `.72`; no `.73` was found in tracked history/current governance or candidate records; `.73` selected as the smallest unused immediate successor under the existing `<release>-codex.<revision>` policy.

## E1 - P1 Evidence

Matching plan items: `P1-A`, `P1-B`.

- `E1-P1A-PRODUCER1`: pin producer implementation and schema binding.
- `E1-P1A-PACKAGE1`: producer membership in package distribution.
- `E1-P1A-TEST1`: normal lifecycle producer behavior tests.
- `E1-P1B-NEG1..E1-P1B-NEG6`: required fail-closed pin/mutation cases.
- `E1-P1B-RUNTIME1`: focused installer/project-context/Doctor/MAP-BEFORE-WORK results.

## E2 - P2 Evidence

Matching plan items: `P2-A`, `P2-B`.

- `E2-P2A-CLASS1`: project-eval ownership/lifecycle classification.
- `E2-P2A-EVAL1`: normal project-eval setup and PASS evidence.
- `E2-P2B-SOURCE1`: clean source commit/tree/object binding and Anvien detect-changes.
- `E2-P2B-DRIFT1`: derived governance regeneration and drift PASS without historical mutation.

## E3 - P3 Evidence

Matching plan items: `P3-A`, `P3-B`.

- `E3-P3A-MINT1`: one-version selection, artifact identity, inventory/checksum/safety evidence.
- `E3-P3A-SEAL1`: immediate durable seal and fresh remote-derived byte verification.
- `E3-P3B-PILOT1`: fresh package-only install/adoption/pin/eval/Doctor/MAP-BEFORE-WORK matrix.
- `E3-P3B-GATE1`: regression/security/provider-neutral/technical prepare evidence.
- `E3-P3B-PUSH1`: branch push and local/remote match from fresh remote-derived worktree.

## Closure Evidence

### E0 closure — preserved authority and historical truth

- `E0-CLOSE-AUTHORITY1`: fresh remote-derived checkout confirms `origin/main` remains official `8.4.7-C-codex.19` with artifact SHA `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`; official baseline changed `NO`.
- `E0-CLOSE-HISTORY1`: `.72` remains byte-identical at SHA `70613080d2ddbb92a52d2d79186e125439ec7f5ba8a6fa87bda9208d1b39d872`, size `2899774`; no historical approval or promotion report was rewritten.
- `E0-CLOSE-SCOPE1`: `p2p-controlled-execution-hardening-01` is not an ancestor of the successor (`C43_ANCESTOR=False`); C43 remains a separate historical/development lane. AERG/Large Goal completeness remains planned/not implemented in this successor.

### E1 closure — canonical pin and fail-closed runtime

- `E1-CLOSE-PIN1`: candidate packages one canonical producer/validator using `p2p-project-pin/1`; the pin binds project fingerprint, candidate version/artifact SHA, official baseline, install class, source commit/tree, Doctor result, provenance, and verification status. No handwritten fixture is used as the installed pin producer.
- `E1-CLOSE-TEST1`: `scripts/test_project_pin_lifecycle.py` returned `PASS`, including `5` negative pin cases and fail-closed map behavior; `scripts/test_bootstrap.py`, `scripts/test_map_gate.py`, `scripts/test_map_freshness.py`, and `scripts/test_invariant_inversion.py` all returned `PASS`.
- `E1-CLOSE-MAP1`: disposable installed pilot proved fresh map + authorized bounded mutation `ALLOWED`; stale map, missing map, and permission denied each `BLOCKED` with `MAP_BEFORE_WORK_VIOLATION`. `MAP_BEFORE_WORK_GATE_RUNTIME_ENFORCED=VERIFIED`.

### E2 closure — eval and governance

- `E2-CLOSE-EVAL1`: project-owned eval suite was created through the installed eval helper and validated normally. Five case pairs completed with two baseline and two p2p trials each; baseline mean `1.0`, p2p mean `1.0`, delta `0.0`, case regressions `0`, p2p pass rate `1.0`.
- `E2-CLOSE-DRIFT1`: derived governance was regenerated after source freeze; current governance drift is `PASS` with zero failures. Historical approval records remain semantically unchanged.
- `E2-CLOSE-SECURITY1`: candidate package/pilot and candidate identity report secret scans returned no findings. A whole-source scan still reports two pre-existing token-shaped strings in historical documentation/tests; they are outside the candidate distribution and are disclosed, not reclassified as new findings.

### E3 closure — one sealed successor and remote proof

- `E3-CLOSE-ARTIFACT1`: exactly one successor `.73` was minted and durably sealed. Artifact path `reports/candidates/P2P-8.4.7-C-Codex-Edition-v73.zip`; size `2909357`; SHA `72bfbef935a41b68ebe3c7fc5464d99d2a47e849cb77e85507ceb90cdf19ef1a`; Python hashlib and PowerShell `Get-FileHash` agree.
- `E3-CLOSE-PACKAGE1`: fresh package verification reports `493` total members, `493` accounted, `0` unaccounted, `0` duplicates, `0` unsafe paths, `0` absolute paths, `0` missing expected members, inventory match `TRUE`, checksum match `TRUE`, checksum mismatch count `0`. Metadata hashes are recorded in `reports/reconciliation/p2p-c72-successor-installation-lifecycle-01-candidate-identity.json`.
- `E3-CLOSE-PROVENANCE1`: source at mint was clean and bound to commit `4fba15e47f8c7290d71992dc0f44356321080c1b`, tree `dff1ccbbcab439f806c4f391e3a62ac857a1e1d3`; commit/tree objects and tree-to-commit binding were verified. Post-mint commits contain only seal/evidence/governance material.
- `E3-CLOSE-REMOTE1`: fresh remote-derived checkout resolved local and remote branch head to `f43336c3439871968713c922ae28e0435c9d0b90`; artifact hash and package verification matched the durable seal.
- `E3-CLOSE-PUSH2`: evidence delivery resolved local and remote head to `03b582deeedecfdfc5a1ae44967a21ce071557c6`; a new remote-derived checkout at that head was clean and repeated candidate hash/package verification. The subsequent closure-only commit was pushed without changing the candidate artifact.

### E3 closure — installed adoption and technical prepare

- `E3-CLOSE-PILOT1`: fresh package-only pilot installed from the extracted candidate with the exact artifact SHA. Normal install generated `.p2p/project-pin.json`, bound version `8.4.7-C-codex.73`, exact artifact SHA, project fingerprint, install class `FRESH_INSTALL`, and `verification_status=VERIFIED`.
- `E3-CLOSE-DOCTOR1`: final installed strict Doctor returned `ok: true`, including `project-pin`, installed foundation, decision trace, governance drift, and project eval checks all `PASS`; `PROJECT_LOCAL_DOCTOR=HEALTHY`.
- `E3-CLOSE-GATE1`: `p2p_gate.py prepare` returned `TECHNICAL_GATES_PASS_USER_APPROVAL_REQUIRED`. Technical report status is `PASS`, subject SHA is the exact `.73` SHA, rollback SHA is the exact `.72` SHA, and approval state is `PENDING`. No approve/finalize/promotion command was run.
- `E3-CLOSE-REGRESSION1`: repository-native capability discovery from `.p2p/system` returned `335 tests`, `OK`, `6` skips; the provider-neutral C35 suite returned `57 tests`, `OK`; bounded FW suites returned `94 tests`, `OK`. `NEW_UNEXPLAINED_FAILURES=0`.
- `E3-CLOSE-MANUS1`: live Manus sentinel was not run because no live transport/credentials were available; no intention-only result is claimed. Provider neutrality is preserved.
- `E3-CLOSE-SAFETY1`: authoritative Game Truyện mutation `0`, Gia Phả mutation `0`, Logistics mutation/install `0/NO`, project auto-upgrade `NO`; all work was confined to the successor branch and repo-local disposable pilots.

### Final closure

`PASS_WITH_DISCLOSURES / P2P_INSTALLATION_LIFECYCLE_SUCCESSOR_CANDIDATE_VERIFIED`

Disclosure: live Manus sentinel was unavailable; the whole-source secret scan found two pre-existing historical token-shaped strings outside the candidate distribution; FW05 reports `29 tests OK` with one unrelated shadow-project skip because those external shadow trees are absent. These disclosures do not change the technical candidate verdict.

No promotion, final approval, main merge, tag, deployment, authoritative-project mutation, or `.72` remint was performed.
