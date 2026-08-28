"""Small, deterministic Beginner Mode intake for the existing P2P workflow.

The gateway is an intake and projection boundary.  It derives a bounded
product-language charter from owner text, but it does not execute work, select
a host/provider, grant permissions, or replace the canonical request router.
Persistence and recovery are deliberately left to the existing workflow,
Goal Contract, Task State, Execution Ledger, and Control Tower surfaces.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

from .orchestration_policy import derive_requirement


BEGINNER_GATEWAY_SCHEMA = "p2p-beginner-gateway/1"
BEGINNER_MODE = "BEGINNER"
STATUS_IN_PROGRESS = "ĐANG LÀM"
STATUS_DONE = "ĐÃ XONG"
STATUS_NEEDS_DECISION = "CẦN BẠN QUYẾT ĐỊNH"

_MAX_REQUEST_LENGTH = 12000
_PUBLIC_FIELDS = (
    "mode",
    "status",
    "request",
    "intended_outcome",
    "project_type",
    "project_state",
    "acceptance_criteria",
    "important_constraints",
    "execution_workstreams",
    "safe_next_action",
    "question",
    "question_options",
)

_NEW_PATTERNS = (
    r"\b(?:new\s+project|from\s+scratch|start\s+(?:a|an|new)|build|create|make|develop)\b",
    r"\b(?:muốn|cần)\s+(?:làm|tạo|xây|dựng|phát triển)\b",
    r"\b(?:làm|tạo|xây|dựng|phát triển)\s+(?:một|1|mới)\b",
    r"\b(?:dự\s+án\s+mới|bắt\s+đầu\s+từ\s+đầu)\b",
)
_EXISTING_PATTERNS = (
    r"\b(?:current|existing|this\s+(?:project|app|application)|in\s+this|my\s+(?:current|existing)|improve|fix|update|enhance|refactor|maintain)\b",
    r"\b(?:hiện\s+tại|đang\s+có|dự\s+án\s+này|ứng\s+dụng\s+hiện\s+có|cải\s+thiện|sửa|cập\s+nhật|nâng\s+cấp|bảo\s+trì)\b",
    r"\b(?:thêm|bổ\s+sung)\s+(?:tính\s+năng|chức\s+năng)\b",
)
_PROTECTED_PATTERNS = (
    r"\b(?:deploy|release|publish|promote|force[- ]push|go\s+live|production)\b",
    r"\b(?:triển\s+khai|phát\s+hành|công\s+khai|đưa\s+lên\s+môi\s+trường\s+thật)\b",
    r"\b(?:xóa|xoá)\s+(?:toàn\s+bộ|hết|dữ\s+liệu|dự\s+án)\b",
)
_PROJECT_TYPES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "genealogy_application",
        "Ứng dụng gia phả",
        ("gia phả", "cây gia đình", "genealogy", "family tree", "family history"),
    ),
    (
        "story_game",
        "Trò chơi kể chuyện",
        ("truyện", "game", "story", "visual novel"),
    ),
    (
        "logistics_software",
        "Phần mềm vận hành hàng hóa",
        ("logistics", "warehouse", "inventory", "delivery", "kho", "vận tải"),
    ),
    (
        "data_product",
        "Sản phẩm dữ liệu",
        ("data", "dataset", "csv", "dữ liệu", "phân tích"),
    ),
    (
        "web_application",
        "Ứng dụng web",
        ("app", "application", "website", "web app", "ứng dụng", "trang web"),
    ),
)


class BeginnerGatewayError(ValueError):
    """Raised when an intake cannot be represented safely."""


def _normalise_request(value: Any) -> str:
    if not isinstance(value, str):
        raise BeginnerGatewayError("BEGINNER_REQUEST_MUST_BE_TEXT")
    request = re.sub(r"\s+", " ", value).strip()
    if len(request) > _MAX_REQUEST_LENGTH:
        raise BeginnerGatewayError("BEGINNER_REQUEST_TOO_LONG")
    return request


def _matches(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def _inspection_value(inspection: Mapping[str, Any] | None, key: str, default: Any = None) -> Any:
    if not isinstance(inspection, Mapping):
        return default
    return inspection.get(key, default)


def _language_is_vietnamese(text: str) -> bool:
    return bool(
        re.search(r"[ăâđêôơưĂÂĐÊÔƠƯ]", text)
        or re.search(r"\b(?:tôi|mình|muốn|làm|tạo|xây|dựng|cho|người|hiện|cải thiện)\b", text, re.IGNORECASE)
    )


def _strip_leading_request_words(value: str) -> str:
    result = value.strip(" .!?\n\t")
    prefixes = (
        r"^(?:tôi|mình|em|chúng tôi)\s+(?:muốn|cần|đang\s+muốn)\s+",
        r"^(?:i|we)\s+(?:want|need|would\s+like)\s+to\s+",
        r"^(?:please|help\s+me|giúp\s+(?:tôi|mình)|hãy)\s+",
    )
    changed = True
    while changed:
        changed = False
        for prefix in prefixes:
            stripped = re.sub(prefix, "", result, count=1, flags=re.IGNORECASE).strip()
            if stripped != result:
                result = stripped
                changed = True
                break
    return result.strip(" .!?\n\t")


def _subject_from_request(request: str) -> str:
    subject = _strip_leading_request_words(request)
    subject = re.sub(
        r"^(?:build|create|make|develop|start|improve|fix|update|enhance|refactor|làm|tạo|xây|dựng|phát triển|cải thiện|sửa|cập nhật|nâng cấp)\s+",
        "",
        subject,
        count=1,
        flags=re.IGNORECASE,
    ).strip(" .!?\n\t")
    vague_subject = subject.casefold().strip(" .!?\n\t")
    if not subject or vague_subject in {
        "something",
        "anything",
        "a thing",
        "somehow",
        "whatever",
        "it",
        "một thứ gì đó",
        "cái gì đó",
        "gì đó",
        "làm gì đó",
    }:
        return ""
    return subject


def _project_type(request: str, inspection: Mapping[str, Any] | None) -> tuple[str, str]:
    lower = request.casefold()
    for key, label, terms in _PROJECT_TYPES:
        if any(term.casefold() in lower for term in terms):
            return key, label
    inspected = str(_inspection_value(inspection, "project_type", "")).strip().lower()
    inspected_labels = {
        "genealogy_application": "Ứng dụng gia phả",
        "story_game": "Trò chơi kể chuyện",
        "logistics_software": "Phần mềm vận hành hàng hóa",
        "data_analysis": "Sản phẩm dữ liệu",
        "web_application": "Ứng dụng web",
        "automation": "Công cụ tự động hóa",
        "research": "Nghiên cứu",
    }
    if inspected in inspected_labels:
        return inspected, inspected_labels[inspected]
    return "general_product", "Sản phẩm số"


def _project_state(request: str, inspection: Mapping[str, Any] | None) -> tuple[str, str]:
    is_new = _matches(request, _NEW_PATTERNS)
    is_existing = _matches(request, _EXISTING_PATTERNS)
    if is_new and is_existing:
        return "NEEDS_DECISION", "CONFLICTING_NEW_AND_EXISTING_SIGNALS"
    if is_existing:
        return "EXISTING_PROJECT", "EXPLICIT_EXISTING_SIGNAL"
    if is_new:
        return "NEW_PROJECT", "EXPLICIT_NEW_SIGNAL"
    if _matches(request, (r"\b(?:app|application|website|product|tool)\b", r"\b(?:ứng\s+dụng|sản\s+phẩm|công\s+cụ)\b")):
        return "NEW_PROJECT", "PRODUCT_IDEA_WITHOUT_EXISTING_SIGNAL"
    if _inspection_value(inspection, "p2p_installed", False) or _inspection_value(inspection, "has_project_profile", False):
        return "EXISTING_PROJECT", "PROJECT_CONTEXT_EVIDENCE"
    return "NEEDS_DECISION", "PROJECT_STATE_NOT_MATERIALIZED"


def _intended_outcome(request: str, state: str) -> str:
    subject = _subject_from_request(request)
    vietnamese = _language_is_vietnamese(request)
    if not subject:
        return "Xác định sản phẩm và kết quả đầu tiên cần đạt." if vietnamese else "Define the product and its first useful outcome."
    if state == "EXISTING_PROJECT":
        prefix = "Cải thiện" if vietnamese else "Improve"
    else:
        prefix = "Xây dựng" if vietnamese else "Build"
    return f"{prefix} {subject}."


def _audience_and_constraints(request: str, state: str) -> tuple[list[str], list[str]]:
    lower = request.casefold()
    audiences: list[str] = []
    constraints = ["Bắt đầu từ phạm vi nhỏ nhất có thể kiểm tra."]
    if any(term in lower for term in ("người lớn tuổi", "người cao tuổi", "older adults", "elderly", "seniors")):
        audiences.append("người lớn tuổi")
        constraints.append("Chữ rõ, thao tác ít bước, và không cần thuật ngữ kỹ thuật.")
    if any(term in lower for term in ("private", "privacy", "sensitive", "riêng tư", "bảo mật", "nhạy cảm")):
        constraints.append("Dữ liệu riêng tư chỉ được xử lý trong phạm vi đã đồng ý.")
    if state == "EXISTING_PROJECT":
        constraints.append("Giữ nguyên phần đang hoạt động; chỉ thay đổi phần đã xác định.")
    return audiences, list(dict.fromkeys(constraints))


def _acceptance_criteria(project_type: str, state: str, audiences: list[str]) -> list[str]:
    if state == "EXISTING_PROJECT":
        criteria = [
            "Phần cần cải thiện có thay đổi quan sát được theo mục tiêu đã nêu.",
            "Luồng chính đang có vẫn hoạt động sau thay đổi.",
            "Kết quả được kiểm tra theo tiêu chí đã chốt trước khi mở rộng.",
        ]
    else:
        criteria = [
            "Có một phiên bản đầu tiên thực hiện được mục tiêu chính.",
            "Người dùng mục tiêu hoàn tất được luồng chính.",
            "Phạm vi và điều chưa làm được được ghi rõ trước khi mở rộng.",
        ]
    if project_type == "genealogy_application" and "người lớn tuổi" in audiences:
        criteria[1] = "Người lớn tuổi có thể xem cây gia đình và tìm được mối quan hệ cần thiết bằng thao tác rõ ràng."
    return criteria


def _workstreams(state: str, question: str | None) -> list[str]:
    if question:
        return [
            "Làm rõ một quyết định sản phẩm còn thiếu.",
            "Chốt phạm vi phiên bản đầu tiên.",
            "Kiểm tra lại mục tiêu trước khi bắt đầu thực hiện.",
        ]
    if state == "EXISTING_PROJECT":
        return [
            "Xác định phần cần cải thiện.",
            "Thực hiện thay đổi trong phạm vi nhỏ.",
            "Kiểm tra phần mới và phần đang có.",
        ]
    return [
        "Xác định phiên bản đầu tiên.",
        "Xây dựng luồng chính cho người dùng mục tiêu.",
        "Kiểm tra kết quả theo tiêu chí đã nêu.",
    ]


def _question_for(request: str, subject: str, state: str, protected: bool) -> tuple[str | None, list[str], str | None]:
    vietnamese = _language_is_vietnamese(request)
    if protected:
        if vietnamese:
            return (
                "Bạn muốn P2P chỉ chuẩn bị và kiểm tra an toàn, chưa đưa sản phẩm ra ngoài, đúng không?",
                ["Chỉ chuẩn bị an toàn", "Dừng yêu cầu này"],
                "PROTECTED_ACTION_REQUIRES_OWNER_DECISION",
            )
        return (
            "Should P2P only prepare and verify safely without putting the product live?",
            ["Prepare safely only", "Stop this request"],
            "PROTECTED_ACTION_REQUIRES_OWNER_DECISION",
        )
    if not subject:
        if vietnamese:
            return "Bạn muốn làm sản phẩm gì và ai sẽ sử dụng sản phẩm đó?", [], "OUTCOME_MISSING"
        return "What product do you want to make, and who will use it?", [], "OUTCOME_MISSING"
    if state == "NEEDS_DECISION":
        if vietnamese:
            return "Bạn muốn tạo một dự án mới hay cải thiện một dự án đang có?", ["Tạo dự án mới", "Cải thiện dự án đang có"], "PROJECT_STATE_AMBIGUOUS"
        return "Do you want to create a new project or improve an existing one?", ["Create a new project", "Improve an existing project"], "PROJECT_STATE_AMBIGUOUS"
    return None, [], None


def _policy_for(question: str | None, protected: bool) -> dict[str, Any]:
    return derive_requirement(
        {
            "task_size": "SMALL",
            "dependency_complexity": "NONE",
            "mutation_risk": "HIGH" if protected else "NONE",
            "reversibility": "REVERSIBLE",
            "ambiguity": "HIGH" if question else "LOW",
            "acceptance_clarity": "PARTIAL" if question else "CLEAR",
            "evidence_availability": "COMPLETE",
            "context_breadth": "LOCAL",
            "owner_gate": "REQUIRED" if protected else "NOT_REQUIRED",
            "deterministic_verifier": True,
            "task_kind": "INTAKE",
            "source_mutation": False,
            "runtime_change": False,
            "registry_change": False,
            "governance_change": False,
            "security_risk": False,
            "promotion": False,
            "destructive": protected,
            "acceptance_requires_testing": False,
            "acceptance_proven": False,
        }
    )


def _fingerprint(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def derive_charter(request: str, inspection: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Derive one bounded Beginner charter without performing work."""

    normalized = _normalise_request(request)
    subject = _subject_from_request(normalized)
    state, state_reason = _project_state(normalized, inspection)
    project_type_key, project_type_label = _project_type(normalized, inspection)
    protected = _matches(normalized, _PROTECTED_PATTERNS)
    question, question_options, question_reason = _question_for(normalized, subject, state, protected)
    audiences, constraints = _audience_and_constraints(normalized, state)
    criteria = _acceptance_criteria(project_type_key, state, audiences)
    outcome = _intended_outcome(normalized, state)
    if protected:
        safe_action = (
            "Giữ yêu cầu ở bước chuẩn bị và kiểm tra an toàn; chưa đưa sản phẩm ra ngoài."
            if _language_is_vietnamese(normalized)
            else "Keep the request in safe preparation and verification; do not put the product live."
        )
    elif question:
        safe_action = (
            "Chờ bạn trả lời câu hỏi trên; chưa bắt đầu thay đổi nào."
            if _language_is_vietnamese(normalized)
            else "Wait for your answer above; do not start changes yet."
        )
    elif state == "EXISTING_PROJECT":
        safe_action = "Xác định một điểm cải thiện cụ thể trong dự án hiện có rồi kiểm tra trước và sau thay đổi."
    else:
        safe_action = "Chốt phiên bản đầu tiên bằng các tiêu chí trên rồi bắt đầu phần nhỏ nhất có thể kiểm tra."
    policy = _policy_for(question, protected)
    signals = {
        "state_reason": state_reason,
        "subject_present": bool(subject),
        "explicit_new_signal": _matches(normalized, _NEW_PATTERNS),
        "explicit_existing_signal": _matches(normalized, _EXISTING_PATTERNS),
        "protected_action_detected": protected,
        "question_reason": question_reason,
        "audiences": audiences,
    }
    safety = {
        "canonical_integrity": "PRESERVED",
        "permission_expansion": False,
        "destructive_operations": "FAIL_CLOSED",
        "production_protection": "FAIL_CLOSED",
        "owner_approval": "UNCHANGED",
        "automatic_execution": False,
        "provenance": ["OWNER_INPUT", "PROJECT_INSPECTION"],
    }
    internal = {
        "project_type_key": project_type_key,
        "signals": signals,
        "inspection_summary": {
            "project_type": _inspection_value(inspection, "project_type", "UNKNOWN"),
            "markers": list(_inspection_value(inspection, "markers", []) or []),
            "p2p_installed": bool(_inspection_value(inspection, "p2p_installed", False)),
            "has_project_profile": bool(_inspection_value(inspection, "has_project_profile", False)),
        },
        "execution_policy": policy,
        "safety": safety,
        "canonical_surfaces": {
            "request_router": "existing canonical router; not replaced",
            "goal_contract": "existing Goal Contract",
            "task_state": "existing TaskStateStore",
            "recovery": "existing Control Tower recommendation",
        },
    }
    fingerprint_basis = {
        "request": normalized,
        "intended_outcome": outcome,
        "project_type_key": project_type_key,
        "project_state": state,
        "acceptance_criteria": criteria,
        "important_constraints": constraints,
        "execution_workstreams": _workstreams(state, question),
        "safe_next_action": safe_action,
        "question": question,
    }
    return {
        "schema_version": BEGINNER_GATEWAY_SCHEMA,
        "mode": BEGINNER_MODE,
        "status": STATUS_NEEDS_DECISION if question else STATUS_IN_PROGRESS,
        "request": normalized,
        "intended_outcome": outcome,
        "project_type": project_type_label,
        "project_state": state,
        "acceptance_criteria": criteria,
        "important_constraints": constraints,
        "execution_workstreams": _workstreams(state, question),
        "safe_next_action": safe_action,
        "question": question,
        "question_options": question_options,
        "internal": internal,
        "charter_fingerprint": _fingerprint(fingerprint_basis),
    }


