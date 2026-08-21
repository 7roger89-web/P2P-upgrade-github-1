# Supervisor Report: Canonical lineage repair successor candidate 01A

Verdict: PASS

## Metadata

- Report file: `reports/supervisor/rp_supervisor_260821_234102_by_gpt-5-codex_p2p-canonical-lineage-repair-01a.md`
- Review time: 260821 234102 Asia/Saigon
- Reviewer: gpt-5-codex
- Repo/project: P2P-upgrade-github reconciliation worktree
- Scope reviewed: `codex/p2p-canonical-lineage-repair-01a`, candidate `.72`, source binding commit `6f88798cb3c7008167e5dd071247a4279cb31f3e`, post-mint evidence commit `ee1dfca`
- Claim reviewed: one clean, provider-neutral, unpromoted successor candidate was rebuilt from `origin/main` `.19` and verified without live Manus credentials.
- Authority used: latest Owner instruction `P2P-CANONICAL-LINEAGE-REPAIR-01A`, repository `AGENTS.md`, `origin/main`, package contract, source/runtime, current tests, disposable pilot, and Anvien.
- Related artifacts: candidate identity report, pre-mint disclosure, recovery matrix, authority model, historical blocker, candidate ZIP.

## Executive Summary

- Problem: prior independent audit found multiple competing historical governance authorities and the earlier candidate path was blocked by missing live Manus credentials.
- Decision: PASS for the requested candidate scope, with the explicit disclosures below. The official `.19` baseline is unchanged; no promotion or authoritative project mutation occurred.
- Required outcome: accepted as an unpromoted successor candidate, not as an official release or promotion.

## Source-Level Clearance Notes

- `scripts/package_release.py`: clear. `source_binding()` at line 212 requires a clean worktree and verifies commit/tree objects; the runtime staging, staged checksum, deterministic snapshot normalization, metadata, and disclosed drift gate are implemented at lines 312, 390, 410, 449, and 648-716. The candidate ZIP independently verifies against the recorded source commit/tree and package metadata.
- `governance/development-control.json`: clear. The official baseline remains `.19` with the canonical SHA; candidate binding is separate and records `.72`, artifact SHA, source commit/tree, and `MINTED_UNPROMOTED_CANDIDATE`.
- `reports/reconciliation/p2p-canonical-lineage-repair-01a-candidate-identity.json`: clear. It records the exact artifact identity, inventory, archive safety, pilot, Manus disclosure, regression, and safety evidence without claiming promotion.

## Evidence Checked

Passed:

- `origin/main` remains `bda3e228e67d1ca117e6b3105e920445830b4a0d`; official artifact identity remains `.19` / `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`.
- Candidate ZIP exists once at `.tmp/candidates/P2P-8.4.7-C-Codex-Edition-v72.zip`; Python hashlib and PowerShell `Get-FileHash` both produce `70613080d2ddbb92a52d2d79186e125439ec7f5ba8a6fa87bda9208d1b39d872`; size is 2,899,774 bytes.
- `scripts/package_release.py --root .tmp/pilot-v72/package --package .tmp/pilot-v72/package verify` passes with source commit `6f88798cb3c7008167e5dd071247a4279cb31f3e`, source tree `a03b8d76fcd018ebd4e7064dc6c85aae058d392e`, and 491/491 accounted archive members.
- Inventory/checksum/archive checks are all closed: unaccounted 0, duplicate 0, unsafe 0, absolute 0, missing expected 0, inventory match TRUE, checksum match TRUE, mismatch count 0.
- Candidate `install.ps1` into disposable `project-ps1` passes and candidate `doctor.ps1` returns `RESULT: PASS`; exact project pin is verified against `.72`, its artifact SHA, and official `.19`.
- MAP-BEFORE-WORK pilot proves fresh-map authorized mutation allowed, stale-map mutation blocked, missing-map mutation blocked, and context-ready permission denial blocked.
- Local Manus adapter conformance passes without credentials; P2P request identity is separate from backend task identity and unauthenticated execution returns `AUTH_REQUIRED`.
- Live Manus is intentionally `NOT_RUN / NO_CREDENTIALS`; no credentials were requested and no historical or synthetic live IDs were reused as fresh proof.
- Native council remains honest: backend-attested internal members, raw results and per-member failure supported, per-member external IDs and direct child control not exposed/supported, adapter feasible; canonical denominator remains 8 and quorum 8/8.
- FW05 A-Z negative matrix is 26/26 and fail-closed 26/26; the focused runner reports 29 tests OK with one unrelated absent-project shadow skip.
- Regression: full capability discovery 335/335 PASS with 6 skips; focused C35 provider-neutral suite 57/57 PASS; bounded FW suites 94/94 PASS; new unexplained failures 0.
- Security/portability/safety checks record no new secret findings, zero runtime absolute mint-path dependencies, preserved provider neutrality, absent authority widening, and zero Game Truyện/Gia Phả/Logistics/authoritative-project mutation.
- `anvien analyze --force` completed with 848 files scanned, 159 parsed code files, 0 parse failures. `anvien detect-changes --repo <reconciliation-worktree> --scope all` reports only the post-mint governance file as changed, low risk, with no affected symbols or processes.
- `git diff --check` passes and the review worktree is clean.

Failed or disclosed, not silently promoted:

- Governance drift audit is `FAIL_DISCLOSED`: pre-existing FACT_LEDGER/Live Specs/technical-preview/approval hash drift remains. The candidate builder reports it instead of rebuilding protected Live Specs or manufacturing approval. This does not change official authority or promotion state.
- The strict installed-role Python Doctor reports the same disclosed governance drift; the required project-local installation Doctor is the package `doctor.ps1` path invoked by `install.ps1`, and that path is HEALTHY. The distinction is recorded in the candidate identity report.
- The initial source-only installer probe was incompatible with the package's installed-project layout; it was a disposable failed probe. The final candidate install path is the packaged `install.ps1`, which passed.

Not run:

- Live Manus transport sentinel and material external result: not run because this host has no credentials, per Owner instruction. This is a disclosure, not a candidate blocker under 01A.

## Invariant Closure

- affected invariant: one canonical authority (`origin/main` `.19`) with one separate, clean, unpromoted successor candidate; provider-neutral execution; map-before-work mutation safety; artifact/source/inventory/checksum binding; no authoritative project mutation.
- sibling surfaces checked: governance control, package manifest, runtime capability registry, runtime adapters, installer/Doctor, project pin, map gate, FW05 A-Z matrix, full capability tests, archive metadata, source Git objects, Anvien graph/change detection, and disposable pilot.
- residual unverified same-invariant surfaces: none for the requested candidate scope. Live Manus external execution remains explicitly uncertified because credentials are unavailable.

## Overall Evaluation

The candidate claim is accepted only at the requested `PASS_WITH_DISCLOSURES` boundary. `.19` remains official, `.72` is exactly one externally bound candidate, and the branch is not promoted. The governance drift and absent live Manus evidence are visible disclosures, not hidden substitutions. No direct promotion, merge, public release, deployment, credential request, or authoritative project mutation was performed.
