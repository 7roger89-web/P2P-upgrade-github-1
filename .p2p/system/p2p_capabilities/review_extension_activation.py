"""Task-scoped activation decision for the optional OpenCodeReview scaffold.

This is deliberately not a router. It recognizes only explicit review-coverage
failure signals already present in the current task text. A generic request to
"review code" is insufficient. The returned guidance never grants authority,
permission, acceptance, or promotion.
"""
from __future__ import annotations

import re
from typing import Any


SCHEMA = "p2p-review-extension-activation/1"
ACTIVATION = "OPTIONAL_EXTENSION_AFTER_DOCUMENTED_REVIEW_GAP"
CLASSIFICATION = "NON_AUTHORITATIVE_REVIEW_SCAFFOLD"

_REVIEW_GAP_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("LARGE_COMPLEX_DIFF", re.compile(r"\b(?:large|complex|huge|very large)\s+(?:code\s+)?diff\b", re.I)),
    ("MISSED_FILE", re.compile(r"\b(?:missed|omitted|skipped|forgot(?:ten)?)\s+(?:changed\s+)?files?\b", re.I)),
    ("COVERAGE_GAP", re.compile(r"\b(?:review\s+)?coverage\s+(?:gap|uncertainty|incomplete|unknown)\b", re.I)),
    ("REPEATED_REPAIR", re.compile(r"\b(?:repeated|second|third|another)\s+(?:review\s+)?repair(?:\s+round)?\b|\brepair\s+round\s*[2-9]\b", re.I)),
    ("ALL_CHANGED_FILES", re.compile(r"\breview\s+all\s+changed\s+files\b", re.I)),
    ("LINE_TARGETING_GAP", re.compile(r"\b(?:line|comment)\s+(?:anchoring|targeting)\s+(?:gap|uncertainty|wrong|incorrect)\b", re.I)),
    ("RULE_TARGETING_GAP", re.compile(r"\brule\s+(?:matching|targeting|resolution)\s+(?:gap|uncertainty|wrong|incorrect)\b", re.I)),
)


def review_gap_decision(task_text: str) -> dict[str, Any]:
    task = " ".join(str(task_text or "").split())
    matched: list[str] = []
    for code, pattern in _REVIEW_GAP_PATTERNS:
        if pattern.search(task):
            matched.append(code)
    active = bool(matched)
    return {
        "schema": SCHEMA,
        "decision": "USE_OCR_DELEGATION" if active else "NO_REVIEW_GAP",
        "activation_policy": ACTIVATION,
        "classification": CLASSIFICATION,
        "matched_signals": matched,
        "authority": "NONE",
        "permission_effect": "NONE",
        "acceptance_authority": False,
        "native_review_still_required": True,
        "shield_and_acceptance_replay_still_required": True,
    }


def render_review_guidance(task_text: str) -> str:
    decision = review_gap_decision(task_text)
    if decision["decision"] != "USE_OCR_DELEGATION":
        return ""
    signals = ",".join(decision["matched_signals"])
    return (
        "OPEN_CODE_REVIEW_DELEGATION=USE_IF_AVAILABLE; "
        f"GAP={signals}; OCR>=1.12.4 delegation only: preview JSON -> rule JSON -> "
        "host agent accounts every (path,status) as REVIEWED or SKIPPED_WITH_REASON; "
        "OCR finding is NONAUTHORITATIVE; OCR unavailable => NATIVE_REVIEW_FALLBACK, never PASS-by-absence; "
        "Shield/native-code-impact/tests/task acceptance still required."
    )
