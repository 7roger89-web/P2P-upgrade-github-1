from __future__ import annotations

"""Video-production adapter for story.script.production_mvp.

The adapter consumes a validated Story Core and adds production metadata only.
It may warn or gate on AI-video feasibility. It never rewrites beat causality,
preconditions, consequences, identity locks, canon, or world logic.
"""

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from .story_script_core import CAPABILITY_ID, StoryValidationError, load_yaml_json_subset

ADAPTER_SCHEMA = "story-video-adapter/1"
PRODUCTION_PACK_SCHEMA = "story-production-pack/1"
FEASIBILITY_RISKS = ("LOW", "MEDIUM", "HIGH")
FORBIDDEN_SHOT_FIELDS = {
    "spine_ref", "preconditions", "consequences", "identity_assertions",
    "canon_assertions", "canon_updates", "locks", "world", "state", "why_now",
}
ALLOWED_SHOT_FIELDS = {
    "id", "beat_id", "duration_s", "framing", "action", "feasibility_risk",
    "continuity_notes", "generation_notes",
}


def load_video_adapter(path: Path) -> dict[str, Any]:
    return load_yaml_json_subset(path)


def _fingerprint(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_production_pack(
    core_bundle: Mapping[str, Mapping[str, Any]],
    core_report: Mapping[str, Any],
    adapter: Mapping[str, Any],
) -> dict[str, Any]:
    if core_report.get("status") != "PASS":
        raise StoryValidationError("VIDEO_ADAPTER_REQUIRES_VALIDATED_STORY_CORE")
    if adapter.get("schema") != ADAPTER_SCHEMA:
        raise StoryValidationError("VIDEO_ADAPTER_SCHEMA_INVALID")
    story_id = str(core_report.get("story_id") or "")
    if str(adapter.get("story_id") or "") != story_id:
        raise StoryValidationError("VIDEO_ADAPTER_STORY_ID_MISMATCH")

    beats = core_bundle["beats"].get("beats")
    if not isinstance(beats, list):
        raise StoryValidationError("VIDEO_ADAPTER_BEATS_INVALID")
    beat_ids = [str(beat.get("id") or "") for beat in beats]
    beat_pos = {beat_id: index for index, beat_id in enumerate(beat_ids)}

    raw_shots = adapter.get("shots")
    if not isinstance(raw_shots, list) or not raw_shots:
        raise StoryValidationError("VIDEO_ADAPTER_SHOTS_REQUIRED")

    errors: list[str] = []
    warnings: list[str] = []
    shots: list[dict[str, Any]] = []
    seen_shots: set[str] = set()
    covered_beats: set[str] = set()
    previous_pos = -1
    total_duration = 0.0

    for index, raw in enumerate(raw_shots):
        if not isinstance(raw, Mapping):
            errors.append(f"SHOT_INVALID:{index}")
            continue
        shot = deepcopy(dict(raw))
        shot_id = str(shot.get("id") or "")
        if not shot_id:
            errors.append(f"SHOT_ID_REQUIRED:{index}")
            continue
        if shot_id in seen_shots:
            errors.append(f"SHOT_DUPLICATE:{shot_id}")
            continue
        seen_shots.add(shot_id)

        for field in sorted(set(shot) - ALLOWED_SHOT_FIELDS):
            if field in FORBIDDEN_SHOT_FIELDS:
                errors.append(f"VIDEO_ADAPTER_NARRATIVE_REWRITE_FORBIDDEN:{shot_id}:{field}")
            else:
                errors.append(f"SHOT_FIELD_UNKNOWN:{shot_id}:{field}")

        beat_id = str(shot.get("beat_id") or "")
        if beat_id not in beat_pos:
            errors.append(f"SHOT_BEAT_REF_INVALID:{shot_id}:{beat_id}")
        else:
            pos = beat_pos[beat_id]
            if pos < previous_pos:
                errors.append(f"SHOT_BEAT_ORDER_REGRESSION:{shot_id}:{beat_id}")
            previous_pos = max(previous_pos, pos)
            covered_beats.add(beat_id)

        risk = str(shot.get("feasibility_risk") or "")
        if risk not in FEASIBILITY_RISKS:
            errors.append(f"SHOT_FEASIBILITY_RISK_INVALID:{shot_id}")
        elif risk == "HIGH":
            warnings.append(f"AI_VIDEO_FEASIBILITY_HIGH:{shot_id}:{beat_id}")

        duration = shot.get("duration_s")
        if not isinstance(duration, (int, float)) or isinstance(duration, bool) or duration <= 0:
            errors.append(f"SHOT_DURATION_INVALID:{shot_id}")
        else:
            total_duration += float(duration)

        shots.append(shot)

    for beat_id in beat_ids:
        if beat_id not in covered_beats:
            errors.append(f"BEAT_WITHOUT_SHOT:{beat_id}")

    brief_duration = core_bundle["brief"].get("duration_s")
    if isinstance(brief_duration, (int, float)):
        if abs(total_duration - float(brief_duration)) > 1e-6:
            errors.append("SHOT_DURATION_TOTAL_MISMATCH")

    if errors:
        raise StoryValidationError("VIDEO_ADAPTER_INVALID:" + "|".join(errors))

    return {
        "schema": PRODUCTION_PACK_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "story_id": story_id,
        "owner_gate": "PENDING",
        "narrative_source_fingerprints": {
            name: _fingerprint(core_bundle[name])
            for name in ("brief", "locks", "spine", "state", "beats")
        },
        "narrative_refs": {
            "spine_nodes": list(core_report.get("validated_spine_nodes") or []),
            "beats": beat_ids,
        },
        "shots": shots,
        "warnings": warnings,
        "generation_authorized": False,
        "adapter_boundary": {
            "narrative_rewrite": "FORBIDDEN",
            "feasibility_high": "WARN_ONLY",
            "final_video_generation": "OUT_OF_SCOPE",
        },
    }


def export_production_pack(pack: Mapping[str, Any], path: Path) -> Path:
    if path.suffix.lower() not in {".yaml", ".yml"}:
        raise StoryValidationError("PRODUCTION_PACK_MUST_BE_YAML")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(pack, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return path
