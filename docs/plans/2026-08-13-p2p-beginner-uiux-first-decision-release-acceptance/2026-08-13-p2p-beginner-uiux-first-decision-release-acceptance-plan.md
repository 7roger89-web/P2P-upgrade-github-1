# P2P Beginner UIUX First-Decision & Release Acceptance Closure Plan

**Goal ID:** `goal-20260813-p2p-beginner-uiux-first-decision-release-acceptance`
**Date:** 2026-08-13
**Status:** BLOCKED — A/B/C and regression pass; fresh native acceptance and new-release acceptance do not
**Baseline:** `8.4.7-C-codex.12`
**Baseline artifact SHA-256:** `7250b5864ecc06afaf360ba72a44da674ea58c8acce643f8f5915a04f2437cfb`
**Companion evidence:** `2026-08-13-p2p-beginner-uiux-first-decision-release-acceptance-evidence.md`
**Companion benchmark:** `2026-08-13-p2p-beginner-uiux-first-decision-release-acceptance-benchmark.md`
**Companion status:** `2026-08-13-p2p-beginner-uiux-first-decision-release-acceptance-actual-status.md`

## Goal

Close the three explicitly remaining blockers for the P2P beginner UI/UX release-acceptance goal:

1. Make the first material planning classification for a concrete UI/UX outcome UIUX, before later capability routing.
2. Produce real, isolated baseline and current-P2P evaluation evidence, or revise the gate semantics honestly if a legitimate baseline cannot execute.
3. Individually classify and remediate the current governance-drift findings without a blanket whitelist or evidence deletion.

After those blockers pass, run exactly one new native beginner acceptance task. Create immutable patch `.13` only if the full acceptance contract and independent supervisor review pass. `.12` must remain untouched.

## Governing rules

- `p2p_uiux.router` remains the only router. No second router, capability, canonical agent, quorum system, or AESTHETICA promotion is allowed.
- Canonical identities remain exactly eight; denominator remains eight; `p2p_aesthetica` remains optional and noncanonical.
- The first-planning contract and later runtime routing are separate measurements. A later UIUX result cannot repair a wrong initial planning classification.
- Use outcome precedence, not a larger keyword list: concrete interface, usability, readability, accessibility, responsive, navigation, or interaction outcomes outrank generic beginner uncertainty.
- Preserve `p2p-idea` for undeveloped concepts, feature/product/gameplay ideation, and unknown product structure.
- Do not fabricate trial counts, receipts, specialist identity, or PASS evidence.
- Keep temporary paths below the repository `.tmp` directory. Do not modify the release ZIP, `.9`, `.10`, v5, immutable baseline, App Game Truyện, Logistics, or any user project.
- Do not request or perform release/promotion approval until the technical gates are PASS and the exact subject and technical-report hashes are bound.

## Current problem and boundary

The previous fresh beginner task ultimately produced a correct UI/UX result, but the first planning trace selected `p2p-idea` and only later self-corrected to UIUX. That proves a boundary leak between model/planner intent selection and the existing runtime capability router; it does not prove the runtime router is wrong.

The project evaluation suite was schema-valid but had empty `baseline_runs` and `p2p_runs`; it now contains real paired trial records and passes its policy gate. The governance drift gate reported 35 exact volatile-claim matches in unrelated MCP, payment, supervisor, and UI-taste material; each is now classified on its own evidence.

## Scope

### In scope

- Inspect and minimally correct the existing P2P planning/routing instruction boundary.
- Extend the first-decision evaluation contract so initial planning and final routing are separate fields.
- Run the real isolated project trials against frozen fixtures; add only the smallest evidence-runner support required by the existing schema.
- Forensically classify and narrowly remediate every current drift finding.
- Re-run the required regression, security, governance, lifecycle, host-receipt, fallback, and supervisor gates.
- If and only if all gates pass, build and verify immutable `8.4.7-C-codex.13`.

### Out of scope

- Any new capability or router.
- Host/API research, private APIs, network enablement, hooks/proxy changes, dependency installation, or user-project changes.
- AESTHETICA final behavioral value, Context Economics, Code-Impact, App Game Truyện, or Logistics upgrades.
- Optional hardening after the acceptance stop rule.

