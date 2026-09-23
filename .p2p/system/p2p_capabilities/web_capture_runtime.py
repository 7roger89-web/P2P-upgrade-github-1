"""Generic public-web capture runtime for the P2P ``web.*`` capability family.

Task: ``P2P_PUBLIC_WEB_SCRAPE_RUNTIME_01`` (Issue #241). This module is the
missing RUNTIME/CAPTURE seam under the capability declarations added by
Issue #224 (``web.browser.evidence``, ``web.js.reverse``,
``web.endpoint.discovery``, ``web.public.reconstruction``). It reuses those
existing capability IDs unchanged and creates no new capability, no second
router, no second registry, no crawler service, no scheduler, no queue, no
database, no traffic store, and no scraping DSL.

What this module owns (generic, source-neutral):

* one normalized immutable capture contract (:class:`CaptureRecord`) with
  provenance and hashing — unknown HTTP metadata stays ``None`` and is never
  fabricated;
* thin pluggable transport adapters and a cheapest-first transport policy
  (plain HTTP, executor-native text, optional browser document — browser is
  never mandatory and is never launched by this module);
* bounded explicit navigation plans (single URL, finite discovered page
  ranges, discovered record/detail follow-ups, discovered attachment URLs);
* checkpoint/resume metadata;
* a small evidence writer.

What stays OUTSIDE this runtime (project-owned): VIMDA/VBPL/Công Báo parsers,
record semantics, attachment semantics, legal interpretation, and any business
meaning of captured content. Captured content is data, never instruction
authority.

Safety boundary (fail closed): public unauthenticated http/https content only;
no credentials or cookies; no login/WAF/CAPTCHA bypass; no TLS weakening; no
proxy rotation; no hidden numeric record-ID enumeration (the runtime never
generates URLs from numeric ranges — every non-seed plan step must replay an
explicitly discovered URL, optionally verified as literally present in the
discovery capture text); no unbounded crawl (hard plan caps). Live interaction
sits under the existing security contract ceiling ``ACTIVE_TEST_AUTHORIZED``
and requires an explicit per-call authorization flag.

This module performs no routing/classification of task text. Callers arrive
here only after the sole P2P router has selected a ``web.*`` capability.
"""

from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from .security_contract import ACTIVE_TEST_AUTHORIZED
from .web_reverse_reference import WEB_REVERSE_FAMILY_FLOW

WEB_CAPTURE_RUNTIME_SCHEMA = "p2p-web-capture-runtime/1"
WEB_CAPTURE_RUNTIME_MODULE = ".p2p/system/p2p_capabilities/web_capture_runtime.py"

# Reuse of the existing Issue #224 capability family; NO new capability IDs.
RELATED_CAPABILITY_IDS: tuple[str, ...] = WEB_REVERSE_FAMILY_FLOW
LIVE_CAPTURE_EXECUTION_CLASS = ACTIVE_TEST_AUTHORIZED

# Normalized capture contract vocabularies (Issue #241).
REPRESENTATIONS = ("RAW_BYTES", "TEXT_CAPTURE", "BROWSER_DOCUMENT", "NETWORK_RESPONSE")
RAW_BYTES = "RAW_BYTES"
TEXT_CAPTURE = "TEXT_CAPTURE"
BROWSER_DOCUMENT = "BROWSER_DOCUMENT"
NETWORK_RESPONSE = "NETWORK_RESPONSE"

TRANSPORT_KINDS = ("PLAIN_HTTP", "EXECUTOR_TEXT", "EXECUTOR_BROWSER", "RECORDED_RESULT")
PLAIN_HTTP = "PLAIN_HTTP"
EXECUTOR_TEXT = "EXECUTOR_TEXT"
EXECUTOR_BROWSER = "EXECUTOR_BROWSER"
RECORDED_RESULT = "RECORDED_RESULT"

# Cheapest working transport first. Browser is LAST and OPTIONAL: a capture
# run without any browser adapter is fully supported by design.
TRANSPORT_POLICY_ORDER = (PLAIN_HTTP, EXECUTOR_TEXT, EXECUTOR_BROWSER)

PLAN_KINDS = ("SINGLE_URL", "PAGE_RANGE", "DISCOVERED_LINKS", "ATTACHMENT_DISCOVERY")
SINGLE_URL = "SINGLE_URL"
PAGE_RANGE = "PAGE_RANGE"
DISCOVERED_LINKS = "DISCOVERED_LINKS"
ATTACHMENT_DISCOVERY = "ATTACHMENT_DISCOVERY"

STEP_KINDS = ("SEED", "PAGINATION", "RECORD_FOLLOWUP", "ATTACHMENT")
STEP_STATUSES = ("PENDING", "CAPTURED", "FAILED", "BLOCKED", "SKIPPED")

# Hard bounded-plan ceilings. There is no unbounded mode.
MAX_PLAN_CAPTURES = 64
MAX_CAPTURE_BYTES = 8 * 1024 * 1024
DEFAULT_TIMEOUT_SECONDS = 30.0
HONEST_USER_AGENT = (
    "P2P-web-capture-runtime/1 (bounded public capture; no credentials; Issue #241)"
)

