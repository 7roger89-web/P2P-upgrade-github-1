# OpenCodeReview research — 2026-09-16

## Source

- Upstream: `alibaba/open-code-review`
- License: Apache-2.0
- Evaluated release: `v1.12.4`
- Release commit: `f1101fd7f51304c82e4a4f292bbee88aea0823cf`
- Upstream project states that the tool originated as Alibaba's internal AI code-review assistant and ran internally for two years before open sourcing.
- Upstream AACR-Bench describes 200 real PRs from 50 open-source repositories across 10 languages, with expert cross-validation. The upstream authors report higher precision/F1 and lower token usage than a general-purpose agent under their benchmark, while explicitly reporting lower recall.

External benchmark claims are provenance, not P2P acceptance evidence. P2P does not reproduce or adopt the upstream ranking as authority.

## P2P fit

The useful pattern is OpenCodeReview Delegation Mode, not a second review authority.

Delegation Mode separates deterministic review scaffolding from semantic judgment:

1. `ocr delegate preview` deterministically selects reviewable files and records exclusions/ref metadata.
2. `ocr delegate rule` deterministically resolves review rules for those files.
3. The existing host agent reviews every selected file, using repository context as needed.
4. Every previewed `(path, status)` must be accounted for as reviewed or explicitly skipped with a reason.

This maps well to P2P's existing Evidence-First and deterministic-first principles.

## Selected ideas

- deterministic changed-file coverage before model judgment;
- deterministic review-rule resolution per file/group;
- explicit file-accounting contract to prevent silent coverage gaps;
- delegation mode so the already-selected P2P executor performs semantic review without a separate OCR LLM/API key;
- line/rule targeting as supplemental review evidence;
- machine-readable review scaffold suitable for Control Tower handoff.

## Rejected / bounded ideas

- OCR does not replace Shield, native code-impact, tests, task acceptance, or Control Tower reconciliation;
- OCR findings are not acceptance authority;
- no OCR-managed LLM configuration or API key from the P2P bridge;
- no automatic installation, upgrade, viewer, MCP server, telemetry, daemon, or background service;
- no pin to upstream `main`; the bridge targets a known minimum release contract;
- no automatic fix/mutation from review output;
- no mandatory always-on review for every tiny diff;
- because upstream reports lower recall than a general-purpose agent, OCR may not be the only semantic reviewer for high-risk work.

## Activation policy

`OPTIONAL_EXTENSION_AFTER_DOCUMENTED_REVIEW_GAP`

Typical activation reasons:

- large or complex diff where complete changed-file coverage is uncertain;
- repeated repair loop where a previous review omitted files or rule-specific checks;
- line/rule targeting gap that native P2P evidence does not establish;
- Control Tower explicitly requests deterministic review coverage for a code-changing task.

A concrete gap reason is mandatory. The bridge fails closed when OCR is missing, below the pinned minimum version, returns malformed JSON, exceeds output bounds, or receives conflicting target modes.

## Authority

The bridge returns `NON_AUTHORITATIVE_REVIEW_SCAFFOLD` only.

Current project state, Supreme Law, task contract, project tests, Shield, native code-impact evidence, and Control Tower acceptance remain authoritative. The host agent must still review the scaffolded files and acceptance replay remains mandatory.
