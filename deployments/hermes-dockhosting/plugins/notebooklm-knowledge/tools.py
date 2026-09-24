"""Read-only NotebookLM domain search for the Hermes Telegram assistant.

This plugin intentionally uses NotebookLM's read-only ranked passage search
instead of chat.ask(). That avoids sharing NotebookLM conversation history
between staff questions and avoids destructive conversation resets.

Consumer NotebookLM has no stable official automation API. The pinned
notebooklm-py dependency uses undocumented Google APIs, so failures are isolated
behind one tool and must never degrade into invented results.

Verified against notebooklm-py==0.8.2 (installed source, 2026-09-24):

- Auth: ``NotebookLMClient.from_storage()`` (no path) natively reads the
  ``NOTEBOOKLM_AUTH_JSON`` environment variable as inline Playwright storage
  state — a JSON object with a ``cookies`` list. No storage file is
  materialized in the container, and the library's error messages for
  malformed values do not echo the secret content.
- ``client.notebooks.list() -> list[Notebook]`` (fields: ``id``, ``title``).
- ``client.sources.list(notebook_id) -> list[Source]`` (fields: ``id``,
  ``title`` may be ``None``).
- ``client.sources.search(notebook_id, query, *, source_ids=None,
  limit=None) -> list[RelevantChunk]`` (fields: ``source_id``, ``text``,
  ``rank``, ``start``, ``end`` — offsets are ``None`` when the backend
  omits a span).

The handler is an async coroutine registered with ``is_async=True`` so the
Hermes registry bridges it through its own sync->async path (works both from
the CLI and from the gateway's running event loop). It must never be wrapped
in a raw ``asyncio.run`` call, which would fail inside a running loop.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import unicodedata
from typing import Any, Optional

TOOLSET = "notebooklm_knowledge"
AUTH_ENV = "NOTEBOOKLM_AUTH_JSON"
IDS_ENV = "NOTEBOOKLM_NOTEBOOKS_JSON"
TITLES_ENV = "NOTEBOOKLM_NOTEBOOK_TITLES_JSON"
SUPPORTED_DOMAINS = ("HS", "CHEMICAL", "BKHCN", "BTTTT")
DEFAULT_LIMIT_PER_DOMAIN = 4
MAX_LIMIT_PER_DOMAIN = 6
MAX_DOMAINS = 3
MAX_PASSAGE_CHARS = 700

DOMAIN_LABELS = {
    "HS": "Tra mã HS",
    "CHEMICAL": "Hóa chất",
    "BKHCN": "Bộ KH&CN",
    "BTTTT": "Bộ TT&TT",
}

DEFAULT_TITLE_ALIASES = {
    "HS": ("Tra mã HS",),
    "CHEMICAL": ("Hóa chất", "Hoá chất"),
    "BKHCN": (
        "Bộ khoa học công nghệ",
        "Bộ Khoa học và Công nghệ",
        "Bộ khoa học công nghê",
        "BKHCN",
    ),
    "BTTTT": (
        "Bộ Thông Tin truyền thông",
        "Bộ Thông tin và Truyền thông",
        "BTTTT",
    ),
}

DOMAIN_PATTERNS = {
    "HS": (
        r"\bhs\b",
        r"mã\s*hs",
        r"hs\s*code",
        r"phân\s*loại\s*hàng",
        r"biểu\s*thuế",
        r"thuế\s*nhập\s*khẩu",
    ),
    "CHEMICAL": (
        r"hóa\s*chất",
        r"hoá\s*chất",
        r"\bcas\b",
        r"\bmsds\b",
        r"\bsds\b",
        r"thành\s*phần",
        r"tiền\s*chất",
        r"toluene|acetone|methanol|ethanol|acid|axit",
    ),
    "BKHCN": (
        r"bộ\s*khoa\s*học",
        r"\bbkhcn\b",
        r"kiểm\s*tra\s*chất\s*lượng",
        r"quy\s*chuẩn\s*kỹ\s*thuật",
        r"đo\s*lường",
        r"máy\s*móc\s*đã\s*qua\s*sử\s*dụng",
        r"máy\s*móc\s*cũ",
    ),
    "BTTTT": (
        r"bộ\s*thông\s*tin",
        r"\bbtttt\b",
        r"wifi|wi-fi|bluetooth",
        r"vô\s*tuyến",
        r"tần\s*số",
        r"router|modem",
        r"thiết\s*bị\s*phát\s*sóng",
        r"viễn\s*thông",
        r"ict",
    ),
}


def _json_default(value: Any) -> str:
    if isinstance(value, (_dt.datetime, _dt.date)):
        return value.isoformat()
    return str(value)


def tool_result(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=_json_default)


def tool_error(message: str, **extra: Any) -> str:
    return json.dumps(
        {"error": message, **extra},
        ensure_ascii=False,
        default=_json_default,
    )


def _check_notebooklm_configured() -> bool:
    return bool(os.environ.get(AUTH_ENV, "").strip())


def _validate_auth_state() -> None:
    """Validate NOTEBOOKLM_AUTH_JSON against the pinned library's contract.

    notebooklm-py 0.8.2 reads NOTEBOOKLM_AUTH_JSON natively as inline
    Playwright storage state: a JSON object with a ``cookies`` list. Checking
    the same contract locally lets a malformed secret fail closed as a config
    error before any upstream call. The secret value is never included in the
    raised message (the raised text is a fixed string, not the parsed value).
    """
    try:
        value = json.loads(os.environ.get(AUTH_ENV, ""))
    except json.JSONDecodeError:
        raise _ConfigError(f"{AUTH_ENV} is not valid JSON") from None
    if not isinstance(value, dict) or not isinstance(value.get("cookies"), list):
        raise _ConfigError(
            f"{AUTH_ENV} must be a JSON object with a 'cookies' list "
            "(Playwright storage state)"
        )


def _schema(
    name: str,
    description: str,
    properties: dict,
    required: tuple[str, ...] = (),
) -> dict:
    return {
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": list(required),
        },
    }


NOTEBOOKLM_SEARCH_SCHEMA = _schema(
    "notebooklm_domain_search",
    "Search Trường Thành Logistics' configured NotebookLM knowledge notebooks. "
    "Use this for Support/Sale questions about HS classification, chemicals, "
    "Bộ KH&CN / quality-regulation topics, and Bộ TT&TT / telecom-radio topics. "
    "If domains is omitted, the tool deterministically routes the Vietnamese "
    "question to up to three matching notebooks. It returns ranked source "
    "passages and source titles from NotebookLM; it does NOT create or modify "
    "notebooks and does NOT use NotebookLM chat history. Ground any answer only "
    "in the returned passages. NotebookLM is an operational research layer, NOT "
    "final legal authority; do not claim a binding legal conclusion solely from "
    "this tool. If status is NEEDS_MORE_DETAIL, ask the user for product facts "
    "instead of guessing.",
    {
        "question": {
            "type": "string",
            "description": "The staff user's Vietnamese product/regulatory question.",
        },
        "domains": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": list(SUPPORTED_DOMAINS),
            },
            "description": (
                "Optional explicit notebook domains. Omit to auto-route. "
                "Supported: HS, CHEMICAL, BKHCN, BTTTT."
            ),
        },
        "limit_per_domain": {
            "type": "integer",
            "description": "Ranked passages per domain (default 4, max 6).",
        },
    },
    required=("question",),
)


class _BadRequest(Exception):
    pass


class _ConfigError(Exception):
    pass


def _normalize_title(value: Any) -> str:
    text = unicodedata.normalize("NFD", str(value or "").casefold())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _load_json_object(env_name: str) -> dict:
    raw = os.environ.get(env_name, "").strip()
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise _ConfigError(f"{env_name} is not valid JSON") from exc
    if not isinstance(value, dict):
        raise _ConfigError(f"{env_name} must be a JSON object")
    return value


def _notebook_id_overrides() -> dict[str, str]:
    raw = _load_json_object(IDS_ENV)
    result: dict[str, str] = {}
    for key, value in raw.items():
        domain = str(key).upper().strip()
        notebook_id = str(value or "").strip()
        if domain in SUPPORTED_DOMAINS and notebook_id:
            result[domain] = notebook_id
    return result


def _title_aliases() -> dict[str, tuple[str, ...]]:
    result = {key: tuple(values) for key, values in DEFAULT_TITLE_ALIASES.items()}
    raw = _load_json_object(TITLES_ENV)
    for key, value in raw.items():
        domain = str(key).upper().strip()
        if domain not in SUPPORTED_DOMAINS:
            continue
        values = value if isinstance(value, list) else [value]
        cleaned = tuple(str(item).strip() for item in values if str(item).strip())
        if cleaned:
            result[domain] = cleaned
    return result


def route_domains(question: str) -> tuple[str, ...]:
    text = str(question or "").strip()
    if not text:
        return ()
    lowered = text.casefold()
    scored: list[tuple[int, str]] = []
    for domain, patterns in DOMAIN_PATTERNS.items():
        score = sum(
            1
            for pattern in patterns
            if re.search(pattern, lowered, flags=re.IGNORECASE)
        )
        if score:
            scored.append((score, domain))
    scored.sort(key=lambda item: (-item[0], SUPPORTED_DOMAINS.index(item[1])))
    return tuple(domain for _, domain in scored[:MAX_DOMAINS])


def _requested_domains(args: dict, question: str) -> tuple[str, ...]:
    raw = args.get("domains")
    if raw is None:
        return route_domains(question)
    if not isinstance(raw, list):
        raise _BadRequest("domains must be an array")
    domains: list[str] = []
    for value in raw:
        domain = str(value or "").upper().strip()
        if domain not in SUPPORTED_DOMAINS:
            raise _BadRequest(
                "unsupported domain; use HS, CHEMICAL, BKHCN, or BTTTT"
            )
        if domain not in domains:
            domains.append(domain)
    if len(domains) > MAX_DOMAINS:
        raise _BadRequest(f"at most {MAX_DOMAINS} domains may be queried")
    return tuple(domains)


def _bounded_limit(args: dict) -> int:
    raw = args.get("limit_per_domain")
    if raw is None:
        return DEFAULT_LIMIT_PER_DOMAIN
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise _BadRequest("limit_per_domain must be an integer") from exc
    return max(1, min(value, MAX_LIMIT_PER_DOMAIN))


def _clip(value: Any, limit: int = MAX_PASSAGE_CHARS) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


async def _resolve_notebooks(
    client: Any,
    domains: tuple[str, ...],
) -> list[tuple[str, str, str]]:
    overrides = _notebook_id_overrides()
    aliases = _title_aliases()
    notebooks = await client.notebooks.list()

    by_id = {
        str(getattr(item, "id", "") or ""): item
        for item in notebooks
        if str(getattr(item, "id", "") or "").strip()
    }
    by_title: dict[str, list[Any]] = {}
    for item in notebooks:
        title_key = _normalize_title(getattr(item, "title", ""))
        if title_key:
            by_title.setdefault(title_key, []).append(item)

    resolved: list[tuple[str, str, str]] = []
    for domain in domains:
        override_id = overrides.get(domain)
        if override_id:
            item = by_id.get(override_id)
            title = str(getattr(item, "title", "") or DOMAIN_LABELS[domain])
            resolved.append((domain, override_id, title))
            continue

        matches: dict[str, Any] = {}
        for alias in aliases.get(domain, ()):
            for item in by_title.get(_normalize_title(alias), ()):
                item_id = str(getattr(item, "id", "") or "").strip()
                if item_id:
                    matches[item_id] = item

        if len(matches) == 1:
            notebook_id, item = next(iter(matches.items()))
            resolved.append(
                (domain, notebook_id, str(getattr(item, "title", "") or DOMAIN_LABELS[domain]))
            )
            continue
        if len(matches) > 1:
            raise _ConfigError(
                f"multiple notebooks match {domain}; configure {IDS_ENV}"
            )
        raise _ConfigError(
            f"no notebook found for {domain}; check sharing/title or configure {IDS_ENV}"
        )

    return resolved


async def _search_async(
    question: str,
    domains: tuple[str, ...],
    limit_per_domain: int,
) -> dict:
    try:
        from notebooklm import NotebookLMClient
    except ImportError as exc:
        raise _ConfigError("notebooklm-py is not installed") from exc

    async with NotebookLMClient.from_storage() as client:
        resolved = await _resolve_notebooks(client, domains)
        domain_results: list[dict] = []

        for domain, notebook_id, notebook_title in resolved:
            sources = await client.sources.list(notebook_id)
            title_by_id = {
                str(getattr(source, "id", "") or ""): str(
                    getattr(source, "title", "") or "Nguồn NotebookLM"
                )
                for source in sources
            }
            passages = await client.sources.search(
                notebook_id,
                question,
                limit=limit_per_domain,
            )

            items: list[dict] = []
            for passage in list(passages or [])[:limit_per_domain]:
                source_id = str(getattr(passage, "source_id", "") or "")
                items.append(
                    {
                        "rank": getattr(passage, "rank", None),
                        "source_id": source_id or None,
                        "source_title": title_by_id.get(
                            source_id, "Nguồn NotebookLM"
                        ),
                        "text": _clip(getattr(passage, "text", "")),
                        "start": getattr(passage, "start", None),
                        "end": getattr(passage, "end", None),
                    }
                )

            domain_results.append(
                {
                    "domain": domain,
                    "label": DOMAIN_LABELS[domain],
                    "notebook_title": notebook_title,
                    "status": "OK" if items else "NOT_FOUND",
                    "passages": items,
                }
            )

    return {
        "status": "OK" if any(x["passages"] for x in domain_results) else "NOT_FOUND",
        "query": question,
        "routed_domains": list(domains),
        "results": domain_results,
        "provider": "NotebookLM via notebooklm-py 0.8.2 (unofficial)",
        "mode": "READ_ONLY_RANKED_PASSAGE_SEARCH",
        "legal_authority": False,
        "notice": (
            "NotebookLM is an operational research source. Ground summaries only "
            "in returned passages and verify binding legal conclusions against "
            "VNLAW / official sources."
        ),
        "queried_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
    }


async def handle_notebooklm_search(args: Optional[dict], **_kwargs: Any) -> str:
    """Async tool handler (registered with ``is_async=True``).

    The Hermes registry bridges async handlers through its own sync->async
    path, which is safe both from the CLI and from the gateway's running
    event loop. A raw ``asyncio.run`` here would raise inside a running
    loop and break the tool in the live Telegram runtime.
    """
    args = args or {}
    question = str(args.get("question") or "").strip()
    if not question:
        return tool_error(
            "question is required",
            error_type="notebooklm_bad_request",
        )

    if not _check_notebooklm_configured():
        return tool_error(
            "NotebookLM authentication is not configured",
            error_type="notebooklm_config_missing",
            required_env=[AUTH_ENV],
        )

    try:
        # Validate the secret shape locally so a malformed value fails
        # closed before any upstream call, without forwarding credential
        # material into an upstream exception/log.
        _validate_auth_state()

        domains = _requested_domains(args, question)
        if not domains:
            return tool_result(
                {
                    "status": "NEEDS_MORE_DETAIL",
                    "query": question,
                    "routed_domains": [],
                    "needed": (
                        "Bổ sung loại hàng/công dụng/thành phần/CAS/model/tần số "
                        "hoặc chỉ rõ nhóm HS, Hóa chất, Bộ KH&CN, Bộ TT&TT."
                    ),
                    "legal_authority": False,
                }
            )
        limit_per_domain = _bounded_limit(args)
        return tool_result(
            await _search_async(
                question,
                domains,
                limit_per_domain,
            )
        )
    except _BadRequest as exc:
        return tool_error(
            str(exc),
            error_type="notebooklm_bad_request",
        )
    except _ConfigError as exc:
        return tool_error(
            str(exc),
            error_type="notebooklm_config_error",
        )
    except Exception as exc:
        # Fail closed and never echo request/response/cookie details:
        # only the exception type name is reported, never its message.
        return tool_error(
            f"NotebookLM request failed: {type(exc).__name__}",
            error_type="notebooklm_upstream_error",
        )


TOOL_REGISTRATIONS = (
    {
        "name": "notebooklm_domain_search",
        "toolset": TOOLSET,
        "schema": NOTEBOOKLM_SEARCH_SCHEMA,
        "handler": handle_notebooklm_search,
        "is_async": True,
        "check_fn": _check_notebooklm_configured,
        "requires_env": [AUTH_ENV],
        "emoji": "📚",
    },
)
