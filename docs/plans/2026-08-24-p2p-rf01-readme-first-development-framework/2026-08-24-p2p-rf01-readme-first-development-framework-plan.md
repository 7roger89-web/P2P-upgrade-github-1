# RF01 README-First Project Orientation + Development Framework Revision Plan

## Metadata

- Date: `2026-08-24`
- Status: `active`
- Plan: `docs/plans/2026-08-24-p2p-rf01-readme-first-development-framework/2026-08-24-p2p-rf01-readme-first-development-framework-plan.md`
- Evidence: `docs/plans/2026-08-24-p2p-rf01-readme-first-development-framework/2026-08-24-p2p-rf01-readme-first-development-framework-evidence.md`
- Benchmark: `docs/plans/2026-08-24-p2p-rf01-readme-first-development-framework/2026-08-24-p2p-rf01-readme-first-development-framework-benchmark.md`
- Actual status: `docs/plans/2026-08-24-p2p-rf01-readme-first-development-framework/2026-08-24-p2p-rf01-readme-first-development-framework-actual-status.md`

## Goal

Implement RF01 on a new noncanonical development branch based exactly on sealed `.74`: provide a compact managed README orientation block, a deterministic fail-closed updater that preserves Owner-authored README text outside that block, and a single coherent product-development framework projection across existing authoritative development surfaces. Preserve `.19` as the official canonical baseline, preserve CPT01-R2 and the sealed `.74` artifact, and stop before C43 or any release/promotion action.

## Rules

- Complete P0 actual status before implementation work.
- The editable basis is `codex/p2p-post74-development-01` at closure commit `54d15cb02b04a0fea35fb7d2fd0af1fd564bb264`.
- Do not modify `codex/p2p-c74-successor-eval-lifecycle-01`, the sealed `.74` ZIP, CPT01-R2, or any release/promotion state.
- Keep `.19` official canonical and `.74` noncanonical/unpromoted. The external blocker remains `EXTERNAL_HOST_CAPABILITY_LIMITATION`.
- Keep canonical governance, FACT_LEDGER/Live Specs, existing Goal/approval policy, execution ledger, and existing router as the only authorities. README and framework documents are projections and must say so.
- Preserve Owner-authored README content byte-for-byte outside the managed marker block. Malformed or ambiguous markers fail closed; no whole-file rewrite.
- Use only standard-library/local deterministic code. Do not add a vector database, generic memory graph, daemon, orchestration framework, autonomous promotion, provider package, MCP setup, or background dependency.
- Run Anvien graph refresh before graph evidence, file-detail and impact before editing existing code/config surfaces, detect-changes before implementation commits, and commit each verified implementation slice.

## Problem

The development source has existing charter, roadmap, capability, governance, installer, and packaging surfaces, but no root README orientation contract and no explicit RF01 product-fast-loop/assurance-loop projection. The current `.74` lifecycle is sealed and host-capability-blocked, so ordinary development must be able to start from a truthful orientation without rediscovering release authority or accidentally treating a development candidate as promoted.

## Scope

- Add `README.md` with a compact managed block between `<!-- P2P:BEGIN ORIENTATION -->` and `<!-- P2P:END ORIENTATION -->`.
- Add a narrow standard-library `scripts/p2p_orientation.py` updater/parser with deterministic replacement, preservation, and fail-closed marker handling.
- Add behavior tests for insertion, replacement, idempotence, outside-content preservation, malformed markers, and routing guidance.
- Record RF01 in the existing charter/framework/governance development surfaces without replacing current canonical reconciliation governance.
- Make the README and orientation helper available through the existing release/package allowlists and installers without triggering automatic README mutation.
- Verify exact `.74` lineage/artifact immutability, source/closure relation, owner-content preservation, framework links, existing policy preservation, and no release/promotion mutation.

## Non-Goals

- No CPT01-R3, GitHub plan change, host-protection bypass, release candidate rebuild, package publish, promotion, deployment, merge, or external communication.
- No edit to the sealed `.74` ZIP or its source/closure branch.
- No change to `scripts/p2p_workflow.py` or `scripts/p2p_development_control.py`; their HIGH blast-radius surfaces remain preserve-only for RF01.
- No new router, agent, quorum, certification system, memory/RAG platform, scheduler, daemon, or vendor-specific routing.
- No claim that RF01 is canonical, promoted, independently certified, or release-ready.

## Requirements

