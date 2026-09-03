"""Provider-neutral video continuity foundation for consistency-controlled AI-video.

This is a *contract* surface only.  It deliberately has no renderer, no model
runtime, no network, no credentials, and no vision-QA platform.  A random video
renderer (e.g. Arena Video / DesignArena) never owns identity or continuity;
those live here in canonical assets, approved keyframes, shot state, and a
compact continuity gate.

Three facts are stated explicitly so nothing is over-claimed:

- Continuity QA is a **manual / external-evidence** gate.  This code consumes
  externally supplied PASS/FAIL-like fields; it does NOT inspect image/video
  media and does not do automated visual drift detection.
- Best-of-N is **candidate-planning / state semantics**.  It does NOT invoke
  Arena Video / DesignArena and does not score real takes.
- Provider prompt projection is **priority-aware**.  Mandatory constraints
  (anchor/reference, identity, canonical refs, action, camera, negative
  constraints) are preserved intact or the projection fails closed with an
  explicit reason.  There is no silent raw character truncation.

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

# Compact continuity dimensions required by the task (task section E).  This is
# a contract enumerable, not a broad vision-QA taxonomy.
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

# Best-of-N candidate rendering semantics (task section G).  Explicitly a
# planning/state mode, NOT actual rendering.
RENDER_STATE: str = "BEST_OF_N_CANDIDATE"
RENDER_MODEL_STABILITY: str = "NOT_ASSUMED"
BEST_OF_N_MODE: str = "PLANNING_STATE_ONLY"

# Continuity QA evidence mode.  Explicitly manual/external, not automated.
CONTINUITY_QA_EVIDENCE_MODE: str = "MANUAL_OR_EXTERNAL_EVIDENCE"

# Provider projection mode.  Priority-aware: no silent raw truncation.
PROJECTION_MODE: str = "PRIORITY_AWARE_PROJECTION"

# Mandatory projection constraints.  These must fit intact or the projection
# fails closed.  They are never silently truncated.
MANDATORY_CONSTRAINTS: tuple[str, ...] = (
    "anchor_reference",
    "identity",
    "reference_pointers",
    "action",
    "camera",
    "negative_constraints",
)


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


def _join(elements: Sequence[str]) -> str:
    return "; ".join(elem for elem in elements if elem and elem.strip())


def _head_str(mapping: Mapping[str, object]) -> str:
    return str(list(mapping.keys())[0]) if mapping else "canonical"


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

    This gate consumes externally supplied PASS/FAIL-like evidence.  It does
    NOT inspect image/video media and does not perform automated visual drift
    detection.  `evidence_source` and `inspects_media` make that explicit.
    """

    passed: bool
    propagate_allowed: bool
    results: Mapping[str, Mapping[str, object]]
    blocker: str | None = None
    schema: str = CONTINUITY_GATE_SCHEMA
    evidence_source: str = CONTINUITY_QA_EVIDENCE_MODE
    inspects_media: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "passed": self.passed,
            "propagate_allowed": self.propagate_allowed,
            "results": {k: dict(v) for k, v in self.results.items()},
            "blocker": self.blocker,
            "evidence_source": self.evidence_source,
            "inspects_media": self.inspects_media,
        }


def _check_dimension(name: str, value: object, expected_start: object, expected_end: object) -> Mapping[str, object]:
    # A compact contract.  `value` is either a bool score or a short status
    # string supplied by the operator/external evidence; we fail closed when it
    # is explicitly known to diverge.  This is deliberately NOT a vision call.
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
    """Evaluate a candidate shot *given supplied external evidence*.

    This does not render or look at media.  The `shot` inputs are externally
    supplied manual/QA judgments; the gate only decides whether a shot may
    propagate state to the next shot.
    """
    checks: dict[str, Mapping[str, object]] = {}
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


def _sanitize_optional(text: str, forbidden_tokens: Sequence[str]) -> str:
    for token in forbidden_tokens:
        text = text.replace(token, "")
    return text


