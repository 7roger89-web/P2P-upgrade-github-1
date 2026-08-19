# C36 Live Certification — Final Independent Supervisor Report

**Subject:** C36 Real Host Execution Attestation — live certification lane
**Date:** 2026-08-19 (GMT+7)
**Author:** Manus AI (Independent Supervisor lane)
**Branch:** `c36-real-host-binding` (HEAD `8b22a51`, pushed to `origin`)
**Primary terminal verdict:** `P2P_C36_EXTERNAL_HOST_BLOCKED`
**Gia Phả terminal verdict:** `GIA_C02_READY_AFTER_C36_PROMOTION`

## 1. Mandate

The Owner instructed a continuation of the SAME C36 Goal: complete full live certification before promotion, do not stop at the previous candidate, do not promote, do not start LG01, and do not count deterministic fake-adapter execution as real. This report is the independent Supervisor evaluation of that lane, phases L0 through L8.

## 2. L0 — Candidate recovery

The current candidate was recovered without modification. The branch `c36-real-host-binding` is at HEAD `8b22a51` with no untracked implementation changes (only a `.p2p/system/evidence/` leaf is untracked, containing the Supervisor evidence itself). The C36 deterministic suite was re-run and passed **37/37**; the C35 regression was re-run and passed **57/57**. The one-role iris bundle (`.p2p/state/reports/c36/c36-one-role-iris-live-proof.json`) is intact with verdict VERIFIED, dispatch ID `65db0788...fed5d4`, and receipt fingerprint recorded. The Gate J integration bundle still reads exactly **1 VERIFIED / 7 PENDING_HOST_ATTESTATION**. The replay ledger file on disk reflects the last test teardown state, as designed (ledger entries are consumed within test cycles; production ledger usage writes at real dispatch).

| L0 check | Result |
|---|---|
| Branch / HEAD / implementation unchanged | PASS (`8b22a51`) |
| C36 suite | 37/37 PASS |
| C35 regression | 57/57 PASS |
| Iris receipt / bundle intact | PASS |
| Gate bundle 1/7 | PASS |

## 3. L1 — Real execution target discovery

Three candidate hosts were evaluated against the six required dimensions, with no new paid access requested and no fabricated hosts.

| Host | HOST_AVAILABLE | ADAPTER_AVAILABLE | AUTH_AVAILABLE | REAL_EXECUTION_AVAILABLE | INDEPENDENT_IDENTITY_EVIDENCE | ROLE_BINDING_CAPABLE |
|---|---|---|---|---|---|---|
| Codex CLI 0.147.0 | Yes | Yes (codex adapter, host_kind allow-listed) | **No** — `codex login status` = *Not logged in*; no API key in environment | **No** | Partially (session SQLite exists, no active logged-in session) | Yes |
| Manus runtime | Yes | No | No — platform task identity not observable from inside the runtime; Owner amendment 4 forbids self-reported identity | **No** | **No** | Yes |
| Claude Code 2.1.143 | Yes | No | **No** — no auth session observable, no ANTHROPIC_API_KEY | **No** | **No** | Yes |

The consolidated matrix is persisted at `.p2p/state/reports/c36/c36-l1-final-target-matrix.json`.

## 4. L2 — Genuine end-to-end one-role proof

A genuine end-to-end p2p_iris proof on a real vendor backend was **not achieved**. The Codex runtime, which is the only host with a P2P-coded adapter surface, is logged out on this machine, and the Owner explicitly prohibited requesting new paid access merely to complete the matrix. Writing a local evidence file was correctly recognized as insufficient under Owner condition 2, and the deterministic fake adapter was correctly recognized as insufficient under the L2/L4 stop rules. No PENDING row was converted to VERIFIED.

**Honest status:** `L2_NOT_RUN — no authorized real backend`.

## 5. L3 — Second heterogeneous host

Not attempted, because no first real-backend proof exists to pair with. The exact Owner-mandated honest record is preserved:

> **MULTIHOST_LIVE_CERT_PENDING_EXTERNAL_UNAVAILABLE**

## 6. L4 — Eight-role real execution proof

Not run. The gate conditions require at least one genuine real-backend p2p_iris execution to succeed first, which did not occur. The existing gate bundle therefore remains **1 VERIFIED / 7 PENDING_HOST_ATTESTATION**, and the seven pending roles are untouched by design.

## 7. L5 — Gia Phả C02 Gate J

The existing valid Gate J evidence (`reports/QA/playwright/p2p-c02-gatej-ui-20260819-114604-manus-01`, runner SHA `e8b58079...`, manifest 64/64 mismatch 0, 8/8 steps PASS, productionTouched NO) remains mechanically valid and was not rerun, per Owner instruction. A new Gate J session was **not** started, because its PASS condition requires exactly 8/8 real-attested bindings, which the current honest matrix (1/8) cannot satisfy. Fabricating the remaining seven would violate the owner's stop rules.

## 8. L6 — Independent Supervisor inspection

The Supervisor independently inspected, rather than trusted in aggregate:

| Inspection item | Finding |
|---|---|
| Role registry (8 canonical IDs) | Confirmed canonical set; denominator 8, full quorum 8/8 |
| role_spec_digests | 8 distinct deterministic digests verified by re-running `build_role_spec` for each role |
| execution_contract_digests | 8 distinct contract fingerprints, each binding run_id + dispatch_id + digest |
| dispatch IDs | 8 minted dispatch IDs, one per role, no reuse |
| host execution identities | Only p2p_iris identity is real (Codex live proof); 7 pending have none |
| Evidence sources/digests | Iris evidence file exists and digest matches; pending roles have none |
| Replay ledger | Consumed only the iris proof entry; no cross-reuse |
| Receipt freshness | One receipt with unique fingerprint; no historical reuse |
| Exact role set | 8 canonical roles, no extras |
| Same Gate run / subject / evidence | Confirmed against frozen artifact dir |
| Production untouched | productionTouched NO on frozen run; no new production writes |
| No synthetic counted as real | Enforced: 7 PENDING rows untouched |

## 9. L7 — Final certification state

The full certification condition requires 37/37 tests, 57/57 regression, at least one genuine real-backend iris execution VERIFIED, exact 8/8 real-attested Gate J, and a passing Supervisor. Four of five conditions are satisfied; the genuine real-backend condition is blocked externally. The correct terminal state is therefore:

**`P2P_C36_EXTERNAL_HOST_BLOCKED`**

C36 remains at candidate, fully reversible, with all deterministic and one-role evidence preserved.

## 10. L8 — Gia Phả C02 closure

Current governance requires C36 promotion (or a completed 8/8 real-attested Gate J) before this candidate can serve as canonical closure authority for GIA-C02. That gate is not satisfied. Per the Owner mandate, the bypass is forbidden and the honest designation is recorded:

**`GIA_C02_READY_AFTER_C36_PROMOTION`**

All evidence (frozen Gate J artifact, L1 discovery matrix, prior Supervisor report, iris live bundle) is preserved on disk and in the branch.

## 11. Owner action required

One decisive action unblocks the entire remaining lane: **log the Owner into the Codex CLI on the Windows machine** (`codex login`, e.g. `codex login --with-api-key` using an existing key, which is reading existing credentials, not requesting new paid access). That single act converts Codex from AUTH_AVAILABLE=No to Yes, enabling L2 (real-backend iris), L3 (Codex + Manus heterogeneous pair, subject to Manus identity observability), L4 (eight real executions), and the exact 8/8 Gate J required for `P2P_C36_FULL_LIVE_CERTIFICATION_READY`. Until then, the candidate stands externally blocked, unpromoted, with LG01 untouched.