1. The managed README block must state project identity/outcome, `.19` canonical baseline, sealed `.74` development base, `.74` unpromoted state, CPT01-R2 host limitation, active RF01 goal, blockers, invariants, AI start path, task-to-files routing, anti-overengineering order, deep-document links, and the exact disclaimer:
   `Implemented against sealed .74 NONCANONICAL DEVELOPMENT BASE. Official canonical baseline remains .19. Release/promotion authority remains deferred due to external GitHub private repository host-protection limitation.`
2. The updater must accept explicit managed content, preserve all text outside the block, replace exactly one valid block, append when markers are absent, and reject one-sided or duplicate markers.
3. The framework must distinguish PRODUCT FAST LOOP from ASSURANCE/RELEASE LOOP and record the state sequence `IDEA -> PROTOTYPE -> OWNER TRUTH -> IMPLEMENTATION -> SYSTEM TRUTH -> VERIFICATION -> RELEASE TRUTH`.
4. The framework must include measurable human-outcome acceptance, risk-proportional assurance, OXP read-only orientation, one-capable-agent-first execution, and the anti-overengineering order.
5. Existing development-control reconciliation fields remain valid; RF01 is an explicit noncanonical development-plane record and not a replacement for the current C-line governance contract.

## Acceptance Criteria

- [ ] README orientation is present, compact, linked, truthful, and does not claim promotion or authority.
- [ ] Updater behavior tests pass and prove the trigger -> process -> observable output, including malformed-marker fail-closed behavior.
- [ ] Existing README content outside the managed block is preserved exactly in a CRLF and LF fixture.
- [ ] Charter, product architecture, master roadmap, and development-control surfaces describe one RF01 framework without duplicate governance.
- [ ] Package/installer surfaces include the helper and README while installers never auto-edit a project README.
- [ ] Framework validation, focused tests, syntax checks, `git diff --check`, final Anvien analysis, and `anvien detect-changes --scope all` pass for the changed scope.
- [ ] Exact `.74` artifact SHA-256, source/closure commits, sealed branch, and `.19` canonical records remain unchanged.
- [ ] Supervisor review finds no release/promotion mutation, fake authority, dead work, or unauthorized platform/framework.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish the real current state.
  - Work Steps: inspect exact `.74` objects/artifact, refresh Anvien, inspect relevant SPEC/docs/governance/packaging surfaces, classify each target, and record downstream decisions.
  - Implementation Gate: completed in companion `actual-status.md` before any RF01 implementation edit.
  - Acceptance: target surfaces are classified with exact evidence IDs and preserve-only boundaries.

### P1: Implement RF01 orientation and framework projection

- Phase Goal: add the smallest truthful README-first orientation capability and update existing authoritative development projections without touching high-risk workflow/governance executors.
- Phase Boundary:
  - In scope: root README, new orientation helper/tests, charter/framework documents, development-plane metadata, package allowlists, installer script lists.
  - Out of scope: workflow/control executors, sealed candidate/branch, release build, promotion, deployment, external host actions.
  - Dependencies: P0 complete; exact `.74` base and blocker facts verified; all managed content supplied explicitly.
- Phase Implementation Rule: do not implement `P1` directly. Implement each slice in order, verify it, refresh actual status, and commit only after its acceptance passes.
- Ordered Slice List:
  - P1-A: deterministic README managed-block contract and behavior tests.
  - P1-B: framework and development-plane documentation/governance projection.
  - P1-C: package/installer availability with README mutation prohibition.