## Requirements and acceptance

The work is accepted only when RA1–RA24 from the attached goal are evidenced:

- RA1–RA5: first-planning root cause is proven; the smallest existing-router/instruction fix is applied; clear UIUX, IDEA, and mixed behavior is preserved.
- RA6–RA10: real baseline/current trial evidence exists or the gate is honestly corrected with a documented impossibility; no fabricated counts; every drift finding is classified and remediated without a blanket bypass.
- RA11–RA16: the new native beginner task passes from the first planning decision, material specialist routing behaves as required, any invoked AESTHETICA child has a fresh official receipt, and fallback remains functional.
- RA17–RA20: DW1–DW18, full regression, governance/drift, and secret/security checks pass.
- RA21–RA23: canonical count is 8, quorum denominator is 8, and fresh/upgrade/reinstall lifecycle checks pass for the new artifact if one is built.
- RA24: an independent supervisor reviews A–F and returns PASS.

## P0 — Actual status before implementation

P0 establishes the current evidence without changing runtime source. The current evidence is recorded in the companion evidence and actual-status files.

- `.12` is the immutable comparison candidate; preserve its recorded SHA-256.
- Prior verification recorded native AESTHETICA Level A, DW1–DW18, 64/64 full regression, canonical 8, fresh/upgrade/reinstall PASS, but release acceptance REJECTED because A/B/C were unresolved.
- The previous fresh task `019ffaea-1c46-7293-9b55-913045ed7038` is partial for this goal because its first planning selection was `p2p-idea` before UIUX.
- `.p2p/evals/suite.json` validates, but all five cases have empty baseline and P2P trial arrays; policy requires two trials per variant.
- The current drift finding set contained 35 exact matches; the final report classifies them as C/D scoped references and records zero active volatile findings.
- Anvien was refreshed with exclusions for `.tmp`, caches, and its own graph: 234 files, 9,501 nodes, 10,850 relationships, and 24 unresolved references. The relevant evaluation/governance surfaces are high-risk; `scan_volatile` has HIGH impact and three affected processes. The root is not a Git worktree, so Git diff/commit evidence is unavailable and must not be claimed.

**P0 decision:** Closed. P1–P4 technical work completed; the final native acceptance is BLOCKED and no `.13` packaging is authorized.

## P1 — First-decision root cause and minimal fix

### P1.1 — Trace the two decision surfaces

Inspect the primary `p2p` dispatcher, `p2p-idea` boundary, `p2p-uiux` boundary, and existing router/evaluation code. Record which text or trigger causes the first planning selection and which code performs later capability routing. Confirm that the fix is outcome precedence, not keyword accumulation.

### P1.2 — Apply the smallest existing-surface correction

Change only the existing P2P/UIUX/IDEA instruction or classifier surface needed to make concrete UI/UX outcomes win the first material planning decision. Keep genuine ideation and technical/backend boundaries intact. Do not add a parallel router or agent.

### P1.3 — Verify the first-decision contract

Add deterministic cases for clear UIUX, clear IDEA, mixed, beginner uncertainty, backend, cosmetic-only, accessibility, responsive, and greenfield visual direction. Each case must expose `INITIAL_PLANNING_CLASSIFICATION` and `FINAL_ROUTING_CLASSIFICATION`; clear UIUX cases must be UIUX initially.

## P2 — Legitimate project evaluation trials

### P2.1 — Freeze and hash the comparison inputs

Use the existing five project fixtures and their recorded hashes. Use isolated temporary roots and equivalent environment/criteria for both variants. Capture model/surface, command, timestamps, input/evidence hashes, and run IDs.

### P2.2 — Execute baseline trials

Run two independent baseline trials against the frozen suite using the legitimate pre-change candidate (`.12`) or, if the suite cannot execute against it, produce a concrete impossibility record. Never substitute a fabricated score or a copied result.

### P2.3 — Execute current-P2P trials

Run two independent current-source trials with the same fixtures and acceptance conditions. Record attempted, passed, partial, failed, outcome, and evidence for every case. Populate the suite only from these actual run records.

### P2.4 — Apply the quality-equivalence gate

Validate that the routing improvement does not pass solely by changing a label: final UIUX output must remain useful, bounded, accessible, non-backend, and implementation-feasible, with no regression against the baseline policy.

