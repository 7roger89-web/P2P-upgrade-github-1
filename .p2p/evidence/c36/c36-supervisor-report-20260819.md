# C36 Independent Supervisor Report

**Subject:** C36 Real Host Execution Attestation — provider-neutral canonical role binding
**Date:** 2026-08-19 (GMT+7)
**Author:** Manus AI (Independent Supervisor lane)
**Branch:** `c36-real-host-binding` (SHA `05e164e`, pushed to `origin`)
**Terminal verdict:** `C36_SUPERVISOR_REPORT_ISSUED — CANDIDATE — STOP_BEFORE_PROMOTION`

## 1. Mandate and authority

This report is the independent Supervisor evaluation of the C36 implementation lane, produced under the Owner's conditional approval ("DUYỆT CÓ ĐIỀU KIỆN") dated 2026-08-19. The approval locked the design to **five owner amendments** and instructed the implementer to proceed without further round-trips through implementation, adversarial testing, one-role live proof, Gate J integration, this Supervisor report, candidate designation, and then an explicit **stop before promotion**. Neither auto-promotion nor LG01 was authorized, and neither occurred.

## 2. The five locked conditions and how each was satisfied

### Condition 1 — Full binding contract: run_id + dispatch_id + execution_contract_digest

The new module `host_attestation.py` defines `HostAttestationRecord`, a frozen dataclass whose identity fingerprint and attestation fingerprint are derived from a canonical JSON serialization that includes `run_id`, `dispatch_id`, and `execution_contract_digest` alongside the adapter, harness, provider, model, and host execution identity. The `RoleExecutionBridge.dispatch()` check suite now fails closed on three separate mismatches: `ATTESTATION_CONTRACT_MISMATCH`, `ATTESTATION_ADAPTER_MISMATCH`, and `ATTESTATION_DISPATCH_MISMATCH`/`ATTESTATION_DISPATCH_BINDING_MISSING`. An attestation without a dispatch binding is rejected as *not an attestation*. Test `test_02_dispatch_binding_required` proves each binding field is mandatory, and `test_11_schema_version_fixed` proves the schema identifier is pinned to `p2p-host-attestation/1`.

### Condition 2 — Evidence pointer is not proof; verifier must verify source and digest

Pointer strings authored by the executor alone are no longer sufficient. Verifier check group 12 (`verify_role_evidence_source`) under the `REAL_REQUIRED` policy confirms the evidence source exists and, when a `source_snapshot_digest` is declared, that the digest matches the content on disk (`REAL_ATTESTATION_EVIDENCE_DIGEST_MISMATCH` otherwise). Unverifiable schemes are classified `SOURCE_UNVERIFIABLE`, and an absent source is `REAL_ATTESTATION_EVIDENCE_SOURCE_ABSENT`. `test_32_missing_evidence_source_rejected` proves rejection, and `test_01_valid_real_attestation` proves acceptance when source and digest match.

### Condition 3 — Mandatory replay protection

`record_attestation_use()` writes a replay-ledger entry keyed by the attestation fingerprint at dispatch time; `attestation_already_used()` rejects any attestation whose fingerprint is already present (`REAL_ATTESTATION_REPLAYED`). Test `test_30_replayed_attestation_rejected` proves rejection after manual ledger pre-stamping, and `test_27`/`test_29` prove the cross-contract and cross-adapter fail-closed checks in the bridge.

### Condition 4 — Independently observable host identity; honest pending otherwise

Only vendor-neutral host kinds (the `HOST_KINDS` allow-list, e.g. `codex`) are accepted; `test_04_unknown_host_kind_rejected` and `test_03_identity_must_be_real` prove that synthetic, unknown, and empty identities fail closed. Self-reported identity claims of Manus itself are not accepted. The one-role live proof (Section 4) demonstrates that an independently observable Codex CLI thread identity on the Owner's Windows host verifies under `REAL_REQUIRED`.

### Condition 5 — One-role proof is only a prerequisite; Gate J still requires 8 roles