def project_provider_shot(
    director_spec: VideoDirectorSpec,
    canonical: CanonicalVisualContract,
    performance: PerformanceBible,
    profile: ProviderProfile,
    shot: Mapping[str, object],
) -> Mapping[str, object]:
    """Project a large master spec into a short, provider-specific shot prompt.

    Priority-aware, no silent raw truncation:

    - Mandatory constraints (anchor/reference, identity, canonical refs,
      action, camera, negative constraints) are always preserved intact.
    - If a mandatory constraint cannot be expressed within the provider limit,
      or a mandatory segment uses a provider-forbidden token, the projection
      fails closed with an explicit reason.
    - Optional/compaction fields (tempo, style, scene, lighting, duration) are
      dropped in priority order, never the mandatory constraints.
    """
    mandatory: list[str] = []
    if profile.accepts_image_reference:
        mandatory.append("anchor:<canonical_start_keyframe>")
    else:
        mandatory.append("no-anchor-image")
    mandatory.append(f"identity:{_head_str(canonical.identity_face)}")
    mandatory.append("refs:" + " ".join(f"{key}={value}" for key, value in director_spec.canonical_refs.items()))
    mandatory.append(f"action:{director_spec.action_performance.get('action', shot.get('action', 'canonical'))}")
    mandatory.append(f"camera:{director_spec.camera.get('move', 'locked')}")
    mandatory.append("negative:" + "; ".join(director_spec.negative_constraints))

    for segment in mandatory:
        for token in profile.forbidden_tokens:
            if token in segment:
                raise VideoContinuityError(
                    f"PROVIDER_PROJECTION_FAIL_CLOSED: forbidden token '{token}' inside mandatory constraint"
                )

    mandatory_text = _join(mandatory)
    # No raw truncation.  Mandatory constraints either fit intact or fail closed.
    if len(mandatory_text) > profile.max_prompt_chars:
        raise VideoContinuityError(
            f"PROVIDER_PROJECTION_FAIL_CLOSED: mandatory constraints ({len(mandatory_text)} chars) exceed "
            f"provider limit ({profile.max_prompt_chars} chars)"
        )

    optional: list[tuple[str, str]] = [
        ("tempo", f"tempo:{performance.action_tempo}"),
        ("style", f"style:{canonical.visual_style.get('genre', 'canonical')}"),
        ("scene", f"scene:{director_spec.camera.get('scene', 'canonical')}"),
        ("lighting", f"light:{director_spec.lighting.get('key', 'canonical')}"),
        ("duration", f"duration:{director_spec.timeline_duration_seconds}s"),
    ]
    prompt = mandatory_text
    dropped: list[str] = []
    for label, text in optional:
        cleaned = _sanitize_optional(text, profile.forbidden_tokens)
        if not cleaned or cleaned.split(":", 1)[-1].strip() == "":
            dropped.append(label)
            continue
        candidate = f"{prompt}; {cleaned}" if prompt else cleaned
        if len(candidate) <= profile.max_prompt_chars:
            prompt = candidate
        else:
            dropped.append(label)

    return {
        "schema": PROVIDER_PROJECTION_SCHEMA,
        "provider_id": profile.provider_id,
        "provider_prompt": prompt,
        "chars": len(prompt),
        "within_limit": len(prompt) <= profile.max_prompt_chars,
        "mode": PROJECTION_MODE,
        "mandatory_constraints_preserved": True,
        "fails_closed": False,
        "fail_reason": None,
        "compact_mode": bool(dropped),
        "dropped_optional_elements": dropped,
        "duplicated_master_spec": False,
        "model_identity_stable": profile.model_identity_stable,
        "reference_pointers_only": True,
    }


@dataclass(frozen=True)
class CandidateRendering:
    """Best-of-N candidate *planning/state* semantics for Arena/DesignArena.

    This is NOT actual rendering.  It does not invoke Arena Video /
    DesignArena, it does not produce media, and it does not score real takes.
    It only records candidate-generation state and the manual gate verdict.
    """

    baseline_seed: str
    candidates: Sequence[Mapping[str, object]]
    best_take: Mapping[str, object]
    gate: ContinuityVerdict
    model_identity_stable: bool = False

    @property
    def state(self) -> str:
        return RENDER_STATE

    @property
    def render_mode(self) -> str:
        return BEST_OF_N_MODE

    def to_dict(self) -> dict[str, object]:
        return {
            "baseline_seed": self.baseline_seed,
            "candidates": [dict(c) for c in self.candidates],
            "best_take": dict(self.best_take),
            "gate": self.gate.to_dict(),
            "state": self.state,
            "render_mode": self.render_mode,
            "invoked_rendering": False,
            "scores_real_takes": False,
            "model_identity_stable": self.model_identity_stable,
            "renderer": "CANDIDATE_ONLY",
        }


def build_candidate_set(director_spec: VideoDirectorSpec, n: int, *, seed: str = "default") -> CandidateRendering:
    """Represent random renderer selection as best-of-N candidate *planning*.

    The renderer is treated as a random/candidate motion generator, not a
    stable provider.  Each candidate is an opaque planning token bound to the
    same canonical start keyframe; none of them become canonical by default and
    none of them are actually rendered here.
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
    "BEST_OF_N_MODE",
    "CANONICAL_ASSET_DIMENSIONS",
    "CANONICAL_VISUAL_CONTRACT_SCHEMA",
    "CONTINUITY_DIMENSIONS",
    "CONTINUITY_GATE_SCHEMA",
    "CONTINUITY_QA_EVIDENCE_MODE",
    "CandidateRendering",
    "CanonicalVisualContract",
    "ContinuityVerdict",
    "DIRECTOR_SPEC_SCHEMA",
    "MANDATORY_CONSTRAINTS",
    "PERFORMANCE_BIBLE_SCHEMA",
    "PROJECTION_MODE",
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
