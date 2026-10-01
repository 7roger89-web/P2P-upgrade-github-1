# P2P-KONG-REVERSE-INTAKE-01

Status: `READ_COMPLETE / PILOT_DEFERRED_UNTIL_REAL_BINARY`  
Date: `2026-10-01`  
Upstream: `amruth-sn/kong`  
Observed upstream main: `8c4ee4bf52e0eb9efc3a0b22ad6da03387543fd2`  
Package version observed: `kong-re 0.2.2`  
License: `Apache-2.0`  
P2P authority effect: `NONE`

## 1. Bounded question

Does Kong contribute a missing P2P core architecture, or is it better treated as a future external backend candidate for P2P's existing security/reverse-engineering capability contracts?

## 2. Fresh upstream facts

The upstream repository was fresh-read from GitHub on 2026-10-01.

Observed implementation surfaces:

- `kong/agent/supervisor.py`: triage -> analysis -> cleanup -> synthesis -> export orchestration.
- `kong/agent/analyzer.py`: decompilation plus callers/callees, referenced strings, known functions and known structs as LLM context; writes names/signatures/comments back to Ghidra.
- `kong/agent/deobfuscator.py`: heuristic classification for control-flow flattening, bogus control flow, instruction substitution, string encryption and VM-style protection.
- `kong/llm/tools.py`: bounded tool calls for Z3-backed expression simplification, dead-code elimination, state-machine tracing, crypto-constant identification, decompilation and basic-block/CFG retrieval.
- `kong/evals/*`: symbol/type scoring against ground truth.
- `.github/workflows/ci.yml`: pytest matrix for Python 3.11-3.14.
- PR #16 head `4c5f09294cfc712e37cabd88d69ccdc11cd915c3` had a successful four-version CI run.

The upstream XZ/liblzma benchmark is useful evidence of author-observed behavior, but it is NOT independent P2P proof. The repository reports 558 functions enumerated, 396 queued, 355 analyzed, 15 minutes, USD 6.63, using Claude Opus 4.6, and claims reconstruction of five core backdoor functions. P2P did not reproduce this benchmark in this intake.

Relevant upstream limitations observed from open issues:

- #17 reports that one Ghidra decompilation failure can terminate a large analysis run.
- #18 reports long decompilation periods with little UI feedback.
- #10 reports packed software not being unpacked.

Therefore `UPSTREAM_BENCHMARK_CLAIM != P2P_CERTIFICATION` and `UPSTREAM_CONFIDENCE_SCORE != STATISTICAL_PROBABILITY_OF_CORRECTNESS`.

## 3. Existing P2P overlap

Kong does NOT justify a new P2P router, task graph, context framework, quality framework, evidence ledger or agent identity.

P2P already has:

- deterministic task dependency ordering and cycle rejection in C11 task state;
- C19 targeted retrieval order: task contract -> authoritative refs -> dependency outputs -> evidence/fact pointers -> project/repo map -> targeted source -> bounded fallback;
- C37 quality/risk selection gates with fail-closed quality floors;
- provider-neutral execution-target/toolset composition;
- existing security/reverse capability contracts:
  - `reverse.decompile.native`
  - `reverse.deobfuscate`
  - `reverse.callgraph`
  - `reverse.semantic_reconstruct`
- an existing Ghidra external-runtime candidate record (`P2P-SEC01-GHIDRA`) with installation disabled and no runtime claim;
- RA-EXT-070 reverse-skill adoption already preserving the single-router, scope-before-ACT and selective-tool-loading boundaries.

The useful Kong delta is implementation evidence for a possible FUTURE backend composition across those existing reverse capabilities.

## 4. P2P translation

### KEEP

1. Ghidra-derived structural context before LLM inference.
2. Bottom-up call-graph processing so already-resolved callees improve caller context.
3. Deterministic/symbolic tools as evidence helpers during deobfuscation.
4. Structured outputs and explicit cost/token tracking.
5. Ground-truth evaluation where a known reference exists.

### REUSE EXISTING P2P INSTEAD

1. Task/dependency graph -> reuse C11.
2. Context selection -> reuse C19.
3. Quality gating -> reuse C37.
4. Tool permission/selection -> reuse existing ToolSet / execution-target / permission surfaces.
5. Evidence authority -> reuse existing EvidenceClaim / verification / Decision Trace surfaces.
6. Reverse capability identity -> reuse SEC01 capability IDs; do not mint a Kong-specific canonical capability.

### REJECT

1. A second orchestrator/router/control plane inside P2P.
2. Vendoring Kong into P2P core.
3. Automatic Ghidra/JDK/Kong installation.
4. Treating Kong's own confidence as acceptance proof.
5. Treating the XZ benchmark as independent P2P certification.
6. Any automatic external-target interaction, offensive execution, bypass flow, credential widening, promotion, release or deployment.
7. Claiming original-source recovery from semantic reconstruction.

## 5. Admission decision

`READ_STAGE=COMPLETE`

`PILOT_STAGE=DEFER_UNTIL_NEEDED`

`ADOPT_STAGE=NOT_AUTHORIZED`

`CORE_STAGE=REJECTED_AS_UNNECESSARY`

The smallest future pilot, if a real need appears, is one external adapter/evaluation slice over an authorized local binary. Kong remains an external backend candidate; P2P remains the authority.

Pilot re-entry conditions:

1. A real authorized binary-analysis task exists, or a bounded benign fixture with known ground truth is required to validate the capability.
2. The selected executor already has, or is separately authorized to obtain, the required Ghidra/JDK/runtime environment.
3. LLM/API cost and credential use are explicitly within task authority.
4. Acceptance criteria are written before the run (for example known symbols/types/behavioral facts, or a bounded comparison against known source).
5. Kong output is ingested only as proposed evidence and is independently checked before any task completion claim.

## 6. Mapping

| Kong mechanism | Existing P2P surface | Decision |
| --- | --- | --- |
| call-graph ordered analysis | C11 dependency semantics + reverse.callgraph | REUSE |
| rich caller/callee/string context | C19 targeted context + reverse semantic evidence contract | REUSE/ADAPT |
| Ghidra in-process analysis | P2P-SEC01-GHIDRA + reverse.decompile.native | FUTURE ADAPTER CANDIDATE |
| symbolic deobfuscation tools | reverse.deobfuscate + existing ToolSet boundary | FUTURE ADAPTER CANDIDATE |
| semantic synthesis | reverse.semantic_reconstruct | FUTURE ADAPTER CANDIDATE |
| eval against ground truth | existing Quality/Evidence/Evaluation family | REUSE METHODOLOGY |
| Kong supervisor as control plane | P2P router/execution control | REJECT DUPLICATION |

## 7. Over-engineering gate

Không bị over engineering chứ?

`OE_VERDICT=DO_IT` for this bounded research intake: it creates no runtime, dependency, adapter, router or background service and preserves a useful discoverable future option.

`PILOT_OE_VERDICT=DEFER_UNTIL_NEEDED`: no binary task currently proves that installing/integrating Kong materially advances an active P2P outcome.

## 8. Stop condition

This intake stops at durable READ-stage evidence. No Kong runtime, Ghidra runtime, package dependency, adapter implementation, benchmark execution, model call, release, deployment or promotion is performed by this task.
