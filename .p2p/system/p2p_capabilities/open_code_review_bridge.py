"""Bounded OpenCodeReview delegation bridge for supplemental review coverage.

P2P already has authoritative acceptance surfaces: Supreme Law, task contract,
Shield, native code-impact evidence, project tests and Control Tower review.
This module does not replace any of them.

It exposes only Alibaba OpenCodeReview's delegation scaffold:

- deterministic reviewable-file selection (`ocr delegate preview`);
- deterministic per-file rule resolution (`ocr delegate rule`).

The host agent (Arena/Codex/Claude/etc.) still performs the semantic review.
No OCR-managed LLM call is allowed here, no API key is configured, no files are
mutated, and no review finding becomes acceptance authority by itself.

Pinned upstream research target:
  alibaba/open-code-review v1.12.4
  commit f1101fd7f51304c82e4a4f292bbee88aea0823cf

The bridge is an OPTIONAL_EXTENSION, intended for a documented review gap such
as a large/complex diff, repeated repair loop, uncertain changed-file coverage,
or line/rule targeting that native P2P evidence does not establish by itself.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


UPSTREAM_PIN = "alibaba/open-code-review@v1.12.4:f1101fd7f51304c82e4a4f292bbee88aea0823cf"
DEFAULT_BINARY = "ocr"
MIN_VERSION = (1, 12, 4)
MAX_OUTPUT_BYTES = 5_000_000
MAX_BACKGROUND_CHARS = 8_000
MAX_EXCLUDES = 64
MIN_GAP_REASON_CHARS = 12
CLASSIFICATION = "NON_AUTHORITATIVE_REVIEW_SCAFFOLD"
ACTIVATION_POLICY = "OPTIONAL_EXTENSION_AFTER_DOCUMENTED_REVIEW_GAP"


class OpenCodeReviewBridgeError(RuntimeError):
    """Base class for bounded OCR bridge failures."""


class OpenCodeReviewUnavailable(OpenCodeReviewBridgeError):
    """OCR is not installed or cannot be version-verified."""


class UnsafeOpenCodeReviewRequest(OpenCodeReviewBridgeError):
    """The requested OCR operation exceeds the bounded delegation surface."""


class OpenCodeReviewExecutionFailed(OpenCodeReviewBridgeError):
    """The OCR process failed or returned invalid machine-readable output."""


@dataclass(frozen=True)
class OCRInvocation:
    argv: tuple[str, ...]
    cwd: str
    timeout_seconds: int
    gap_reason: str


Runner = Callable[[OCRInvocation], subprocess.CompletedProcess[str]]
Which = Callable[[str], str | None]


def _default_runner(invocation: OCRInvocation) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(invocation.argv),
        cwd=invocation.cwd,
        capture_output=True,
        text=True,
        timeout=invocation.timeout_seconds,
        check=False,
    )


def _clean_text(value: object, *, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:limit]


def _validated_gap_reason(reason: str) -> str:
    cleaned = _clean_text(reason, limit=1024)
    if len(cleaned) < MIN_GAP_REASON_CHARS:
        raise UnsafeOpenCodeReviewRequest("OCR_REVIEW_GAP_REASON_REQUIRED")
    return cleaned


def _validated_repo_root(repo_root: str | Path) -> str:
    path = Path(repo_root).resolve()
    if not path.is_dir():
        raise UnsafeOpenCodeReviewRequest("OCR_REPO_ROOT_INVALID")
    return str(path)


def _parse_version(text: str) -> tuple[int, int, int]:
    match = re.search(r"(?:open-code-review|opencodereview)?\s*v?(\d+)\.(\d+)\.(\d+)", text, re.I)
    if not match:
        match = re.search(r"v?(\d+)\.(\d+)\.(\d+)", text)
    if not match:
        raise OpenCodeReviewUnavailable("OCR_VERSION_UNPARSEABLE")
    return tuple(int(x) for x in match.groups())


def _json_payload(result: subprocess.CompletedProcess[str]) -> Any:
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()[:1000]
        raise OpenCodeReviewExecutionFailed(
            f"OCR_COMMAND_FAILED:{result.returncode}:{stderr}"
        )
    stdout = result.stdout or ""
    if len(stdout.encode("utf-8")) > MAX_OUTPUT_BYTES:
        raise OpenCodeReviewExecutionFailed("OCR_OUTPUT_TOO_LARGE")
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise OpenCodeReviewExecutionFailed("OCR_JSON_INVALID") from exc


class OpenCodeReviewDelegationBridge:
    """Read-only deterministic OCR scaffold; host agent remains the reviewer."""

    def __init__(
        self,
        *,
        binary: str = DEFAULT_BINARY,
        runner: Runner | None = None,
        which: Which | None = None,
    ) -> None:
        self.binary = binary
        self._runner = runner or _default_runner
        self._which = which or shutil.which

    def _ensure_available(self, *, repo_root: str, gap_reason: str) -> dict[str, Any]:
        if not self._which(self.binary):
            raise OpenCodeReviewUnavailable("OCR_NOT_INSTALLED")
        invocation = OCRInvocation(
            argv=(self.binary, "version"),
            cwd=repo_root,
            timeout_seconds=15,
            gap_reason=gap_reason,
        )
        result = self._runner(invocation)
        if result.returncode != 0:
            raise OpenCodeReviewUnavailable("OCR_VERSION_CHECK_FAILED")
        version_text = (result.stdout or result.stderr or "").strip()
        version = _parse_version(version_text)
        if version < MIN_VERSION:
            raise OpenCodeReviewUnavailable(
                "OCR_VERSION_TOO_OLD:" + ".".join(map(str, version))
            )
        return {
            "version": ".".join(map(str, version)),
            "upstream_pin": UPSTREAM_PIN,
        }

    def build_preview_invocation(
        self,
        *,
        repo_root: str | Path,
        gap_reason: str,
        from_ref: str | None = None,
        to_ref: str | None = None,
        commit: str | None = None,
        excludes: Sequence[str] = (),
        background: str | None = None,
        timeout_seconds: int = 60,
    ) -> OCRInvocation:
        root = _validated_repo_root(repo_root)
        reason = _validated_gap_reason(gap_reason)
        if not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= 300:
            raise UnsafeOpenCodeReviewRequest("OCR_TIMEOUT_OUT_OF_RANGE")
        if commit and (from_ref or to_ref):
            raise UnsafeOpenCodeReviewRequest("OCR_TARGET_MODE_CONFLICT")
        if bool(from_ref) ^ bool(to_ref):
            raise UnsafeOpenCodeReviewRequest("OCR_RANGE_REQUIRES_FROM_AND_TO")
        if len(excludes) > MAX_EXCLUDES:
            raise UnsafeOpenCodeReviewRequest("OCR_TOO_MANY_EXCLUDES")

        argv: list[str] = [self.binary, "delegate", "preview", "--format", "json", "--repo", root]
        if commit:
            argv += ["--commit", _clean_text(commit, limit=256)]
        elif from_ref and to_ref:
            argv += ["--from", _clean_text(from_ref, limit=256), "--to", _clean_text(to_ref, limit=256)]
        if excludes:
            cleaned = [_clean_text(x, limit=512) for x in excludes if _clean_text(x, limit=512)]
            if cleaned:
                argv += ["--exclude", ",".join(cleaned)]
        if background:
            cleaned_background = _clean_text(background, limit=MAX_BACKGROUND_CHARS + 1)
            if len(cleaned_background) > MAX_BACKGROUND_CHARS:
                raise UnsafeOpenCodeReviewRequest("OCR_BACKGROUND_TOO_LARGE")
            argv += ["--background", cleaned_background]
        return OCRInvocation(tuple(argv), root, timeout_seconds, reason)

    def preview(self, **kwargs: Any) -> dict[str, Any]:
        invocation = self.build_preview_invocation(**kwargs)
        availability = self._ensure_available(
            repo_root=invocation.cwd,
            gap_reason=invocation.gap_reason,
        )
        payload = _json_payload(self._runner(invocation))
        if not isinstance(payload, Mapping):
            raise OpenCodeReviewExecutionFailed("OCR_PREVIEW_SHAPE_INVALID")
        files = payload.get("reviewable_files")
        if not isinstance(files, list):
            raise OpenCodeReviewExecutionFailed("OCR_REVIEWABLE_FILES_MISSING")
        normalized_files: list[dict[str, Any]] = []
        for raw in files:
            if not isinstance(raw, Mapping):
                raise OpenCodeReviewExecutionFailed("OCR_REVIEWABLE_FILE_INVALID")
            path = str(raw.get("path") or "").strip()
            status = str(raw.get("status") or "").strip()
            if not path or not status:
                raise OpenCodeReviewExecutionFailed("OCR_REVIEWABLE_FILE_IDENTITY_INVALID")
            normalized_files.append(dict(raw))
        return {
            "classification": CLASSIFICATION,
            "activation_policy": ACTIVATION_POLICY,
            "authority": "NONE",
            "acceptance_authority": False,
            "permission_effect": "NONE",
            "host_agent_must_review": True,
            "native_shield_still_required": True,
            "gap_reason": invocation.gap_reason,
            "availability": availability,
            "reviewable_files": normalized_files,
            "excluded_files": payload.get("excluded_files") or [],
            "mode": payload.get("mode"),
            "ref_metadata": {
                key: payload.get(key)
                for key in ("from", "to", "commit", "merge_base")
                if payload.get(key) is not None
            },
            "raw": dict(payload),
        }

    def rules(
        self,
        *,
        repo_root: str | Path,
        paths: Sequence[str],
        gap_reason: str,
        timeout_seconds: int = 60,
    ) -> dict[str, Any]:
        root = _validated_repo_root(repo_root)
        reason = _validated_gap_reason(gap_reason)
        if not paths:
            raise UnsafeOpenCodeReviewRequest("OCR_RULE_PATHS_REQUIRED")
        if len(paths) > 512:
            raise UnsafeOpenCodeReviewRequest("OCR_RULE_PATHS_TOO_MANY")
        if not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= 300:
            raise UnsafeOpenCodeReviewRequest("OCR_TIMEOUT_OUT_OF_RANGE")
        clean_paths = [_clean_text(path, limit=2048) for path in paths]
        if any(not path for path in clean_paths):
            raise UnsafeOpenCodeReviewRequest("OCR_RULE_PATH_INVALID")
        self._ensure_available(repo_root=root, gap_reason=reason)
        invocation = OCRInvocation(
            argv=(self.binary, "delegate", "rule", "--format", "json", "--repo", root, *clean_paths),
            cwd=root,
            timeout_seconds=timeout_seconds,
            gap_reason=reason,
        )
        payload = _json_payload(self._runner(invocation))
        if not isinstance(payload, (Mapping, list)):
            raise OpenCodeReviewExecutionFailed("OCR_RULE_SHAPE_INVALID")
        return {
            "classification": CLASSIFICATION,
            "activation_policy": ACTIVATION_POLICY,
            "authority": "NONE",
            "acceptance_authority": False,
            "permission_effect": "NONE",
            "gap_reason": reason,
            "paths": clean_paths,
            "rules": payload,
        }


def build_host_review_contract(preview: Mapping[str, Any], rules: Mapping[str, Any]) -> dict[str, Any]:
    """Turn OCR scaffold output into a host-agent coverage contract.

    The contract deliberately contains no findings. It makes coverage explicit:
    every `(path, status)` from OCR preview must end as REVIEWED or SKIPPED with
    a concrete reason, and review findings still require independent validation.
    """

    files = preview.get("reviewable_files") or []
    if not isinstance(files, list):
        raise UnsafeOpenCodeReviewRequest("OCR_CONTRACT_PREVIEW_INVALID")
    checklist: list[dict[str, Any]] = []
    for raw in files:
        if not isinstance(raw, Mapping):
            raise UnsafeOpenCodeReviewRequest("OCR_CONTRACT_FILE_INVALID")
        path = str(raw.get("path") or "").strip()
        status = str(raw.get("status") or "").strip()
        if not path or not status:
            raise UnsafeOpenCodeReviewRequest("OCR_CONTRACT_FILE_IDENTITY_INVALID")
        checklist.append({
            "path": path,
            "status": status,
            "required_disposition": "REVIEWED_OR_SKIPPED_WITH_REASON",
        })
    return {
        "schema": "p2p-open-code-review-host-contract/1",
        "classification": CLASSIFICATION,
        "authority": "NONE",
        "acceptance_authority": False,
        "permission_effect": "NONE",
        "coverage_required": True,
        "total_files": len(checklist),
        "checklist": checklist,
        "rules": rules.get("rules"),
        "finding_policy": {
            "critical_high": "REPORT_AND_CHALLENGE",
            "medium": "REPORT_WITH_CONTEXT_AND_VALIDATE",
            "low": "DISCARD_UNLESS_MATERIALLY_USEFUL",
        },
        "completion_invariant": "EVERY_PREVIEWED_FILE_ACCOUNTED_FOR",
        "shield_and_acceptance_replay_still_required": True,
    }
