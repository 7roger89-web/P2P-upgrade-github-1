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
AUTO_DECOMPOSITION_SCHEMA = "p2p-auto-goal-decomposition/1"
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
    "progress_summary",
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
    r"\b(?:current|existing|this\s+(?:project|app|application)|in\s+this|my\s+(?:current|existing)|improve|fix|update|enhance|refactor|maintain|continue|resume|finish|complete)\b",
    r"\b(?:hiện\s+tại|đang\s+có|dự\s+án\s+này|ứng\s+dụng\s+hiện\s+có|cải\s+thiện|sửa|cập\s+nhật|nâng\s+cấp|bảo\s+trì|tiếp\s+tục|hoàn\s+thiện)\b",
    r"\b(?:thêm|bổ\s+sung)\s+(?:tính\s+năng|chức\s+năng)\b",
)
_CONTINUATION_PATTERNS = (
    r"\b(?:continue|resume|finish|complete|keep\s+(?:working|improving)|carry\s+on)\b",
    r"\b(?:tiếp\s+tục|hoàn\s+thiện|đang\s+làm|phần\s+còn\s+lại)\b",
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


def is_continuation_request(value: str) -> bool:
    """Return whether the request explicitly asks to continue existing work."""

    return isinstance(value, str) and _matches(value, _CONTINUATION_PATTERNS)


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
    action_prefix = (
        r"^(?:build|create|make|develop|start|improve|fix|update|enhance|refactor|"
        r"continue|resume|finish|complete|keep\s+(?:working|improving)|"
        r"làm|tạo|xây|dựng|phát triển|cải thiện|sửa|cập nhật|nâng cấp|tiếp\s+tục|hoàn\s+thiện)\s+"
    )
    for _ in range(3):
        stripped = re.sub(action_prefix, "", subject, count=1, flags=re.IGNORECASE).strip(" .!?\n\t")
        if stripped == subject:
            break
        subject = stripped
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


def _workstream(
    workstream_id: str,
    title: str,
    purpose: str,
    acceptance: str,
    *,
    depends_on: tuple[str, ...] = (),
    question: str | None = None,
) -> dict[str, Any]:
    return {
        "workstream_id": workstream_id,
        "title": title,
        "purpose": purpose,
        "depends_on": list(depends_on),
        "acceptance": [acceptance],
        "status": "WAITING_OWNER" if question else "READY" if not depends_on else "PLANNED",
        "can_start_now": not bool(question) and not bool(depends_on),
        "owner_input": question,
    }


def _auto_workstreams(
    request: str,
    state: str,
    criteria: list[str],
    question: str | None,
) -> list[dict[str, Any]]:
    """Derive a small, ordered workstream list inside the BG01 boundary."""

    vietnamese = _language_is_vietnamese(request)
    if question:
        return [
            _workstream(
                "decision",
                "Chốt quyết định còn thiếu." if vietnamese else "Resolve the missing decision.",
                "Chỉ tiếp tục sau khi Owner chọn hướng sản phẩm an toàn." if vietnamese else "Continue only after the Owner chooses the safe product direction.",
                "Câu hỏi sản phẩm có câu trả lời rõ ràng trước khi bắt đầu." if vietnamese else "The product question has a clear answer before work starts.",
                question=question,
            )
        ]

    if vietnamese:
        scope_title = "Xác định phiên bản đầu tiên." if state != "EXISTING_PROJECT" else "Xác định phần đang cần cải thiện."
        scope_purpose = "Chọn phạm vi nhỏ nhất có thể kiểm tra." if state != "EXISTING_PROJECT" else "Xác định đúng phần cần cải thiện và giữ nguyên phần đang hoạt động."
        data_title = "Chuẩn bị dữ liệu cần thiết."
        data_purpose = "Xác định dữ liệu đầu vào và cách kiểm tra dữ liệu trước khi dùng."
        safety_title = "Chốt ranh giới an toàn và riêng tư."
        safety_purpose = "Giữ dữ liệu và quyền truy cập trong phạm vi đã được đồng ý."
        core_title = "Xây dựng luồng chính cho người dùng mục tiêu." if state != "EXISTING_PROJECT" else "Thực hiện thay đổi trong phạm vi nhỏ."
        core_purpose = "Làm phần tạo ra giá trị chính cho người dùng." if state != "EXISTING_PROJECT" else "Thay đổi đúng phần đã xác định mà không làm hỏng luồng đang có."
        verify_title = "Kiểm tra kết quả theo tiêu chí đã nêu."
        verify_purpose = "Kiểm tra cả mục tiêu mới và phần đang được giữ nguyên."
    else:
        scope_title = "Define the smallest first version." if state != "EXISTING_PROJECT" else "Identify the part to improve."
        scope_purpose = "Choose the smallest scope that can be checked." if state != "EXISTING_PROJECT" else "Identify the exact improvement while preserving working parts."
        data_title = "Prepare the required data."
        data_purpose = "Define input data and how it will be checked before use."
        safety_title = "Set the safety and privacy boundary."
        safety_purpose = "Keep data and access within the agreed boundary."
        core_title = "Build the main user flow." if state != "EXISTING_PROJECT" else "Make the change within a small scope."
        core_purpose = "Implement the part that creates the main user value." if state != "EXISTING_PROJECT" else "Change the identified part without breaking the current flow."
        verify_title = "Check the result against the stated criteria."
        verify_purpose = "Check both the new objective and the parts that must remain working."

    lower = request.casefold()
    data_needed = any(
        term in lower
        for term in ("import", "upload", "csv", "dataset", "inventory", "data", "dữ liệu", "nhập", "đồng bộ", "sync")
    )
    safety_needed = any(
        term in lower
        for term in ("private", "privacy", "sensitive", "secure", "security", "share", "permission", "auth", "riêng tư", "nhạy cảm", "bảo mật", "chia sẻ", "quyền truy cập")
    )
    workstreams = [_workstream("scope", scope_title, scope_purpose, criteria[0])]
    if data_needed:
        workstreams.append(
            _workstream(
                "data",
                data_title,
                data_purpose,
                criteria[0],
                depends_on=("scope",),
            )
        )
    if safety_needed:
        workstreams.append(
            _workstream(
                "safety",
                safety_title,
                safety_purpose,
                criteria[-1],
                depends_on=("scope",),
            )
        )
    core_dependencies = tuple(item["workstream_id"] for item in workstreams[1:])
    workstreams.append(
        _workstream(
            "core",
            core_title,
            core_purpose,
            criteria[min(1, len(criteria) - 1)],
            depends_on=core_dependencies or ("scope",),
        )
    )
    workstreams.append(
        _workstream(
            "verify",
            verify_title,
            verify_purpose,
            criteria[-1],
            depends_on=("core",),
        )
    )
    return workstreams[:5]


def _progress_summary(
    continuity: Mapping[str, Any] | None,
    *,
    question: str | None,
    safe_next_action: str,
) -> dict[str, Any]:
    if not isinstance(continuity, Mapping) or not continuity.get("tasks"):
        return {
            "status": "Cần bạn chọn" if question else "Có thể bắt đầu",
            "completed": [],
            "active": [],
            "blocked": [],
            "waiting_for_you": ["Quyết định sản phẩm còn thiếu."] if question else [],
            "next": safe_next_action,
        }
    tasks = [item for item in continuity.get("tasks", []) if isinstance(item, Mapping)]
    def titles(status: str) -> list[str]:
        return [str(item.get("title")) for item in tasks if item.get("status") == status and str(item.get("title") or "").strip()]
    completed = titles("DONE")
    active = titles("ACTIVE")
    blocked = titles("BLOCKED")
    waiting = titles("WAITING_OWNER")
    if question:
        status = "Cần bạn chọn"
    elif active:
        status = "Đang làm"
    elif blocked:
        status = "Đang bị chặn"
    elif waiting:
        status = "Cần bạn trả lời"
    elif continuity.get("next_task_title"):
        status = "Có thể bắt đầu"
    else:
        status = "Đã hoàn tất"
    return {
        "status": status,
        "completed": completed,
        "active": active,
        "blocked": blocked,
        "waiting_for_you": waiting,
        "next": safe_next_action if question else str(continuity.get("safe_next_action") or safe_next_action),
    }


def _derive_auto_decomposition(
    request: str,
    state: str,
    project_type_key: str,
    outcome: str,
    criteria: list[str],
    constraints: list[str],
    question: str | None,
    question_reason: str | None,
    safe_next_action: str,
    continuity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    workstreams = _auto_workstreams(request, state, criteria, question)
    workstream_ids = [str(item["workstream_id"]) for item in workstreams]
    edges = [
        {"from": dependency, "to": str(item["workstream_id"])}
        for item in workstreams
        for dependency in item.get("depends_on", [])
    ]
    owner_decisions = []
    if question:
        owner_decisions.append(
            {
                "status": "PENDING",
                "question": question,
                "reason": question_reason or "MATERIAL_PRODUCT_DECISION_REQUIRED",
            }
        )
    continuity_value = dict(continuity) if isinstance(continuity, Mapping) else {
        "status": "NOT_INITIALIZED",
        "tasks": [],
        "completed": [],
        "active": [],
        "blocked": [],
        "waiting_owner": [],
        "now_startable": [],
        "next_task_id": None,
        "next_task_title": None,
    }
    return {
        "schema_version": AUTO_DECOMPOSITION_SCHEMA,
        "goal_derivation": {
            "outcome": outcome,
            "project_state": state,
            "project_type_key": project_type_key,
            "source": "OWNER_INPUT_AND_PROJECT_INSPECTION",
        },
        "acceptance_derivation": [
            {
                "criterion_id": f"C{index}",
                "criterion": criterion,
                "reason": "minimum sufficient outcome check",
            }
            for index, criterion in enumerate(criteria, 1)
        ],
        "material_constraints": list(constraints),
        "workstreams": workstreams,
        "dependency_model": {
            "topological_order": workstream_ids,
            "edges": edges,
            "real_dependencies_only": True,
            "cycle_detected": False,
        },
        "now_startable": [
            str(item["workstream_id"])
            for item in workstreams
            if bool(item.get("can_start_now"))
        ],
        "owner_decisions": owner_decisions,
        "question_policy": {
            "ask_only_material": True,
            "material_triggers": [
                "PRODUCT_INTENT",
                "DESTRUCTIVE_OR_IRREVERSIBLE_ACTION",
                "PRODUCTION_OR_SECURITY_BOUNDARY",
                "MUTUALLY_EXCLUSIVE_DIRECTION",
                "OWNER_GATE",
            ],
            "technical_ambiguity_asks_beginner": False,
            "decision": question,
            "reason": question_reason,
        },
        "existing_project_continuity": continuity_value,
        "safe_next_action": safe_next_action,
        "workstream_count": len(workstreams),
        "max_workstreams": 5,
    }


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


def derive_charter(
    request: str,
    inspection: Mapping[str, Any] | None = None,
    continuity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
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
    auto_decomposition = _derive_auto_decomposition(
        normalized,
        state,
        project_type_key,
        outcome,
        criteria,
        constraints,
        question,
        question_reason,
        safe_action,
        continuity,
    )
    progress = _progress_summary(continuity, question=question, safe_next_action=safe_action)
    execution_workstreams = [str(item.get("title")) for item in auto_decomposition["workstreams"]]
    signals = {
        "state_reason": state_reason,
        "subject_present": bool(subject),
        "explicit_new_signal": _matches(normalized, _NEW_PATTERNS),
        "explicit_existing_signal": _matches(normalized, _EXISTING_PATTERNS),
        "protected_action_detected": protected,
        "question_reason": question_reason,
        "audiences": audiences,
        "continuation_request": is_continuation_request(normalized),
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
        "execution_workstreams": execution_workstreams,
        "progress_summary": progress,
        "auto_decomposition": auto_decomposition,
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
        "execution_workstreams": execution_workstreams,
        "progress_summary": progress,
        "safe_next_action": safe_action,
        "question": question,
        "question_options": question_options,
        "auto_decomposition": auto_decomposition,
        "internal": internal,
        "charter_fingerprint": _fingerprint(fingerprint_basis),
    }


def bind_continuity(charter: Mapping[str, Any], continuity: Mapping[str, Any] | None) -> dict[str, Any]:
    """Project existing Task State onto a fresh charter without replacing it."""

    if not isinstance(charter, Mapping):
        raise BeginnerGatewayError("BEGINNER_CHARTER_REQUIRED")
    if not isinstance(continuity, Mapping) or not continuity.get("tasks"):
        return dict(charter)
    updated = dict(charter)
    auto = dict(updated.get("auto_decomposition") or {})
    has_question = bool(str(updated.get("question") or "").strip())
    bound_workstreams: list[dict[str, Any]] = []
    for item in continuity.get("tasks", []):
        if not isinstance(item, Mapping):
            continue
        task_id = str(item.get("task_id") or "").strip()
        title = str(item.get("title") or "").strip()
        if not task_id or not title:
            continue
        bound_workstreams.append(
            {
                "workstream_id": str(item.get("workstream_id") or task_id),
                "task_id": task_id,
                "title": title,
                "purpose": str(item.get("purpose") or title),
                "depends_on": list(item.get("dependencies") or []),
                "acceptance": list(item.get("acceptance") or updated.get("acceptance_criteria") or []),
                "status": str(item.get("status") or "UNKNOWN"),
                "can_start_now": bool(item.get("can_start_now")) and not has_question,
                "owner_input": item.get("owner_input"),
            }
        )
    if not bound_workstreams:
        return dict(charter)
    task_to_workstream = {
        str(item.get("task_id")): str(item.get("workstream_id"))
        for item in bound_workstreams
        if str(item.get("task_id") or "").strip()
    }
    for item in bound_workstreams:
        item["depends_on"] = [
            task_to_workstream.get(str(dependency), str(dependency))
            for dependency in list(item.get("depends_on") or [])
        ]
    continuity_dependency_model = continuity.get("dependency_model")
    if not isinstance(continuity_dependency_model, Mapping):
        continuity_dependency_model = {}
    auto["workstreams"] = bound_workstreams
    auto["workstream_count"] = len(bound_workstreams)
    auto["dependency_model"] = {
        "topological_order": [str(item["workstream_id"]) for item in bound_workstreams],
        "edges": [
            {"from": dependency, "to": str(item["workstream_id"])}
            for item in bound_workstreams
            for dependency in item.get("depends_on", [])
        ],
        "real_dependencies_only": True,
        "cycle_detected": bool(continuity_dependency_model.get("cycle_detected", False)),
    }
    auto["now_startable"] = [] if has_question else [
        str(item["workstream_id"])
        for item in bound_workstreams
        if bool(item.get("can_start_now"))
    ]
    auto["existing_project_continuity"] = dict(continuity)
    auto["safe_next_action"] = (
        str(updated.get("safe_next_action") or "")
        if has_question
        else str(continuity.get("safe_next_action") or updated.get("safe_next_action") or "")
    )
    if has_question:
        auto["owner_decisions"] = [
            {
                "status": "PENDING",
                "question": str(updated.get("question")),
                "reason": "MATERIAL_PRODUCT_DECISION_REQUIRED",
            }
        ]
        question_policy = dict(auto.get("question_policy") or {})
        question_policy["decision"] = str(updated.get("question"))
        question_policy["reason"] = "MATERIAL_PRODUCT_DECISION_REQUIRED"
        auto["question_policy"] = question_policy
    updated["auto_decomposition"] = auto
    updated["execution_workstreams"] = [item["title"] for item in bound_workstreams]
    updated["safe_next_action"] = auto["safe_next_action"]
    updated["progress_summary"] = _progress_summary(
        continuity,
        question=str(updated.get("question") or "").strip() or None,
        safe_next_action=auto["safe_next_action"],
    )
    internal = dict(updated.get("internal") or {})
    internal["continuity_status"] = continuity.get("status", "AVAILABLE")
    internal["continuity_source"] = [".p2p/state/task-state.json", ".p2p/state/execution-ledger.jsonl"]
    updated["internal"] = internal
    fingerprint_basis = {
        "request": updated.get("request"),
        "intended_outcome": updated.get("intended_outcome"),
        "project_type": updated.get("project_type"),
        "project_state": updated.get("project_state"),
        "acceptance_criteria": updated.get("acceptance_criteria"),
        "important_constraints": updated.get("important_constraints"),
        "execution_workstreams": updated.get("execution_workstreams"),
        "progress_summary": updated.get("progress_summary"),
        "safe_next_action": updated.get("safe_next_action"),
        "question": updated.get("question"),
        "auto_decomposition": auto,
    }
    updated["charter_fingerprint"] = _fingerprint(fingerprint_basis)
    return updated


def task_specs_for_charter(charter: Mapping[str, Any], goal_id: str) -> list[dict[str, Any]]:
    """Build bounded Goal-scoped workstream tasks for the existing Task State store."""

    if not isinstance(charter, Mapping):
        raise BeginnerGatewayError("BEGINNER_CHARTER_REQUIRED")
    question = str(charter.get("question") or "").strip()
    auto = charter.get("auto_decomposition") if isinstance(charter.get("auto_decomposition"), Mapping) else {}
    workstreams = auto.get("workstreams") if isinstance(auto, Mapping) else None
    if not isinstance(workstreams, list) or not workstreams:
        workstreams = [
            {
                "workstream_id": "next",
                "title": "Continue the bounded project request",
                "purpose": str(charter.get("safe_next_action") or "Continue the bounded request safely."),
                "depends_on": [],
                "acceptance": list(charter.get("acceptance_criteria") or []),
                "status": "WAITING_OWNER" if question else "READY",
                "can_start_now": not bool(question),
                "owner_input": question,
            }
        ]
    workstream_ids = {str(item.get("workstream_id")): index for index, item in enumerate(workstreams) if isinstance(item, Mapping)}
    task_ids = {
        workstream_id: "beginner-gateway-next" if index == 0 else f"beginner-gateway-next-{index + 1}"
        for workstream_id, index in workstream_ids.items()
    }
    tasks: list[dict[str, Any]] = []
    for index, item in enumerate(workstreams):
        if not isinstance(item, Mapping):
            continue
        workstream_id = str(item.get("workstream_id") or f"workstream-{index + 1}")
        task_id = str(item.get("task_id") or task_ids.get(workstream_id) or f"beginner-gateway-next-{index + 1}")
        dependencies = [
            task_ids.get(str(dependency), str(dependency))
            for dependency in list(item.get("depends_on") or [])
        ]
        status = "WAITING_OWNER" if question and index == 0 else "PLANNED" if dependencies else "READY"
        task: dict[str, Any] = {
            "task_id": task_id,
            "goal_id": str(goal_id),
            "title": str(item.get("title") or "Continue the bounded project request"),
            "purpose": str(item.get("purpose") or charter.get("safe_next_action") or "Continue the bounded request safely."),
            "status": status,
            "dependencies": dependencies,
            "scope": ["BEGINNER_INTAKE", "AUTO01_GOAL_DECOMPOSITION", f"WORKSTREAM:{workstream_id}"],
            "non_scope": ["UNAUTHORIZED_PROTECTED_ACTIONS", "AUTOMATIC_HOST_START"],
            "acceptance_requirements": list(item.get("acceptance") or charter.get("acceptance_criteria") or []),
            "required_evidence": [".p2p/state/goal-contract.json", ".p2p/state/execution-ledger.jsonl"],
            "context_refs": [".p2p/state/goal-contract.json"],
            "requirement_refs": ["BEGINNER_GATEWAY_CHARTER", "AUTO01_GOAL_DECOMPOSITION"],
            "required_capabilities": [],
            "permission_needs": [],
        }
        if question and index == 0:
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
        tasks.append(task)
    if not tasks:
        raise BeginnerGatewayError("BEGINNER_WORKSTREAMS_INVALID")
    return tasks


def task_spec_for_charter(charter: Mapping[str, Any], goal_id: str) -> dict[str, Any]:
    """Return the compatibility first-task projection for existing callers."""

    return task_specs_for_charter(charter, goal_id)[0]


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
        "auto_decomposition": charter.get("auto_decomposition", {}),
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
    progress = projection.get("progress_summary")
    if isinstance(progress, Mapping):
        lines.append("\nTIẾN ĐỘ HIỆN TẠI")
        lines.append(f"- Trạng thái: {progress.get('status', '')}")
        if progress.get("completed"):
            lines.append("- Đã xong: " + "; ".join(str(item) for item in progress["completed"]))
        if progress.get("active"):
            lines.append("- Đang làm: " + "; ".join(str(item) for item in progress["active"]))
        if progress.get("blocked"):
            lines.append("- Đang chờ xử lý: " + "; ".join(str(item) for item in progress["blocked"]))
        if progress.get("waiting_for_you"):
            lines.append("- Cần bạn trả lời: " + "; ".join(str(item) for item in progress["waiting_for_you"]))
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
    "AUTO_DECOMPOSITION_SCHEMA",
    "BEGINNER_GATEWAY_SCHEMA",
    "BEGINNER_MODE",
    "STATUS_DONE",
    "STATUS_IN_PROGRESS",
    "STATUS_NEEDS_DECISION",
    "BeginnerGatewayError",
    "advanced_projection",
    "bind_continuity",
    "beginner_projection",
    "derive_charter",
    "is_continuation_request",
    "render_beginner",
    "task_spec_for_charter",
    "task_specs_for_charter",
]
