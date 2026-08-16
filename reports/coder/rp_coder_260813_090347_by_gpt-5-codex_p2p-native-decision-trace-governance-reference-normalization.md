# Coder Report - P2P Native Decision Trace Governance Reference Normalization

- Date: `2026-08-13`
- Scope: `D:\\AI\\P2P_dev\\P2P-8.4.6-C-Codex-Edition-v4`
- Goal: surgical normalization of `POLICY_REFS` only
- Baseline: `8.4.7-C-codex.5`
- Status: implementation and lifecycle evidence complete; supervisor review pending

## Invariant family map

`p2p_workflow.py` emitter -> `make_trace()` -> existing
`.p2p/state/execution-ledger.jsonl` -> `resolve_trace()` -> CLI/export/WHY ->
installed/package lifecycle.

The defect was isolated to the `POLICY_REFS` capture/resolve family. Workflow
emission shape, trace schema, ledger format, and every other reference family
were preserved. Forbidden behavior is arbitrary search, fuzzy basename
matching, absolute machine-path identity, fabricated evidence, or historical
ledger rewriting.

## Root cause and implementation

The `.5` workflow emitted the valid bare names `approval-policy.json` and
`drift-policy.json`. The installed files existed under
`.p2p/system/governance/`, but the old resolver checked the project root after
catalog lookup. This was proven before edits in the Goal evidence ledger
(`E0-P0A-CASE1`, `E0-P0A-CASE2`, `E0-P0A-ROOTCAUSE1`).

The smallest compatible rule is:

```text
new policy refs  -> governance/<safe POSIX-relative-path>
legacy bare refs -> exact lookup under .p2p/system/governance or governance
unsafe/invalid   -> rejection at capture or honest MISSING_REFERENCE at query
```

The native runtime now performs exact separator normalization, rejects drive,
URI, traversal, home, and absolute paths, canonicalizes new records, and keeps
legacy records byte-for-byte unchanged while resolving them deterministically.
No reference database or schema change was introduced.

## Files changed by implementation

- `.p2p/system/p2p_capabilities/decision_trace.py`
- `tests/test_p2p_decision_trace.py`

Release metadata/documentation required by the shipped runtime change:

- `VERSION`
- `manifest/package.json`
- `manifest/build-report.json`
- `.p2p/system/VERSION`
- `.p2p/system/p2p.manifest.json`
- `.p2p/system/p2p_uiux/__init__.py`
- `.p2p/system/p2p_capabilities/capabilities.json`
- `RELEASE-NOTES.md`
- `BAT-DAU.md`
- `docs/AI-HANDOFF.md`

Goal evidence, QA, coder, notes, and supervisor reports are audit artifacts;
they are outside the release package boundary.

## Validation

- Exact `.5` reproduction: 9 resolved, 2 policy `MISSING_REFERENCE`.
- Focused normalization/negative test: PASS.
- Existing workflow and relationship tests: PASS.
- Full unittest discovery: `49/49 PASS`.
- Native Decision Trace evaluator: `DT1-DT24`, `24/24 PASS`.
- Fresh `.6` install: `FRESH_INSTALL`, valid policy refs `2/2 PRESENT`, WHY
  query `PASS`, `11` resolved links.
- `.5` -> `.6` upgrade: legacy ledger hash and trace count preserved; legacy
  bare policy refs resolve `PRESENT` with normalized lookup metadata.
- Same-version reinstall: no ledger, policy, trace, or backup churn.
- Windows separators and WSL/POSIX query: PASS.
- Deliberately invalid policy ref: remains `MISSING_REFERENCE`, query
  `PARTIAL`; no fuzzy or fabricated resolution.
- Package verify/doctor/drift/secret/boundary: PASS.
- Installed UIUX evaluator: `DW1-DW18 PASS`; Foundation doctor: PASS.
- Canonical identities: exact eight; denominator `8`; full quorum `8/8`.
- `p2p_aesthetica`: optional/supporting/noncanonical; no execution identity
  was simulated.
- External dependency list: empty.

## Topology and repository evidence

Fresh Anvien analysis: 196 files, 76 dependency edges, 8,805 graph nodes,
10,105 relationships. `scripts/p2p_workflow.py` remains a high-risk hotspot
and was inspect-only. The target has no Git metadata; commit/diff evidence is
`N/A`. Source hashes and reproducible command outputs are the local audit
trail.

## Boundary

The verified `.5` ZIP is immutable. No App Game Truyen, Logistics, or real
user project was targeted. No agent, specialist, graph/RDF/MCP, external
dependency, Anvien integration, Semantica, Brigade/Tideline, discovery fix,
UIUX redesign, or unrelated Decision Trace hardening was implemented.

Handoff: supervisor must independently verify the candidate artifact,
lifecycle evidence, negative test, regression matrix, boundary, and RN1-RN20
before closure.
