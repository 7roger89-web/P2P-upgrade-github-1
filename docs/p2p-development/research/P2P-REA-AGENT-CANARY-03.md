# P2P — REA AGENT-FACING CANARY 03

Status: `BOUNDED_CANARY_COMPLETE`  
Decision: `OBSERVE_ONLY`  
Capability family: `SECURITY_REVERSE_ENGINEERING`  
Candidate: `morluto/rea` / npm `rea-agents@4.1.0`  
Lineage: Canary 01 -> Canary 02 -> Canary 03  
Canary branch: `canary/rea-admission-03-agent-token-20261007`

## Question

Does exposing REA to a real Codex agent materially improve the bounded reverse-engineering task, and does simply shrinking the MCP tool catalog materially reduce real agent token usage?

## Host and model preflight

The Owner-authorized Windows Codex host had:

- Codex CLI `0.147.0`
- authenticated through ChatGPT
- bundled Node `24.21.0`
- local REA `4.1.0`
- Ghidra `12.1.4`
- Temurin JDK `21.0.12.1+1`

The user's existing Codex config selected `gpt-6.1-sol`. The first canary attempt failed before task execution with:

`The 'gpt-6.1-sol' model is not supported when using Codex with a ChatGPT account.`

No evaluation result had been produced. The canary therefore switched all successful variants to the currently supported `gpt-5.6-terra` model explicitly and kept the same model for every measured successful variant.

No API key was created or exposed.

## Source-owned target

The target was a newly built Windows PE x86-64 executable with a separate debug oracle. The tested agents were explicitly forbidden from reading the source, debug binary, parent/sibling files, build history, GitHub, or the web.

The tested target was stripped with `strip --strip-all`.

Target:

`C:\Temp\p2p-rea-agent-canary-03\target\canary.stripped.exe`

SHA-256:

`D6B689198BC38F680606BEA81E2A0DEA2A9006A9C8E501C5029CE4CF347DCCE5`

Ground truth was frozen before successful agent runs:

```text
gate_mode=9
score_transform=((x * 13) + 5) XOR 55
post_score_addend=17
direct_call_relation=true
```

Runtime oracle for input 4:

`P2P_AGENT_CANARY:31`

## Variants

All measured agent variants used the same host, target, task, Codex model, read-only sandbox request, and JSONL usage receipts.

### NO_REA

Wall: `20.486 s`

Codex reported:

```text
input_tokens=38,593
cached_input_tokens=18,176
output_tokens=621
```

Result: all four requested facts `UNKNOWN`.

Reason: the local Codex Windows sandbox could not launch its helper:

`codex-windows-sandbox-setup.exe ... program not found`

The agent correctly refused to invent facts.

Therefore NO_REA is a useful current-host observation but is not a fair proof that native local tools generally cannot solve the task.

### REA_FULL_125

Profile: unrestricted REA MCP tool catalog.

Wall: `181.081 s`

Usage:

```text
input_tokens=660,586
cached_input_tokens=574,976
uncached_input_tokens=85,610
output_tokens=1,784
reasoning_output_tokens=704
```

Tool path selected by Codex:

```text
open_binary
list_procedures
batch_decompile
analyze_function
analyze_function
close_binary
```

Correctness: `4/4 PASS`.

Recovered evidence included:

- gate compares mode to `0x9`;
- score function computes `x * 0xd + 5`, then XOR `0x37`;
- gate adds `0x11` after the score call;
- direct `CALL 0x1400014e0` from gate at `0x14000151d`;
- decompiler output explicitly treated as non-original-source evidence.

### REA_BOUNDED_8 — frozen Canary 02 projection

Allowed tools:

```text
open_binary
close_binary
binary_session
list_procedures
analyze_function
get_call_graph
search_strings
procedure_info
```

Wall: `179.150 s`

Usage:

```text
input_tokens=815,521
cached_input_tokens=723,456
uncached_input_tokens=92,065
output_tokens=2,327
reasoning_output_tokens=802
```

Correctness: `4/4 PASS`.

But the frozen token criterion failed badly:

- input tokens vs FULL: `+23.46%`
- wall time vs FULL: about `-1.07%`

Why: the projection removed `batch_decompile`. Codex compensated by probing many individual functions with `analyze_function`, creating more turns and more evidence payload.

This falsifies the assumption that a smaller tool count automatically means fewer agent tokens.

### REA_BOUNDED_5 — observed FULL successful tool path

Follow-up criteria were frozen before this run after the BOUNDED_8 failure.

Allowed tools:

```text
open_binary
list_procedures
batch_decompile
analyze_function
close_binary
```

Wall: `146.386 s`

Usage:

```text
input_tokens=598,878
cached_input_tokens=527,616
uncached_input_tokens=71,262
output_tokens=1,913
reasoning_output_tokens=859
```

Correctness: `4/4 PASS`.

Comparison vs FULL:

- input tokens: `-9.34%`
- uncached input tokens: `-16.76%`
- wall time: `-19.16%`

This is better, but it missed the frozen >=20% total-input-token win.

### REA_NARROW_5 — result-bounded evidence path

