# P2P DeepGEMM intake 01

Date: 2026-10-12  
Decision class: READ-stage capability intake  
Upstream: `deepseek-ai/DeepGEMM`  
Observed upstream head: `057ca5964aae0879ff2e0eb71ee05a3cb0ba3df7` (public release 2026-09-30)  
License: MIT

## Owner claim checked

The supplied post makes three materially different claims:

1. DeepGEMM is a real DeepSeek GPU kernel library used for modern LLM computation.
2. Faster GEMM can improve GPU throughput and therefore may reduce self-hosted inference/training cost.
3. Installing DeepGEMM can cut hosted GPT/Claude token bills by about 98% (for example "$50 -> $1.6").

Verdict:

- Claim 1: **SUPPORTED** by the current upstream repository.
- Claim 2: **PLAUSIBLE BUT WORKLOAD-SPECIFIC**. It requires a compatible self-hosted NVIDIA runtime and same-workload measurement.
- Claim 3: **NOT SUPPORTED**. A CUDA kernel library does not change OpenAI/Anthropic hosted API pricing. No first-party DeepGEMM source inspected for this intake supplies the advertised 98% token-bill reduction.

## Fresh upstream reality

Current DeepGEMM describes itself as a CUDA tensor-core kernel library covering FP8/FP4/BF16 GEMMs, Mega MoE, MQA scoring, HyperConnection and related primitives. The current quick-start requires, among other things:

- NVIDIA SM90 or SM100 architecture;
- CUDA Toolkit 12.9+;
- PyTorch 2.3+;
- CUTLASS 4.0+.

The repository is actively maintained. Its 2026-09-30 public release added further locality-aware and Mega-MoE work. This is a real performance-engineering project, not a token-caching trick or prompt-compression library.

Upstream:
- https://github.com/deepseek-ai/DeepGEMM
- https://github.com/deepseek-ai/DeepGEMM/blob/main/README.md
- https://github.com/deepseek-ai/DeepGEMM/blob/main/LICENSE

## Integration boundary

DeepGEMM sits **below** an inference serving stack. It accelerates matrix kernels on compatible GPUs; it is not an LLM provider, agent router, prompt layer, token accounting layer, or API billing layer.

Current P2P local-provider work is centered on provider/runtime boundaries such as Ollama, LM Studio and llama.cpp. No current P2P runtime surface directly owns CUDA GEMM kernels.

By contrast, serving frameworks already integrate DeepGEMM at the correct layer:

- vLLM currently carries an explicit DeepGEMM external-project integration and vendors the kernel package into its serving build.
- SGLang carries benchmark/integration code comparing its FP8 path with DeepGEMM.

Evidence:
- https://github.com/vllm-project/vllm/blob/main/cmake/external_projects/deepgemm.cmake
- https://github.com/sgl-project/sglang/blob/main/benchmark/kernels/deepseek/benchmark_deepgemm_fp8_gemm.py

Therefore the correct P2P seam, if this ever becomes relevant, is **provider-native acceleration**. P2P should select/use a serving backend that already owns DeepGEMM integration rather than vendor DeepGEMM into P2P core.

## DOMAIN_CAPABILITY_ADMISSION_V1 result

```text
WHAT_NEW_THING_IS_BEING_CONSIDERED=DeepGEMM GPU kernel acceleration for a future self-hosted NVIDIA inference lane
WHAT_IT_MUST_PROVE_HERE=better same-workload latency/throughput/cost-per-token without correctness regression on a real P2P-selected serving backend
WHAT_SIMPLE_CURRENT_PATH_IT_MUST_BEAT=current provider-native path with DeepGEMM disabled/not selected
WHAT_COUNTED_AS_PASS_FAIL_UNSURE=predeclared task-specific acceptance + correctness parity + measured benefit + acceptable ops cost; otherwise FAIL/UNSURE
WHAT_IT_COSTS_AND_HOW_EASILY_IT_CAN_BE_UNDONE=GPU runtime/toolchain/provider complexity; reversible if kept at provider boundary and feature/config toggle
DECISION=OBSERVE_ONLY
OWNER_ACTION_NOW=NONE
```

Admission ladder:

```text
CAN_RUN_IN_CURRENT_P2P_PATH=NO_DIRECT_SEAM
WORKS_FOR_TARGET_TASK=NOT_TESTED
MATERIALLY_BETTER_THAN_CURRENT_PATH=NOT_TESTED
WORTH_COMPLEXITY=NOT_PROVEN
READY_FOR_PRODUCT_CONTROL=NO
```

## Re-entry trigger

Open a bounded pilot only when **all** are true:

1. P2P has an authorized self-hosted NVIDIA inference lane using a framework such as vLLM, SGLang or another runtime with a real DeepGEMM seam.
2. The target hardware/runtime is supported by that serving stack and the selected DeepGEMM build.
3. A task-specific latency/throughput/cost acceptance target exists and the current path measurably misses it.
4. Profiling shows GEMM/tensor-core work is a material bottleneck or the serving framework exposes DeepGEMM as a credible provider-native candidate.
5. Owner authorization exists for any paid GPU spend required by the probe.

Then run the smallest same-workload A/B:

```text
BASELINE=provider-native serving path without DeepGEMM selected
CANDIDATE=same provider/model/quantization/batch/workload with DeepGEMM selected
MUST_MATCH=correctness/output tolerance + model/task configuration
MEASURE=latency + throughput + GPU memory + end-to-end cost proxy
ROLLBACK=disable provider DeepGEMM path / revert provider config
```

No generic benchmark is required before those triggers exist.

## Rejected now

- vendoring DeepGEMM into P2P core;
- adding CUDA/PyTorch/CUTLASS dependencies to P2P merely because the upstream benchmark is attractive;
- claiming hosted GPT/Claude API token savings from a client-side kernel;
- introducing a new GPU service, daemon, router, benchmark platform or registry;
- spending GPU money before the existing Owner Gate;
- converting upstream TFLOPS into P2P cost savings without a target workload.

## OE gate

```text
OE_VERDICT=DO_IT
READ_STAGE_RECORD=YES
DIRECT_RUNTIME_INTEGRATION=SKIP_IT
PILOT_OE_VERDICT=DEFER_UNTIL_NEEDED
```

Reason: one bounded durable intake record prevents future hype-driven reintegration attempts while preserving the correct provider-level re-entry path. Installing the kernel now would add a heavy native dependency to a layer that does not own the relevant computation.
