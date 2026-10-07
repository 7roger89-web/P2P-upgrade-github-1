# P2P — REA ADMISSION CANARY 01

Status: `BOUNDED_CANARY_COMPLETE`  
Decision: `OBSERVE_ONLY`  
Capability family: `SECURITY_REVERSE_ENGINEERING`  
Candidate: `morluto/rea` / npm `rea-agents@4.1.0`  
Baseline P2P main at canary start: `6ef4520781350db6f1c870e4cbbfeeaaa4e9c403`  
Canary branch: `canary/rea-admission-01-20261007`

## Claim tested

Can REA act as a bounded external backend over an existing P2P native reverse-engineering capability without becoming a second router/control plane, while producing source-bound evidence and honest unknowns on a source-owned benign native fixture?

This canary does not promote REA into P2P, does not change canonical routing, and does not claim superiority over Kong.

## Frozen fixture and acceptance

The evaluation set and acceptance facts were committed before the successful run in:

- `experiments/rea-admission-canary/canary.c`
- `experiments/rea-admission-canary/criteria.json`

Frozen ground truth:

- string: `P2P_REA_CANARY_OK`
- functions: `score_record`, `feature_gate`, `main`
- `feature_gate` mode: `7`
- score multiplier: `7`
- score addend: `3`
- score xor: `0x2A`
- feature-gate addend: `11`
- call relation: `feature_gate -> score_record`

Fixture runtime receipt:

`P2P_REA_CANARY_OK:23`

Fixture binary SHA-256:

`fab55602d07ac0c2298f3482b174e032e5e05d9c0ab256472f2b5da62ee46b4f`

## Runtime

Successful run:

- GitHub Actions run: `37565816027`
- head: `ef838636ce37631744aab18be49190f3e88ba4c0`
- conclusion: `success`
- Node: `24.11.0`
- Java: Temurin JDK 21
- REA: `4.1.0`
- Ghidra: `12.1.4`
- official Ghidra archive SHA-256 verified as:
  `ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db`

REA receipts:

```text
REA_PROVIDERS_EXIT=0
REA_ANALYZE_EXIT=0
REA_FEATURE_GATE_EXIT=0
REA_SCORE_RECORD_EXIT=0
REA_STRING_SEARCH_EXIT=0
```

The aggregate `rea doctor --json` returned exit 1 because optional Hopper, IDA registration, and installed REA skill identity were absent. Its provider-specific inspection simultaneously reported Ghidra configured, available, version 12.1.4, headless healthy, and JDK 21 healthy. Therefore aggregate doctor failure is not equivalent to target-provider failure.

## Ground-truth recovery

REA/Ghidra recovered every frozen discrete fact in this fixture.

Representative recovered pseudocode:

```text
feature_gate:
if (param_1 == 7) {
  iVar1 = score_record(param_2);
  iVar1 = iVar1 + 0xb;
} else {
  iVar1 = -1;
}

score_record:
return param_1 * 7 + 3U ^ 0x2a;
```

String search recovered `P2P_REA_CANARY_OK:%d\n` at `0x402004`.

## Evidence and unknown handling

Observed REA output bound findings to:

- evidence ID
- binary subject identity and SHA-256
- ELF/x86_64 identity
- provider ID/name/version
- operation and parameters
- raw and normalized results
- confidence
- authority
- provider-specific analysis profile and digest

The output also explicitly preserved limitations, including:

- decompiler output is not original source or runtime behavior;
- unresolved indirect/targetless flows remain unknown;
- recovered types may carry low confidence;
- def-use may omit aliasing, call side effects, or cross-function links;
- truncation and omitted-count boundaries must be checked.

This matches the P2P requirement that missing evidence must not be promoted into a confident fact.

## Latency and setup burden

Observed one-shot CLI wall times:

- doctor: ~9.6 s
- providers: ~2.7 s
- analyze: ~22.3 s
- feature-gate function: ~18.2 s
- score-record function: ~18.0 s
- string search: ~17.9 s

The successful workflow took roughly two minutes end-to-end including runner setup, pinned Ghidra download/unzip, REA package resolution, and analysis.

The repeated deep-analysis calls each paid a substantial one-shot startup/import cost. This canary does not establish that persistent MCP or snapshot reuse has the same overhead.

## Token boundary

No LLM/API call was used in this canary, therefore model-token cost for the deterministic REA+Ghidra slice was zero.

Agent-context/tool-schema token overhead was not measured because the canary exercised the CLI rather than a connected agent MCP session. No token-saving claim is made.

## Kong boundary

`KONG_STATUS=NOT_RUN`.

The existing Kong intake requires explicit LLM/API credential and cost authority before its pilot. This no-secret canary did not widen authority merely to manufacture a comparison. Therefore this result does not establish REA > Kong.

## Admission result

```text
CAN_RUN=YES
WORKS_FOR_THIS_BOUNDED_TARGET_TASK=YES
EVIDENCE_QUALITY=PASS
UNKNOWN_HANDLING=PASS
MATERIALLY_BETTER_THAN_CURRENT_PATH=PARTIAL_NOT_PROVEN
WORTH_COMPLEXITY=NOT_YET_PROVEN
READY_FOR_PRODUCT_CONTROL=NO
DECISION=OBSERVE_ONLY
```

Reason:

REA already supplies a credible provider-neutral evidence surface over Ghidra and successfully recovered the frozen ground truth. However, this single benign unstripped fixture does not prove superiority over Kong or prove that the installation/runtime/context overhead is worth permanent integration.

Smallest next probe, if this capability is reopened: reuse the same or a stripped source-owned fixture through a persistent REA MCP session or immutable snapshot, measure repeated-call latency plus agent/tool-schema context cost, and expose only the existing P2P reverse capability subset. Do not register the entire REA tool surface globally and do not create a second router.

## Canary correction / learning reconciliation

First run `37565689254` exposed two operational failures:

1. treating aggregate `rea doctor` non-zero as fatal would have falsely classified a healthy configured Ghidra provider as unavailable;
2. GitHub artifact upload was blocked by repository artifact-storage quota, although the analysis inputs had succeeded.

The second run `37565816027` preserved evidence in job logs, evaluated provider-specific health, and completed successfully.

```text
LEARNING_RECONCILIATION=CANDIDATE
FAILURE_CLASS=AGGREGATE_HEALTH_FALSE_NEGATIVE
TRIGGER_CONDITIONS=external capability admission; aggregate doctor/health command; provider-specific execution
CORRECTION=provider-specific availability must decide provider usability; aggregate optional-provider health must not be promoted into target-provider failure
EVIDENCE=Actions 37565689254 + 37565816027
SCOPE=DOMAIN
AUTHORITY=NON_AUTHORITATIVE_CANDIDATE
```

A second observed optimization hypothesis is retained as evidence, not promoted experience: repeated one-shot native analysis paid substantial startup/import cost; persistent MCP/snapshot reuse should be measured before P2P chooses an integration shape.