A second follow-up tested the more important hypothesis suggested by the previous runs: reduce result cardinality, not merely schema count.

Allowed tools:

```text
open_binary
search_strings
xrefs
analyze_function
close_binary
```

The prompt explicitly prohibited listing all procedures and required a narrow path:

`P2P_AGENT_CANARY string -> xrefs -> containing function -> gate -> score`.

Wall: `175.040 s`

Usage:

```text
input_tokens=604,610
cached_input_tokens=559,104
uncached_input_tokens=45,506
output_tokens=1,827
reasoning_output_tokens=644
```

Tool path:

```text
open_binary
search_strings
xrefs
analyze_function(main-containing function)
analyze_function(gate)
analyze_function(score)
close_binary
```

Correctness: `4/4 PASS`.

Comparison vs FULL:

- total input tokens: `-8.47%`
- uncached input tokens: `-46.85%`
- wall time: `-3.34%`

The frozen >=20% total-input-token win still did not pass. The uncached-input reduction is large, but the run does not authorize treating cached-token accounting as identical to total context or plan usage.

## What the canary actually proved

```text
REA_AGENT_PATH_WORKS=YES
REA_CORRECTNESS=PASS
REA_EVIDENCE_QUALITY=PASS
REA_UNKNOWN_HANDLING=PASS

FULL_125_CORRECTNESS=PASS
BOUNDED_8_CORRECTNESS=PASS
BOUNDED_5_CORRECTNESS=PASS
NARROW_5_CORRECTNESS=PASS

BOUNDED_8_TOTAL_TOKEN_WIN=FAIL
BOUNDED_5_TOTAL_TOKEN_WIN=FAIL
NARROW_5_TOTAL_TOKEN_WIN=FAIL

NARROW_5_UNCACHED_INPUT_REDUCTION=46.85_PERCENT
NARROW_5_TOTAL_INPUT_REDUCTION=8.47_PERCENT

GLOBAL_FULL_SURFACE_REQUIRED=NO
TOOL_COUNT_ALONE_IS_TOKEN_OPTIMIZATION=FALSE
RESULT_CARDINALITY_MATTERS=YES
CURRENT_HOST_NO_REA_BASELINE=BLOCKED_BY_CODEX_SANDBOX_HELPER
```

## Reality correction

The previous working theory was too simple:

`fewer registered MCP tools -> dramatically fewer real agent tokens`.

This canary falsified that theory.

The stronger observed rule is:

`right tools + bounded result shape + low query fan-out -> lower agent context burden`.

A tiny catalog that removes the high-leverage batch operation can be worse than the full catalog. Conversely, a narrow evidence route materially reduced uncached input, but verbose per-call evidence and common cached context still kept total input high.

The architectural optimization target is therefore not “fewest tools.” It is “smallest sufficient workflow with bounded response cardinality.”

## Admission verdict

```text
CAN_RUN=YES
WORKS_FOR_TARGET_TASK=YES
MATERIALLY_BETTER_THAN_NO_REA_ON_THIS_HOST=YES_FOR_CAPABILITY
MATERIALLY_BETTER_THAN_FULL_REA_ON_TOTAL_TOKENS=NOT_PROVEN
WORTH_COMPLEXITY=PARTIAL
READY_FOR_PRODUCT_CONTROL=NO
DECISION=OBSERVE_ONLY
```

Why not ADMIT yet:

1. REA clearly rescued a task the current host's ordinary local-tool path could not execute, but that baseline was blocked by a Codex Windows sandbox installation defect, not by intrinsic inability.
2. Every REA variant solved the task correctly.
3. The frozen >=20% total-input-token criterion failed for every bounded projection.
4. The best result came from narrowing evidence flow, not just tool schemas.
5. One fixture is insufficient to lock a universal reverse-tool projection.

## Smallest worthwhile next action

Do not add REA globally and do not build a router.

If this lane is reopened, first fix the Codex Windows sandbox helper so NO_REA becomes a fair baseline. Then run one second representative fixture with a narrow REA workflow whose tool responses are intentionally bounded. The next engineering target should be response shaping/pagination/summary evidence, not deleting tools blindly.

## Learning reconciliation

```text
LEARNING_RECONCILIATION=CANDIDATE
FAILURE_CLASS=TOOL_COUNT_PROXY_FAILURE
TRIGGER_CONDITIONS=MCP admission; token optimization; tool allowlist; large tool results; agent query fan-out
LESSON=Reducing MCP tool count is not a reliable proxy for reducing real agent token use. Removing a high-leverage batch or search operation can increase query fan-out and total tokens.
CORRECTION=Optimize the smallest sufficient workflow and bound result cardinality first; measure real agent usage after routing, rather than promoting schema/tool-count reduction as token savings.
EVIDENCE=NO_REA + REA_FULL_125 + REA_BOUNDED_8 + REA_BOUNDED_5 + REA_NARROW_5 local JSONL receipts on the same source-owned stripped target
AUTHORITY=NON_AUTHORITATIVE_CANDIDATE
PERMISSION_EFFECT=NONE
```

The candidate is recorded here for reconciliation evidence only. It is not ACTIVE, not shared, and grants no permission or promotion.