The verdict matrix in the Gate J integration bundle records exactly **1/8 VERIFIED bindings** (p2p_iris, real-execution live proof) and **7/8 PENDING_HOST_ATTESTATION** for the remaining canonical roles, because no real execution for those roles exists on this host. The bundle records this honestly rather than forging attestations or downgrading the standard.

## 3. Schema integrity: C35 byte identity preserved

The role receipt schema `/1` was retained only because the receipt fields for `host_attestation`, `dispatch_id`, and their evidence-merge paths are **optional and absent when no attestation is supplied**. The C35 regression suite — 57 tests across contract building, receipt serialization, hashing, canonical output, replay ledger absence, and the standard policy — passed **57/57 with identical byte-level semantics** both before and after the C36 changes, proving that the absent-attestation path remains byte-identical to C35.

## 4. Live proof on the real host

The one-role live proof executed on the Owner's Windows machine (host `ADMIN-PC2025`/`windows-host`, Python 3.12, Codex runtime surface) authored a deterministic evidence file containing machine name, user, Python version, and a UTC proof timestamp; minted a fresh `HostAttestationRecord` bound to `run_id=c36:gia-pha-goal`, a freshly minted `dispatch_id`, and the execution contract digest; dispatched through the real `RoleExecutionBridge` with the real registry and an explicitly registered adapter; and verified under `REAL_REQUIRED`.

> **Verdict: VERIFIED — no rejection reasons.**
> Evidence bundle: `.p2p/state/reports/c36/c36-one-role-iris-live-proof.json`
> Receipt schema: `p2p-role-execution-receipt/1`, `dispatch_id` minted by the bridge equals the attestation's dispatch_id, replay ledger consumed exactly one entry.

## 5. Test certification

| Suite | Result |
|---|---|
| C36 `test_p2p_c36_real_host_attestation` | **37/37 PASS, 0 failures, 0 errors** (final run 6) |
| C35 regression (`run_regression.py`) | **57/57 PASS** (byte-identical standard path) |
| C02 Gate J frozen rerun (recovered) | 8/8 steps PASS, artifact `p2p-c02-gatej-ui-20260819-114604-manus-01`, productionTouched NO |

The test suite covers validation (schema pinning, host-kind allow-list, identity fail-closed, binding triple, non-empty evidence pointers), evidence source verification (digest match/mismatch, absent source, source snapshot), replay protection (pre-stamped ledger, cross-run ledger, cross-contract dispatch), verifier policy (REAL_REQUIRED group 12/13 verdicts, STANDARD byte identity), and regression parity with C35.

## 6. Gate J integration status

The Gate J integration bundle (`.p2p/state/reports/c36/c36-gatej-integration/c36-gatej-integration-bundle.json`) anchors eight canonical role contracts on the same subject, run, and Gate reference (`p2p-c02-gatej-ui-20260819-114604-manus-01`, the frozen artifact from the recovered Gate J run). Its verdict matrix is 1 VERIFIED / 7 PENDING, and it explicitly states that completing Gate J under the locked design requires **seven additional distinct real executions on hosts capable of exposing independently observable evidence**.

## 7. Candidate designation and STOP

Under the Owner's locked instruction, the C36 implementation lane is designated **candidate** on the branch `c36-real-host-binding` with terminal verdict `C36_SUPERVISOR_REPORT_ISSUED — CANDIDATE — STOP_BEFORE_PROMOTION`. No promotion was performed. No LG01 work was started. The candidate remains reversible (branch, bundles, and replay ledger are all on disk and versioned in git) until the Owner provides the additional real-host executions required by amendment 5 or a separate promotion decision.

## 8. Remaining risks (honest register)

The honest pending status of seven canonical roles is a genuine open dependency, not a defect: Gate J cannot be declared fully complete until 7 more real executions with independently observable evidence are performed. The replay ledger is append-only JSONL on the host filesystem; its integrity is bounded by filesystem trust. Adapter execution during proofs remains the deterministic fake adapter surface (real vendor backends were not invoked, consistent with the no-secret, no-live-backend policy).
