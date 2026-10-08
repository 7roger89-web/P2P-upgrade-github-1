# P2P — ANE CONTEXT CANARY 03 — BOUNDED SELECTOR PATCH

Status: `PRE_RESULT_FROZEN`
Decision authority: `DOMAIN_CAPABILITY_ADMISSION_V1`
Upstream candidate: `ericlam2k/ane-context-harness@26d6fbb7a86fd47e1a3184dc4dc03d3867ac5835`
Target: `7roger89-web/P2P-upgrade-github-1@6ef4520781350db6f1c870e4cbbfeeaaa4e9c403`

## Why this canary is allowed

Canary 01 proved default selection failed on absolute pack size and 5/5 authority survival.
Canary 02 proved existing config-only exclusions are insufficient: 4/5 anchors and 0/5 packs <= 2,000.

Therefore one bounded algorithm patch is justified.

## Patch scope — frozen before result

Only two behaviors may change:

1. **Bound named-symbol mandatory fanout**
   - A task term may promote symbol-matching chunks to mandatory only when that
     term matches at most **8 chunks** in the current corpus.
   - A broader term remains a ranking signal but loses unconditional retention.
   - Threshold is frozen at 8 before execution.

2. **Hard user-facing budget guard**
   - For normal selected-context requests, if final serialized evidence exceeds
     the effective token budget, return an error instead of a giant pack.
   - Existing explicit-path or developer-authority pins remain allowed to exceed
     budget because the caller deliberately crowned those inputs.
   - Full-context benchmark mode remains exempt.

No other ranking weights, BM25 behavior, MMR, chunking, tokenizer, query expansion,
authority model, or P2P code may change.

## Corpus controls

Use exactly Canary 02 exclusions:

- `.agents/**`
- `.claude/**`
- `.p2p/system/.agents/**`
- `.p2p/system/.claude/**`

No canonical docs, root scripts, root tests, P2P runtime, or portable law are excluded.

## Frozen evaluation

Exactly the same five task texts and primary anchors as Canary 01 and 02.
Budget: **2,000 ANE-estimator tokens per task**.

## PASS

ALL:

1. patch applies cleanly to the exact upstream revision;
2. focused upstream deterministic tests remain green;
3. a synthetic broad-symbol regression proves fanout suppression and budget-bounded selection;
4. exact P2P target indexes successfully;
5. 5/5 frozen tasks complete without hard-budget refusal;
6. 5/5 frozen primary anchors survive;
7. 5/5 returned packs are <= 2,000;
8. median local reduction >= 20%.

## Interpretation

PASS => patch is technically interesting enough for a separate real-agent A/B canary.
FAIL => stop ANE work for current P2P conditions; do not widen the patch or tune thresholds.

PASS still does NOT prove provider-billed token savings, cheaper Codex/OpenCode use,
or lower hallucination.

## Prohibitions

- no upstream push/fork/vendor;
- no global ANE install into P2P;
- no router/daemon/service;
- no changing the 8-chunk threshold after results;
- no changing task text, anchor, target SHA, or 2,000-token budget;
- no Stage B actual-agent run unless Canary 03 passes.