_REQUIRED_RECORD_FIELDS = (
    "requested_url",
    "final_url",
    "retrieved_at",
    "source_host",
    "transport_kind",
    "http_status",
    "content_type",
    "representation",
    "byte_count",
    "char_count",
    "sha256",
    "capture_scope",
    "parent_capture",
    "discovered_from",
    "executor",
)


class WebCaptureError(ValueError):
    """Base error: the capture runtime fails closed."""


class CaptureScopeError(WebCaptureError):
    """Raised when a URL or scope violates the explicit public target scope."""


class CapturePlanError(WebCaptureError):
    """Raised when a navigation plan is unbounded, unprovenanced, or unsafe."""


class CaptureAuthorizationError(WebCaptureError):
    """Raised when live interaction lacks explicit authorization."""


class CaptureTransportError(WebCaptureError):
    """Raised when no available transport can expose the requested content."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_public_url(url: Any, *, allowed_schemes: Sequence[str] = ("https", "http")) -> str:
    """Validate a public unauthenticated http/https URL; fail closed.

    Rejects: empty/non-string URLs, non-http(s) schemes, embedded credentials
    (userinfo), and empty hosts. Never rewrites the URL beyond returning it
    unchanged; percent-encoding is left exactly as provided.
    """

    if not isinstance(url, str) or not url.strip():
        raise CaptureScopeError("EMPTY_OR_NON_STRING_URL")
    candidate = url.strip()
    parsed = urllib.parse.urlsplit(candidate)
    if parsed.scheme.lower() not in {scheme.lower() for scheme in allowed_schemes}:
        raise CaptureScopeError(f"SCHEME_NOT_ALLOWED:{parsed.scheme or 'EMPTY'}")
    if "@" in (parsed.netloc or ""):
        raise CaptureScopeError("CREDENTIALS_IN_URL_REJECTED")
    if not parsed.hostname:
        raise CaptureScopeError("EMPTY_HOST")
    return candidate


@dataclass(frozen=True)
class CaptureScope:
    """Explicit public target scope. Anything outside it fails closed."""

    scope_id: str
    allowed_host: str
    allowed_path_prefixes: tuple[str, ...]
    task_authority: str
    allowed_schemes: tuple[str, ...] = ("https",)

    def __post_init__(self) -> None:
        if not self.scope_id.strip():
            raise CaptureScopeError("EMPTY_SCOPE_ID")
        if not self.task_authority.strip():
            raise CaptureScopeError("SCOPE_REQUIRES_EXPLICIT_TASK_AUTHORITY")
        host = self.allowed_host.strip().lower()
        if not host or "/" in host or "@" in host or ":" in host:
            raise CaptureScopeError(f"INVALID_ALLOWED_HOST:{self.allowed_host!r}")
        object.__setattr__(self, "allowed_host", host)
        if not self.allowed_path_prefixes:
            raise CaptureScopeError("SCOPE_REQUIRES_EXPLICIT_PATH_PREFIXES")
        for prefix in self.allowed_path_prefixes:
            if not prefix.startswith("/"):
                raise CaptureScopeError(f"PATH_PREFIX_MUST_START_WITH_SLASH:{prefix!r}")
        for scheme in self.allowed_schemes:
            if scheme.lower() not in ("http", "https"):
                raise CaptureScopeError(f"SCHEME_NOT_ALLOWED:{scheme}")

    def allows(self, url: str) -> bool:
        try:
            candidate = validate_public_url(url, allowed_schemes=self.allowed_schemes)
        except CaptureScopeError:
            return False
        parsed = urllib.parse.urlsplit(candidate)
        if (parsed.hostname or "").lower() != self.allowed_host:
            return False
        path = parsed.path or "/"
        return any(path.startswith(prefix) for prefix in self.allowed_path_prefixes)

    def require_allows(self, url: str) -> str:
        candidate = validate_public_url(url, allowed_schemes=self.allowed_schemes)
        if not self.allows(candidate):
            raise CaptureScopeError(f"URL_OUTSIDE_CAPTURE_SCOPE:{candidate}")
        return candidate

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope_id": self.scope_id,
            "allowed_host": self.allowed_host,
            "allowed_path_prefixes": list(self.allowed_path_prefixes),
            "allowed_schemes": list(self.allowed_schemes),
            "task_authority": self.task_authority,
        }


@dataclass(frozen=True)
class TransportResult:
    """Raw result handed back by one transport adapter.

    ``http_status``/``content_type``/``final_url`` stay ``None`` unless the
    transport actually observed them. Adapters must never invent HTTP metadata.
    """

    requested_url: str
    content: bytes | str
    transport_kind: str
    representation: str
    executor: str
    retrieved_at: str | None = None
    final_url: str | None = None
    http_status: int | None = None
    content_type: str | None = None
    executor_meta: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.transport_kind not in TRANSPORT_KINDS:
            raise CaptureTransportError(f"UNKNOWN_TRANSPORT_KIND:{self.transport_kind}")
        if self.representation not in REPRESENTATIONS:
            raise CaptureTransportError(f"UNKNOWN_REPRESENTATION:{self.representation}")
        if self.http_status is not None and not isinstance(self.http_status, int):
            raise CaptureTransportError("HTTP_STATUS_MUST_BE_INT_OR_NONE")
        if not self.executor.strip():
            raise CaptureTransportError("EMPTY_EXECUTOR")


def compute_capture_id(
    *,
    requested_url: str,
    representation: str,
    transport_kind: str,
    content_sha256: str,
    capture_scope: str,
    parent_capture: str | None,
    discovered_from: str | None,
    executor: str,
) -> str:
    """Deterministic capture identity: same inputs -> same id, no timestamps."""

    payload = _canonical_json(
        [
            requested_url,
            representation,
            transport_kind,
            content_sha256,
            capture_scope,
            parent_capture,
            discovered_from,
            executor,
        ]
    )
    return "cap-" + _sha256_bytes(payload.encode("utf-8"))


@dataclass(frozen=True)
class CaptureRecord:
    """Normalized immutable capture. Unknown values stay None/unobserved."""

    capture_id: str
    requested_url: str
    final_url: str | None
    retrieved_at: str | None
    source_host: str
    transport_kind: str
    http_status: int | None
    content_type: str | None
    representation: str
    byte_count: int
    char_count: int | None
    sha256: str
    capture_scope: str
    parent_capture: str | None
    discovered_from: str | None
    executor: str
    content_path: str | None = None
    executor_meta: Mapping[str, Any] | None = None
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "capture_id": self.capture_id,
            "requested_url": self.requested_url,
            "final_url": self.final_url,
            "retrieved_at": self.retrieved_at,
            "source_host": self.source_host,
            "transport_kind": self.transport_kind,
            "http_status": self.http_status,
            "content_type": self.content_type,
            "representation": self.representation,
            "byte_count": self.byte_count,
            "char_count": self.char_count,
            "sha256": self.sha256,
            "capture_scope": self.capture_scope,
            "parent_capture": self.parent_capture,
            "discovered_from": self.discovered_from,
            "executor": self.executor,
            "content_path": self.content_path,
            "notes": list(self.notes),
        }
        if self.executor_meta is not None:
            payload["executor_meta"] = dict(self.executor_meta)
        return payload


def normalize_capture(
    result: TransportResult,
    scope: CaptureScope,
    *,
    parent_capture: str | None = None,
    discovered_from: str | None = None,
    content_path: str | None = None,
    notes: Sequence[str] = (),
) -> CaptureRecord:
    """Normalize one transport result into the generic capture contract.

    Scope is enforced on both ``requested_url`` and any observed ``final_url``
    (an out-of-scope redirect fails closed). Hashes/counts are computed from
    the actual content bytes; nothing else is derived or invented.
    """

    scope.require_allows(result.requested_url)
    if result.final_url is not None:
        scope.require_allows(result.final_url)

    if isinstance(result.content, bytes):
        raw = result.content
        try:
            char_count: int | None = len(raw.decode("utf-8"))
        except UnicodeDecodeError:
            char_count = None
    else:
        raw = result.content.encode("utf-8")
        char_count = len(result.content)

    host = urllib.parse.urlsplit(result.final_url or result.requested_url).hostname or ""
    capture_id = compute_capture_id(
        requested_url=result.requested_url,
        representation=result.representation,
        transport_kind=result.transport_kind,
        content_sha256=_sha256_bytes(raw),
        capture_scope=scope.scope_id,
        parent_capture=parent_capture,
        discovered_from=discovered_from,
        executor=result.executor,
    )
    return CaptureRecord(
        capture_id=capture_id,
        requested_url=result.requested_url,
        final_url=result.final_url,
        retrieved_at=result.retrieved_at,
        source_host=host.lower(),
        transport_kind=result.transport_kind,
        http_status=result.http_status,
        content_type=result.content_type,
        representation=result.representation,
        byte_count=len(raw),
        char_count=char_count,
        sha256=_sha256_bytes(raw),
        capture_scope=scope.scope_id,
        parent_capture=parent_capture,
        discovered_from=discovered_from,
        executor=result.executor,
        content_path=content_path,
        executor_meta=dict(result.executor_meta) if result.executor_meta else None,
        notes=tuple(notes),
    )


@dataclass(frozen=True)
class Capture:
    """One normalized capture plus the exact bytes/text it was built from."""

    record: CaptureRecord
    content: bytes
    text: str | None


# ---------------------------------------------------------------------------
# Thin transport adapters. Each adapter is a small callable wrapper; the
# runtime never launches a browser, installs anything, or registers anything.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PlainHttpTransport:
    """Cheapest transport: direct public HTTP GET via stdlib urllib.

    Fail-closed properties: requires explicit per-call ``authorized=True``;
    GET only; no cookies, no credential headers, no proxy configuration
    (environment proxies are disabled, never rotated), default TLS
    verification is never weakened, and reads are bounded by ``max_bytes``.
    HTTP metadata is recorded only from the real response.
    """

    kind: str = PLAIN_HTTP
    representation: str = RAW_BYTES
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_bytes: int = MAX_CAPTURE_BYTES
    user_agent: str = HONEST_USER_AGENT

    def fetch(self, url: str, *, authorized: bool = False) -> TransportResult:
        if not authorized:
            raise CaptureAuthorizationError(
                "LIVE_HTTP_REQUIRES_EXPLICIT_AUTHORIZATION:"
                f"{LIVE_CAPTURE_EXECUTION_CLASS}"
            )
        candidate = validate_public_url(url)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        request = urllib.request.Request(
            candidate,
            method="GET",
            headers={"User-Agent": self.user_agent, "Accept": "*/*"},
        )
        try:
            with opener.open(request, timeout=self.timeout_seconds) as response:
                raw = response.read(self.max_bytes + 1)
                status: int | None = getattr(response, "status", None)
                if status is None:  # pragma: no cover - py<3.9 fallback shape
                    status = response.getcode()
                content_type = response.headers.get("Content-Type")
                final_url = response.geturl()
        except urllib.error.HTTPError as error:  # observed error responses are truth
            raw = error.read(self.max_bytes + 1)
            status = error.code
            content_type = error.headers.get("Content-Type") if error.headers else None
            final_url = url
        except (urllib.error.URLError, OSError, ValueError) as error:
            raise CaptureTransportError(f"PLAIN_HTTP_UNAVAILABLE:{error}") from error
        if len(raw) > self.max_bytes:
            raise CaptureTransportError("CAPTURE_SIZE_LIMIT_EXCEEDED")
        return TransportResult(
            requested_url=candidate,
            content=raw,
            transport_kind=self.kind,
            representation=self.representation,
            executor="P2P_PLAIN_HTTP",
            retrieved_at=_utc_now(),
            final_url=final_url,
            http_status=status,
            content_type=content_type,
        )


@dataclass(frozen=True)
class ExecutorTextTransport:
    """Executor-native public text transport (e.g. Arena ``fetch_page``).

    The executor supplies a callable ``url -> mapping`` with at least
    ``content`` (str/bytes) and optionally observed ``url``/``final_url``,
    ``http_status``, ``content_type``, ``retrieved_at`` and ``executor_meta``
    (for example honest chunk information). Unobserved HTTP metadata stays
    None — this adapter never guesses a status code or content type.
    """

    executor_name: str
    fetch_callable: Callable[[str], Mapping[str, Any]]
    kind: str = EXECUTOR_TEXT
    representation: str = TEXT_CAPTURE

    def fetch(self, url: str, *, authorized: bool = False) -> TransportResult:
        del authorized  # executor-native public text fetch needs no live-HTTP flag
        candidate = validate_public_url(url)
        raw = self.fetch_callable(candidate)
        if not isinstance(raw, Mapping):
            raise CaptureTransportError("EXECUTOR_RESULT_MUST_BE_MAPPING")
        content = raw.get("content")
        if not isinstance(content, (str, bytes)):
            raise CaptureTransportError("EXECUTOR_RESULT_MISSING_CONTENT")
        status = raw.get("http_status")
        if status is not None and not isinstance(status, int):
            raise CaptureTransportError("EXECUTOR_HTTP_STATUS_MUST_BE_INT_OR_NONE")
        return TransportResult(
            requested_url=candidate,
            content=content,
            transport_kind=self.kind,
            representation=str(raw.get("representation") or self.representation),
            executor=self.executor_name,
            retrieved_at=raw.get("retrieved_at") or _utc_now(),
            final_url=raw.get("url") or raw.get("final_url"),
            http_status=status,
            content_type=raw.get("content_type"),
            executor_meta=raw.get("executor_meta"),
        )


@dataclass(frozen=True)
class ExecutorBrowserTransport:
    """OPTIONAL browser-document adapter slot. Never mandatory.

    This runtime never launches, installs, or drives a browser itself. An
    executor that already owns a working browser surface (for example a
    browser-use/jev-ultrafast or Browser Harness integration elsewhere) may
    inject ``render_callable``; without one, this adapter fails closed and the
    transport policy simply proceeds without a browser lane.
    """

    executor_name: str = "UNPROVIDED_BROWSER_ADAPTER"
    render_callable: Callable[[str], Mapping[str, Any]] | None = None
    kind: str = EXECUTOR_BROWSER
    representation: str = BROWSER_DOCUMENT

    def fetch(self, url: str, *, authorized: bool = False) -> TransportResult:
        del authorized
        if self.render_callable is None:
            raise CaptureTransportError(
                "BROWSER_ADAPTER_NOT_PROVIDED:OPTIONAL_ONLY_NEVER_MANDATORY"
            )
        candidate = validate_public_url(url)
        raw = self.render_callable(candidate)
        content = raw.get("content") if isinstance(raw, Mapping) else None
        if not isinstance(content, (str, bytes)):
            raise CaptureTransportError("BROWSER_RESULT_MISSING_DOCUMENT")
        return TransportResult(
            requested_url=candidate,
            content=content,
            transport_kind=self.kind,
            representation=self.representation,
            executor=self.executor_name,
            retrieved_at=(raw.get("retrieved_at") if isinstance(raw, Mapping) else None) or _utc_now(),
            final_url=raw.get("url") if isinstance(raw, Mapping) else None,
            http_status=raw.get("http_status") if isinstance(raw, Mapping) else None,
            content_type=raw.get("content_type") if isinstance(raw, Mapping) else None,
            executor_meta=raw.get("executor_meta") if isinstance(raw, Mapping) else None,
        )


def capture_with_policy(
    url: str,
    scope: CaptureScope,
    adapters: Sequence[Any],
    *,
    authorized: bool = False,
    parent_capture: str | None = None,
    discovered_from: str | None = None,
    notes: Sequence[str] = (),
) -> Capture:
    """Capture one in-scope URL using the cheapest WORKING transport.

    Adapters are tried in ``TRANSPORT_POLICY_ORDER`` (plain HTTP -> executor
    text -> browser), regardless of the order they are supplied in. An adapter
    that cannot expose the content (unavailable, unauthorized, or failing)
    yields to the next one; the browser lane is used only when the cheaper
    lanes cannot work, and is never required at all.
    """

    by_kind: dict[str, Any] = {}
    for adapter in adapters:
        kind = getattr(adapter, "kind", None)
        if kind not in TRANSPORT_KINDS:
            raise CaptureTransportError(f"UNKNOWN_ADAPTER_KIND:{kind!r}")
        by_kind.setdefault(kind, adapter)

    failures: list[str] = []
    for kind in TRANSPORT_POLICY_ORDER:
        adapter = by_kind.get(kind)
        if adapter is None:
            failures.append(f"{kind}:ADAPTER_NOT_PROVIDED")
            continue
        try:
            result = adapter.fetch(url, authorized=authorized)
        except (CaptureAuthorizationError, CaptureTransportError) as error:
            failures.append(f"{kind}:{error}")
            continue
        record = normalize_capture(
            result,
            scope,
            parent_capture=parent_capture,
            discovered_from=discovered_from,
            notes=tuple(notes),
        )
        content = (
            result.content
            if isinstance(result.content, bytes)
            else result.content.encode("utf-8")
        )
        text = None
        if isinstance(result.content, str):
            text = result.content
        else:
            try:
                text = result.content.decode("utf-8")
            except UnicodeDecodeError:
                text = None
        return Capture(record=record, content=content, text=text)
    raise CaptureTransportError("NO_AVAILABLE_TRANSPORT_FOR_URL:" + "; ".join(failures))


# ---------------------------------------------------------------------------
# Generic link extraction mechanics. Semantics stay project-owned: the runtime
# only extracts URL strings and applies caller-provided filters; it never
# decides what a link MEANS (record vs attachment vs pagination).
# ---------------------------------------------------------------------------

_URL_PATTERN = re.compile(r"https?://[^\s\"'<>()\[\]\\{}|^\x00-\x1f]+", re.IGNORECASE)
_TRAILING_JUNK = ".,;:!?)'\"»”’>*"


def extract_urls(text: str) -> tuple[str, ...]:
    """Extract candidate http/https URLs from HTML/markdown/plain text.

    Deterministic: returns a sorted, de-duplicated tuple. ``&amp;`` entities
    are unescaped so HTML-embedded URLs compare equal to their literal form.
    """

    if not isinstance(text, str) or not text:
        return ()
    found: set[str] = set()
    for match in _URL_PATTERN.findall(text.replace("&amp;", "&")):
        candidate = match.rstrip(_TRAILING_JUNK)
        if candidate:
            found.add(candidate)
    return tuple(sorted(found))


def select_urls(
    urls: Iterable[str],
    *,
    include_hosts: Sequence[str] | None = None,
    include_path_prefixes: Sequence[str] | None = None,
    include_pattern: str | None = None,
    exclude_pattern: str | None = None,
    limit: int | None = None,
) -> tuple[str, ...]:
    """Apply caller-provided (project-owned) filters to extracted URLs.

    ``include_pattern``/``exclude_pattern`` are caller-supplied regular
    expressions: the runtime provides the mechanism, the consuming project
    supplies the source-specific semantics. Deterministic sorted output.
    """

    include_re = re.compile(include_pattern) if include_pattern else None
    exclude_re = re.compile(exclude_pattern) if exclude_pattern else None
    hosts = {host.lower() for host in include_hosts} if include_hosts else None
    selected: set[str] = set()
    for url in urls:
        try:
            candidate = validate_public_url(url)
        except CaptureScopeError:
            continue
        parsed = urllib.parse.urlsplit(candidate)
        if hosts is not None and (parsed.hostname or "").lower() not in hosts:
            continue
        if include_path_prefixes is not None and not any(
            (parsed.path or "/").startswith(prefix) for prefix in include_path_prefixes
        ):
            continue
        if include_re is not None and not include_re.search(candidate):
            continue
        if exclude_re is not None and exclude_re.search(candidate):
            continue
        selected.add(candidate)
    ordered = tuple(sorted(selected))
    if limit is not None:
        if limit < 0:
            raise CapturePlanError("LIMIT_MUST_BE_NON_NEGATIVE")
        ordered = ordered[:limit]
    return ordered


# ---------------------------------------------------------------------------
# Bounded navigation plans. The runtime NEVER generates URLs from numeric
# ranges; every step is an explicit URL, seeds come from the task scope and
# all follow-up steps must replay discovered URLs with capture provenance.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PlanStep:
    step_index: int
    url: str
    step_kind: str
    discovered_from: str | None = None

    def __post_init__(self) -> None:
        if self.step_kind not in STEP_KINDS:
            raise CapturePlanError(f"UNKNOWN_STEP_KIND:{self.step_kind}")
        if self.step_index < 0:
            raise CapturePlanError("NEGATIVE_STEP_INDEX")

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "url": self.url,
            "step_kind": self.step_kind,
            "discovered_from": self.discovered_from,
        }


@dataclass(frozen=True)
class CapturePlan:
    """Deterministic bounded plan. Same inputs -> same plan_id and steps."""

    plan_kind: str
    scope: CaptureScope
    steps: tuple[PlanStep, ...]
    max_captures: int
    max_bytes_per_capture: int = MAX_CAPTURE_BYTES
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.plan_kind not in PLAN_KINDS:
            raise CapturePlanError(f"UNKNOWN_PLAN_KIND:{self.plan_kind}")
        if not self.steps:
            raise CapturePlanError("PLAN_REQUIRES_AT_LEAST_ONE_EXPLICIT_STEP")
        if not isinstance(self.max_captures, int) or self.max_captures < 1:
            raise CapturePlanError("PLAN_REQUIRES_POSITIVE_MAX_CAPTURES")
        if self.max_captures > MAX_PLAN_CAPTURES:
            raise CapturePlanError(
                f"PLAN_EXCEEDS_HARD_CAP:{self.max_captures}>{MAX_PLAN_CAPTURES}"
            )
        if len(self.steps) > self.max_captures:
            raise CapturePlanError("PLAN_HAS_MORE_STEPS_THAN_MAX_CAPTURES")
        if (
            not isinstance(self.max_bytes_per_capture, int)
            or self.max_bytes_per_capture < 1
            or self.max_bytes_per_capture > MAX_CAPTURE_BYTES
        ):
            raise CapturePlanError("INVALID_MAX_BYTES_PER_CAPTURE")
        seen_indexes: set[int] = set()
        seed_seen = False
        for step in self.steps:
            if step.step_index in seen_indexes:
                raise CapturePlanError(f"DUPLICATE_STEP_INDEX:{step.step_index}")
            seen_indexes.add(step.step_index)
            self.scope.require_allows(step.url)
            if step.step_kind == "SEED":
                if seed_seen:
                    raise CapturePlanError("PLAN_ALL_ONLY_ONE_SEED_STEP")
                seed_seen = True
            elif not step.discovered_from or not str(step.discovered_from).strip():
                # Fail closed against hidden-ID enumeration/brute force: a
                # non-seed step without discovery provenance is indistinguishable
                # from a fabricated numeric-ID probe, so it is rejected.
                raise CapturePlanError(
                    f"NON_SEED_STEP_REQUIRES_DISCOVERY_PROVENANCE:step={step.step_index}"
                )

    @property
    def plan_id(self) -> str:
        payload = _canonical_json(
            {
                "plan_kind": self.plan_kind,
                "scope": self.scope.to_dict(),
                "steps": [step.to_dict() for step in self.steps],
                "max_captures": self.max_captures,
                "max_bytes_per_capture": self.max_bytes_per_capture,
            }
        )
        return "plan-" + _sha256_bytes(payload.encode("utf-8"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "plan_kind": self.plan_kind,
            "scope": self.scope.to_dict(),
            "steps": [step.to_dict() for step in self.steps],
            "max_captures": self.max_captures,
            "max_bytes_per_capture": self.max_bytes_per_capture,
            "notes": list(self.notes),
        }


def _verify_discovery(
    urls: Sequence[str],
    discovery_text: str | None,
    discovery_capture_id: str | None,
) -> None:
    """When discovery text is supplied, every URL must literally appear in it.

    This mechanically blocks fabricated/enumerated URLs from entering a plan:
    a hidden record ID that was never exposed by a captured page cannot pass.
    """

    if discovery_text is None:
        return
    haystack = discovery_text.replace("&amp;", "&")
    for url in urls:
        if url.replace("&amp;", "&") not in haystack:
            raise CapturePlanError(f"URL_NOT_PRESENT_IN_DISCOVERY_CAPTURE:{url}")
    if not discovery_capture_id or not str(discovery_capture_id).strip():
        raise CapturePlanError("DISCOVERY_TEXT_REQUIRES_DISCOVERY_CAPTURE_ID")


def single_url_plan(
    url: str,
    scope: CaptureScope,
    *,
    max_bytes_per_capture: int = MAX_CAPTURE_BYTES,
    notes: Sequence[str] = (),
) -> CapturePlan:
    return CapturePlan(
        plan_kind=SINGLE_URL,
        scope=scope,
        steps=(PlanStep(step_index=0, url=url, step_kind="SEED"),),
        max_captures=1,
        max_bytes_per_capture=max_bytes_per_capture,
        notes=tuple(notes),
    )


def page_range_plan(
    page_urls: Sequence[str],
    scope: CaptureScope,
    *,
    discovered_from: str,
    discovery_text: str | None = None,
    max_captures: int | None = None,
    notes: Sequence[str] = (),
) -> CapturePlan:
    """Finite page range from EXPLICIT discovered pagination URLs.

    ``page_urls`` must already be literal URLs observed in public pagination
    links/parameters (the first entry may be the already-captured seed page).
    The runtime never computes page URLs from numeric ranges.
    """

    urls = tuple(page_urls)
    if len(urls) < 2:
        raise CapturePlanError("PAGE_RANGE_REQUIRES_SEED_PLUS_AT_LEAST_ONE_PAGE_URL")
    _verify_discovery(urls[1:], discovery_text, discovered_from)
    bound = max_captures if max_captures is not None else len(urls)
    steps = [PlanStep(step_index=0, url=urls[0], step_kind="SEED")]
    steps.extend(
        PlanStep(step_index=index, url=url, step_kind="PAGINATION", discovered_from=discovered_from)
        for index, url in enumerate(urls[1:], start=1)
    )
    return CapturePlan(
        plan_kind=PAGE_RANGE,
        scope=scope,
        steps=tuple(steps),
        max_captures=bound,
        notes=tuple(notes),
    )


def discovered_links_plan(
    urls: Sequence[str],
    scope: CaptureScope,
    *,
    discovered_from: str,
    discovery_text: str | None = None,
    step_kind: str = "RECORD_FOLLOWUP",
    max_captures: int | None = None,
    notes: Sequence[str] = (),
) -> CapturePlan:
    """Follow-up plan over explicit links discovered from one capture."""

    candidates = tuple(urls)
    if not candidates:
        raise CapturePlanError("DISCOVERED_LINKS_PLAN_REQUIRES_AT_LEAST_ONE_URL")
    if step_kind not in ("RECORD_FOLLOWUP", "ATTACHMENT"):
        raise CapturePlanError(f"INVALID_FOLLOWUP_STEP_KIND:{step_kind}")
    _verify_discovery(candidates, discovery_text, discovered_from)
    bound = max_captures if max_captures is not None else len(candidates)
    steps = tuple(
        PlanStep(step_index=index, url=url, step_kind=step_kind, discovered_from=discovered_from)
        for index, url in enumerate(candidates)
    )
    plan_kind = ATTACHMENT_DISCOVERY if step_kind == "ATTACHMENT" else DISCOVERED_LINKS
    return CapturePlan(
        plan_kind=plan_kind,
        scope=scope,
        steps=steps,
        max_captures=bound,
        notes=tuple(notes),
    )


# ---------------------------------------------------------------------------
# Checkpoint / resume metadata. Deterministic; timestamps are explicit inputs.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CheckpointState:
    plan_id: str
    scope_id: str
    completed: tuple[tuple[int, str], ...] = ()
    blocked: tuple[tuple[int, str], ...] = ()
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "scope_id": self.scope_id,
            "completed": {str(index): capture_id for index, capture_id in sorted(self.completed)},
            "blocked": {str(index): reason for index, reason in sorted(self.blocked)},
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CheckpointState":
        completed = tuple(
            (int(index), str(capture_id))
            for index, capture_id in sorted((payload.get("completed") or {}).items(), key=lambda kv: int(kv[0]))
        )
        blocked = tuple(
            (int(index), str(reason))
            for index, reason in sorted((payload.get("blocked") or {}).items(), key=lambda kv: int(kv[0]))
        )
        return cls(
            plan_id=str(payload["plan_id"]),
            scope_id=str(payload["scope_id"]),
            completed=completed,
            blocked=blocked,
            updated_at=payload.get("updated_at"),
        )


def build_checkpoint(
    plan: CapturePlan,
    captured: Mapping[int, str] | None = None,
    blocked: Mapping[int, str] | None = None,
    *,
    updated_at: str | None = None,
) -> CheckpointState:
    """Build checkpoint metadata for a plan. Deterministic given inputs."""

    captured_items = tuple(sorted((int(k), str(v)) for k, v in (captured or {}).items()))
    blocked_items = tuple(sorted((int(k), str(v)) for k, v in (blocked or {}).items()))
    valid_indexes = {step.step_index for step in plan.steps}
    for index, _ in captured_items + blocked_items:
        if index not in valid_indexes:
            raise CapturePlanError(f"CHECKPOINT_REFERENCES_UNKNOWN_STEP:{index}")
    overlap = {index for index, _ in captured_items} & {index for index, _ in blocked_items}
    if overlap:
        raise CapturePlanError(f"STEP_BOTH_CAPTURED_AND_BLOCKED:{sorted(overlap)}")
    return CheckpointState(
        plan_id=plan.plan_id,
        scope_id=plan.scope.scope_id,
        completed=captured_items,
        blocked=blocked_items,
        updated_at=updated_at,
    )


def pending_steps(plan: CapturePlan, checkpoint: CheckpointState) -> tuple[PlanStep, ...]:
    """Steps that remain to be executed. Deterministic, index-ordered."""

    if checkpoint.plan_id != plan.plan_id:
        raise CapturePlanError("CHECKPOINT_DOES_NOT_MATCH_PLAN")
    settled = {index for index, _ in checkpoint.completed}
    return tuple(step for step in plan.steps if step.step_index not in settled)


def resume_plan(plan: CapturePlan, checkpoint: CheckpointState) -> CapturePlan:
    """Derived bounded plan containing only the pending steps (same scope)."""

    remaining = pending_steps(plan, checkpoint)
    if not remaining:
        raise CapturePlanError("NOTHING_TO_RESUME")
    return CapturePlan(
        plan_kind=plan.plan_kind,
        scope=plan.scope,
        steps=remaining,
        max_captures=max(1, min(len(remaining), plan.max_captures)),
        max_bytes_per_capture=plan.max_bytes_per_capture,
        notes=tuple(plan.notes) + (f"RESUMED_FROM_CHECKPOINT:{checkpoint.plan_id}",),
    )


# ---------------------------------------------------------------------------
# Small evidence writer (files + canonical JSON). No database, no queue.
# ---------------------------------------------------------------------------


def write_capture(
    directory: Path,
    capture: Capture,
    *,
    extension: str = ".txt",
) -> CaptureRecord:
    """Persist captured bytes under ``<capture_id><extension>``; return record."""

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    relative = f"{capture.record.capture_id}{extension}"
    (directory / relative).write_bytes(capture.content)
    return replace(capture.record, content_path=relative)


def write_canonical_json(path: Path, payload: Mapping[str, Any]) -> str:
    """Write deterministic canonical JSON; return its sha256."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")
    return _sha256_bytes(text.encode("utf-8"))


