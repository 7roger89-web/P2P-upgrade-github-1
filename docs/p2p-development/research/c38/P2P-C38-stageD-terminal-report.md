# P2P-C38 Stage-D Terminal Report

**Stage:** D — Fresh-Session / Continuation-Capsule Proof
**Goal:** C38 — Live Role Certification & Multi-Backend Execution Proof
**Date:** 2026-08-18 (GMT+7)
**Report identity:** `c38-stage-d-terminal-report-v1`
**Authority:** Independent (evidence-based, fail-closed)

---

## 1. Verdict

**STAGE_D_INDEPENDENT_VERDICT: VERIFIED — `failure_class: NONE`**

Independent verifier (`p2p-role-execution-verifier/1`, fail-closed, 11/11 check groups):
`verdict: VERIFIED`, `reasons: []`, `failure_class: NONE`.

Capsule-specific behavioral checks (exact string equality, all `true`):

| Check | Answer value | Capsule value | Result |
|---|---|---|---|
| `challenge_id_exact_match` | `challenge-1d19b45139c2ae99` | same | TRUE |
| `challenge_hash_exact_canonical` | `7eb15e5ac78c...eadaad86d7f` | same (canonical fp) | TRUE |
| `git_revision_exact_match` | `2a371777438c...4283d8bed` | `current_verified_git_revision` | TRUE |
| `stage_exact_match` | `D` | `current_stage: D` | TRUE |
| `owner_gate_exact_match` | `SECOND_BACKEND_AUTH_REQUIRED` | `current_owner_gate` | TRUE |
| `capsule_integrity_ok_true` | `true` | — | TRUE |

## 2. What was actually run

A **genuinely new Manus execution** was dispatched through `manus_adapter.py` under `RoleExecutionContract(task_id=c38-stage-d-fresh-session-capsule-proof)`. The delivered context was **the continuation capsule alone** — no Stage-B transcript, no conversation history, no parent session state. The fresh executor reproduced the **unpredictable 16-hex-char capsule challenge ID** (`secrets.token_hex(8)`, entropy ≈ 2^64) and computed `challenge_hash = sha256(canonical(capsule_id))` exactly, which is only possible if the capsule content was read in that execution.

| Evidence item | Value |
|---|---|
| Stage-D task id | `JpWLAR4CcaG4qkXvN96etX` |
| Stage-B task id (distinct) | `NWnoWkrrJeQiYWZMv8jCS5` |
| Adapter result | `SUCCEEDED` / `stopped` / `auth_state_after=VALID` / no error |
| Execution latency | ≈ 5.7 s (1787038924653 → 1787038930330) |
| Credit usage | `0` (source: `task.detail.credit_usage`; no cost inference) |
| Mutation state | `NO_MUTATION_OBSERVED` (NON_MUTATING_TASK) |
| Independent observation | `GET /v2/task.listMessages` — not executor self-claim |

## 3. Honest classification (no overstatement)

**`FRESH_EXECUTION_CAPSULE_RECOVERY: VERIFIED`** — a fresh task read the capsule and reconstructed P2P task state exactly.

**`SESSION_DEATH_RECOVERY: NOT_PROVEN`** — the Manus API layer provides no mechanical guarantee that cross-task memory is absent. Behavioral proof (unpredictable challenge reproduced) covers capsule read; it does not mechanically exclude hidden provider-side session memory. This classification follows the P2P deliverable != read rule.

One rehearsal call (`c38-stage-d-fresh-session-capsule-proof-01`, aborted by an adapter-attribute bug before evidence capture) was made before the final call; both were bounded, non-mutating, and its transient task id was never used in any claim. Total Stage-D live calls: 2 task.create (1 rehearsal, 1 final).

## 4. Terminal state and stop condition

C38 goal state after Stage D:

| Stage | Status |
|---|---|
| A (Bootstrap + Auth preflight) | DONE — BLOCKED originally, unlocked by Owner-provided Manus key |
| B (First live role proof) | VERIFIED — independent, failure_class NONE |
| C (Second backend proof) | **BLOCKED** — Codex `AUTH_INVALID` (HTTP 401, durable), Hermes `AUTH_ABSENT` |
| D (Fresh-session capsule proof) | **VERIFIED** — failure_class NONE |

**Terminal verdict: `BLOCKED / OWNER_AUTH_REQUIRED_FOR_SECOND_BACKEND`.** The C38 goal required two certified backends; only one (Manus, `AUTH_VALID`) is available. Stage C cannot be entered from here. **No candidate minted.** Per C38 rules I do not mint a PARTIAL candidate without explicit Owner instruction.

## 5. What the Owner must do to unblock

Provide working authentication for **one** of: (a) Codex (resolve the 401 — valid token/model entitlement), or (b) Hermes (install + credential). Resume point on reconnection: Stage C, `docs/p2p-development/research/c38/c38-operating-digest.md` + `c38-task-graph-revision.md` (both durable on branch `p2p-c38-live-role-certification`).

## 6. Evidence pointers (all on branch `p2p-c38-live-role-certification`)

`docs/p2p-development/research/c38/evidence/`: `c38-stage-d-continuation-capsule.json`, `c38-stage-d-delivery-receipt.json`, `c38-stage-d-role-contract.json`, `c38-stage-d-live-receipt.json`, `c38-stage-d-messages-observed.json`, `c38-stage-d-observation.json`, `c38-stage-d-role-receipt.json` (verifier VERIFIED).
`docs/p2p-development/research/c38/harness/`: `c38_stage_d_capsule_build.py`, `c38_stage_d_fresh_execution.py`, `c38_stage_d_observe_result.py`, `c38_stage_d_independent_verify.py`.
Prior stages: `c38-task-graph-revision.md`, `c38-operating-digest.md`, Stage-A evidence (`c38-auth-preflight*`, `P2P-C38-stageA-terminal-report.md`), Stage-B evidence (`c38-stage-b-role-contract.json`, `c38-stage-b-live-receipt.json`, `c38-stage-b-role-receipt.json`, `P2P-C38-stageB-terminal-report.md`).

## 7. Security posture

Secrets never enter the repository or chat-adjacent files: the Manus key lives only at `/home/ubuntu/.secrets/manus_api_key` (0600, out of repo). Secret-scan of every commit passed (no secret patterns in evidence). Git HEAD advanced from `2a37177` (Stage-B checkpoint) through Stage-D checkpoints to `d99e6c1` (this report).
