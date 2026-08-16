# Supervisor Report: P2P-C07 supported live A/B boundary

Verdict: PASS

## Metadata

- Report file: `reports/supervisor/rp_supervisor_260814_130000_by_gpt-5-codex_p2p-c07-live-ab-boundary.md`
- Review time: `2026-08-14 13:00:00 Asia/Saigon`
- Reviewer: `gpt-5-codex`
- Repo/project: `P2P-8.4.6-C-Codex-Edition-v4`
- Scope reviewed: current development-source C07 boundary, immutable `.17`
  candidate, C1/C7 native-host receipts, artifacts, tests, gates, and reports
- Claim reviewed: `SUPPORTED_LIVE_AB_BOUNDARY_READY` for the bounded C1 plus
  one non-trivial C7 paired A/B slice
- Authority used: attached P2P-C07 request, repository `AGENTS.md`, active
  C07 plan/acceptance criteria, source contracts, existing host hook and
  Execution Ledger, current runtime/test evidence
- Related artifacts: coder handoff, paired-live aggregate, four receipt/output
  roots, `.15`, `.16-r2`, and `.17` package hashes

## Executive Summary

- Problem: the supported C06 context modes needed a real supported Codex host
  execution boundary without relabeling the existing local proxy.
- Decision: PASS. Current source inspection, independent receipt/artifact
  validation, focused/full tests, package/lifecycle checks, governance and
  capability gates, and fresh native-host evidence close the bounded invariant.
- Required outcome: accepted for this C07 boundary only. This is not a quality,
  efficiency, token, cost, release, or deployment claim.

## Source-Level Clearance Notes

- `.p2p/system/p2p_capabilities/live_execution.py`: clear for the reviewed
  scope. Lines 364–454 validate scenario/mode/context/artifact/fixture/request
  bindings and emit `runtime_task_execution=false` before host execution;
  lines 602–737 require supported host completion plus a fresh official identity
  receipt, capture output, label telemetry, and append only the existing live
  event; lines 740–758 keep the host integration as one injected executor
  seam. The module is standard-library-only and has no provider client or
  credential path.
- `.p2p/system/p2p_capabilities/context.py`: clear and preserved. The existing
  C06 builder remains the source of actual A/B payloads; no existing production
  symbol was edited. Anvien impact for `build_context_view` is LOW with zero
  direct upstream nodes.
- `.p2p/system/scripts/p2p_host_identity_hook.py` and `.codex/config.toml`:
  clear and preserved. Fresh receipts use the existing official hook schema and
  source; no private RPC, UI scraping, or self-reported host identity was used.
- `scripts/p2p_eval.py`: clear and preserved as proxy-only. Its local path is
  not promoted and the focused proxy test keeps live status false.
- `tests/test_p2p_live_execution.py`: clear. It directly covers the new
  fail-closed contract, including stale/request/root/artifact/secret,
  delegation, host identity, output, and proxy cases.

## Evidence Checked

Passed:

- Independent current receipt/artifact check: four accepted trials, C1/C7
  pairs, four `runtime_task_execution=true` receipts, four existing-ledger
  events, distinct A/B context fingerprints, equal requested execution
  fingerprints within each pair, disjoint roots, output hashes, official hook
  identity, and all telemetry authority labels valid.
- Focused C07/context/identity suite: 28/28 PASS.
- Full repository regression: 101 tests, 173.397 seconds, OK.
- Decision Trace DT1–DT24: 24/24 PASS in the supported evaluator environment.
- Candidate package verify: PASS, 399 files / 400 checksums; extracted build
  check verify and package doctor also PASS.
- Candidate lifecycle: fresh install, `.15` upgrade, and same-version
  reinstall PASS with protected state unchanged.
- Capability doctor: PASS; canonical denominator 8, full quorum 8/8, Aesthetica
  resolved as optional/noncanonical, no simulated execution identity.
- Governance drift and source metadata drift: PASS.
- Scoped secret scans for the changed capability modules, host hook, and UI/UX
  runtime: PASS with no findings.
- Root and `p2p-system` Anvien graphs are fresh; the new module is parsed.

Failed or limited, with disposition:

- Broad inherited secret scan reports the same documented
  `ghp_xxxxxxxxxxxxxxxxxxxx` placeholder in duplicated marketplace reference
  files. It is not a credential and is outside the changed C07 source; the
  changed-scope scans are clean.
- `anvien detect-changes` cannot run because the workspace has no `.git` and
  returns `Git diff failed: exit status 129`; artifact/source hashes are the
  applicable checkpoint and no commit is claimed.
- The evaluator’s optional repo-local-temp rerun makes existing CF15 fail
  because the foundation test intentionally rejects targets inside the
  preserve-only repository root. The supported evaluator run with its own
  isolated temporary root passes DT24; this is a harness-location conflict,
  not a C07 regression.
- Two native host attempts completed without a matching official identity
  receipt. They are explicitly classified as host-evidence capture failures
  and were not certified; no fabricated receipt was accepted.

Not run:

- The remaining ten live scenarios, full-12 benchmark, quality scoring,
  efficiency/non-inferiority analysis, provider token/cost measurement, and
  release/deployment gates. These are explicit C07 non-goals or protected
  follow-up work.

## Invariant Closure

- Affected invariant: exact C06 context payload → supported host request →
  official host identity → captured output → existing Execution Ledger receipt.
- Sibling surfaces checked: context builder and tests, proxy evaluator, host
  hook/config, artifact/package/lifecycle paths, existing ledger, focused/full
  tests, capability/governance/secret gates, and the C07 plan/evidence/report
  files.
- Residual unverified same-invariant surfaces: none for the bounded C1/C7
  acceptance slice. The ten unexecuted scenarios are intentionally outside the
  live certification scope, and no claim is made for them.

## Overall Evaluation

The prior Supervisor report accepted only the old blocked boundary and expressly
did not certify live execution. This review independently inspected the new
source and current evidence. The new boundary is fail-closed for proxy,
stale, unsafe, secret-like, artifact-mismatch, missing-identity, and recursive
delegation paths. Four fresh native-host executions prove the requested C1 and
C7 chains with the correct C06 context modes and fingerprints. The remaining
risks are disclosed non-goals or inherited tooling limitations, not open
acceptance defects for this bounded slice. The C07 plan may close with terminal
`PASS` and must stop without additional live scenarios or release activity.