def _validate_module_contracts() -> None:
    """Import-time self-check: vocabularies and policy order are consistent."""

    if tuple(TRANSPORT_POLICY_ORDER) != (PLAIN_HTTP, EXECUTOR_TEXT, EXECUTOR_BROWSER):
        raise WebCaptureError("TRANSPORT_POLICY_ORDER_DRIFTED")
    if EXECUTOR_BROWSER not in TRANSPORT_POLICY_ORDER:
        raise WebCaptureError("BROWSER_LANE_MUST_REMAIN_OPTIONAL_LAST")
    for field_name in _REQUIRED_RECORD_FIELDS:
        if field_name not in CaptureRecord.__dataclass_fields__:
            raise WebCaptureError(f"CAPTURE_CONTRACT_MISSING_FIELD:{field_name}")
    if not RELATED_CAPABILITY_IDS:
        raise WebCaptureError("EXISTING_WEB_FAMILY_NOT_REUSED")


_validate_module_contracts()


__all__ = [
    "ATTACHMENT_DISCOVERY",
    "BROWSER_DOCUMENT",
    "CaptureAuthorizationError",
    "CapturePlan",
    "CapturePlanError",
    "CaptureRecord",
    "CaptureScope",
    "CaptureScopeError",
    "CaptureTransportError",
    "Capture",
    "CheckpointState",
    "DISCOVERED_LINKS",
    "EXECUTOR_BROWSER",
    "EXECUTOR_TEXT",
    "ExecutorBrowserTransport",
    "ExecutorTextTransport",
    "HONEST_USER_AGENT",
    "LIVE_CAPTURE_EXECUTION_CLASS",
    "MAX_CAPTURE_BYTES",
    "MAX_PLAN_CAPTURES",
    "NETWORK_RESPONSE",
    "PAGE_RANGE",
    "PLAIN_HTTP",
    "PlanStep",
    "PlainHttpTransport",
    "RAW_BYTES",
    "RELATED_CAPABILITY_IDS",
    "RECORDED_RESULT",
    "REPRESENTATIONS",
    "SINGLE_URL",
    "STEP_KINDS",
    "STEP_STATUSES",
    "TEXT_CAPTURE",
    "TRANSPORT_KINDS",
    "TRANSPORT_POLICY_ORDER",
    "TransportResult",
    "WEB_CAPTURE_RUNTIME_MODULE",
    "WEB_CAPTURE_RUNTIME_SCHEMA",
    "WebCaptureError",
    "build_checkpoint",
    "capture_with_policy",
    "compute_capture_id",
    "discovered_links_plan",
    "extract_urls",
    "normalize_capture",
    "page_range_plan",
    "pending_steps",
    "resume_plan",
    "select_urls",
    "single_url_plan",
    "validate_public_url",
    "write_canonical_json",
    "write_capture",
]
