# Supervisor Report: P2P-C15 Real Host Hardening and Lineage

Verdict: REJECT

## Metadata

- Report file: `rp_supervisor_260816_112735_by_gpt-5-codex_p2p-c15-hardening.md`
- Review time: `2026-08-16 11:27:35 +07:00`
- Reviewer: `gpt-5-codex`
- Repo/project: `P2P-8.4.6-C-Codex-Edition-v4`
- Scope reviewed: C15 hardening field proof and official `.19` integration lineage
- Claim reviewed: C15 is proven through a real host worker end-to-end and `.19 + C15` is integration-safe
- Authority used: latest user hardening brief, `AGENTS.md`, C15 plan/contracts, source, runtime evidence, official ZIP

## Executive Summary

- The generic Codex host subagent capability is real and one bounded read-only
  subagent completed successfully.
- The local C15 foundation remains internally coherent and its controls pass.
- The claim of end-to-end C15 live delegation is not proven because the local
  controller has no callable host callback/receipt adapter.
- The `.19 + C15` lineage is not proven; 403 mapped entries yielded 390 exact
  matches and 13 content/metadata mismatches, and the package guard rejects
  the `.15` development source below `.19`.

## Blocking Findings

### [P1] C15 native host callback/receipt bridge is unavailable

File: `.p2p/system/p2p_capabilities/bounded_delegation.py` and host boundary

Issue: A real `multi_agent_v1` subagent ran, but no C15 `WorkerHandoff` was
consumed by a host callback and no real host receipt was passed through the C15
parent-verification transition to a final C11 task transition.

Evidence: agent ID `01a008ca-1c74-7592-a316-4e45894027ce`, status `completed`,
read-only proposal; C15 field A-F remains local callback-backed only.

Why this blocks acceptance: the requested claim is specifically real-host
end-to-end C15 delegation, not merely generic host subagent availability.

Fix direction: provide a governed, synchronous C15 host callback/receipt
adapter in a future explicitly scoped task, without adding background,
parallel, scheduler, grandchild, or second executor behavior.

### [P1] `.19 + C15` integration lineage is not proven

File: `VERSION`, `manifest/package.json`, runtime manifests/locks, package
builder

Issue: Development `.15` is not byte-identical or provenance-equivalent to
official `.19`; C15 surfaces are absent from `.19`, while 13 mapped files differ.

Evidence: 403 remapped official entries; 390 exact matches, 13 mismatches;
package build returns `LINEAGE_REGRESSION` for `.15 < .19`.

Why this blocks acceptance: the user explicitly requires content-level lineage
resolution before declaring combined integration safe.

Fix direction: resolve lineage through the existing canonical release mechanism
in a separate protected task; do not relabel, overwrite, promote, or release
the current tree here.

## Source-Level Clearance Notes

- C15 strategy/handoff/verification source: clear for local bounded behavior;
  semantic fingerprint and one-child/proposal-only invariants remain intact.
- C11 `task_state.py`, C12 `foreground_execution.py`, C10 trace/evidence:
  clear and shared content hashes match official runtime mappings.
- Host integration surface: blocked; no native adapter exists.
- Package/release surfaces: correctly fail closed on stale lineage.

## Evidence Checked

Passed:

- Real subagent receipt and bounded worker proposal, no edits or side effects.
- Direct control and bad-result controls: `3/3 PASS`.
- Project field A-F: `all_checks_pass=true`.
- Prior current full regression: `218/218 PASS`; source hashes unchanged.
- Official ZIP SHA-256 matches required value.
- Content comparison: 403 entries mapped; 390 exact matches.

Failed:

- Real-host C15 end-to-end handoff/receipt/parent transition: not available.
- Combined `.19 + C15` lineage safety: not proven.
- Package build: blocked by `LINEAGE_REGRESSION`.

Not run:

- No combined artifact was built because the canonical lineage guard is a real
  blocker; no bypass was attempted.

## Invariant Closure

- affected invariants: host handoff/receipt binding and release lineage.
- sibling surfaces checked: C10 trace/evidence, C11 task state, C12 foreground
  execution, C15 controller/tests/field harness, package manifest/runtime
  mapping, official ZIP.
- residual unverified same-invariant surfaces: native C15 host adapter and
  canonical release assembly remain open.

## Required Fix List For Resubmission

1. Add or expose a governed C15 host callback/receipt adapter, then prove the
   exact handoff → real agent → receipt → parent verification → C11 transition.
2. Resolve `.19` versus development lineage using the existing protected
   release mechanism and fresh content/hash evidence.

## Overall Evaluation

The real host subagent field test is valid evidence that the current Codex host
can run one bounded read-only subagent. It does not prove the C15 controller is
integrated with that host surface. The local C15 foundation remains PASS, but
the hardening claim requested by this review is REJECTED. Do not begin C16,
promote, release, deploy, mutate Logistics, or simulate the missing bridge.
