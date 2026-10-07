# P2P — ANE CONTEXT CANARY 02 — CONFIG-ONLY RETEST

Status: `PRE_RESULT_FROZEN`
Decision authority: `DOMAIN_CAPABILITY_ADMISSION_V1`
Candidate: `ericlam2k/ane-context-harness`
Candidate revision: `26d6fbb7a86fd47e1a3184dc4dc03d3867ac5835`
Target repository: `7roger89-web/P2P-upgrade-github-1`
Target baseline: `6ef4520781350db6f1c870e4cbbfeeaaa4e9c403`

## Changed condition

Canary 01 failed because the default index admitted duplicate agent-skill projection trees and named-symbol mandatory retention exploded the selected pack.

Before changing ANE code, Canary 02 tests the smallest existing upstream knobs only:

- keep ANE source byte-identical at the pinned revision;
- extend `privacy.never_read` only for clearly duplicated agent-skill projection trees;
- do NOT exclude canonical P2P runtime, root tests, root scripts, portable law, or docs;
- do NOT use `authoritative_paths`, because pinning the entire canonical notebook would itself exceed the requested 2,000-token budget.

## Frozen exclusions

Only:

- `.agents/**`
- `.claude/**`
- `.p2p/system/.agents/**`
- `.p2p/system/.claude/**`

Default secret/privacy exclusions remain active.

## Frozen tasks

Exactly the same five task texts and primary anchors as Canary 01.

Budget: `2000` ANE estimator tokens per task.

## PASS

ALL must hold:

1. exact ANE revision installs and focused checks pass;
2. P2P target indexes with only the frozen exclusions;
3. 5/5 frozen primary anchors survive;
4. every selected pack is <= 2000 ANE-estimator tokens;
5. median local reduction is >= 20%.

A reported percentage reduction cannot compensate for an absolute budget violation.

## Interpretation

- PASS means existing configuration is enough to rescue the selector on this exact P2P canary.
- FAIL means configuration-only rescue is insufficient; only then is a bounded algorithm patch justified.
- PASS does NOT authorize a real Codex/OpenCode token-savings claim. Stage B actual-agent telemetry remains separate.

## Prohibitions

- no algorithm patch in this canary;
- no global install;
- no P2P router/daemon/context service;
- no threshold movement after results;
- no provider-token or hallucination claim.
