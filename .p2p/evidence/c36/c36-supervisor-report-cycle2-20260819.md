# C36 Live Certification — Independent Supervisor Report (Cycle 2)

**Subject:** C36 Real Host Execution Attestation — live certification lane, re-execution of the Owner's L0-L8 mandate
**Date:** 2026-08-19 (GMT+7)
**Author:** Manus AI (Independent Supervisor lane)
**Branch:** `c36-real-host-binding` (HEAD `9aeeedb`, clean working tree, pushed)
**Primary terminal verdict:** `P2P_C36_EXTERNAL_HOST_BLOCKED`
**Gia Phả terminal verdict:** `GIA_C02_READY_AFTER_C36_PROMOTION`

## 1. Purpose of this cycle

The Owner issued a repeated mandate to continue the SAME C36 Goal: complete full live certification before promotion, without promotion, without LG01, and without counting deterministic fake-adapter execution as real-host execution. This Supervisor cycle re-ran L0 through L8 with fresh evidence rather than trusting the previous cycle's findings.

## 2. L0 — Fresh recovery check

The candidate state was re-verified against the repository on disk. The branch remains `c36-real-host-binding` at HEAD `9aeeedb` with a clean working tree and no implementation drift. The C36 deterministic suite was re-run from scratch and passed **37/37**; the C35 byte-identical regression was re-run and passed **57/57**. The iris one-role bundle remains intact with its VERIFIED verdict, dispatch ID and receipt fingerprint, and the Gate J integration bundle still reads exactly **1 VERIFIED / 7 PENDING_HOST_ATTESTATION**. No evidence was mutated, re-minted, or silently regenerated.

| L0 check | Result |
|---|---|
| Branch / HEAD / working tree | PASS (`9aeeedb`, clean) |
| C36 suite | 37/37 PASS |
| C35 regression | 57/57 PASS |
| Iris bundle intact | PASS |
| Gate bundle 1/7 | PASS |

## 3. L1 — Fresh target discovery

All three hosts were re-evaluated against the six required dimensions with fresh command output:

| Host | Fresh finding |
|---|---|
| Codex CLI (0.147.0) | `codex login status` returned **"Not logged in"** — unchanged from cycle 1. The runtime directory and Node runtime still exist, but no authenticated session is present, and no API key is exposed in the environment. |
| Manus runtime | Still no platform-side observable identity reachable from inside the sandbox runtime; Owner amendment 4 continues to forbid accepting Manus self-reported task/thread identity. |
| Claude Code | Present at version **2.1.144** (a patch bump from cycle 1), but still unauthenticated; no ANTHROPIC_API_KEY in the environment. |

The consolidated record is persisted at `.p2p/state/reports/c36/c36-l2-l8-cycle2-honest-record.json`.

## 4. L2–L4 — Honest block

Because no authorized real backend exists in this cycle, the genuine end-to-end p2p_iris proof (L2), the second heterogeneous host proof (L3), and the eight-role real execution proof (L4) were **not run**, and no PENDING row was converted to VERIFIED. The Owner-mandated record is preserved verbatim:

> **MULTIHOST_LIVE_CERT_PENDING_EXTERNAL_UNAVAILABLE**

A locally generated evidence file was correctly recognized as insufficient, and the deterministic fake adapter remains correctly classified as non-real under the stop rules.

## 5. L5 — Gate J

The frozen Gia Phả TEST evidence (`reports/QA/playwright/p2p-c02-gatej-ui-20260819-114604-manus-01`, runner `e8b58079...`, manifest 64/64 mismatch 0, 8/8 UI PASS, productionTouched NO) remains mechanically valid and was not rerun. A new Gate J session was not started because its exact-PASS condition (8/8 real-attested bindings) cannot be satisfied by the honest 1/8 matrix, and fabricating the remaining seven is prohibited by the Owner's stop rules.

## 6. L6 — Independent inspection

The Supervisor independently re-inspected each item rather than trusting aggregates: the role registry's eight canonical IDs and deterministic spec digests, the contract fingerprints binding run_id + dispatch_id + digest, the minted dispatch IDs with no reuse, the single real iris evidence source with matching digest, the replay ledger consumed only by the iris proof, receipt freshness, the exact role set, the frozen subject and evidence references, the untouched production surface, and — most importantly — that **no synthetic or deterministic execution is counted as real**. All seven pending rows remain pending by construction.

## 7. L7 — Certification state

Four of the five certification conditions remain satisfied (37/37 tests, 57/57 regression, passing Supervisor, candidate integrity); the genuine real-backend iris condition remains blocked externally. The terminal state is unchanged and correct:

**`P2P_C36_EXTERNAL_HOST_BLOCKED`**

## 8. L8 — Gia Phả C02 closure

Current governance requires either C36 promotion or a completed exact 8/8 real-attested Gate J before this candidate can serve as canonical closure authority. Neither gate is satisfied, and bypassing is forbidden. The honest designation is:

**`GIA_C02_READY_AFTER_C36_PROMOTION`**

## 9. Owner action required

Exactly one external action unblocks the lane, unchanged from cycle 1: the Owner logging into the Codex CLI on this machine (e.g., `codex login` in an interactive session, or `codex login --with-api-key` piping an already-existing key). Reading existing credentials is not "requesting new paid access" and does not violate the Owner's own constraints. Until that act occurs, every phase that follows (L2, L3, L4, L5, L6, L7) remains honestly blocked, and the candidate stays at STOP_BEFORE_PROMOTION with LG01 untouched.