def task_spec_for_charter(charter: Mapping[str, Any], goal_id: str) -> dict[str, Any]:
    """Build one Goal-scoped task projection for the existing Task State store."""

    if not isinstance(charter, Mapping):
        raise BeginnerGatewayError("BEGINNER_CHARTER_REQUIRED")
    question = str(charter.get("question") or "").strip()
    task: dict[str, Any] = {
        "task_id": "beginner-gateway-next",
        "goal_id": str(goal_id),
        "title": "Continue the bounded project request",
        "purpose": str(charter.get("safe_next_action") or "Continue the bounded request safely."),
        "status": "WAITING_OWNER" if question else "READY",
        "scope": ["BEGINNER_INTAKE", "BOUNDED_PROJECT_CHARTER"],
        "non_scope": ["UNAUTHORIZED_PROTECTED_ACTIONS", "AUTOMATIC_HOST_START"],
        "acceptance_requirements": list(charter.get("acceptance_criteria") or []),
        "required_evidence": [".p2p/state/goal-contract.json", ".p2p/state/execution-ledger.jsonl"],
        "context_refs": [".p2p/state/goal-contract.json"],
        "requirement_refs": ["BEGINNER_GATEWAY_CHARTER"],
        "required_capabilities": [],
        "permission_needs": [],
    }
    if question:
        task["owner_decision"] = {
            "status": "PENDING",
            "question": question,
            "options": list(charter.get("question_options") or []),
            "recommendation": "Keep the task paused until this product decision is answered.",
            "consequences": {
                "answer": "P2P can refine the same bounded request.",
                "no_answer": "No project change starts.",
            },
            "approval_metadata": {"decision_scope": "PRODUCT_SCOPE_ONLY"},
        }
    return task


