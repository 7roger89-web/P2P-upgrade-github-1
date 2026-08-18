# C38 Operating Digest (PROVISIONAL)

**GOAL:** P2P-C38 — Live Role Certification & Multi-Backend Execution Proof. Falsifiable question: can the SAME P2P authority/role/context/permission/evidence model remain trustworthy when the real execution backend changes?

**CURRENT STAGE:** Stage A — AUTH / ELIGIBILITY PREFLIGHT (per C38 proof ladder §4).

**CURRENT TASK:** Recover CURRENT auth state for Manus / Hermes / Codex without exposing secret values; decide STOP vs. proceed to Stage B.

**ROLE:** Executor (human-in-the-loop Owner session; single canonical P2P role to be selected for proof: TBD after target selection).

**TARGET:** None yet — no backend currently known eligible (Stage A unresolved).

**PERMISSION:** Owner authorized C38 start. NOT authorized: secret disclosure, permission widening, production mutation, unbounded external spending, merge, promotion, release, deployment. Owner gates: real auth on supported host required before live proof; no auto-start beyond authorized scope.

**MUTATION STATE:** No C38 mutation. No branch created yet (per §24: branch only after preflight proves meaningful start). Working tree at C37 HEAD clean. Durable C37 truth preserved: candidate SHA 0f540edd... UNPROMOTED; closure CONSISTENT; 0 hard findings; current_development = C31/BLOCKED is EXPLAINED and must NOT be cosmetically repaired.

**RELEVANT EVIDENCE:**
- Starting truth verified 2026-08-18: branch p2p-c37-adaptive-target-model-effort @ 4e5ef54931bb623a6ba45ca325a920412e9fa131 (local == remote == expected), worktree 0 untracked/modified, candidate SHA256 matches.
- C35 canonical roles: p2p_iris, p2p_tecton, p2p_axiom, p2p_vector, p2p_datos, p2p_anon, p2p_architecton, p2p_helios (+ optional p2p_aesthetica). Source: `.p2p/system/p2p_capabilities/agent_role.py`.
- Adapters: `.p2p/system/p2p_capabilities/{manus,hermes}_adapter.py`, `backend_contract.py`, `backend_execution_bridge.py`. Contract: C34 ADAPTER_STATES 5-state chain; LIVE_CERTIFIED never blanket, scope-bound.
- Selection machinery: `.p2p/system/p2p_capabilities/selection_*.py` (8 modules) — hard gates CAPABILITY→CERTIFICATION→AUTH→PERMISSION→ENVIRONMENT→CONTEXT→QUALITY before cost/latency.
- Historical auth (HISTORICAL ONLY, not current eligibility): Manus C34 real live proof (task 8Eqa4QGo4x35raVTPnnA7c) then key REVOKED after git-history exposure; Hermes installed v0.20.2 no credentials; Codex 0.147.0 HTTP 401 pre-model.
- C31 reopen condition: fresh probe returns AUTH_REQUIRED or stronger on a supported host.
- **AUTH PATH CORRECTION (Owner review):** "Manus API connector in Settings → Connectors" does NOT exist as an auth mechanism. Correct path: Manus webapp → **API Integration settings → Create API Key** (v2 current, v1 deprecated; `x-manus-api-key` or OAuth2 bearer). Store key securely (env var / secret manager), never in chat or git. Suggested key name: `p2p-c38-live-certification`. If no secure secret input visible in UI, Owner screenshots the settings page (no key) and sends it.
- **STAGE B ENTRY SEQUENCE (agreed):** verify C37 HEAD = 4e5ef54 → create branch `p2p-c38-live-role-certification` → carry Stage-A evidence onto branch → secret-scan → commit Stage-A checkpoint → then live role proof. Evidence in sandbox only is NOT durable project state.

**VERIFICATION RULE:** REQUESTED_TARGET != OBSERVED_TARGET until evidence binds; CLAIM != EVIDENCE; unknowns remain UNKNOWN; fail closed on material unknown.

**NEXT SAFE TASK:** Perform auth preflight health checks (non-mutating, no secret values printed) for each backend; classify each AUTH_VALID / AUTH_INVALID / AUTH_ABSENT / AUTH_UNKNOWN; decide BLOCKED vs Stage B.
