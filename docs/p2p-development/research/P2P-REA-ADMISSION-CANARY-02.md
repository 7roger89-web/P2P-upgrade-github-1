# P2P — REA ADMISSION CANARY 02

Status: `BOUNDED_CANARY_COMPLETE`  
Decision: `OBSERVE_ONLY`  
Capability family: `SECURITY_REVERSE_ENGINEERING`  
Candidate: `morluto/rea` / npm `rea-agents@4.1.0`  
Pinned upstream release commit: `9622b4b4cf0b2eb92305afd52fd67e932d57c753`  
P2P main baseline: `6ef4520781350db6f1c870e4cbbfeeaaa4e9c403`  
Canary branch: `canary/rea-admission-02-persistent-20261007`

## Question

Does the useful part of REA survive a harder source-owned test after symbol stripping, and is the right integration shape a persistent task-scoped MCP with a bounded tool surface rather than one-shot CLI calls, full global registration, or snapshot-first reuse?

## Frozen acceptance

Before the successful run, `experiments/rea-admission-canary-02/criteria.json` froze:

- source symbols must be absent from the stripped binary;
- the known arithmetic/control-flow facts must still be recovered;
- evidence limitations must remain explicit;
- repeated analysis counts as materially faster at >=50% reduction;
- the selected P2P reverse-tool surface must be <=25% of the full REA schema bytes;
- actual agent token cost is required before any token-saving claim;
- no agent credential may be created or widened merely for this canary.

The source-owned fixture remained the Canary 01 program. A debug copy supplied ground-truth function addresses; an otherwise identical copy was stripped with `strip --strip-all`. The stripped target did not retain the source function names.

Final stripped binary SHA-256:

`8f9592aa125144389726ea1e98eb568dba779e130add09fe72a6d1f0bd27a155`

Ground-truth addresses:

```text
score_record  = 0x401156
feature_gate  = 0x401173
main          = 0x4011a1
```

Runtime receipt remained:

`P2P_REA_CANARY_OK:23`

## Final successful run

- GitHub Actions run: `37568527562`
- branch head under test: `2895f1a13350b3f80b6724dd2860eb197d2145e3`
- conclusion: `success`
- REA: `4.1.0`
- Ghidra: `12.1.4`
- Node: `24.11.0`
- JDK: Temurin 21

## Stripped-binary correctness

PASS.

REA/Ghidra recovered the source-owned facts without the source function names. The decompiler named the stripped functions `FUN_00401156` and `FUN_00401173`, while still recovering:

```text
uint FUN_00401156(int param_1)
{
  return param_1 * 7 + 3U ^ 0x2a;
}
```

and:

```text
int FUN_00401173(int param_1,undefined4 param_2)
{
  if (param_1 == 7) {
    iVar1 = FUN_00401156(param_2);
    iVar1 = iVar1 + 0xb;
  } else {
    iVar1 = -1;
  }
  return iVar1;
}
```

The bounded call graph also contained the source-grounded score function address. Both dossiers preserved explicit limitations; neither output was treated as original source.

```text
STRIPPED_NAMES_ABSENT=YES
GROUND_TRUTH_PASS=YES
CALL_GRAPH_PASS=YES
LIMITATIONS_PRESERVED=YES
```

## One-shot versus persistent MCP

The same stripped target was first measured through one-shot CLI calls:

```text
one-shot score function   = 21.59 s
one-shot feature function = 16.87 s
one-shot total            = 38.46 s
```

The persistent MCP session then paid analysis readiness once:

```text
MCP connect               = 1.834 s
open_binary               = 3.801 s
list_procedures/analysis  = 14.595 s
binary_session            = 0.115 s
first two function calls  = 0.182 s
cold session analysis     = 18.693 s
```

After the provider was warm, the same two function analyses took:

```text
warm two-function total   = 0.102 s
reduction vs cold session = 99.45%
reduction vs one-shot     = 99.73%
```

This crosses the frozen >=50% material-improvement threshold by a wide margin.

The important interpretation is not "Ghidra became 300x smarter." The expensive import/auto-analysis lifecycle was paid once and then reused. Repeated one-shot CLI calls keep paying the entrance fee like a nightclub charging cover every time you go outside to answer the phone.

## Snapshot result

Snapshot reuse did not pass the same material-improvement threshold.

```text
snapshot size                 = 73,478 bytes
snapshot open                 = 0.319 s
snapshot binary_session       = 0.036 s
snapshot score function       = 14.582 s
snapshot feature function     = 0.064 s
snapshot analysis total       = 15.001 s
reduction vs cold session     = 19.75%
SNAPSHOT_MATERIAL_IMPROVEMENT = NO
```

The first exact function query after reopening the snapshot still paid a large provider/analysis cost. For this target and REA 4.1.0, snapshot persistence is useful evidence state but is not a substitute for keeping the live task-scoped MCP/provider session warm.

No general claim is made beyond this tested fixture/version.

## Tool-surface cost

REA 4.1.0 exposed:

```text
FULL_TOOL_COUNT       = 125
FULL_SCHEMA_BYTES     = 2,043,150
SELECTED_TOOL_COUNT   = 8
SELECTED_SCHEMA_BYTES = 112,563
SELECTED_RATIO        = 5.51%
```

The frozen eight-tool projection was:

- `open_binary`
- `close_binary`
- `binary_session`
- `list_procedures`
- `analyze_function`
- `get_call_graph`
- `search_strings`
- `procedure_info`

All eight existed. The selected schema was only 5.51% of the full schema, comfortably below the frozen 25% ceiling.

This is direct evidence against globally exposing the full REA catalog to every P2P executor. It is not yet a model-token measurement: JSON/schema bytes are context payload size, not model tokens.

## Agent-token boundary

```text
ACTUAL_AGENT_TOKEN_MEASUREMENT=BLOCKED_NOT_RUN_NO_AUTHORIZED_AGENT_RUNTIME_OR_CREDENTIAL
OFFLINE_SCHEMA_BYTES_ARE_MODEL_TOKENS=FALSE
TOKEN_SAVING_CLAIM=NOT_AUTHORIZED_BY_EVIDENCE
```

The canary did not create, request, or widen an API credential merely to complete the table. A real Codex/OpenCode agent measurement remains a separate bounded gate.

## Harness correction

Run `37568086518` failed because the probe attempted to parse every provider address with `BigInt`. REA legitimately returned a non-flat address such as `external:0x1`. The corrected probe distinguishes flat executable addresses from provider-specific address spaces. Run `37568323210` then passed, and the final metric-corrected run `37568527562` passed.

The second correction was measurement semantics: the frozen criterion referred to cold repeated-analysis cost, but the initial implementation compared only function-call milliseconds after auto-analysis had already occurred. The corrected denominator includes the first provider readiness/analysis path. The threshold itself was not changed.

Reusable candidate lesson:

```text
LEARNING_RECONCILIATION=CANDIDATE
FAILURE_CLASS=PROVIDER_ADDRESS_SPACE_NORMALIZATION
TRIGGER=reverse adapter parses provider addresses as integers
LESSON=Provider address inventories can include non-flat spaces such as external:0x1; only flat executable addresses may be normalized numerically.
CORRECTION=Preserve provider address-space identity and parse numerically only after validating a flat hexadecimal address.
EVIDENCE=Actions 37568086518 failure + 37568323210 success + 37568527562 success
AUTHORITY=NON_AUTHORITATIVE_CANDIDATE
PERMISSION_EFFECT=NONE
```

No ACTIVE shared experience is created or promoted by this canary.

## Admission decision

```text
CAN_RUN=YES
WORKS_ON_STRIPPED_SOURCE_OWNED_TARGET=YES
EVIDENCE_QUALITY=PASS
UNKNOWN_HANDLING=PASS
PERSISTENT_MCP_MATERIAL_IMPROVEMENT=YES
SNAPSHOT_MATERIAL_IMPROVEMENT=NO
SELECTIVE_TOOL_SURFACE_MATERIALLY_SMALLER=YES
ACTUAL_AGENT_TOKEN_COST=NOT_MEASURED
MATERIALLY_BETTER_THAN_REPEATED_ONE_SHOT_FOR_THIS_TASK=YES
WORTH_COMPLEXITY=PARTIAL
READY_FOR_PRODUCT_CONTROL=NO
DECISION=OBSERVE_ONLY
```

## Beginner-facing admission receipt

```text
WHAT_NEW_THING_IS_BEING_CONSIDERED=REA as a task-scoped persistent external reverse-engineering backend behind existing P2P capability IDs.
WHAT_IT_MUST_PROVE_HERE=Correct stripped-binary evidence, honest unknowns, materially lower repeated-analysis cost, and bounded tool/context exposure.
WHAT_SIMPLE_CURRENT_PATH_IT_MUST_BEAT=Repeated one-shot local native analysis while P2P keeps its current routing/evidence authority.
WHAT_COUNTED_AS_PASS_FAIL_UNSURE=Frozen ground truth + >=50% repeated-cost reduction + selected schema <=25% of full; actual agent-token claim remains UNSURE until measured.
WHAT_IT_COSTS_AND_HOW_EASILY_IT_CAN_BE_UNDONE=Requires Node/JDK/Ghidra/REA and a live task-scoped MCP process; no core vendoring or router change, so removal is straightforward.
DECISION=OBSERVE_ONLY
OWNER_ACTION_NOW=NONE
```

## Smallest next gate

If REA is reopened, do only one agent-facing canary:

1. use an already-authorized Codex or OpenCode session;
2. expose the bounded reverse subset, not all 125 tools;
3. run the same stripped fixture/task;
4. compare actual input/context tokens, tool-selection correctness, total completion tokens, latency, and evidence quality against the same agent without REA/full-catalog exposure;
5. stop after one decision.

Do not build a second router, daemon, capability registry, or always-on global REA service.