## P3 — Governance drift forensics and remediation

### P3.1 — Reproduce and enumerate exact findings

Run the drift scanner into a fresh repository-local `.tmp` report and inspect each finding with path, line/context, claim, source class, and current runtime reachability. Do not classify by directory alone.

### P3.2 — Assign categories A–F individually

Classify each exact claim as current material fact requiring ledger, stale, historical evidence, non-canonical reference, invalid/unsupported, or gate false-positive. For category A, use the existing FACT authority only. For B/C/D, normalize scope/status. For E, correct/remove the unsupported claim. For F, narrow the gate assumption. Preserve evidence.

### P3.3 — Re-run the governance gate

Verify that the remediation is narrow, that no second ledger or blanket ignore exists, and that all active volatile claims are ledger-authorized before continuing.

## P4 — Regression and final fresh acceptance

### P4.1 — Run all affected checks

Run first-decision evals, the 40-case routing suite, legitimate project trials, DW1–DW18, full unittest, Capability Foundation, DT1–DT24, host identity hook/receipt tests, fallback, governance/drift, secret scan, and canonical/quorum checks. Record evidence immediately for each completed slice.

### P4.2 — Run one new native beginner task

Only after A/B/C pass, use a new trusted native Desktop session and submit exactly one natural-language warehouse-dashboard request with no technical terms. The first material planning classification must be UIUX; there may be no initial `p2p-idea` selection or correction. If material specialist value is detected and AESTHETICA is invoked, require a new native child and an official receipt with `agent_type=p2p_aesthetica`, `source=codex_official_hook`, and `receipt.agent_id` equal to that child’s actual thread ID. Separately exercise unavailable fallback through the existing test mechanism.

## P5 — Candidate packaging, lifecycle, and independent review

### P5.1 — Build only after PASS

If source/runtime changes exist and all required gates pass, build `8.4.7-C-codex.13` without overwriting `.12`. Verify package checksums, package doctor, source inventory, protected-runtime lock, and rollback artifact.

### P5.2 — Verify installed lifecycle

Run fresh install, upgrade from `.9`, upgrade from `.10`, upgrade from `.12`, and same-version reinstall. Verify the installed runtime, custom profiles, hooks/receipt behavior, UIUX capability, optional AESTHETICA semantics, canonical 8, and no development-path leakage.

### P5.3 — Supervisor and closure

Prepare the technical report and request independent supervisor review of A–F, exact subject/report hashes, fresh receipt, trials, drift remediation, regressions, and lifecycle. A supervisor PASS is required before any release promotion. Stop at PASS, BLOCKED, or REJECT and do not begin out-of-scope goals.

### Final closure state

The fresh native task `019ffb17-8066-74b1-8973-4fc57080ac36` made no initial IDEA selection or correction and produced bounded UI/UX guidance, but ended `BLOCKED` because this repository has no warehouse-dashboard runtime. No fresh official AESTHETICA receipt matches that task. Fallback, regression, governance, and paired-eval evidence pass; the independent supervisor verdict is `REJECT` for release acceptance. The protected `.12` artifact remains the current candidate and no `.13` artifact was created.

## Required evidence and reporting

Use the companion evidence file for immutable IDs and command results, the benchmark file for measured trial/packaging data, and the actual-status file for the current matrix and refresh log. Every claimed PASS must point to a concrete artifact, command output, or official host receipt. A blocked gate remains BLOCKED; it is not converted to PASS by narrative.

## Risks and controls

- **Planner/runtime conflation:** keep the two classifications as separate fields and separate tests.
- **Over-broad IDEA weakening:** retain negative and greenfield ideation cases in every focused run.
- **Trial contamination:** use fresh isolated roots, frozen fixture hashes, and no cross-run memory.
- **Drift laundering:** retain the original finding, category, evidence, remediation, and post-remediation result for every claim.
- **Baseline ambiguity:** record impossibility rather than inventing baseline evidence.
- **Release contamination:** treat `.12` as immutable and package a new version only after the technical gate and supervisor PASS.
- **Host receipt mismatch:** compare official receipt `agent_id` to the actual new child ID; historical receipts do not satisfy this goal.