- [x] P1-A: Deterministic README managed-block contract
  - Goal: create the helper, root README projection, and behavior tests.
  - Scope Boundary:
    - Editable: `scripts/p2p_orientation.py`, `README.md`, `tests/test_p2p_orientation.py`.
    - Inspect-only: existing workflow and governance executors.
    - Preserve-only: historical `source/8.4.6-C/README*`, sealed candidate, Owner content outside markers.
    - Out of scope: automatic workflow integration and canonical fact writes.
  - Non-Goals: no fallback/mock orientation, no implicit promotion inference, no whole README rewrite.
  - Pre-flight Questions:
    - Data source: explicit managed block content supplied by this RF01 projection; deep links remain the authority.
    - Display permission: safe local project orientation only; no secrets or hidden reasoning.
    - DB read flow: N/A; no database.
    - DB write flow: N/A; only a user-selected README path may be updated.
    - Render location: repository root `README.md` and explicit target paths.
    - UI behavior flow: CLI/API call -> marker validation -> exact managed slice replacement -> observable file bytes.
    - Docker runtime: N/A; no app/runtime surface.
    - Playwright target: N/A; no browser surface.
    - Behavior test: Python unittest against temporary in-repo fixture paths.
    - Cleanup/quarantine: fixtures under repo `.tmp`; remove or quarantine after tests.
    - External side effects: none; no network, host, release, or promotion calls.
    - N/A notes: standard-library-only documentation tooling.
  - Work Steps:
    1. Implement marker parsing, exact slice replacement, append-on-absent, idempotence, and fail-closed malformed-marker behavior.
       - UI flow check: N/A; CLI/file observable behavior is the user surface.
       - DB/data flow check: N/A.
       - Render location check: assert prefix/suffix bytes remain unchanged.
       - Evidence target: `E1-P1A-ORIENT1..E1-P1A-ORIENT5`.
    2. Add the README projection and behavior tests, including LF/CRLF owner-content preservation and routing classifications.
       - UI flow check: N/A; inspect rendered Markdown text.
       - DB/data flow check: N/A.
       - Render location check: assert managed block markers and required disclaimer/links.
       - Evidence target: `E1-P1A-TEST1..E1-P1A-TEST4`.
  - Implementation Gate:
    - New helper has no existing symbol impact; tests must use temporary in-repo fixtures and no product-state path.
    - README content must keep canonical authority in deep documents and represent unknowns explicitly.
  - Acceptance:
    - Source: helper parses and replaces only one managed block.
    - Runtime/UI: N/A; local Markdown orientation is inspected as text.
    - DB/data: N/A.
    - Behavior test: all focused orientation tests pass.
    - Cleanup/quarantine: fixture roots are bounded to `.tmp` and cleaned/quarantined.
    - Evidence IDs: `E1-P1A-ORIENT1..E1-P1A-TEST4`.
    - Actual-status rows refreshed: README, helper, and tests transition from missing/partial to correct.
  - Evidence Targets: changed file list, required phrase/link inventory, test output, diff check.
  - Actual-status Update: record exact status transitions and the first implementation commit.
  - Commit Boundary: commit only the P1-A helper/README/tests slice after focused validation.

- [x] P1-B: Framework and development-plane projection
  - Goal: revise existing charter/framework/governance surfaces to state the two loops, lifecycle states, OXP direction, human outcomes, risk-proportional assurance, and RF01 roadmap.
  - Scope Boundary:
    - Editable: `docs/p2p-development/P2P-DEVELOPMENT-CHARTER.md`, `docs/p2p-development/framework/product-architecture.md`, `docs/p2p-development/framework/master-roadmap.md`, `governance/development-control.json`.
    - Inspect-only: `scripts/p2p_development_control.py` validator and generated/derived roadmap consumers.
    - Preserve-only: current `.19` and `.74` reconciliation fields, all prior decisions, sealed artifacts.
    - Out of scope: new governance engine or validator semantics unless a mechanical schema check requires it.
  - Non-Goals: no duplicate roadmap authority, no replacement of current development-control contract, no promotion.
  - Pre-flight Questions:
    - Data source: existing charter/framework/governance plus exact RF01 request and verified `.74` facts.
    - Display permission: development-plane status is noncanonical and explicitly labeled.
    - DB read/write flow: N/A; JSON/document edits only.
    - Render location: existing charter/framework/governance surfaces.
    - UI behavior flow: N/A; document projection is inspected with validators.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: framework validator plus charter/development-control tests.
    - Cleanup/quarantine: no generated temporary output retained.
    - External side effects: none.
    - N/A notes: existing authoritative surfaces remain the only source families.
  - Work Steps:
    1. Add the RF01 framework sections and exact disclaimer while preserving existing authority tables and prior roadmap decisions.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: Markdown headings/links and no duplicate governance claims.
       - Evidence target: `E1-P1B-DOC1..E1-P1B-DOC3`.
    2. Add a noncanonical development-plane object without changing the validator’s current reconciliation semantics; run JSON/framework/charter checks.
       - UI flow check: N/A.
       - DB/data flow check: validate JSON shape and preserve canonical fields.
       - Render location check: status projection and exact disclaimer.
       - Evidence target: `E1-P1B-GOV1..E1-P1B-TEST3`.
  - Implementation Gate:
    - `scripts/p2p_development_control.py` is HIGH and preserve-only; any required edit stops for a new impact review.
    - No field may imply `.74` promotion or host authority.
  - Acceptance:
    - Source: existing framework docs remain internally coherent and links resolve.
    - Runtime/UI: N/A.
    - DB/data: development-control JSON parses and canonical reconciliation remains valid.
    - Behavior test: scoped RF01/framework checks pass; the full legacy framework/charter gate remains blocked by a pre-existing capability-ledger schema/status defect at `capabilities[175]` and is not repaired in RF01.
    - Cleanup/quarantine: no generated release output.
    - Evidence IDs: `E1-P1B-DOC1..E1-P1B-TEST3`.
    - Actual-status rows refreshed: framework and development-plane metadata transition to correct.
  - Evidence Targets: diff, validator output, JSON-preservation comparison, link inventory.
  - Actual-status Update: record status transitions and second implementation commit.
  - Commit Boundary: commit P1-B after scoped documentation/governance checks pass; carry the inherited ledger gate as an explicit blocker.

