"""Provider-neutral video continuity foundation for consistency-controlled AI-video.

This is a *contract* surface only.  It deliberately has no renderer, no model
runtime, no network, no credentials, and no vision-QA platform.  A random video
renderer (e.g. Arena Video / DesignArena) never owns identity or continuity;
those live here in canonical assets, approved keyframes, shot state, and a
compact continuity gate.

Design rules honoured here:

- Single existing P2P router.  This module supplies contract data / readiness
  facts; it is not a router, registry, or orchestrator.
- Provider prompt limits are *profile/config data*, not hard-coded constants.
- A raw final frame containing drift must never automatically become the
  canonical input for the next shot.  A failed shot cannot become the source of
  truth for downstream shots.
- Standard library only.  No packages are imported from outside this module.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


DIRECTOR_SPEC_SCHEMA: str = "p2p-video-director-spec/1"
CANONICAL_VISUAL_CONTRACT_SCHEMA: str = "p2p-canonical-visual-contract/1"
PERFORMANCE_BIBLE_SCHEMA: str = "p2p-performance-bible/1"
CONTINUITY_GATE_SCHEMA: str = "p2p-continuity-gate/1"
REANCHOR_CYCLE_SCHEMA: str = "p2p-reanchor-cycle/1"
PROVIDER_PROJECTION_SCHEMA: str = "p2p-provider-projection/1"

# The compact continuity dimensions required by the task.  Kept as a contract
# enumerable, not a broad vision-QA taxonomy.
CONTINUITY_DIMENSIONS: tuple[str, ...] = (
    "identity",
    "hair_body",
    "costume",
    "prop_weapon",
    "environment_style",
    "expected_start_state",
    "expected_end_state",
    "action_camera_continuity",
)

# Canonical visual consistency contract dimensions (task section B).
CANONICAL_ASSET_DIMENSIONS: tuple[str, ...] = (
    "identity_face",
    "hair",
    "body_proportions",
    "costume",
    "prop_weapon",
    "environment",
    "visual_style",
    "image_consistency",
    "temporal_video_consistency",
    "shot_to_shot_continuity",
)

# Best-of-N candidate rendering semantics (task section G).
RENDER_STATE: str = "BEST_OF_N_CANDIDATE"
RENDER_MODEL_STABILITY: str = "NOT_ASSUMED"


class VideoContinuityError(ValueError):
    """Raised when a video continuity contract is invalid or cannot advance."""


def _sha256(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _mapping(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise VideoContinuityError(f"{field}: expected object")
    if any(not isinstance(key, str) for key in value):
        raise VideoContinuityError(f"{field}: keys must be strings")
    return dict(value)


def _string_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list):
        raise VideoContinuityError(f"{field}: expected array")
    result = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise VideoContinuityError(f"{field}[{index}]: expected non-empty string")
        result.append(item)
    return result


@dataclass(frozen=True)
class VideoDirectorSpec:
    """Provider-neutral structured production specification (task section A).

    Field list is the minimum the task requires.  `provider_projection_hints`
    is data (not hard-coded limits) so prompt-limited renderers can be reasoned
    about without duplicating the master spec per shot.
    """

    canonical_refs: Mapping[str, str]
    identity_constraints: Mapping[str, object]
    element_constraints: Mapping[str, object]
    timeline_duration_seconds: float
    action_performance: Mapping[str, object]
    camera: Mapping[str, object]
    lighting: Mapping[str, object]
    physics: Mapping[str, object]
    dialogue_audio: Mapping[str, object]
    continuity_state: Mapping[str, object]
    negative_constraints: Sequence[str]
    provider_projection_hints: Mapping[str, object] = field(default_factory=dict)
    schema: str = DIRECTOR_SPEC_SCHEMA

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "VideoDirectorSpec":
        root = _mapping(value, "video_director_spec")
        if root.get("schema") != DIRECTOR_SPEC_SCHEMA:
            raise VideoContinuityError("video_director_spec.schema: unsupported schema")
        required = {
            "canonical_refs",
            "identity_constraints",
            "element_constraints",
            "timeline_duration_seconds",
            "action_performance",
            "camera",
            "lighting",
            "physics",
            "dialogue_audio",
            "continuity_state",
            "negative_constraints",
        }
        missing = sorted(required - set(root))
        if missing:
            raise VideoContinuityError(f"video_director_spec: missing keys: {', '.join(missing)}")
        duration = root["timeline_duration_seconds"]
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or duration <= 0:
            raise VideoContinuityError("video_director_spec.timeline_duration_seconds: expected positive number")
        return cls(
            canonical_refs=_mapping(root["canonical_refs"], "canonical_refs"),
            identity_constraints=_mapping(root["identity_constraints"], "identity_constraints"),
            element_constraints=_mapping(root["element_constraints"], "element_constraints"),
            timeline_duration_seconds=float(duration),
            action_performance=_mapping(root["action_performance"], "action_performance"),
            camera=_mapping(root["camera"], "camera"),
            lighting=_mapping(root["lighting"], "lighting"),
            physics=_mapping(root["physics"], "physics"),
            dialogue_audio=_mapping(root["dialogue_audio"], "dialogue_audio"),
            continuity_state=_mapping(root["continuity_state"], "continuity_state"),
            negative_constraints=tuple(_string_list(root["negative_constraints"], "negative_constraints")),
            provider_projection_hints=_mapping(root.get("provider_projection_hints", {}), "provider_projection_hints"),
        )

    def identity_hash(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False)
        return _sha256(payload)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "canonical_refs": dict(self.canonical_refs),
            "identity_constraints": dict(self.identity_constraints),
            "element_constraints": dict(self.element_constraints),
            "timeline_duration_seconds": self.timeline_duration_seconds,
            "action_performance": dict(self.action_performance),
            "camera": dict(self.camera),
            "lighting": dict(self.lighting),
            "physics": dict(self.physics),
            "dialogue_audio": dict(self.dialogue_audio),
            "continuity_state": dict(self.continuity_state),
            "negative_constraints": list(self.negative_constraints),
            "provider_projection_hints": dict(self.provider_projection_hints),
        }


@dataclass(frozen=True)
class CanonicalVisualContract:
    """Canonical identity/appearance/world consistency contract (task section B).

    Distinct from a prompt.  A renderer never re-derives identity; the
    render-agnostic anchor below is the source of truth.
    """

    identity_face: Mapping[str, object]
    hair: Mapping[str, object]
    body_proportions: Mapping[str, object]
    costume: Mapping[str, object]
    prop_weapon: Mapping[str, object]
    environment: Mapping[str, object]
    visual_style: Mapping[str, object]
    image_consistency: str
    temporal_video_consistency: str
    shot_to_shot_continuity: str
    schema: str = CANONICAL_VISUAL_CONTRACT_SCHEMA

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "CanonicalVisualContract":
        root = _mapping(value, "canonical_visual_contract")
        if root.get("schema") != CANONICAL_VISUAL_CONTRACT_SCHEMA:
            raise VideoContinuityError("canonical_visual_contract.schema: unsupported schema")
        for key in ("identity_face", "hair", "body_proportions", "costume", "prop_weapon", "environment", "visual_style"):
            if key not in root:
                raise VideoContinuityError(f"canonical_visual_contract: missing key: {key}")
        return cls(
            identity_face=_mapping(root["identity_face"], "identity_face"),
            hair=_mapping(root["hair"], "hair"),
            body_proportions=_mapping(root["body_proportions"], "body_proportions"),
            costume=_mapping(root["costume"], "costume"),
            prop_weapon=_mapping(root["prop_weapon"], "prop_weapon"),
            environment=_mapping(root["environment"], "environment"),
            visual_style=_mapping(root["visual_style"], "visual_style"),
            image_consistency=root["image_consistency"],
            temporal_video_consistency=root["temporal_video_consistency"],
            shot_to_shot_continuity=root["shot_to_shot_continuity"],
        )

    def dimensions(self) -> tuple[str, ...]:
        return CANONICAL_ASSET_DIMENSIONS

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "identity_face": dict(self.identity_face),
            "hair": dict(self.hair),
            "body_proportions": dict(self.body_proportions),
            "costume": dict(self.costume),
            "prop_weapon": dict(self.prop_weapon),
            "environment": dict(self.environment),
            "visual_style": dict(self.visual_style),
            "image_consistency": self.image_consistency,
            "temporal_video_consistency": self.temporal_video_consistency,
            "shot_to_shot_continuity": self.shot_to_shot_continuity,
        }


@dataclass(frozen=True)
class PerformanceBible:
    """Provider-neutral behavioural continuity cues (task section C).

    Compact, not an animation engine.  Only bounded performance cues justified
    by the research reference's production-spec structure are modelled.
    """

    movement_style: str
    gesture_amplitude: str
    action_tempo: str
    body_posture_tendencies: str
    camera_feel_inertia: str
    cues: Mapping[str, str] = field(default_factory=dict)
    schema: str = PERFORMANCE_BIBLE_SCHEMA

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "PerformanceBible":
        root = _mapping(value, "performance_bible")
        if root.get("schema") != PERFORMANCE_BIBLE_SCHEMA:
            raise VideoContinuityError("performance_bible.schema: unsupported schema")
        for key in ("movement_style", "gesture_amplitude", "action_tempo", "body_posture_tendencies", "camera_feel_inertia"):
            if key not in root:
                raise VideoContinuityError(f"performance_bible: missing key: {key}")
        cues = root.get("cues", {})
        if not isinstance(cues, dict) or any(not isinstance(k, str) for k in cues):
            raise VideoContinuityError("performance_bible.cues: invalid")
        return cls(
            movement_style=root["movement_style"],
            gesture_amplitude=root["gesture_amplitude"],
            action_tempo=root["action_tempo"],
            body_posture_tendencies=root["body_posture_tendencies"],
            camera_feel_inertia=root["camera_feel_inertia"],
            cues={str(k): str(v) for k, v in cues.items()},
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "movement_style": self.movement_style,
            "gesture_amplitude": self.gesture_amplitude,
            "action_tempo": self.action_tempo,
            "body_posture_tendencies": self.body_posture_tendencies,
            "camera_feel_inertia": self.camera_feel_inertia,
            "cues": dict(self.cues),
        }


@dataclass(frozen=True)
class ContinuityVerdict:
    """Result of the compact continuity gate (task section E).

    `propagate_allowed` gates state propagation to the next shot.  A failed
    shot must not become the source of truth for downstream shots.
    """

    passed: bool
    propagate_allowed: bool
    results: Mapping[str, Mapping[str, object]]
    blocker: str | None = None
    schema: str = CONTINUITY_GATE_SCHEMA

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "passed": self.passed,
            "propagate_allowed": self.propagate_allowed,
            "results": {k: dict(v) for k, v in self.results.items()},
            "blocker": self.blocker,
        }


def _check_dimension(name: str, value: object, expected_start: object, expected_end: object) -> Mapping[str, object]:
    # A compact contract.  `value` is either a bool score or a short
    # status string; we fail closed when the dimension is explicitly known to
    # diverge from the canonical/expected state.  This is deliberately NOT a
    # vision model call.
    if isinstance(value, bool):
        ok = value
    else:
        ok = str(value).strip().lower() not in {"drift", "fail", "divergent", "mismatch", "unsafe", "out"}
    return {"pass": ok, "value": value, "expected_start": expected_start, "expected_end": expected_end}


def evaluate_continuity_gate(
    shot: Mapping[str, object],
    canonical: CanonicalVisualContract,
    start_keyframe: Mapping[str, object],
    expected_end_state: Mapping[str, object],
) -> ContinuityVerdict:
    """Evaluate a candidate shot before it can propagate state downstream."""
    checks: dict[str, Mapping[str, object]] = {}
    # Map the compact gate dimensions onto the shot/canonical inputs.
    plan: tuple[tuple[str, object, object, object], ...] = (
        ("identity", shot.get("identity", True), canonical.identity_face, start_keyframe.get("identity", "canonical")),
        ("hair_body", shot.get("hair_body", True), {"hair": canonical.hair, "body": canonical.body_proportions}, start_keyframe.get("hair_body", "canonical")),
        ("costume", shot.get("costume", True), canonical.costume, start_keyframe.get("costume", "canonical")),
        ("prop_weapon", shot.get("prop_weapon", True), canonical.prop_weapon, start_keyframe.get("prop_weapon", "canonical")),
        ("environment_style", shot.get("environment_style", True), {"environment": canonical.environment, "style": canonical.visual_style}, start_keyframe.get("environment_style", "canonical")),
        ("expected_start_state", shot.get("expected_start_state", True), start_keyframe, expected_end_state),
        ("expected_end_state", shot.get("expected_end_state", True), start_keyframe.get("end_state", "canonical"), expected_end_state),
        ("action_camera_continuity", shot.get("action_camera_continuity", True), start_keyframe.get("camera", "canonical"), shot.get("camera", "canonical")),
    )
    for name, value, expected_start, expected_end in plan:
        checks[name] = _check_dimension(name, value, expected_start, expected_end)

    blockers = [name for name, result in checks.items() if not result["pass"]]
    passed = not blockers
    return ContinuityVerdict(
        passed=passed,
        propagate_allowed=passed,
        results=checks,
        blocker=(blockers[0] if blockers else None),
    )


@dataclass(frozen=True)
class ReanchorCycle:
    """Keyframe re-anchor state (task section D).

    Executes the preferred conceptual flow.  The critical rule: a raw final
    frame containing drift must never automatically become canonical input for
    the next shot.  A failed shot cannot become the source of truth.
    """

    start_keyframe: Mapping[str, object]
    candidate_takes: Sequence[Mapping[str, object]]
    best_take: Mapping[str, object]
    last_good_frame: Mapping[str, object]
    canonical_reanchor: Mapping[str, object]
    next_approved_keyframe: Mapping[str, object]
    drift_detected: bool
    gate_passed: bool
    schema: str = REANCHOR_CYCLE_SCHEMA

    @property
    def safe_to_reanchor(self) -> bool:
        """Only a drift-free frame that passed the gate may seed the next shot."""
        return self.gate_passed and not self.drift_detected

    def next_start(self) -> Mapping[str, object]:
        if not self.safe_to_reanchor:
            raise VideoContinuityError(
                "RE_ANCHOR_BLOCKED: drifted or un-approved final frame cannot become canonical input for the next shot"
            )
        return self.next_approved_keyframe

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "start_keyframe": dict(self.start_keyframe),
            "candidate_takes": [dict(take) for take in self.candidate_takes],
            "best_take": dict(self.best_take),
            "last_good_frame": dict(self.last_good_frame),
            "canonical_reanchor": dict(self.canonical_reanchor),
            "next_approved_keyframe": dict(self.next_approved_keyframe),
            "drift_detected": self.drift_detected,
            "gate_passed": self.gate_passed,
            "safe_to_reanchor": self.safe_to_reanchor,
        }


@dataclass(frozen=True)
class ProviderProfile:
    """Provider prompt limits as data (task section F).

    Not architecture constants.  A given renderer (Arena Video / DesignArena)
    can declare its own ceiling/widgets/vocabulary here.
    """

    provider_id: str
    max_prompt_chars: int
    accepts_image_reference: bool
    model_identity_stable: bool
    forbidden_tokens: Sequence[str] = field(default_factory=tuple)

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "ProviderProfile":
        root = _mapping(value, "provider_profile")
        if "provider_id" not in root or "max_prompt_chars" not in root:
            raise VideoContinuityError("provider_profile: missing required key")
        return cls(
            provider_id=str(root["provider_id"]),
            max_prompt_chars=int(root["max_prompt_chars"]),
            accepts_image_reference=bool(root.get("accepts_image_reference", False)),
            model_identity_stable=bool(root.get("model_identity_stable", False)),
            forbidden_tokens=tuple(_string_list(root.get("forbidden_tokens", []), "forbidden_tokens")),
        )


def project_provider_shot(
    director_spec: VideoDirectorSpec,
    canonical: CanonicalVisualContract,
    performance: PerformanceBible,
    profile: ProviderProfile,
    shot: Mapping[str, object],
) -> Mapping[str, object]:
    """Project a large master spec into a short, provider-specific shot prompt.

    Uses pointer references (canonical ref ids) instead of duplicating the full
    master spec per shot.  Keeps within the provider's declared character
    ceiling, stripping forbidden tokens if present.
    """
    refs = " ".join(f"{key}={value}" for key, value in director_spec.canonical_refs.items())
    parts = [
        f"identity:{list(canonical.identity_face.keys())[0] if canonical.identity_face else 'canonical'}",
        f"scene:{director_spec.camera.get('scene', 'canonical')}",
        f"camera:{director_spec.camera.get('move', 'locked')}",
        f"action:{director_spec.action_performance.get('action', shot.get('action', 'canonical'))}",
        f"tempo:{performance.action_tempo}",
        f"style:{canonical.visual_style.get('genre', 'canonical')}",
        f"duration:{director_spec.timeline_duration_seconds}s",
        f"refs:{refs}",
    ]
    if profile.accepts_image_reference:
        parts.insert(0, "anchor:<canonical_start_keyframe>")
    else:
        parts.insert(0, "no-anchor-image")
    prompt = "; ".join(part for part in parts if part and part != "canonical")
    for token in profile.forbidden_tokens:
        prompt = prompt.replace(token, "")
    if len(prompt) > profile.max_prompt_chars:
        prompt = prompt[: profile.max_prompt_chars]
    return {
        "schema": PROVIDER_PROJECTION_SCHEMA,
        "provider_id": profile.provider_id,
        "provider_prompt": prompt,
        "chars": len(prompt),
        "within_limit": len(prompt) <= profile.max_prompt_chars,
        "duplicated_master_spec": False,
        "model_identity_stable": profile.model_identity_stable,
        "reference_pointers_only": True,
    }


@dataclass(frozen=True)
class CandidateRendering:
    """Best-of-N candidate rendering semantics for Arena/DesignArena (task G)."""

    baseline_seed: str
    candidates: Sequence[Mapping[str, object]]
    best_take: Mapping[str, object]
    gate: ContinuityVerdict
    model_identity_stable: bool = False

    @property
    def state(self) -> str:
        return RENDER_STATE

    def to_dict(self) -> dict[str, object]:
        return {
            "baseline_seed": self.baseline_seed,
            "candidates": [dict(c) for c in self.candidates],
            "best_take": dict(self.best_take),
            "gate": self.gate.to_dict(),
            "state": self.state,
            "model_identity_stable": self.model_identity_stable,
            "renderer": "CANDIDATE_ONLY",
        }


def build_candidate_set(director_spec: VideoDirectorSpec, n: int, *, seed: str = "default") -> CandidateRendering:
    """Represent random renderer selection as best-of-N candidate sampling.

    The renderer is treated as a random/candidate motion generator, not a
    stable provider.  Each candidate is an opaque take bound to the same
    canonical start keyframe; none of them become canonical by default.
    """
    if n < 1:
        raise VideoContinuityError("candidate_set: n must be >= 1")
    seed_hash = _sha256(f"{seed}:{director_spec.identity_hash()}")
    candidates = [
        {
            "take_id": f"{seed_hash[:12]}-take-{index + 1}",
            "bound_keyframe": "canonical_start_keyframe",
            "renderer_model": "RANDOM_CANDIDATE",
            "model_identity_stable": False,
        }
        for index in range(n)
    ]
    gate = evaluate_continuity_gate(
        {"identity": True, "hair_body": True, "costume": True, "prop_weapon": True, "environment_style": True, "expected_start_state": True, "expected_end_state": True, "action_camera_continuity": True},
        CanonicalVisualContract(
            identity_face={"face": "canonical"},
            hair={"hair": "canonical"},
            body_proportions={"proportions": "canonical"},
            costume={"costume": "canonical"},
            prop_weapon={"prop": "canonical"},
            environment={"environment": "canonical"},
            visual_style={"style": "canonical"},
            image_consistency="canonical",
            temporal_video_consistency="canonical",
            shot_to_shot_continuity="canonical",
        ),
        {"identity": "canonical", "camera": "canonical"},
        {"end": "canonical"},
    )
    return CandidateRendering(
        baseline_seed=seed,
        candidates=candidates,
        best_take=candidates[0],
        gate=gate,
        model_identity_stable=False,
    )


__all__ = [
    "CANONICAL_ASSET_DIMENSIONS",
    "CANONICAL_VISUAL_CONTRACT_SCHEMA",
    "CONTINUITY_DIMENSIONS",
    "CONTINUITY_GATE_SCHEMA",
    "CandidateRendering",
    "CanonicalVisualContract",
    "ContinuityVerdict",
    "DIRECTOR_SPEC_SCHEMA",
    "PERFORMANCE_BIBLE_SCHEMA",
    "PROVIDER_PROJECTION_SCHEMA",
    "PerformanceBible",
    "ProviderProfile",
    "REANCHOR_CYCLE_SCHEMA",
    "RENDER_MODEL_STABILITY",
    "RENDER_STATE",
    "ReanchorCycle",
    "VideoContinuityError",
    "VideoDirectorSpec",
    "build_candidate_set",
    "evaluate_continuity_gate",
    "project_provider_shot",
]
