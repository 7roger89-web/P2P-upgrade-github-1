# P2P — ANE CONTEXT CANARY 03B — BOUNDED SELECTOR PATCH RETRY

Status: `PRE_RESULT_FROZEN`
Decision authority: `DOMAIN_CAPABILITY_ADMISSION_V1`
Upstream candidate: `ericlam2k/ane-context-harness@26d6fbb7a86fd47e1a3184dc4dc03d3867ac5835`
Target: `7roger89-web/P2P-upgrade-github-1@6ef4520781350db6f1c870e4cbbfeeaaa4e9c403`

Canary 03 was INVALID_HARNESS because its unified-diff artifact was malformed
before any candidate code executed. This retry changes only the patch
application mechanism. Algorithm semantics, threshold, tasks, anchors, target,
config exclusions, and budget remain identical.

## Frozen algorithm semantics

1. Named-symbol mandatory retention applies only when a matched task term fans
   out to at most **8 chunks** in the corpus.
2. Broader symbol terms remain ranking signals but do not become unconditional
   mandatory evidence.
3. Normal selected-context requests fail closed if final serialized evidence
   exceeds the effective token budget.
4. Explicit-path and developer-authority pins may intentionally exceed budget.
5. Full-context benchmark mode remains exempt.

## Frozen evaluation

- same Canary 01/02 five tasks;
- same five primary anchors;
- same Canary 02 duplicate-tree exclusions;
- same target SHA;
- same 2,000-token budget;
- same PASS contract as Canary 03.

## PASS

ALL:

1. exact-text patcher validates every expected upstream source fragment exactly once;
2. focused upstream deterministic tests pass;
3. synthetic broad-symbol regression passes;
4. exact P2P target indexes;
5. 5/5 selects succeed;
6. 5/5 primary anchors survive;
7. 5/5 returned packs <= 2,000;
8. median local reduction >= 20%.

FAIL => stop ANE work for current P2P conditions. Do not widen patch or tune the
fanout threshold.

PASS => only then may a separate real-agent A/B canary be considered.

No result from this canary by itself authorizes a provider-token, cost, or
hallucination claim.