- [ ] P1-C: Package and installer availability
  - Goal: expose the README and helper in the existing package/install allowlists while proving installers do not auto-edit project README content.
  - Scope Boundary:
    - Editable: `scripts/package_release.py`, `install.ps1`, `install.sh` only where the existing lists require the new helper/README.
    - Inspect-only: release builder execution and sealed artifact.
    - Preserve-only: installer managed `AGENTS.md` behavior and all project README content.
    - Out of scope: building a new release ZIP or installing into a user project.
  - Non-Goals: no release/promotion; no automatic orientation update during install.
  - Pre-flight Questions:
    - Data source: package root/script lists and existing installer copy lists.
    - Display permission: helper is explicitly invoked; installer has no README writer.
    - DB/data flow: N/A.
    - Render location: release root README and installed `.p2p/system/scripts/p2p_orientation.py`.
    - UI behavior flow: N/A.
    - Docker runtime: N/A.
    - Playwright target: N/A.
    - Behavior test: static installer inspection and package list tests/validation where available.
    - Cleanup/quarantine: do not invoke release builder; no generated artifact.
    - External side effects: none.
    - N/A notes: package availability is source-level only in this non-release goal.
  - Work Steps:
    1. Add the root README/helper to existing package/script lists after the recorded HIGH impact review of `package_release.py`.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: selected package paths are explicit.
       - Evidence target: `E1-P1C-PKG1..E1-P1C-PKG2`.
    2. Add helper copy entries to both installers and assert no README write path is introduced; do not execute an install.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: installer writes only the managed system script list and existing AGENTS block.
       - Evidence target: `E1-P1C-INSTALL1..E1-P1C-INSTALL3`.
  - Implementation Gate:
    - No release ZIP build is permitted in RF01; source-level allowlist validation is sufficient and explicit.
    - Existing `package_release.py` has 92 symbols, one inbound ref, seven flows, and HIGH risk; keep edits to list entries only.
  - Acceptance:
    - Source: package and installer lists include the helper/README as intended.
    - Runtime/UI: N/A; no install run.
    - DB/data: N/A.
    - Behavior test: static checks confirm no automatic README mutation.
    - Cleanup/quarantine: no release artifact generated.
    - Evidence IDs: `E1-P1C-PKG1..E1-P1C-INSTALL3`.
    - Actual-status rows refreshed: package/install binding transitions to correct.
  - Evidence Targets: changed list entries, static preservation scan, diff check.
  - Actual-status Update: record package/install status and forbidden release-build boundary.
  - Commit Boundary: commit P1-C after source-level checks pass.

### P2: Verification, supervisor review, and hard stop

- [ ] P2-A: Run focused tests, framework validation, syntax/build-equivalent checks, final Anvien analysis, immutability checks, and detect-changes.
- [ ] P2-B: Use the supervisor skill for zero-trust review of the plan, actual status, evidence, diff, and exact noncanonical boundary; repair only if the review identifies an in-scope defect.
- [ ] P2-C: Write coder/supervisor reports, refresh all ledgers, verify clean intended worktree state, commit closure metadata if needed, and stop. Do not start C43.

## Risk Notes

- The correct result may remain development-ready while release/promotion stays blocked; do not collapse these states.
- `scripts/p2p_workflow.py`, `scripts/p2p_development_control.py`, the release builder, and sealed candidate surfaces are high-risk or protected and are preserve-only unless a fresh scope decision is made.
- README claims are projections. If a fact is not verified from current local authority, write `UNKNOWN` or `OWNER_CONFIRMATION_REQUIRED`; never infer it from a profile, cached ref, fixture, or log.
- The exact required report disclaimer is repeated in the README and framework surfaces; it does not itself grant authority.
