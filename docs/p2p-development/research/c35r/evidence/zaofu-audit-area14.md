# Audit Findings: Area Group 14 — AUTORESEARCH, MULTI-AGENT FANOUT & AGENT ROLE MODEL

## 1. Autoresearch Mechanism
- **Implementation**: Autoresearch is implemented as a supervisory mechanism in `src/zf/autoresearch/` (31 files) and `src/zf/runtime/autoresearch_*.py`. It operates in a loop (`loop.py`, `loop_driver.py`, `loop_eval.py`) to diagnose and resolve failures.
- **Semantics**: It uses an orchestrator (`orchestrator.py`) to manage the process, including triggers (`triggers.py`), failure signals (`failure_signals.py`), and review gates (`review_gate.py`). It supports bypassing the loop (`loop_bypass.py`) and reflection (`loop_reflect.py`).
- **Coupling/Boundaries**: Depends on `src/zf/core/state` and `src/zf/core/events`. It emits events like `autoresearch.invocation.requested` and `autoresearch.invocation.accepted` (`src/zf/runtime/autoresearch_invocation.py`).
- **Maturity**: Extensive test coverage in `tests/` (e.g., `test_autoresearch_loop_driver.py`, `test_autoresearch_orchestrator.py`).
- **Provider Neutrality**: Neutral. It relies on the core event system and does not depend on specific LLM provider APIs.

## 2. Multi-Agent Coordination/Fanout & Agent Role Model
- **Implementation**: Multi-agent coordination is managed through channels in `src/zf/runtime/channel_*.py` (e.g., `channel_router.py`, `channel_discussion.py`, `channel_roles.py`).
- **Semantics**:
    - **Routing**: `channel_router.py` handles routing messages based on mentions (`MENTION_RE`). It enforces gates to prevent unauthorized relays.
    - **Discussion State Machine**: `channel_discussion.py` implements a state machine (`idle -> phase1_blind -> phase2_relay -> phase3_synthesis -> idle`). It uses `advance_discussion` to drive transitions based on quorum and deadlines.
    - **Roles**: `channel_roles.py` manages role context references and excerpts (`load_role_definition_excerpt`).
- **Coupling/Boundaries**: Depends on `zf.core.events` for emitting and routing events. It interacts with `channel_projection.py` to read the current state.
- **Maturity**: Highly mature with extensive tests (`test_channel_discussion_driver.py`, `test_channel_router.py`).
- **Provider Neutrality**: Neutral. The coordination logic is deterministic and provider-agnostic.

## 3. Skill Model
- **Implementation**: Skills are managed in `src/zf/core/skills/` (`adapter_resolver.py`, `materialize.py`, `provenance.py`).
- **Semantics**:
    - **Resolution**: `adapter_resolver.py` resolves skills based on roles, stages, and strictness.
    - **Materialization**: `materialize.py` materializes skills into specific directories (e.g., `.claude/skills/` or `codex-home/skills`) based on the backend (`codex`, `claude-code`).
    - **Provenance**: `provenance.py` writes provenance lockfiles (`skills.lock.json`) to track skill versions and dependencies.
- **Coupling/Boundaries**: Depends on `zf.core.config.schema` and `zf.core.state.atomic_io`.
- **Maturity**: Well-tested (`test_adapter_skill_resolver.py`, `test_skill_materialization.py`).
- **Provider Neutrality**: Mixed. The core skill model is neutral, but materialization paths are specific to backends like `claude-code` and `codex`.

## 4. Result Schemas & Failure Classification
- **Implementation**: Result schemas and failure classification are part of the self-eval and autoresearch mechanisms.
- **Semantics**:
    - **Self-Eval**: `src/zf/core/self_eval/contract.py` defines `SelfEvalContract` which includes metrics and guards. `runner.py` executes these contracts and classifies failures based on exit codes and metric thresholds.
    - **Autoresearch**: `src/zf/autoresearch/failure_signals.py` (67KB) contains extensive logic for detecting and classifying various failure signals.
- **Coupling/Boundaries**: Depends on `zf.core.events` and `zf.core.task.store`.
- **Maturity**: Mature, with dedicated tests (`test_autoresearch_failure_signals.py`, `test_cli_self_eval.py`).
- **Provider Neutrality**: Neutral. It operates on deterministic execution results and structural signals.

## 5. Agent Briefings
- **Implementation**: Agent briefings and profiles are managed in `src/zf/core/profile/` (`apply.py`, `detector.py`, `schema.py`, `recommender.py`).
- **Semantics**:
    - **Detection**: `detector.py` deterministically detects the project stack (languages, frameworks, surfaces).
    - **Recommendation**: `recommender.py` maps the profile and operator intent to a validated archetype (preset or prod flow).
    - **Application**: `apply.py` injects managed sections into `AGENTS.md` and `CLAUDE.md` to provide briefings to agents.
- **Coupling/Boundaries**: Depends on `zf.core.config` and `yaml`.
- **Maturity**: Mature, with tests in `tests/` (`test_project_profile.py`, `test_workflow_profiles.py`).
- **Provider Neutrality**: Mixed. The detection and recommendation are neutral, but the application targets specific agent configuration files (`CLAUDE.md`, `AGENTS.md`).
