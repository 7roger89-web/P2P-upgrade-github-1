# ZaoFu Audit Findings: Area Group 11 - Verification Architecture & Thin Judge

## 1. Verification Architecture

ZaoFu's verification architecture is designed around a deterministic, evidence-based approach to evaluating task completion. The core of this system is located in `src/zf/core/verification/`.

**Key Implementation Semantics:**
The system relies on a collection of "gates" (`src/zf/core/verification/gates.py:GateResult, CommandGate, FileExistsGate`) which are essentially executable checks (commands or file existence). The results of these gates are captured as `Evidence` (`src/zf/core/verification/evidence.py:Evidence`). A `JudgeEvaluator` (`src/zf/core/verification/judge.py:JudgeEvaluator`) then evaluates this evidence against predefined dimensions (correctness, completeness, code quality, test coverage) to produce a `JudgeResult` with an overall grade (A-D).

The verification process is heavily tied to "validation specs" (`src/zf/core/verification/validation.py`), which allow for exact byte, text line, or regex matching against expected outputs. Furthermore, the `discriminator.py` framework (`src/zf/core/verification/discriminator.py:DiscriminatorReport`) introduces a multi-D verification system where a task can only be marked as "done" if all discriminator checks pass (AND closure).

**Coupling and Boundaries:**
The verification architecture depends heavily on the task schema (`src/zf/core/task/schema.py`) for task definitions and the event log (`src/zf/core/events/log.py`) for recording verification events. It is consumed by the runtime's candidate verification authority (`src/zf/runtime/candidate_verification_authority.py`) to ensure that candidate builds meet the required standards before being accepted.

**Maturity Signals:**
The architecture is well-tested, with dedicated test files like `tests/test_verification_gates.py`, `tests/test_verification_judge.py`, and `tests/test_verification_evidence.py`. The use of dataclasses and clear interfaces indicates a mature, well-structured design.

**Provider Neutrality:**
This area is largely **provider-neutral**. While it interacts with provider-specific execution (e.g., via Codex), the verification logic itself operates on abstract concepts like gates, evidence, and validation specs, rather than specific provider APIs.

## 2. Thin Judge Concept

The "Thin Judge" is a specialized role in ZaoFu designed for the final, read-only evaluation of a task or goal completion.

**Key Implementation Semantics:**
The Thin Judge is constrained to be strictly read-only, ensuring it cannot modify the product or re-run tests. It operates at the "goal closure" boundary (`src/zf/core/workflow/runner_policy.py:apply_goal_closure_judge_policy`). The Thin Judge's primary responsibility is to synthesize admitted facts (planning, verification, waivers, and closure facts) into a deterministic result (`src/zf/runtime/goal_closure_result.py:GoalClosureResult`). It does not make product-level decisions but rather determines if the established criteria for closure have been met based on the provided evidence.

**Coupling and Boundaries:**
The Thin Judge depends on the `goal_closure_bridge` (`src/zf/runtime/goal_closure_bridge.py`) to access the immutable objective artifact and the `candidate_result_binding` (`src/zf/runtime/candidate_result_binding.py`) to understand the state of the candidate. It is tightly coupled with the `GoalClosureResult` schema, which requires specific fields like `workflow_run_id`, `goal_id`, `task_map_generation`, and various references to planning and verification artifacts.

**Maturity Signals:**
The Thin Judge is actively developed, with specific e2e tests (`tests/e2e/thin_judge_goal_closure_provider_drill.py`) and unit tests (`tests/test_module_gap_plan_runtime.py`). The design documents (referenced in the code, e.g., `06-verification.md`) suggest a planned evolution towards more complex discrimination types.

**Provider Neutrality:**
The Thin Judge concept is **provider-neutral**. It operates on abstract event logs and immutable sidecars, making it independent of the specific LLM or code execution provider used by ZaoFu.

## 3. Runtime Candidate Verification

ZaoFu implements a robust system for verifying candidates, ensuring that proposed changes are valid and meet the required criteria.

**Key Implementation Semantics:**
The `candidate_verification_authority` (`src/zf/runtime/candidate_verification_authority.py:prepare_candidate_verification_authority`) pins a specific candidate and its associated contract before provider dispatch. This ensures that verification is always performed against the exact state that was evaluated. The `completion_honesty` module (`src/zf/runtime/completion_honesty.py`) provides a layer of protection against "hallucinated" completions by verifying that claimed artifacts and commits actually exist in the workspace and match the recorded state.

The `candidate_incremental` (`src/zf/runtime/candidate_incremental.py`) and `candidate_integration` (`src/zf/runtime/candidate_integration.py`) modules manage the deterministic identity and failure facts for candidate integration, ensuring that each candidate can be uniquely identified and its lineage traced.

**Coupling and Boundaries:**
This area is deeply coupled with the event log and the git state of the workspace. It relies on the `TaskStore` and `EventWriter` to record the outcomes of verification attempts. The boundaries are strictly defined, with the kernel responsible for verifying the existence and consistency of claims, while the quality of the product remains the responsibility of review/verify agents.

**Maturity Signals:**
The presence of comprehensive tests (`tests/test_candidate_verification_authority.py`) and the detailed logic for handling edge cases (e.g., scheme-based references in `completion_honesty.py`) indicate a mature and battle-tested system.

**Provider Neutrality:**
This area is **mixed**. While the core verification logic (e.g., hashing, event recording) is provider-neutral, the execution of verification commands and the handling of specific provider constraints (e.g., Codex's restricted mode) introduce provider-specific dependencies.

## 4. Self-Evaluation

ZaoFu includes a deterministic self-evaluation system designed to continuously monitor and improve the platform's performance.

**Key Implementation Semantics:**
The self-evaluation system uses YAML contracts (`src/zf/core/self_eval/contract.py`) to define the goals, metrics, and verification commands. The `runner` (`src/zf/core/self_eval/runner.py:run_self_eval`) executes these contracts, capturing the results and writing them to an output directory. If a self-evaluation fails, the `backlog` module (`src/zf/core/self_eval/backlog.py:write_failure_backlog`) automatically creates a task in the backlog to address the failure, ensuring that issues are tracked and resolved.

**Coupling and Boundaries:**
The self-evaluation system is integrated with the task pipeline, using the `TaskStore` to create backlog items. It is designed to be isolated, operating on its own contracts and output directories, but it feeds directly into the workflow management system.

**Maturity Signals:**
The system is supported by unit tests (`tests/test_cli_self_eval.py`), demonstrating its readiness for deployment. The use of YAML contracts provides a flexible and maintainable way to define evaluation criteria.

**Provider Neutrality:**
This area is **provider-neutral**. The self-evaluation mechanism relies on executing standard commands and parsing their output, making it independent of the underlying provider.
