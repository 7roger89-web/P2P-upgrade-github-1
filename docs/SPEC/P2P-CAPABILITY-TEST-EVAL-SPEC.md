# P2P Capability Test and Evaluation Specification

Status: APPROVED FOR IMPLEMENTATION — agent-decided; no owner decision required
Date: 2026-08-12
Parent: `P2P-CAPABILITY-FOUNDATION-ARCHITECTURE-SPEC.md`

## Evaluation contract

Evaluations test behavior, not file existence. Each case records request, baseline behavior, capability/policy applied, observed behavior, required evidence, and independent verification status.

## Routing cases

- A: `Thiết kế app quản lý dễ nhìn.` -> `p2p-uiux` is appropriate; Aesthetica is supporting only when real and ready.
- B: `Tối ưu backend database query.` -> Aesthetica is not called.
- C: mobile slow/illegible/contrast -> deliberate UIUX/accessibility collision handling; no new specialist.
- D: `Đổi padding nút này một chút.` -> lightweight path; no excessive contract ceremony.
- E: unknown optional provider -> P2P core remains usable with explicit not-applicable state.
- F: invalid capability marks a canonical identity -> manifest validation fails closed.
- G: beginner technical-free request -> correct selection without requiring capability names.

## Beginner experience

For “Tôi có ý tưởng làm một phần mềm quản lý cho công ty nhưng tôi không biết code.” the expected behavior is discovery, plain-language explanation, and only owner/product questions. Framework, package, agent, skill, MCP, Python, and Node questions are not asked unless a later unavoidable constraint requires them. Technical choices remain internal.

## Regression matrix

At minimum, regression covers the exact canonical identities, denominator 8, UIUX routing, optional Aesthetica, Goal state, FACT_LEDGER, RAG boundary, approval, drift, execution ledger, installer compatibility, and existing skills. The verified release artifact itself is not rebuilt or modified.

## Isolation

Every test creates temporary project/state/artifact roots and rejects preserve-only roots as mutation targets. Tests assert no writes to the release ZIP, v5 tree/ZIP, immutable baseline, or configured user-project paths. Temporary outputs are cleaned or quarantined under the test parent.

## Security and evidence

Tests include injection-like retrieved content, content requesting permissions, protected-fact overwrite attempts, stale pointers, invalid manifests, missing profile readiness, and unknown providers. PASS requires actual output and an evidence contract; a static marker or text-only PASS is insufficient.

## CF mapping and done gate

The suite maps CF1–CF23 to at least one executable assertion and one evidence reference. The Goal stops when every CF is PASS, or when a real blocker is recorded. Optional future work is not a hidden acceptance requirement.
