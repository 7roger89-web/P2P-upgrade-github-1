from __future__ import annotations

"""Minimum deterministic Story Core for story.script.production_mvp.

Storage is flat Markdown/YAML. For dependency-free MVP validation, YAML files
use the JSON-compatible subset of YAML 1.2 and are parsed with the Python
standard library. The core is provider/model/video-tool neutral.
"""

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

CAPABILITY_ID = "story.script.production_mvp"
CORE_FILES = ("brief.yaml", "locks.yaml", "spine.yaml", "state.yaml", "beats.yaml")
CONTEXT_STATE_KEYS = ("time_s", "location", "on_screen")
ALLOWED_BEAT_KEYS = {
    "id", "spine_ref", "actors", "preconditions", "consequences", "transition",
    "identity_assertions", "canon_assertions", "description",
}
FORBIDDEN_BEAT_KEYS = {
    "canon_updates", "lock_updates", "identity_updates", "world_updates", "state_after",
}


class StoryValidationError(ValueError):
    pass


def load_yaml_json_subset(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StoryValidationError(f"STORY_FILE_INVALID:{path}") from exc
    if not isinstance(value, dict):
        raise StoryValidationError(f"STORY_FILE_ROOT_MUST_BE_MAPPING:{path}")
    return value


def load_story_case(case_dir: Path) -> dict[str, dict[str, Any]]:
    missing = [name for name in CORE_FILES if not (case_dir / name).is_file()]
    if missing:
        raise StoryValidationError(f"STORY_CORE_FILES_MISSING:{','.join(missing)}")
    return {
        "brief": load_yaml_json_subset(case_dir / "brief.yaml"),
        "locks": load_yaml_json_subset(case_dir / "locks.yaml"),
        "spine": load_yaml_json_subset(case_dir / "spine.yaml"),
        "state": load_yaml_json_subset(case_dir / "state.yaml"),
        "beats": load_yaml_json_subset(case_dir / "beats.yaml"),
    }


def _character_index(locks: Mapping[str, Any], errors: list[str]) -> dict[str, Mapping[str, Any]]:
    raw = locks.get("characters")
    if not isinstance(raw, list) or not raw:
        errors.append("LOCKS_CHARACTERS_REQUIRED")
        return {}
    result: dict[str, Mapping[str, Any]] = {}
    for index, item in enumerate(raw):
        if not isinstance(item, Mapping):
            errors.append(f"LOCK_CHARACTER_INVALID:{index}")
            continue
        char_id = str(item.get("id") or "")
        if not char_id:
            errors.append(f"LOCK_CHARACTER_ID_REQUIRED:{index}")
            continue
        if char_id in result:
            errors.append(f"LOCK_CHARACTER_DUPLICATE:{char_id}")
            continue
        result[char_id] = item
    return result


def _validate_identity_assertions(assertions: Any, characters: Mapping[str, Mapping[str, Any]], beat_id: str, errors: list[str]) -> None:
    if assertions is None:
        return
    if not isinstance(assertions, Mapping):
        errors.append(f"IDENTITY_ASSERTIONS_INVALID:{beat_id}")
        return
    for char_id, raw_fields in assertions.items():
        char_key = str(char_id)
        locked = characters.get(char_key)
        if locked is None:
            errors.append(f"IDENTITY_ASSERTION_UNKNOWN_CHARACTER:{beat_id}:{char_key}")
            continue
        if not isinstance(raw_fields, Mapping):
            errors.append(f"IDENTITY_ASSERTION_FIELDS_INVALID:{beat_id}:{char_key}")
            continue
        for field, value in raw_fields.items():
            if field not in locked:
                errors.append(f"IDENTITY_ASSERTION_UNLOCKED_FIELD:{beat_id}:{char_key}:{field}")
            elif locked[field] != value:
                errors.append(f"IDENTITY_LOCK_CONTRADICTION:{beat_id}:{char_key}:{field}")


def _validate_canon_assertions(assertions: Any, canon: Mapping[str, Any], beat_id: str, errors: list[str]) -> None:
    if assertions is None:
        return
    if not isinstance(assertions, Mapping):
        errors.append(f"CANON_ASSERTIONS_INVALID:{beat_id}")
        return
    for fact_key, value in assertions.items():
        key = str(fact_key)
        if key not in canon:
            errors.append(f"CANON_ASSERTION_UNKNOWN:{beat_id}:{key}")
        elif canon[key] != value:
            errors.append(f"CANON_CONTRADICTION:{beat_id}:{key}")


def _compare_preconditions(preconditions: Any, current_state: Mapping[str, Any], beat_id: str, errors: list[str]) -> None:
    if not isinstance(preconditions, Mapping):
        errors.append(f"BEAT_PRECONDITIONS_REQUIRED:{beat_id}")
        return
    for key, expected in preconditions.items():
        if key not in current_state:
            errors.append(f"PRECONDITION_UNKNOWN_STATE:{beat_id}:{key}")
        elif current_state[key] != expected:
            errors.append(f"PRECONDITION_MISMATCH:{beat_id}:{key}")


def _apply_consequences(
    consequences: Any,
    transition: Any,
    current_state: dict[str, Any],
    characters: Mapping[str, Mapping[str, Any]],
    beat_id: str,
    errors: list[str],
) -> dict[str, Any]:
    if not isinstance(consequences, Mapping):
        errors.append(f"BEAT_CONSEQUENCES_REQUIRED:{beat_id}")
        return current_state

    changed_context: dict[str, Any] = {}
    for key, value in consequences.items():
        if key not in current_state:
            errors.append(f"CONSEQUENCE_UNKNOWN_STATE:{beat_id}:{key}")
            continue
        if key in CONTEXT_STATE_KEYS and current_state[key] != value:
            changed_context[key] = value

    if transition is None:
        transition_map: Mapping[str, Any] = {}
    elif isinstance(transition, Mapping):
        transition_map = transition
    else:
        errors.append(f"TRANSITION_INVALID:{beat_id}")
        transition_map = {}

    for key, target in changed_context.items():
        if key not in transition_map:
            errors.append(f"DECLARED_TRANSITION_REQUIRED:{beat_id}:{key}")
        elif transition_map[key] != target:
            errors.append(f"TRANSITION_TARGET_MISMATCH:{beat_id}:{key}")

    for key in transition_map:
        if key not in CONTEXT_STATE_KEYS:
            errors.append(f"TRANSITION_KEY_INVALID:{beat_id}:{key}")
        elif key not in changed_context:
            errors.append(f"TRANSITION_WITHOUT_STATE_CHANGE:{beat_id}:{key}")

    next_state = deepcopy(current_state)
    for key, value in consequences.items():
        if key in current_state:
            next_state[key] = deepcopy(value)

    on_screen = next_state.get("on_screen")
    if not isinstance(on_screen, list):
        errors.append(f"ON_SCREEN_MUST_BE_LIST:{beat_id}")
    else:
        unknown = [str(item) for item in on_screen if str(item) not in characters]
        if unknown:
            errors.append(f"ON_SCREEN_UNKNOWN_CHARACTER:{beat_id}:{','.join(unknown)}")
        if len(set(map(str, on_screen))) != len(on_screen):
            errors.append(f"ON_SCREEN_DUPLICATE_CHARACTER:{beat_id}")
    return next_state


def validate_story_core(bundle: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    required = {"brief", "locks", "spine", "state", "beats"}
    if set(bundle) != required:
        missing = sorted(required - set(bundle))
        extra = sorted(set(bundle) - required)
        raise StoryValidationError(f"STORY_CORE_BUNDLE_INVALID:missing={missing}:extra={extra}")

    brief = bundle["brief"]
    locks = bundle["locks"]
    spine = bundle["spine"]
    state_doc = bundle["state"]
    beats_doc = bundle["beats"]

    expected_schemas = {
        "brief": "story-brief/1",
        "locks": "story-locks/1",
        "spine": "story-spine/1",
        "state": "story-state/1",
        "beats": "story-beats/1",
    }
    for name, expected in expected_schemas.items():
        if bundle[name].get("schema") != expected:
            errors.append(f"SCHEMA_INVALID:{name}")

    story_id = str(brief.get("story_id") or "")
    if not story_id:
        errors.append("BRIEF_STORY_ID_REQUIRED")
    for name in ("locks", "spine", "state", "beats"):
        if str(bundle[name].get("story_id") or "") != story_id:
            errors.append(f"STORY_ID_MISMATCH:{name}")

    characters = _character_index(locks, errors)
    canon = locks.get("canon", {})
    if not isinstance(canon, Mapping):
        errors.append("LOCKS_CANON_MUST_BE_MAPPING")
        canon = {}

    if locks.get("owner_gate") != "APPROVED":
        errors.append("OWNER_GATE_LOCKS_NOT_APPROVED")
    if spine.get("owner_gate") != "APPROVED":
        errors.append("OWNER_GATE_SPINE_NOT_APPROVED")

    nodes = spine.get("nodes")
    node_order: dict[str, int] = {}
    if not isinstance(nodes, list) or not nodes:
        errors.append("SPINE_NODES_REQUIRED")
        nodes = []
    for index, node in enumerate(nodes):
        if not isinstance(node, Mapping):
            errors.append(f"SPINE_NODE_INVALID:{index}")
            continue
        node_id = str(node.get("id") or "")
        if not node_id:
            errors.append(f"SPINE_NODE_ID_REQUIRED:{index}")
            continue
        if node_id in node_order:
            errors.append(f"SPINE_NODE_DUPLICATE:{node_id}")
            continue
        node_order[node_id] = index
        if not str(node.get("why_now") or "").strip():
            errors.append(f"SPINE_WHY_NOW_REQUIRED:{node_id}")
        requires = node.get("requires", [])
        if not isinstance(requires, list):
            errors.append(f"SPINE_REQUIRES_INVALID:{node_id}")
            continue
        for parent in requires:
            parent_id = str(parent)
            if parent_id not in node_order:
                errors.append(f"SPINE_CAUSAL_PARENT_MISSING_OR_FORWARD:{node_id}:{parent_id}")

    current_state_raw = state_doc.get("initial")
    if not isinstance(current_state_raw, Mapping):
        errors.append("INITIAL_STATE_REQUIRED")
        current_state: dict[str, Any] = {}
    else:
        current_state = deepcopy(dict(current_state_raw))

    for key in CONTEXT_STATE_KEYS:
        if key not in current_state:
            errors.append(f"INITIAL_CONTEXT_STATE_REQUIRED:{key}")
    if isinstance(current_state.get("on_screen"), list):
        unknown = [str(item) for item in current_state["on_screen"] if str(item) not in characters]
        if unknown:
            errors.append(f"INITIAL_ON_SCREEN_UNKNOWN:{','.join(unknown)}")

    beats = beats_doc.get("beats")
    if not isinstance(beats, list) or not beats:
        errors.append("BEATS_REQUIRED")
        beats = []

    seen_beats: set[str] = set()
    referenced_nodes: set[str] = set()
    previous_node_index = -1
    state_diff_log: list[dict[str, Any]] = []

    for index, beat in enumerate(beats):
        if not isinstance(beat, Mapping):
            errors.append(f"BEAT_INVALID:{index}")
            continue
        beat_id = str(beat.get("id") or "")
        if not beat_id:
            errors.append(f"BEAT_ID_REQUIRED:{index}")
            continue
        if beat_id in seen_beats:
            errors.append(f"BEAT_DUPLICATE:{beat_id}")
            continue
        seen_beats.add(beat_id)

        unknown_keys = set(beat) - ALLOWED_BEAT_KEYS
        for key in sorted(unknown_keys):
            if key in FORBIDDEN_BEAT_KEYS:
                errors.append(f"BEAT_NARRATIVE_MUTATION_FORBIDDEN:{beat_id}:{key}")
            else:
                errors.append(f"BEAT_FIELD_UNKNOWN:{beat_id}:{key}")

        spine_ref = str(beat.get("spine_ref") or "")
        if spine_ref not in node_order:
            errors.append(f"BEAT_SPINE_REF_INVALID:{beat_id}:{spine_ref}")
            node_index = previous_node_index
        else:
            referenced_nodes.add(spine_ref)
            node_index = node_order[spine_ref]
            if node_index < previous_node_index:
                errors.append(f"BEAT_CAUSAL_ORDER_REGRESSION:{beat_id}:{spine_ref}")
            previous_node_index = max(previous_node_index, node_index)

        actors = beat.get("actors", [])
        if not isinstance(actors, list):
            errors.append(f"BEAT_ACTORS_INVALID:{beat_id}")
        else:
            for actor in actors:
                if str(actor) not in characters:
                    errors.append(f"BEAT_ACTOR_UNKNOWN:{beat_id}:{actor}")

        _validate_identity_assertions(beat.get("identity_assertions"), characters, beat_id, errors)
        _validate_canon_assertions(beat.get("canon_assertions"), canon, beat_id, errors)
        _compare_preconditions(beat.get("preconditions"), current_state, beat_id, errors)

        before = deepcopy(current_state)
        current_state = _apply_consequences(
            beat.get("consequences"),
            beat.get("transition"),
            current_state,
            characters,
            beat_id,
            errors,
        )
        changed = {
            key: {"from": before.get(key), "to": current_state.get(key)}
            for key in current_state
            if before.get(key) != current_state.get(key)
        }
        state_diff_log.append({"beat_id": beat_id, "changes": changed})

    for node_id in node_order:
        if node_id not in referenced_nodes:
            errors.append(f"SPINE_NODE_UNCOVERED:{node_id}")

    duration = brief.get("duration_s")
    final_time = current_state.get("time_s")
    if isinstance(duration, (int, float)) and isinstance(final_time, (int, float)):
        if abs(float(duration) - float(final_time)) > 1e-6:
            errors.append("STORY_DURATION_STATE_MISMATCH")

    return {
        "capability_id": CAPABILITY_ID,
        "story_id": story_id,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "final_state": current_state,
        "state_diff_log": state_diff_log,
        "validated_spine_nodes": list(node_order),
        "validated_beats": list(seen_beats),
    }