def beginner_projection(charter: Mapping[str, Any]) -> dict[str, Any]:
    """Return the default nontechnical projection."""

    if not isinstance(charter, Mapping):
        raise BeginnerGatewayError("BEGINNER_CHARTER_REQUIRED")
    return {field: charter.get(field) for field in _PUBLIC_FIELDS}


def advanced_projection(charter: Mapping[str, Any]) -> dict[str, Any]:
    """Return the safe projection plus explicitly requested internal detail."""

    result = beginner_projection(charter)
    result["advanced"] = {
        "schema_version": charter.get("schema_version"),
        "charter_fingerprint": charter.get("charter_fingerprint"),
        "internal": charter.get("internal", {}),
    }
    return result


def render_beginner(projection: Mapping[str, Any]) -> str:
    """Render a compact product-language response for a human beginner."""

    if not isinstance(projection, Mapping):
        raise BeginnerGatewayError("BEGINNER_PROJECTION_REQUIRED")
    state_labels = {
        "NEW_PROJECT": "Dự án mới",
        "EXISTING_PROJECT": "Dự án hiện có",
        "NEEDS_DECISION": "Cần bạn chọn",
    }
    lines = [
        f"TRẠNG THÁI\n{projection.get('status', STATUS_NEEDS_DECISION)}",
        f"\nMỤC TIÊU\n{projection.get('intended_outcome', '')}",
        f"\nLOẠI SẢN PHẨM\n{projection.get('project_type', '')}",
        f"\nPHẠM VI DỰ ÁN\n{state_labels.get(str(projection.get('project_state')), projection.get('project_state', ''))}",
        "\nTIÊU CHÍ TỐI THIỂU",
    ]
    lines.extend(f"- {item}" for item in projection.get("acceptance_criteria", []) or [])
    lines.append("\nRÀNG BUỘC QUAN TRỌNG")
    lines.extend(f"- {item}" for item in projection.get("important_constraints", []) or [])
    lines.append("\nCÁC PHẦN VIỆC")
    lines.extend(f"- {item}" for item in projection.get("execution_workstreams", []) or [])
    lines.append(f"\nBƯỚC TIẾP THEO AN TOÀN\n{projection.get('safe_next_action', '')}")
    question = projection.get("question")
    if question:
        lines.append(f"\nCÂU HỎI CẦN BẠN TRẢ LỜI\n{question}")
        options = projection.get("question_options") or []
        if options:
            lines.extend(f"- {item}" for item in options)
    if projection.get("resume_note"):
        lines.append(f"\nTIẾP TỤC SAU GIÁN ĐOẠN\n{projection.get('resume_note')}")
    return "\n".join(lines) + "\n"


__all__ = [
    "BEGINNER_GATEWAY_SCHEMA",
    "BEGINNER_MODE",
    "STATUS_DONE",
    "STATUS_IN_PROGRESS",
    "STATUS_NEEDS_DECISION",
    "BeginnerGatewayError",
    "advanced_projection",
    "beginner_projection",
    "derive_charter",
    "render_beginner",
    "task_spec_for_charter",
]

