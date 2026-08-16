"""Beginner-first discovery behavior; technical choices stay internal."""

from __future__ import annotations


OWNER_PRODUCT_QUESTIONS = (
    "Mục tiêu chính của phần mềm là gì?",
    "Ai sẽ sử dụng phần mềm và họ cần làm việc gì thường xuyên nhất?",
    "Bạn muốn bắt đầu bằng quy trình nào và thế nào là kết quả tốt?",
)
TECHNICAL_QUESTION_MARKERS = ("framework", "npm", "pip", "python", "node", "mcp", "agent", "skill", "docker", "package")


def discover_beginner_request(request: str) -> dict[str, object]:
    text = str(request or "").strip()
    beginner = any(marker in text.lower() for marker in ("không biết code", "khong biet code", "not a developer", "don't know how to code"))
    if not beginner:
        return {"schema": "p2p-beginner-discovery/1", "mode": "NORMAL", "questions": [], "technical_questions": [], "technical_choices_internal": True}
    return {
        "schema": "p2p-beginner-discovery/1",
        "mode": "DISCOVERY",
        "questions": list(OWNER_PRODUCT_QUESTIONS),
        "technical_questions": [],
        "technical_choices_internal": True,
        "capability_names_required": False,
        "explanation_style": "plain-language",
    }
