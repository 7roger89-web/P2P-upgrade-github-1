"""Minimal personal-AI behavior harness primitives.

This module intentionally owns only four small, deterministic concerns:

1. structured voice/profile state;
2. response-policy selection before generation;
3. post-generation anti-slop linting without rewriting factual content; and
4. memory-candidate classification without performing persistence.

It does not own persona simulation, factual retrieval, durable memory storage,
LLM calls, scheduling, TTS, relationship simulation, or autonomous mutation.
Those remain separate concerns so style cannot silently alter authoritative
facts or promote uncertain observations into durable memory.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal, Mapping, Sequence


ResponseDepth = Literal["short", "normal", "deep"]
MemoryDisposition = Literal[
    "CANDIDATE",
    "HOLD_UNCERTAIN",
    "REVIEW_ELIGIBLE",
    "PROMOTE_ELIGIBLE",
]


@dataclass(frozen=True)
class VoiceProfile:
    """Stable communication preferences, independent from factual content."""

    language: str = "vi"
    familiarity: Literal["low", "medium", "high"] = "high"
    directness: float = 0.9
    humor: float = 0.45
    sarcasm: float = 0.65
    corporate_tolerance: float = 0.05
    mild_profanity: bool = True
    fresh_vietnamese_association: bool = True
    no_generic_offer_at_end: bool = True
    no_sycophantic_opener: bool = True


@dataclass(frozen=True)
class ResponseSignals:
    """Task-state signals resolved before answer wording is generated."""

    explicit_serious: bool = False
    blocking_ambiguity: bool = False
    requires_fresh_information: bool = False
    requires_tool: bool = False
    user_requested_short: bool = False
    user_requested_deep: bool = False


@dataclass(frozen=True)
class ResponsePolicy:
    """Small controller result consumed by the renderer/generator."""

    pre_actions: tuple[str, ...]
    depth: ResponseDepth
    seriousness: float
    humor_allowed: bool
    style_directives: tuple[str, ...]


@dataclass(frozen=True)
class StyleFinding:
    code: str
    excerpt: str


@dataclass(frozen=True)
class MemoryCandidate:
    """Candidate only. This object never writes durable memory itself."""

    kind: str
    text: str
    evidence_count: int = 1
    explicit_owner_instruction: bool = False
    confirmed: bool = False
    uncertain: bool = False


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def select_response_policy(
    profile: VoiceProfile,
    signals: ResponseSignals,
) -> ResponsePolicy:
    """Resolve action/depth/style before prose generation.

    Blocking ambiguity is the only condition that inserts a question-first
    action. Otherwise the controller records required evidence/tool work and
    lets the answering layer continue without a ceremonial clarification loop.
    """

    if signals.blocking_ambiguity:
        pre_actions = ("ASK_ONLY_IF_BLOCKING",)
    else:
        actions: list[str] = []
        if signals.requires_fresh_information:
            actions.append("RESEARCH_FIRST")
        if signals.requires_tool:
            actions.append("USE_REQUIRED_TOOL")
        if not actions:
            actions.append("ANSWER_DIRECTLY")
        pre_actions = tuple(actions)

    if signals.user_requested_short and not signals.user_requested_deep:
        depth: ResponseDepth = "short"
    elif signals.user_requested_deep:
        depth = "deep"
    else:
        depth = "normal"

    seriousness = 1.0 if signals.explicit_serious else 0.25
    humor_allowed = not signals.explicit_serious and _clamp01(profile.humor) > 0.0

    directives = [
        f"Respond in {profile.language}.",
        f"Directness={_clamp01(profile.directness):.2f}.",
        f"Familiarity={profile.familiarity}.",
    ]
    if signals.explicit_serious:
        directives.append("Serious-mode override: no jokes, sarcasm, or decorative banter.")
    else:
        directives.append(f"Humor={_clamp01(profile.humor):.2f}; sarcasm={_clamp01(profile.sarcasm):.2f}.")
        if profile.fresh_vietnamese_association:
            directives.append("Use a fresh Vietnamese association only when it clarifies the point; do not echo the user's metaphor.")
    if profile.mild_profanity and not signals.explicit_serious:
        directives.append("Mild profanity is allowed when natural; never target the user.")
    if profile.no_sycophantic_opener:
        directives.append("Do not open with generic praise, agreement-seeking, or customer-service filler.")
    if profile.no_generic_offer_at_end:
        directives.append("Do not end with a generic offer to do more work when the requested outcome is already complete.")

    return ResponsePolicy(
        pre_actions=pre_actions,
        depth=depth,
        seriousness=seriousness,
        humor_allowed=humor_allowed,
        style_directives=tuple(directives),
    )


_SLOP_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "SYCOPHANTIC_OPENER",
        re.compile(r"^\s*(câu hỏi (?:rất )?hay|ý tưởng (?:rất )?hay)\b", re.IGNORECASE),
    ),
    (
        "GENERIC_UNDERSTANDING_CLAIM",
        re.compile(r"\b(tôi|mình|tao) hoàn toàn hiểu\b", re.IGNORECASE),
    ),
    (
        "GENERIC_FOLLOWUP_OFFER",
        re.compile(
            r"\bnếu (?:bạn|anh|mày) muốn[^.!?\n]{0,80}\b(?:tôi|mình|tao) có thể\b[^.!?\n]{0,120}(?:[.!?…]+)?\s*$",
            re.IGNORECASE,
        ),
    ),
    (
        "CUSTOMER_SERVICE_FILLER",
        re.compile(r"\b(rất vui được hỗ trợ|xin vui lòng cho biết)\b", re.IGNORECASE),
    ),
)


def lint_response(text: str, profile: VoiceProfile) -> tuple[StyleFinding, ...]:
    """Return strong anti-slop findings; never rewrite the answer.

    Deliberately conservative: semantic qualities such as whether a joke is
    useful or an analogy is genuinely fresh are not guessed by regex. Position-
    specific rules stay position-specific: opener findings are anchored to the
    start and generic follow-up offers are anchored to the response tail.
    """

    findings: list[StyleFinding] = []
    for code, pattern in _SLOP_PATTERNS:
        if code == "SYCOPHANTIC_OPENER" and not profile.no_sycophantic_opener:
            continue
        if code == "GENERIC_FOLLOWUP_OFFER" and not profile.no_generic_offer_at_end:
            continue
        match = pattern.search(text)
        if match:
            findings.append(StyleFinding(code=code, excerpt=match.group(0)))
    return tuple(findings)


def classify_memory_candidate(candidate: MemoryCandidate) -> MemoryDisposition:
    """Classify a reflection result without persisting it.

    Explicit owner instructions may be promoted by the surrounding authorized
    memory system. Uncertain material is held separately. Repeated confirmed
    observations are only review-eligible, never auto-promoted here.
    """

    if candidate.explicit_owner_instruction:
        return "PROMOTE_ELIGIBLE"
    if candidate.uncertain:
        return "HOLD_UNCERTAIN"
    if candidate.confirmed and candidate.evidence_count >= 2:
        return "REVIEW_ELIGIBLE"
    return "CANDIDATE"


def build_render_packet(
    *,
    core_answer: str,
    locked_facts: Mapping[str, object],
    profile: VoiceProfile,
    policy: ResponsePolicy,
) -> dict[str, object]:
    """Keep factual payload and style instructions in separate fields.

    Renderers may change wording around ``core_answer`` but must treat
    ``locked_facts`` as immutable authoritative values. This function performs
    no transformation of those values.
    """

    return {
        "core_answer": core_answer,
        "locked_facts": dict(locked_facts),
        "style": {
            "language": profile.language,
            "directives": list(policy.style_directives),
            "depth": policy.depth,
            "seriousness": policy.seriousness,
            "humor_allowed": policy.humor_allowed,
        },
        "pre_actions": list(policy.pre_actions),
    }


def locked_facts_unchanged(
    before: Mapping[str, object],
    after: Mapping[str, object],
    keys: Sequence[str] | None = None,
) -> bool:
    """Small fact-lock check for a renderer boundary."""

    check_keys = tuple(keys) if keys is not None else tuple(before.keys())
    return all(key in after and before[key] == after[key] for key in check_keys)
