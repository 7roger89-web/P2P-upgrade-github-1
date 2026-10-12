"""P2P Skill Consumption Wire — metadata discovery -> bounded match -> exact load.

This module is not a router.  It composes the canonical capability registry,
the existing single router, and exact repo files into one source-bound handoff.
No skill content is read during DISCOVERY; only selected SKILL.md entrypoints
are loaded.  Skills never widen task permissions or authority.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import subprocess
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:  # package import in normal P2P runtime
    from .host_executor import SUPPORTED, HostCapabilityProfile, HostExecutorContractError
    from .host_selection import AVAILABLE, DISCOVERY_SCHEMA, HostDiscoveryRecord
    from .model import CapabilityManifest, load_registry
    from .routing import classify_capabilities
except ImportError:  # legacy focused tests import modules from this directory
    from host_executor import SUPPORTED, HostCapabilityProfile, HostExecutorContractError
    from host_selection import AVAILABLE, DISCOVERY_SCHEMA, HostDiscoveryRecord
    from model import CapabilityManifest, load_registry
    from routing import classify_capabilities


HANDOFF_SCHEMA = "p2p-skill-handoff/1"
RECEIPT_SCHEMA = "p2p-skill-consumption-receipt/1"
FANOUT_INHERITANCE_SCHEMA = "p2p-skill-fanout-inheritance/1"
MAX_SELECTED_SKILLS = 3
HOST_MODES = {
    "ARENA": "ARENA_EXACT_REPO_READ",
    "CODEX": "CODEX_NATIVE_PROJECT_SKILL",
}
GENERIC_PROMPT_ONLY_MODE = "GENERIC_PROMPT_ONLY"
GENERIC_REPO_READ_MODE = "GENERIC_EXACT_REPO_READ"
PROMPT_ONLY_CAPABILITY = "PROMPT_ONLY"
PROMPT_ONLY_MAX_PROMPT_CHARS = 32000
INLINE_PERMITTED_TRUST_LEVELS = frozenset({"PUBLIC"})
INLINE_SHAREABLE_LICENSE_KINDS = frozenset({
    "MIT",
    "APACHE-2.0",
    "BSD-2-CLAUSE",
    "BSD-3-CLAUSE",
    "CC0",
    "PUBLIC",
    "UNLICENSE",
})
_CLASS_RANK = {"PRIMARY": 3, "SECONDARY": 2, "SUPPORTING": 1}


class SkillConsumptionError(ValueError):
    pass



TRUST_EVIDENCE_SCHEMA = "p2p-generic-repo-read-evidence/1"
TRUST_OIDC_ISSUER = "https://token.actions.githubusercontent.com"
TRUST_OIDC_DISCOVERY_URL = (
    TRUST_OIDC_ISSUER + "/.well-known/openid-configuration"
)
TRUST_OIDC_AUDIENCE_PREFIX = "p2p-generic-repo-read:"
TRUST_MAX_EVIDENCE_BYTES = 128 * 1024
TRUST_MAX_TOKEN_CHARS = 32 * 1024
TRUST_MAX_CLOCK_SKEW_SECONDS = 60
TRUST_MAX_TOKEN_LIFETIME_SECONDS = 20 * 60


class TrustedRepoReadEvidenceError(ValueError):
    """Fail-closed external repo-read evidence validation error."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _trusted_reject_duplicates(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise TrustedRepoReadEvidenceError(
                "TRUST_EVIDENCE_JSON_DUPLICATE_KEY"
            )
        result[key] = value
    return result


def _trusted_json_object(
    raw: bytes | str,
    code: str,
) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
        value = json.loads(
            text,
            object_pairs_hook=_trusted_reject_duplicates,
        )
    except TrustedRepoReadEvidenceError:
        raise
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ) as exc:
        raise TrustedRepoReadEvidenceError(code) from exc
    if not isinstance(value, dict):
        raise TrustedRepoReadEvidenceError(code)
    return value


def _trusted_b64url_decode(value: str, code: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise TrustedRepoReadEvidenceError(code)
    try:
        return base64.urlsafe_b64decode(
            value + "=" * (-len(value) % 4)
        )
    except (ValueError, TypeError) as exc:
        raise TrustedRepoReadEvidenceError(code) from exc


def _trusted_b64url_int(value: Any, code: str) -> int:
    if not isinstance(value, str):
        raise TrustedRepoReadEvidenceError(code)
    raw = _trusted_b64url_decode(value, code)
    if not raw:
        raise TrustedRepoReadEvidenceError(code)
    return int.from_bytes(raw, "big")


def _trusted_hex64(value: Any, code: str) -> str:
    text = str(value or "").strip().lower()
    if (
        len(text) != 64
        or any(ch not in "0123456789abcdef" for ch in text)
    ):
        raise TrustedRepoReadEvidenceError(code)
    return text


def _trusted_integer_claim(
    claims: Mapping[str, Any],
    name: str,
) -> int:
    value = claims.get(name)
    if isinstance(value, bool) or not isinstance(value, int):
        raise TrustedRepoReadEvidenceError(
            f"TRUST_OIDC_{name.upper()}_INVALID"
        )
    return value


def _trusted_fetch_json(url: str) -> dict[str, Any]:
    parsed = urllib.parse.urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "token.actions.githubusercontent.com"
    ):
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_ENDPOINT_INVALID"
        )
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "p2p-issue-333/1",
        },
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=15,
        ) as response:
            raw = response.read(256 * 1024 + 1)
    except Exception as exc:
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_PROVIDER_UNAVAILABLE"
        ) from exc
    if len(raw) > 256 * 1024:
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_PROVIDER_RESPONSE_TOO_LARGE"
        )
    return _trusted_json_object(
        raw,
        "TRUST_OIDC_PROVIDER_JSON_INVALID",
    )


def _verify_trusted_repo_read_rs256(
    token: str,
) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_TOKEN_INVALID"
        )
    header64, payload64, signature64 = parts
    header = _trusted_json_object(
        _trusted_b64url_decode(
            header64,
            "TRUST_OIDC_HEADER_INVALID",
        ),
        "TRUST_OIDC_HEADER_INVALID",
    )
    claims = _trusted_json_object(
        _trusted_b64url_decode(
            payload64,
            "TRUST_OIDC_CLAIMS_INVALID",
        ),
        "TRUST_OIDC_CLAIMS_INVALID",
    )
    if header.get("alg") != "RS256":
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_ALG_INVALID"
        )
    kid = header.get("kid")
    if (
        not isinstance(kid, str)
        or not kid
        or len(kid) > 256
    ):
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_KID_INVALID"
        )

    discovery = _trusted_fetch_json(
        TRUST_OIDC_DISCOVERY_URL
    )
    if discovery.get("issuer") != TRUST_OIDC_ISSUER:
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_ISSUER_DISCOVERY_MISMATCH"
        )
    jwks_uri = discovery.get("jwks_uri")
    if not isinstance(jwks_uri, str):
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_JWKS_URI_INVALID"
        )
    jwks = _trusted_fetch_json(jwks_uri)
    keys = jwks.get("keys")
    if not isinstance(keys, list):
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_JWKS_INVALID"
        )
    key = next(
        (
            candidate
            for candidate in keys
            if isinstance(candidate, Mapping)
            and candidate.get("kid") == kid
        ),
        None,
    )
    if key is None:
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_SIGNING_KEY_NOT_FOUND"
        )
    if (
        key.get("kty") != "RSA"
        or key.get("use") not in (None, "sig")
    ):
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_SIGNING_KEY_INVALID"
        )
    if key.get("alg") not in (None, "RS256"):
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_SIGNING_KEY_ALG_INVALID"
        )

    modulus = _trusted_b64url_int(
        key.get("n"),
        "TRUST_OIDC_RSA_MODULUS_INVALID",
    )
    exponent = _trusted_b64url_int(
        key.get("e"),
        "TRUST_OIDC_RSA_EXPONENT_INVALID",
    )
    if (
        modulus.bit_length() < 2048
        or exponent < 3
        or exponent % 2 == 0
    ):
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_RSA_KEY_INVALID"
        )
    signature = _trusted_b64url_decode(
        signature64,
        "TRUST_OIDC_SIGNATURE_INVALID",
    )
    key_bytes = (modulus.bit_length() + 7) // 8
    if len(signature) != key_bytes:
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_SIGNATURE_INVALID"
        )
    decoded = pow(
        int.from_bytes(signature, "big"),
        exponent,
        modulus,
    ).to_bytes(key_bytes, "big")
    digest = hashlib.sha256(
        f"{header64}.{payload64}".encode("ascii")
    ).digest()
    digest_info = (
        bytes.fromhex(
            "3031300d060960864801650304020105000420"
        )
        + digest
    )
    padding_len = key_bytes - len(digest_info) - 3
    if padding_len < 8:
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_SIGNATURE_INVALID"
        )
    expected = (
        b"\x00\x01"
        + (b"\xff" * padding_len)
        + b"\x00"
        + digest_info
    )
    if not hmac.compare_digest(decoded, expected):
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_SIGNATURE_INVALID"
        )
    return claims


def _trusted_exact_string(
    value: Any,
    expected: str,
    code: str,
) -> None:
    if not isinstance(value, str) or value != expected:
        raise TrustedRepoReadEvidenceError(code)


def _trusted_exact_bool(
    value: Any,
    expected: bool,
    code: str,
) -> None:
    if not isinstance(value, bool) or value is not expected:
        raise TrustedRepoReadEvidenceError(code)


def verify_github_oidc_repo_read_evidence(
    evidence_bytes: bytes,
    oidc_token: str,
    *,
    expected_repository: str,
    expected_revision: str,
    expected_workflow_path: str,
    expected_host: str,
    expected_task_sha256: str,
    expected_handoff_fingerprint: str,
    expected_skill_paths: Mapping[str, str],
    expected_skill_hashes: Mapping[str, str],
) -> dict[str, Any]:
    """Verify GitHub-signed evidence for one exact external skill read."""
    if (
        not isinstance(evidence_bytes, bytes)
        or not evidence_bytes
    ):
        raise TrustedRepoReadEvidenceError(
            "TRUST_EVIDENCE_REQUIRED"
        )
    if len(evidence_bytes) > TRUST_MAX_EVIDENCE_BYTES:
        raise TrustedRepoReadEvidenceError(
            "TRUST_EVIDENCE_TOO_LARGE"
        )
    if (
        not isinstance(oidc_token, str)
        or not oidc_token.strip()
    ):
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_TOKEN_REQUIRED"
        )
    token = oidc_token.strip()
    if len(token) > TRUST_MAX_TOKEN_CHARS:
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_TOKEN_TOO_LARGE"
        )

    repository = str(
        expected_repository or ""
    ).strip().lower()
    revision = str(
        expected_revision or ""
    ).strip().lower()
    host = str(
        expected_host or ""
    ).strip().upper()
    workflow_path = str(
        expected_workflow_path or ""
    ).strip()
    if not repository or "/" not in repository:
        raise TrustedRepoReadEvidenceError(
            "TRUST_EXPECTED_REPOSITORY_INVALID"
        )
    if (
        len(revision) != 40
        or any(
            ch not in "0123456789abcdef"
            for ch in revision
        )
    ):
        raise TrustedRepoReadEvidenceError(
            "TRUST_EXPECTED_REVISION_INVALID"
        )
    if (
        not workflow_path.startswith(
            ".github/workflows/"
        )
        or ".." in workflow_path.split("/")
    ):
        raise TrustedRepoReadEvidenceError(
            "TRUST_EXPECTED_WORKFLOW_INVALID"
        )
    if not host:
        raise TrustedRepoReadEvidenceError(
            "TRUST_EXPECTED_HOST_INVALID"
        )
    task_sha = _trusted_hex64(
        expected_task_sha256,
        "TRUST_EXPECTED_TASK_SHA_INVALID",
    )
    handoff_fp = _trusted_hex64(
        expected_handoff_fingerprint,
        "TRUST_EXPECTED_HANDOFF_FINGERPRINT_INVALID",
    )
    skill_paths = {
        str(key): str(value)
        for key, value
        in expected_skill_paths.items()
    }
    skill_hashes = {
        str(key): _trusted_hex64(
            value,
            f"TRUST_EXPECTED_SKILL_HASH_INVALID:{key}",
        )
        for key, value
        in expected_skill_hashes.items()
    }
    if (
        not skill_paths
        or set(skill_paths) != set(skill_hashes)
    ):
        raise TrustedRepoReadEvidenceError(
            "TRUST_EXPECTED_SKILL_SET_INVALID"
        )

    evidence_sha = hashlib.sha256(
        evidence_bytes
    ).hexdigest()
    evidence = _trusted_json_object(
        evidence_bytes,
        "TRUST_EVIDENCE_JSON_INVALID",
    )
    claims = _verify_trusted_repo_read_rs256(
        token
    )

    expected_audience = (
        TRUST_OIDC_AUDIENCE_PREFIX
        + evidence_sha
    )
    audience = claims.get("aud")
    audience_ok = (
        audience == expected_audience
        or (
            isinstance(audience, list)
            and all(
                isinstance(item, str)
                for item in audience
            )
            and expected_audience in audience
        )
    )
    if not audience_ok:
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_AUDIENCE_MISMATCH"
        )
    _trusted_exact_string(
        claims.get("iss"),
        TRUST_OIDC_ISSUER,
        "TRUST_OIDC_ISSUER_MISMATCH",
    )
    _trusted_exact_string(
        str(
            claims.get("repository") or ""
        ).lower(),
        repository,
        "TRUST_OIDC_REPOSITORY_MISMATCH",
    )
    _trusted_exact_string(
        str(
            claims.get("workflow_sha") or ""
        ).lower(),
        revision,
        "TRUST_OIDC_WORKFLOW_SHA_MISMATCH",
    )
    _trusted_exact_string(
        claims.get("runner_environment"),
        "github-hosted",
        "TRUST_OIDC_RUNNER_ENVIRONMENT_INVALID",
    )
    subject = claims.get("sub")
    if (
        not isinstance(subject, str)
        or not subject.startswith(
            f"repo:{repository}:"
        )
    ):
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_SUBJECT_MISMATCH"
        )
    workflow_ref = claims.get("workflow_ref")
    if not isinstance(workflow_ref, str):
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_WORKFLOW_REF_INVALID"
        )
    expected_workflow_prefix = (
        f"{repository}/{workflow_path}@"
    )
    if not workflow_ref.lower().startswith(
        expected_workflow_prefix.lower()
    ):
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_WORKFLOW_REF_MISMATCH"
        )
    jti = claims.get("jti")
    if (
        not isinstance(jti, str)
        or not jti.strip()
        or len(jti) > 256
    ):
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_JTI_INVALID"
        )

    now = int(time.time())
    issued_at = _trusted_integer_claim(
        claims,
        "iat",
    )
    not_before = _trusted_integer_claim(
        claims,
        "nbf",
    )
    expires_at = _trusted_integer_claim(
        claims,
        "exp",
    )
    if (
        issued_at
        > now + TRUST_MAX_CLOCK_SKEW_SECONDS
        or not_before
        > now + TRUST_MAX_CLOCK_SKEW_SECONDS
    ):
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_TOKEN_FROM_FUTURE"
        )
    if (
        expires_at
        < now - TRUST_MAX_CLOCK_SKEW_SECONDS
        or expires_at <= issued_at
    ):
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_TOKEN_EXPIRED"
        )
    if (
        expires_at - issued_at
        > TRUST_MAX_TOKEN_LIFETIME_SECONDS
    ):
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_TOKEN_LIFETIME_INVALID"
        )

    if evidence.get("schema") != TRUST_EVIDENCE_SCHEMA:
        raise TrustedRepoReadEvidenceError(
            "TRUST_EVIDENCE_SCHEMA_INVALID"
        )
    _trusted_exact_string(
        str(
            evidence.get("repository") or ""
        ).lower(),
        repository,
        "TRUST_EVIDENCE_REPOSITORY_MISMATCH",
    )
    _trusted_exact_string(
        str(
            evidence.get("revision") or ""
        ).lower(),
        revision,
        "TRUST_EVIDENCE_REVISION_MISMATCH",
    )
    _trusted_exact_string(
        evidence.get("workflow_ref"),
        workflow_ref,
        "TRUST_EVIDENCE_WORKFLOW_MISMATCH",
    )
    _trusted_exact_string(
        str(evidence.get("run_id") or ""),
        str(claims.get("run_id") or ""),
        "TRUST_EVIDENCE_RUN_ID_MISMATCH",
    )
    run_attempt = evidence.get("run_attempt")
    claim_attempt = claims.get("run_attempt")
    if (
        isinstance(run_attempt, bool)
        or not isinstance(run_attempt, int)
    ):
        raise TrustedRepoReadEvidenceError(
            "TRUST_EVIDENCE_RUN_ATTEMPT_INVALID"
        )
    if str(run_attempt) != str(
        claim_attempt or ""
    ):
        raise TrustedRepoReadEvidenceError(
            "TRUST_EVIDENCE_RUN_ATTEMPT_MISMATCH"
        )
    _trusted_exact_string(
        evidence.get("runner_environment"),
        "github-hosted",
        "TRUST_EVIDENCE_RUNNER_ENVIRONMENT_INVALID",
    )
    _trusted_exact_string(
        str(
            evidence.get("actor") or ""
        ).upper(),
        host,
        "TRUST_EVIDENCE_HOST_MISMATCH",
    )
    _trusted_exact_bool(
        evidence.get("arena"),
        False,
        "TRUST_EVIDENCE_ARENA_INVALID",
    )
    _trusted_exact_bool(
        evidence.get("codex"),
        False,
        "TRUST_EVIDENCE_CODEX_INVALID",
    )
    _trusted_exact_bool(
        evidence.get("skill_applied"),
        True,
        "TRUST_EVIDENCE_SKILL_NOT_APPLIED",
    )
    _trusted_exact_bool(
        evidence.get("tool_trace_validated"),
        True,
        "TRUST_EVIDENCE_TOOL_TRACE_NOT_VALIDATED",
    )
    _trusted_exact_string(
        str(
            evidence.get(
                "permission_widened"
            )
            or ""
        ).upper(),
        "NO",
        "TRUST_EVIDENCE_PERMISSION_WIDENED",
    )
    _trusted_exact_string(
        str(
            evidence.get("task_sha256")
            or ""
        ).lower(),
        task_sha,
        "TRUST_EVIDENCE_TASK_MISMATCH",
    )
    _trusted_exact_string(
        str(
            evidence.get(
                "handoff_fingerprint"
            )
            or ""
        ).lower(),
        handoff_fp,
        "TRUST_EVIDENCE_HANDOFF_MISMATCH",
    )
    _trusted_hex64(
        evidence.get("result_sha256"),
        "TRUST_EVIDENCE_RESULT_SHA_INVALID",
    )
    _trusted_hex64(
        evidence.get("transcript_sha256"),
        "TRUST_EVIDENCE_TRANSCRIPT_SHA_INVALID",
    )

    receipt = evidence.get(
        "skill_consumption_receipt"
    )
    if not isinstance(receipt, Mapping):
        raise TrustedRepoReadEvidenceError(
            "TRUST_EVIDENCE_RECEIPT_MISSING"
        )
    if (
        receipt.get("schema")
        != RECEIPT_SCHEMA
    ):
        raise TrustedRepoReadEvidenceError(
            "TRUST_EVIDENCE_RECEIPT_SCHEMA_INVALID"
        )
    selected = receipt.get(
        "SKILLS_SELECTED"
    )
    if (
        not isinstance(selected, list)
        or selected != list(skill_paths)
    ):
        raise TrustedRepoReadEvidenceError(
            "TRUST_EVIDENCE_SKILL_SET_MISMATCH"
        )
    if (
        dict(
            receipt.get(
                "SKILL_SOURCE_PATHS"
            )
            or {}
        )
        != skill_paths
    ):
        raise TrustedRepoReadEvidenceError(
            "TRUST_EVIDENCE_SKILL_PATH_MISMATCH"
        )
    if {
        str(key): str(value).lower()
        for key, value
        in dict(
            receipt.get(
                "SKILL_SOURCE_HASHES"
            )
            or {}
        ).items()
    } != skill_hashes:
        raise TrustedRepoReadEvidenceError(
            "TRUST_EVIDENCE_SKILL_HASH_MISMATCH"
        )
    _trusted_exact_string(
        receipt.get("SKILL_LOAD_STAGE"),
        "LOAD",
        "TRUST_EVIDENCE_LOAD_STAGE_INVALID",
    )
    _trusted_exact_string(
        receipt.get("SKILL_CONSUMPTION"),
        "CONSUMED",
        "TRUST_EVIDENCE_CONSUMPTION_INVALID",
    )
    _trusted_exact_string(
        receipt.get("SKILL_HOST_MODE"),
        GENERIC_REPO_READ_MODE,
        "TRUST_EVIDENCE_HOST_MODE_INVALID",
    )
    _trusted_exact_string(
        str(
            receipt.get(
                "PERMISSION_WIDENED"
            )
            or ""
        ).upper(),
        "NO",
        "TRUST_EVIDENCE_RECEIPT_PERMISSION_WIDENED",
    )

    return {
        "valid": True,
        "evidence_class": (
            "GITHUB_OIDC_BOUND_EXTERNAL_REPO_READ"
        ),
        "evidence_sha256": evidence_sha,
        "repository": repository,
        "revision": revision,
        "host": host,
        "run_id": str(
            claims.get("run_id")
        ),
        "run_attempt": str(
            claims.get("run_attempt")
        ),
        "workflow_ref": workflow_ref,
        "workflow_sha": revision,
        "runner_environment": "github-hosted",
        "jti": jti,
        "task_sha256": task_sha,
        "handoff_fingerprint": handoff_fp,
    }


def _host_token(value: object) -> str:
    return (
        str(value or "").strip().upper()
        .replace("-", "_").replace(" ", "_")
    )


_CONTROL_OR_LINE_BREAK_RE = re.compile(r"[\x00-\x1f\x7f\x85\u2028\u2029]")
_DESTINATION_HOST_TOKEN_RE = re.compile(r"[A-Z0-9][A-Z0-9_]{0,63}")
_SKILL_ID_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.\-]{0,127}")
_REPOSITORY_TOKEN_RE = re.compile(r"[a-z0-9_.\-]+/[a-z0-9_.\-]+")


def _destination_host_token(value: object) -> str:
    """Strict PROMPT_ONLY destination identity."""
    if value is None:
        return ""
    if not isinstance(value, str):
        raise SkillConsumptionError("PROMPT_ONLY_DESTINATION_HOST_INVALID")
    if _CONTROL_OR_LINE_BREAK_RE.search(value):
        raise SkillConsumptionError("PROMPT_ONLY_DESTINATION_HOST_INVALID")
    token = _host_token(value)
    if not token:
        return ""
    if not _DESTINATION_HOST_TOKEN_RE.fullmatch(token):
        raise SkillConsumptionError("PROMPT_ONLY_DESTINATION_HOST_INVALID")
    return token


def _run_git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=8,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def _normalize_github_repo(value: object) -> str | None:
    raw = str(value or "").strip()
    if not raw or _CONTROL_OR_LINE_BREAK_RE.search(raw):
        return None
    match = None
    for pattern in (
        r"https://github\.com/([^/]+)/([^/]+)/?",
        r"git@github\.com:([^/]+)/([^/]+)",
        r"ssh://git@github\.com/([^/]+)/([^/]+)/?",
    ):
        candidate = re.fullmatch(pattern, raw)
        if candidate is not None:
            match = candidate
            break
    if match is None:
        return None
    owner, name = match.groups()
    if name.lower().endswith(".git"):
        name = name[:-4]
    if not owner or not name:
        return None
    if re.fullmatch(r"[A-Za-z0-9_.\-]+", owner) is None:
        return None
    if re.fullmatch(r"[A-Za-z0-9_.\-]+", name) is None:
        return None
    return f"{owner.lower()}/{name.lower()}"


def _canonical_repo_binding(root: Path) -> str | None:
    return _normalize_github_repo(
        _run_git(root, "config", "--get", "remote.origin.url")
    )


def _current_repo_revision(root: Path) -> str | None:
    revision = str(_run_git(root, "rev-parse", "HEAD") or "").lower()
    return revision if re.fullmatch(r"[0-9a-f]{40}", revision) else None


@dataclass(frozen=True)
class SkillSelection:
    outcome: str
    considered_metadata_count: int
    selected: tuple[str, ...]
    rejected: tuple[str, ...]
    rejection_reasons: tuple[str, ...]
    route: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "considered_metadata_count": self.considered_metadata_count,
            "selected": list(self.selected),
            "rejected": list(self.rejected),
            "rejection_reasons": list(self.rejection_reasons),
            "route": dict(self.route),
        }


@dataclass(frozen=True)
class LoadedSkill:
    capability_id: str
    relative_path: str
    sha256: str
    content: str

    def to_dict(self, *, include_content: bool = False) -> dict[str, Any]:
        result = {
            "capability_id": self.capability_id,
            "relative_path": self.relative_path,
            "sha256": self.sha256,
        }
        if include_content:
            result["content"] = self.content
        return result


@dataclass(frozen=True)
class RepoSkillMetadata:
    """Minimal metadata for repo-native skills that lack capability admission."""

    skill_id: str
    declared_name: str
    relative_path: str


def _repo_skill_metadata(root: Path) -> tuple[RepoSkillMetadata, ...]:
    """Discover top-level project skills without loading their instruction body.

    Repo-native skills outside the canonical capability registry are explicit-
    invocation-only.  Reading the YAML frontmatter name mirrors native skill
    discovery while avoiding implicit authority or a second persisted registry.
    """
    skills_dir = root / ".agents" / "skills"
    if not skills_dir.is_dir():
        return ()
    records: list[RepoSkillMetadata] = []
    for directory in sorted(skills_dir.iterdir(), key=lambda p: p.name.lower()):
        entrypoint = directory / "SKILL.md"
        if not directory.is_dir() or not entrypoint.is_file():
            continue
        declared = directory.name
        try:
            with entrypoint.open(
                "r", encoding="utf-8", errors="replace"
            ) as handle:
                first = handle.readline()
                if first.strip() == "---":
                    for index, line in enumerate(handle, start=1):
                        if line.strip() == "---":
                            break
                        if line.lower().startswith("name:"):
                            value = line.split(":", 1)[1].strip().strip("'\"")
                            if value:
                                declared = value
                        if index >= 64:
                            break
        except OSError:
            continue
        records.append(RepoSkillMetadata(
            skill_id=directory.name,
            declared_name=declared,
            relative_path=entrypoint.relative_to(root).as_posix(),
        ))
    return tuple(records)


def _explicit_repo_skill_ids(
    request_text: str,
    explicit_requests: Iterable[str],
    records: Sequence[RepoSkillMetadata],
) -> set[str]:
    """Resolve only explicit $skill/@skill requests for repo-native metadata."""
    requested = {
        str(value or "").strip().lower().lstrip("@$").replace("_", "-")
        for value in explicit_requests
        if str(value or "").strip()
    }
    text = str(request_text or "").lower()
    selected: set[str] = set()
    for record in records:
        aliases = {
            record.skill_id.lower(),
            record.declared_name.lower(),
            record.skill_id.lower().replace("_", "-"),
            record.declared_name.lower().replace("_", "-"),
        }
        aliases = {alias for alias in aliases if alias}
        if requested & aliases:
            selected.add(record.skill_id)
            continue
        for alias in aliases:
            pattern = r"(?<![a-z0-9_-])[$@]" + re.escape(alias) + (
                r"(?=$|[\s,;:.!?()\[\]{}])"
            )
            if re.search(pattern, text):
                selected.add(record.skill_id)
                break
    return selected


def _registry_path(root: Path) -> Path:
    return root / ".p2p" / "system" / "p2p_capabilities" / "capabilities.json"


def _active_skill_manifests(root: Path) -> tuple[CapabilityManifest, ...]:
    registry = load_registry(_registry_path(root))
    return tuple(
        manifest for manifest in registry["parsed"]
        if manifest.type == "SKILL" and manifest.status == "ACTIVE"
    )


def _normalise_explicit(
    explicit_requests: Iterable[str],
    manifests: Sequence[CapabilityManifest],
) -> set[str]:
    by_lower = {m.capability_id.lower(): m.capability_id for m in manifests}
    result: set[str] = set()
    for raw in explicit_requests:
        value = str(raw or "").strip().lower()
        value = value.lstrip("@$")
        aliases = {
            value,
            value.replace("_", "-"),
            value.replace(" ", "-"),
        }
        for alias in aliases:
            if alias in by_lower:
                result.add(by_lower[alias])
    return result

def _skill_alias(value: object) -> str:
    return (
        str(value or "").strip().lower().lstrip("@$")
        .replace("_", "-").replace(" ", "-")
    )


def _resolve_required_skill_ids(
    root: Path,
    required_skills: Iterable[str],
) -> tuple[str, ...]:
    """Resolve prompt-declared required skills to exact repo skill IDs.

    This validates existing metadata only; it does not create a second router.
    Every required skill must resolve before executor handoff.
    """
    raw_items = tuple(required_skills)
    if not raw_items:
        return ()
    if len(raw_items) > MAX_SELECTED_SKILLS:
        raise SkillConsumptionError("REQUIRED_SKILL_SET_LIMIT_EXCEEDED")

    aliases: dict[str, set[str]] = {}
    for manifest in _active_skill_manifests(root):
        aliases.setdefault(_skill_alias(manifest.capability_id), set()).add(
            manifest.capability_id
        )
    for record in _repo_skill_metadata(root):
        for alias in (record.skill_id, record.declared_name):
            key = _skill_alias(alias)
            if key:
                aliases.setdefault(key, set()).add(record.skill_id)

    resolved: list[str] = []
    for raw in raw_items:
        key = _skill_alias(raw)
        if not key:
            raise SkillConsumptionError("REQUIRED_SKILL_EMPTY")
        matches = aliases.get(key, set())
        if not matches:
            raise SkillConsumptionError(
                f"REQUIRED_SKILL_NOT_FOUND:{str(raw).strip()}"
            )
        if len(matches) != 1:
            raise SkillConsumptionError(
                f"REQUIRED_SKILL_AMBIGUOUS:{str(raw).strip()}"
            )
        skill_id = next(iter(matches))
        if skill_id not in resolved:
            resolved.append(skill_id)
    if len(resolved) > MAX_SELECTED_SKILLS:
        raise SkillConsumptionError("REQUIRED_SKILL_SET_LIMIT_EXCEEDED")
    return tuple(resolved)


def select_skills_for_task(
    root: str | Path,
    request_text: str,
    *,
    explicit_requests: Iterable[str] = (),
    allowed_skill_ids: Iterable[str] | None = None,
    limit: int = MAX_SELECTED_SKILLS,
) -> SkillSelection:
    """Select at most three skills without creating a second router.

    Canonical ACTIVE skills use the existing P2P router. Repo-native skills
    that have no capability admission are discoverable by frontmatter metadata
    but are explicit-invocation-only ($skill/@skill). Their instruction bodies
    are not loaded until selection.
    """
    project_root = Path(root).resolve()
    repo_metadata = _repo_skill_metadata(project_root)
    manifests = _active_skill_manifests(project_root)
    if allowed_skill_ids is not None:
        allowed = {str(value) for value in allowed_skill_ids if str(value)}
        manifests = tuple(
            manifest for manifest in manifests
            if manifest.capability_id in allowed
        )
    if limit < 1 or limit > MAX_SELECTED_SKILLS:
        raise SkillConsumptionError("SKILL_SELECTION_LIMIT_INVALID")
    explicit = _normalise_explicit(explicit_requests, manifests)
    repo_explicit = _explicit_repo_skill_ids(
        request_text, explicit_requests, repo_metadata
    )
    route = classify_capabilities(str(request_text or ""), manifests)
    manifest_by_id = {m.capability_id: m for m in manifests}
    result_by_id = {
        str(item.get("capability_id")): item
        for item in route.get("results", ())
        if isinstance(item, Mapping)
    }
    candidates: list[tuple[int, int, str]] = []
    rejected: list[str] = []
    reasons: list[str] = []
    for manifest in manifests:
        item = result_by_id.get(manifest.capability_id, {})
        classification = str(item.get("classification") or "NOT_APPLICABLE")
        positive = tuple(item.get("positive_triggers") or ())
        if manifest.capability_id in explicit:
            candidates.append((4, int(item.get("value") or 0), manifest.capability_id))
            continue
        if manifest.invocation_class == "USER_REQUESTED" and not positive:
            rejected.append(manifest.capability_id)
            reasons.append(f"{manifest.capability_id}:USER_REQUEST_REQUIRED")
            continue
        rank = _CLASS_RANK.get(classification, 0)
        if rank:
            candidates.append((rank, int(item.get("value") or 0), manifest.capability_id))
        else:
            rejected.append(manifest.capability_id)
            reason_codes = tuple(item.get("reason_codes") or ())
            reason = reason_codes[0] if reason_codes else "NO_MATCH"
            reasons.append(f"{manifest.capability_id}:{reason}")
    for record in repo_metadata:
        if record.skill_id in repo_explicit:
            # Explicit repo invocation is a deterministic user request.  When
            # the same ID is also canonical the later ranking deduplicates it;
            # when it is not admitted, it remains explicit-only.
            candidates.append((4, 0, record.skill_id))

    candidates.sort(key=lambda value: (-value[0], -value[1], value[2]))
    selected_list: list[str] = []
    overflow: list[str] = []
    for _, _, skill_id in candidates:
        if skill_id in selected_list:
            continue
        if len(selected_list) < limit:
            selected_list.append(skill_id)
        else:
            overflow.append(skill_id)
    selected = tuple(selected_list)
    for capability_id in overflow:
        rejected.append(capability_id)
        reasons.append(f"{capability_id}:BOUNDED_SET_LIMIT")
    if not selected:
        outcome = "NO_SKILL_NEEDED"
    elif len(selected) == 1:
        outcome = "ONE_SKILL"
    else:
        outcome = "BOUNDED_SKILL_SET"
    # Keep a compact metadata-only route snapshot; never attach manifest bodies.
    compact_route = {
        "schema": route.get("schema"),
        "selected": list(route.get("selected") or ()),
        "single_router": bool(route.get("single_router")),
    }
    return SkillSelection(
        outcome=outcome,
        considered_metadata_count=(
            len(manifests)
            + sum(
                1 for record in repo_metadata
                if record.skill_id not in {m.capability_id for m in manifests}
            )
        ),
        selected=selected,
        rejected=tuple(dict.fromkeys(rejected)),
        rejection_reasons=tuple(dict.fromkeys(reasons)),
        route=compact_route,
    )


def _safe_repo_path(root: Path, relative: str) -> Path:
    value = str(relative or "").strip().replace("\\", "/")
    if not value or value.startswith(("/", "~")):
        raise SkillConsumptionError("SKILL_ENTRYPOINT_PATH_INVALID")
    candidate = (root / value).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise SkillConsumptionError("SKILL_ENTRYPOINT_PATH_TRAVERSAL") from exc
    return candidate


def _entrypoint_for(root: Path, manifest: CapabilityManifest) -> str:
    raw = manifest.raw
    provenance = raw.get("UPSTREAM_PROVENANCE")
    provenance = provenance if isinstance(provenance, Mapping) else {}
    integration = provenance.get("integration")
    integration = integration if isinstance(integration, Mapping) else {}
    entrypoint = str(integration.get("entrypoint") or "").strip()
    base = str(
        provenance.get("vendor_path")
        or provenance.get("source_path")
        or provenance.get("path")
        or ""
    ).strip()
    candidates: list[str] = []
    if entrypoint and base:
        candidates.append(f"{base.rstrip('/')}/{entrypoint.lstrip('/')}")
    for pointer in manifest.context_pointers:
        if str(pointer).replace("\\", "/").lower().endswith("/skill.md"):
            candidates.append(str(pointer))
    candidates.append(f".agents/skills/{manifest.capability_id}/SKILL.md")
    for relative in dict.fromkeys(candidates):
        path = _safe_repo_path(root, relative)
        if path.is_file():
            return path.relative_to(root).as_posix()
    raise SkillConsumptionError(
        f"SKILL_ENTRYPOINT_MISSING:{manifest.capability_id}"
    )


def load_selected_skills(
    root: str | Path,
    selected_ids: Sequence[str],
) -> tuple[LoadedSkill, ...]:
    """Load only exact selected SKILL.md files and verify declared hashes."""
    project_root = Path(root).resolve()
    manifests = {
        manifest.capability_id: manifest
        for manifest in _active_skill_manifests(project_root)
    }
    repo_skills = {
        record.skill_id: record
        for record in _repo_skill_metadata(project_root)
    }
    loaded: list[LoadedSkill] = []
    for capability_id in selected_ids:
        skill_id = str(capability_id)
        manifest = manifests.get(skill_id)
        repo_record = repo_skills.get(skill_id)
        if manifest is not None:
            relative = _entrypoint_for(project_root, manifest)
        elif repo_record is not None:
            relative = repo_record.relative_path
        else:
            raise SkillConsumptionError(f"SKILL_ENTRYPOINT_UNKNOWN:{capability_id}")
        path = _safe_repo_path(project_root, relative)
        raw = path.read_bytes()
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise SkillConsumptionError(
                f"SKILL_ENTRYPOINT_NOT_UTF8:{capability_id}"
            ) from exc
        actual = hashlib.sha256(raw).hexdigest()
        provenance = (
            manifest.raw.get("UPSTREAM_PROVENANCE")
            if manifest is not None else {}
        )
        provenance = provenance if isinstance(provenance, Mapping) else {}
        integration = provenance.get("integration")
        integration = integration if isinstance(integration, Mapping) else {}
        expected = str(integration.get("entrypoint_sha256") or "").lower()
        if expected and expected != actual:
            raise SkillConsumptionError(
                f"SKILL_ENTRYPOINT_HASH_MISMATCH:{capability_id}"
            )
        loaded.append(LoadedSkill(
            capability_id=capability_id,
            relative_path=relative,
            sha256=actual,
            content=content,
        ))
    return tuple(loaded)


def _source_binding_error(
    loaded: Sequence[LoadedSkill],
    root: Path,
) -> str | None:
    """Fail closed on malformed exact path/hash source bindings."""
    for item in loaded:
        path = str(item.relative_path or "").replace("\\", "/")
        if (
            not path
            or path.startswith(("/", "~"))
            or ".." in Path(path).parts
            or not path.endswith("/SKILL.md")
        ):
            return f"SKILL_SOURCE_PATH_INVALID:{item.capability_id}"
        try:
            candidate = _safe_repo_path(root, path)
        except SkillConsumptionError:
            return f"SKILL_SOURCE_PATH_INVALID:{item.capability_id}"
        if not candidate.is_file():
            return f"SKILL_ENTRYPOINT_MISSING:{item.capability_id}"
        actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if not re.fullmatch(r"[0-9a-f]{64}", item.sha256 or ""):
            return f"SKILL_SOURCE_HASH_INVALID:{item.capability_id}"
        if actual != item.sha256:
            return f"SKILL_ENTRYPOINT_HASH_MISMATCH:{item.capability_id}"
    return None


def prepare_skill_handoff(
    root: str | Path,
    request_text: str,
    *,
    host: str,
    explicit_requests: Iterable[str] = (),
    required_skills: Iterable[str] = (),
) -> dict[str, Any]:
    """Freeze one deterministic source-bound skill handoff for an executor.

    required_skills is a prompt-writer contract: every named skill must
    resolve, fit the bounded set, load exactly, and appear in the executor
    handoff. Narrative prose alone never satisfies this requirement.
    """
    project_root = Path(root).resolve()
    host_name = str(host or "").strip().upper()
    mode = HOST_MODES.get(host_name)
    try:
        required_ids = _resolve_required_skill_ids(
            project_root, required_skills
        )
    except SkillConsumptionError as exc:
        return {
            "schema": HANDOFF_SCHEMA,
            "SKILL_CHECK": "BLOCKED",
            "REQUIRED_SKILLS": [],
            "SKILLS_CONSIDERED_METADATA_COUNT": 0,
            "SKILLS_SELECTED": [],
            "SKILL_LOAD_STAGE": "DISCOVERY",
            "SKILL_SOURCE_HASHES": {},
            "SKILL_SOURCE_PATHS": {},
            "SKILL_CONSUMPTION": "BLOCKED",
            "SKILL_HOST_MODE": mode or "UNSUPPORTED",
            "MATERIAL_ALTERNATIVES_REJECTED": [],
            "REJECTION_REASON": [str(exc)],
            "PERMISSION_WIDENED": "NO",
            "SINGLE_ROUTER_REUSED": "YES",
        }
    combined_explicit = tuple(explicit_requests) + required_ids
    selection = select_skills_for_task(
        project_root,
        request_text,
        explicit_requests=combined_explicit,
    )
    missing_required = tuple(
        skill_id for skill_id in required_ids
        if skill_id not in selection.selected
    )
    if missing_required:
        return {
            "schema": HANDOFF_SCHEMA,
            "SKILL_CHECK": "BLOCKED",
            "REQUIRED_SKILLS": list(required_ids),
            "SKILLS_CONSIDERED_METADATA_COUNT": selection.considered_metadata_count,
            "SKILLS_SELECTED": list(selection.selected),
            "SKILL_LOAD_STAGE": "MATCH",
            "SKILL_SOURCE_HASHES": {},
            "SKILL_SOURCE_PATHS": {},
            "SKILL_CONSUMPTION": "BLOCKED",
            "SKILL_HOST_MODE": mode or "UNSUPPORTED",
            "MATERIAL_ALTERNATIVES_REJECTED": list(selection.rejected),
            "REJECTION_REASON": [
                f"REQUIRED_SKILL_NOT_SELECTED:{skill_id}"
                for skill_id in missing_required
            ],
            "PERMISSION_WIDENED": "NO",
            "SINGLE_ROUTER_REUSED": "YES",
        }
    if mode is None:
        return {
            "schema": HANDOFF_SCHEMA,
            "SKILL_CHECK": "BLOCKED",
            "REQUIRED_SKILLS": list(required_ids),
            "SKILLS_CONSIDERED_METADATA_COUNT": selection.considered_metadata_count,
            "SKILLS_SELECTED": list(selection.selected),
            "SKILL_LOAD_STAGE": "MATCH" if selection.selected else "DISCOVERY",
            "SKILL_SOURCE_HASHES": {},
            "SKILL_SOURCE_PATHS": {},
            "SKILL_CONSUMPTION": "BLOCKED",
            "SKILL_HOST_MODE": "UNSUPPORTED",
            "MATERIAL_ALTERNATIVES_REJECTED": list(selection.rejected),
            "REJECTION_REASON": ["HOST_NOT_SUPPORTED_V1"],
            "PERMISSION_WIDENED": "NO",
            "SINGLE_ROUTER_REUSED": "YES",
        }
    if not selection.selected:
        return {
            "schema": HANDOFF_SCHEMA,
            "SKILL_CHECK": "NO_MATCH",
            "REQUIRED_SKILLS": list(required_ids),
            "SKILLS_CONSIDERED_METADATA_COUNT": selection.considered_metadata_count,
            "SKILLS_SELECTED": [],
            "SKILL_LOAD_STAGE": "DISCOVERY",
            "SKILL_SOURCE_HASHES": {},
            "SKILL_SOURCE_PATHS": {},
            "SKILL_CONSUMPTION": "NO_SKILL_NEEDED",
            "SKILL_HOST_MODE": mode,
            "MATERIAL_ALTERNATIVES_REJECTED": list(selection.rejected),
            "REJECTION_REASON": list(selection.rejection_reasons),
            "PERMISSION_WIDENED": "NO",
            "SINGLE_ROUTER_REUSED": "YES",
        }
    try:
        loaded = load_selected_skills(root, selection.selected)
    except SkillConsumptionError as exc:
        return {
            "schema": HANDOFF_SCHEMA,
            "SKILL_CHECK": "BLOCKED",
            "REQUIRED_SKILLS": list(required_ids),
            "SKILLS_CONSIDERED_METADATA_COUNT": selection.considered_metadata_count,
            "SKILLS_SELECTED": list(selection.selected),
            "SKILL_LOAD_STAGE": "MATCH",
            "SKILL_SOURCE_HASHES": {},
            "SKILL_SOURCE_PATHS": {},
            "SKILL_CONSUMPTION": "LOAD_FAILED",
            "SKILL_HOST_MODE": mode,
            "MATERIAL_ALTERNATIVES_REJECTED": list(selection.rejected),
            "REJECTION_REASON": [str(exc)],
            "PERMISSION_WIDENED": "NO",
            "SINGLE_ROUTER_REUSED": "YES",
        }
    return {
        "schema": HANDOFF_SCHEMA,
        "SKILL_CHECK": "PASS",
        "REQUIRED_SKILLS": list(required_ids),
        "SKILLS_CONSIDERED_METADATA_COUNT": selection.considered_metadata_count,
        "SKILLS_SELECTED": [item.capability_id for item in loaded],
        "SKILL_LOAD_STAGE": "LOAD",
        "SKILL_SOURCE_HASHES": {
            item.capability_id: item.sha256 for item in loaded
        },
        "SKILL_SOURCE_PATHS": {
            item.capability_id: item.relative_path for item in loaded
        },
        "SKILL_CONSUMPTION": "EXPECTED",
        "SKILL_HOST_MODE": mode,
        "MATERIAL_ALTERNATIVES_REJECTED": list(selection.rejected),
        "REJECTION_REASON": list(selection.rejection_reasons),
        "PERMISSION_WIDENED": "NO",
        "SINGLE_ROUTER_REUSED": "YES",
    }



def _frozen_skill_handoff_payload(
    handoff: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the exact immutable subset ORCA candidates are allowed to share.

    Selection has already happened before fanout.  This function never routes,
    reselects, loads an extra skill, or grants permission; it only normalizes
    the source-bound handoff that every candidate must reference identically.
    """
    if not isinstance(handoff, Mapping):
        raise SkillConsumptionError("SKILL_HANDOFF_INVALID")
    if str(handoff.get("schema") or "") != HANDOFF_SCHEMA:
        raise SkillConsumptionError("SKILL_HANDOFF_SCHEMA_INVALID")
    check = str(handoff.get("SKILL_CHECK") or "")
    if check not in ("PASS", "NO_MATCH"):
        raise SkillConsumptionError("SKILL_HANDOFF_NOT_INHERITABLE")
    if str(handoff.get("PERMISSION_WIDENED") or "").upper() != "NO":
        raise SkillConsumptionError("SKILL_PERMISSION_WIDENING_REJECTED")
    if str(handoff.get("SINGLE_ROUTER_REUSED") or "").upper() != "YES":
        raise SkillConsumptionError("SKILL_SINGLE_ROUTER_INVARIANT_REQUIRED")

    selected = tuple(str(v) for v in (handoff.get("SKILLS_SELECTED") or ()))
    required = tuple(str(v) for v in (handoff.get("REQUIRED_SKILLS") or ()))
    if len(selected) != len(set(selected)):
        raise SkillConsumptionError("SKILL_SELECTED_SET_DUPLICATE")
    if len(required) != len(set(required)):
        raise SkillConsumptionError("REQUIRED_SKILL_SET_DUPLICATE")
    if any(skill_id not in selected for skill_id in required):
        raise SkillConsumptionError("REQUIRED_SKILL_SET_NOT_SELECTED")
    hashes = {
        str(k): str(v).lower()
        for k, v in dict(handoff.get("SKILL_SOURCE_HASHES") or {}).items()
    }
    paths = {
        str(k): str(v)
        for k, v in dict(handoff.get("SKILL_SOURCE_PATHS") or {}).items()
    }
    if check == "PASS":
        if not selected or str(handoff.get("SKILL_LOAD_STAGE") or "") != "LOAD":
            raise SkillConsumptionError("SKILL_HANDOFF_PASS_STATE_INVALID")
        if set(hashes) != set(selected) or set(paths) != set(selected):
            raise SkillConsumptionError("SKILL_HANDOFF_SOURCE_SET_MISMATCH")
        if any(re.fullmatch(r"[0-9a-f]{64}", digest) is None
               for digest in hashes.values()):
            raise SkillConsumptionError("SKILL_HANDOFF_SOURCE_HASH_INVALID")
        if any(not path or path.startswith(("/", "~")) for path in paths.values()):
            raise SkillConsumptionError("SKILL_HANDOFF_SOURCE_PATH_INVALID")
    else:
        if selected or hashes or paths:
            raise SkillConsumptionError("SKILL_NO_MATCH_MUST_BE_EMPTY")

    return {
        "schema": HANDOFF_SCHEMA,
        "SKILL_CHECK": check,
        "REQUIRED_SKILLS": list(required),
        "SKILLS_SELECTED": list(selected),
        "SKILL_LOAD_STAGE": str(
            handoff.get("SKILL_LOAD_STAGE") or "DISCOVERY"
        ),
        "SKILL_SOURCE_HASHES": hashes,
        "SKILL_SOURCE_PATHS": paths,
        "SKILL_HOST_MODE": str(handoff.get("SKILL_HOST_MODE") or ""),
        "SKILL_CONSUMPTION": str(handoff.get("SKILL_CONSUMPTION") or ""),
        "PERMISSION_WIDENED": "NO",
        "SINGLE_ROUTER_REUSED": "YES",
    }


def freeze_skill_handoff_for_orca_candidates(
    handoff: Mapping[str, Any],
    candidate_ids: Sequence[str],
) -> dict[str, Any]:
    """Bind one pre-fanout skill selection identically to every ORCA candidate.

    Candidates receive only a fingerprint reference to ONE frozen handoff.
    There is no candidate-local selection surface, so fanout cannot widen or
    swap the selected set without invalidating the inheritance record.
    """
    if isinstance(candidate_ids, (str, bytes, bytearray, dict, set, frozenset)):
        raise SkillConsumptionError("ORCA_CANDIDATE_IDS_INVALID")
    ids = tuple(str(value or "").strip() for value in candidate_ids)
    if not ids or any(not value for value in ids):
        raise SkillConsumptionError("ORCA_CANDIDATE_IDS_INVALID")
    if len(ids) != len(set(ids)):
        raise SkillConsumptionError("ORCA_CANDIDATE_IDS_DUPLICATE")
    try:
        from .orca_candidate_fanout import HARD_FANOUT_CAP
    except ImportError:
        from orca_candidate_fanout import HARD_FANOUT_CAP
    if len(ids) > HARD_FANOUT_CAP:
        raise SkillConsumptionError("ORCA_CANDIDATE_FANOUT_CAP_EXCEEDED")

    frozen = _frozen_skill_handoff_payload(handoff)
    fingerprint = hashlib.sha256(json.dumps(
        frozen,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    return {
        "schema": FANOUT_INHERITANCE_SCHEMA,
        "FROZEN_SKILL_HANDOFF": frozen,
        "FROZEN_SKILL_HANDOFF_FINGERPRINT": fingerprint,
        "CANDIDATE_BINDINGS": [
            {
                "candidate_id": candidate_id,
                "skill_handoff_fingerprint": fingerprint,
            }
            for candidate_id in ids
        ],
        "CANDIDATE_SKILL_RESELECTION": "FORBIDDEN",
        "PERMISSION_WIDENED": "NO",
    }


def validate_orca_skill_inheritance(
    inheritance: Mapping[str, Any] | None,
    handoff: Mapping[str, Any],
    candidate_ids: Sequence[str],
) -> dict[str, Any]:
    """Fail closed when any ORCA candidate diverges from the frozen handoff."""
    try:
        expected = freeze_skill_handoff_for_orca_candidates(
            handoff, candidate_ids
        )
    except (SkillConsumptionError, TypeError, ValueError) as exc:
        return {
            "valid": False,
            "reason_codes": [f"EXPECTED_INHERITANCE_INVALID:{exc}"],
        }
    if not isinstance(inheritance, Mapping):
        return {
            "valid": False,
            "reason_codes": ["SKILL_FANOUT_INHERITANCE_MISSING"],
        }

    reasons: list[str] = []
    if inheritance.get("schema") != FANOUT_INHERITANCE_SCHEMA:
        reasons.append("SKILL_FANOUT_INHERITANCE_SCHEMA_INVALID")
    if inheritance.get("FROZEN_SKILL_HANDOFF") != expected[
            "FROZEN_SKILL_HANDOFF"]:
        reasons.append("FROZEN_SKILL_HANDOFF_MISMATCH")
    if str(inheritance.get("FROZEN_SKILL_HANDOFF_FINGERPRINT") or "") != (
            expected["FROZEN_SKILL_HANDOFF_FINGERPRINT"]):
        reasons.append("FROZEN_SKILL_HANDOFF_FINGERPRINT_MISMATCH")
    if list(inheritance.get("CANDIDATE_BINDINGS") or []) != expected[
            "CANDIDATE_BINDINGS"]:
        reasons.append("ORCA_CANDIDATE_SKILL_BINDING_MISMATCH")
    if str(inheritance.get("CANDIDATE_SKILL_RESELECTION") or "") != "FORBIDDEN":
        reasons.append("ORCA_CANDIDATE_RESELECTION_NOT_FORBIDDEN")
    if str(inheritance.get("PERMISSION_WIDENED") or "UNKNOWN").upper() != "NO":
        reasons.append("SKILL_PERMISSION_WIDENING_REJECTED")
    return {"valid": not reasons, "reason_codes": reasons}


def skill_handoff_prompt_lines(handoff: Mapping[str, Any]) -> tuple[str, ...]:
    """Serialize a frozen handoff without embedding skill bodies in the prompt."""
    check = str(handoff.get("SKILL_CHECK") or "BLOCKED")
    selected = tuple(str(v) for v in (handoff.get("SKILLS_SELECTED") or ()))
    hashes = handoff.get("SKILL_SOURCE_HASHES") or {}
    paths = handoff.get("SKILL_SOURCE_PATHS") or {}
    required = tuple(str(v) for v in (handoff.get("REQUIRED_SKILLS") or ()))
    lines = [
        "P2P_SKILL_HANDOFF:",
        f"SKILL_CHECK={check}",
        "REQUIRED_SKILLS=" + (",".join(required) if required else "NONE"),
        "SKILLS_SELECTED=" + (",".join(selected) if selected else "NONE"),
        f"SKILL_LOAD_STAGE={handoff.get('SKILL_LOAD_STAGE', 'DISCOVERY')}",
        f"SKILL_HOST_MODE={handoff.get('SKILL_HOST_MODE', 'UNSUPPORTED')}",
        "SKILL_PERMISSION_WIDENED=NO",
    ]
    if check == "PREPARED":
        lines.extend((
            f"SOURCE_VALIDATION={handoff.get('SOURCE_VALIDATION', 'PASS')}",
            f"RECIPIENT_CONSUMPTION={handoff.get('RECIPIENT_CONSUMPTION', 'UNVERIFIED')}",
            "EXECUTION_AUTHORIZED=NO",
            "OPERATION=PREPARE",
            "This is source-validated delegated work, not proven recipient consumption and not execution authorization.",
        ))
    elif (
        check == "PASS"
        and str(handoff.get("SKILL_HOST_MODE") or "")
        == GENERIC_REPO_READ_MODE
    ):
        if (
            str(handoff.get("EXECUTION_AUTHORIZED") or "").upper() != "YES"
            or str(handoff.get("RECIPIENT_CONSUMPTION") or "").upper()
            != "VERIFIED"
            or str(handoff.get("TRUST_EVIDENCE_CLASS") or "")
            != "GITHUB_OIDC_BOUND_EXTERNAL_REPO_READ"
        ):
            raise SkillConsumptionError(
                "GENERIC_REPO_READ_TRUST_BINDING_INVALID"
            )
        lines.extend((
            f"SOURCE_VALIDATION={handoff.get('SOURCE_VALIDATION', 'PASS')}",
            "RECIPIENT_CONSUMPTION=VERIFIED",
            "EXECUTION_AUTHORIZED=YES",
            "OPERATION=EXECUTE",
            "TRUST_EVIDENCE_CLASS=GITHUB_OIDC_BOUND_EXTERNAL_REPO_READ",
            f"TRUST_EVIDENCE_SHA256={handoff.get('TRUST_EVIDENCE_SHA256', '')}",
            f"TRUST_EVIDENCE_RUN_ID={handoff.get('TRUST_EVIDENCE_RUN_ID', '')}",
            "Authorization is limited to this exact task, repository revision, host, and frozen skill handoff.",
        ))
    if check in {"PASS", "PREPARED"}:
        lines.extend((
            "Every skill listed in REQUIRED_SKILLS is mandatory for this executor turn. Read and apply every required skill; omission is a failed handoff.",
            "Before substantive task execution, read ONLY the exact selected SKILL.md entrypoints below.",
            "After selection, deep-load only references/scripts explicitly declared by those selected skills and only when materially required; never load an unselected skill.",
            "Verify each entrypoint SHA-256 equals the frozen expected hash before using it.",
            "On a missing file or hash mismatch, fail closed with SKILL_CONSUMPTION=LOAD_FAILED; do not substitute or widen the selected set.",
            "Supreme Law / Owner / permissions / task contract outrank all skill guidance.",
        ))
        for capability_id in selected:
            lines.append(
                "SKILL_SOURCE="
                f"{capability_id}|PATH={paths.get(capability_id, '')}"
                f"|SHA256={hashes.get(capability_id, '')}"
            )
        lines.append(
            "Terminal return must include SKILL_CONSUMPTION_RECEIPT with exact selected ids, hashes, LOAD stage, host mode, CONSUMED, and PERMISSION_WIDENED=NO."
        )
        if check == "PREPARED":
            lines.append(
                "A returned receipt is self-reported. It is not trusted external-actor "
                "read evidence and does not authorize automatic execution."
            )
    elif check == "NO_MATCH":
        lines.append(
            "No relevant eligible skill was selected. Do not preload unrelated skills. "
            "Terminal return uses SKILL_CONSUMPTION=NO_SKILL_NEEDED."
        )
    else:
        lines.append(
            "Skill handoff is blocked. Do not claim a skill was consumed and do not widen the skill set."
        )
    return tuple(lines)


def _inline_skill_forbidden_reason(root: Path, skill_id: str) -> str | None:
    """Inline only explicitly public/shareable skill bodies."""
    manifests = {
        manifest.capability_id: manifest
        for manifest in _active_skill_manifests(root)
    }
    manifest = manifests.get(skill_id)
    if manifest is None:
        return f"INLINE_SKILL_MANIFEST_REQUIRED:{skill_id}"
    trust = str(manifest.raw.get("TRUST_LEVEL") or "").strip().upper()
    provenance = manifest.raw.get("UPSTREAM_PROVENANCE")
    provenance = provenance if isinstance(provenance, Mapping) else {}
    license_info = provenance.get("license")
    license_info = license_info if isinstance(license_info, Mapping) else {}
    license_kind = str(license_info.get("kind") or "").strip().upper()
    if license_kind not in INLINE_SHAREABLE_LICENSE_KINDS:
        return (
            f"INLINE_SKILL_DISCLOSURE_FORBIDDEN:{skill_id}:"
            f"{license_kind or 'MISSING'}"
        )
    if trust not in INLINE_PERMITTED_TRUST_LEVELS:
        return f"INLINE_SKILL_TRUST_LEVEL_FORBIDDEN:{skill_id}:{trust or 'MISSING'}"
    integration = provenance.get("integration")
    integration = integration if isinstance(integration, Mapping) else {}
    if integration.get("credentials") is True:
        return f"INLINE_SKILL_CREDENTIALS_FORBIDDEN:{skill_id}"
    if integration.get("network_runtime") is True:
        return f"INLINE_SKILL_NETWORK_RUNTIME_FORBIDDEN:{skill_id}"
    return None


def _validate_prompt_only_frozen_selection(
    handoff: Mapping[str, Any],
    check: str,
) -> None:
    selected_raw = handoff.get("SKILLS_SELECTED")
    required_raw = handoff.get("REQUIRED_SKILLS")
    hashes = handoff.get("SKILL_SOURCE_HASHES")
    paths = handoff.get("SKILL_SOURCE_PATHS")
    for value in (selected_raw, required_raw):
        if value is not None and not isinstance(value, (list, tuple)):
            raise SkillConsumptionError("PROMPT_ONLY_SELECTED_SET_INVALID")
    for value in (hashes, paths):
        if value is not None and not isinstance(value, Mapping):
            raise SkillConsumptionError("PROMPT_ONLY_SOURCE_MAPPING_INVALID")
    selected = tuple(selected_raw or ())
    required = tuple(required_raw or ())
    for skill_id in selected + required:
        if not isinstance(skill_id, str) or not _SKILL_ID_TOKEN_RE.fullmatch(skill_id):
            raise SkillConsumptionError("PROMPT_ONLY_SKILL_ID_INVALID")
    if check == "NO_MATCH":
        if selected or required or dict(hashes or {}) or dict(paths or {}):
            raise SkillConsumptionError("PROMPT_ONLY_NO_MATCH_NOT_EMPTY")
        if (
            handoff.get("SKILL_LOAD_STAGE") != "DISCOVERY"
            or handoff.get("SKILL_CONSUMPTION") != "NO_SKILL_NEEDED"
            or handoff.get("SOURCE_VALIDATION") != "NO_MATCH"
            or handoff.get("RECIPIENT_CONSUMPTION") != "NOT_REQUIRED"
        ):
            raise SkillConsumptionError("PROMPT_ONLY_LOAD_STATE_INCOHERENT")
        return
    if check != "PREPARED":
        raise SkillConsumptionError("PROMPT_ONLY_HANDOFF_NOT_PREPARED")
    if not selected:
        raise SkillConsumptionError("PROMPT_ONLY_SELECTED_SET_EMPTY")
    if len(selected) > MAX_SELECTED_SKILLS or len(required) > MAX_SELECTED_SKILLS:
        raise SkillConsumptionError("PROMPT_ONLY_SELECTED_SET_LIMIT_EXCEEDED")
    if len(set(selected)) != len(selected) or len(set(required)) != len(required):
        raise SkillConsumptionError("PROMPT_ONLY_SELECTED_SET_DUPLICATE")
    for skill_id in required:
        if skill_id not in selected:
            raise SkillConsumptionError(
                f"PROMPT_ONLY_REQUIRED_NOT_SELECTED:{skill_id}"
            )
    dict_hashes = dict(hashes or {})
    dict_paths = dict(paths or {})
    if set(dict_hashes) != set(selected) or set(dict_paths) != set(selected):
        raise SkillConsumptionError("SKILL_HANDOFF_SOURCE_SET_MISMATCH")
    for skill_id in selected:
        digest = dict_hashes.get(skill_id)
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise SkillConsumptionError(f"SKILL_SOURCE_HASH_INVALID:{skill_id}")
        if not isinstance(dict_paths.get(skill_id), str):
            raise SkillConsumptionError(f"SKILL_SOURCE_PATH_INVALID:{skill_id}")
    if (
        handoff.get("SKILL_LOAD_STAGE") != "LOAD"
        or handoff.get("SKILL_CONSUMPTION") != "EXPECTED_AFTER_RECIPIENT_READ"
        or handoff.get("SOURCE_VALIDATION") != "PASS"
        or handoff.get("RECIPIENT_CONSUMPTION") != "UNVERIFIED"
    ):
        raise SkillConsumptionError("PROMPT_ONLY_LOAD_STATE_INCOHERENT")


def build_prompt_only_delegated_prompt(
    root: str | Path,
    handoff: Mapping[str, Any],
    *,
    request_text: str,
    host: str,
    allow_inline_skill_content: bool = False,
    max_prompt_chars: int | None = None,
) -> str:
    """Build one copyable source-bound prompt; never starts an executor."""
    project_root = Path(root).resolve()
    check = str(handoff.get("SKILL_CHECK") or "BLOCKED")
    if check not in {"PREPARED", "NO_MATCH"}:
        raise SkillConsumptionError("PROMPT_ONLY_HANDOFF_NOT_PREPARED")
    if str(handoff.get("SKILL_HOST_MODE") or "") != GENERIC_PROMPT_ONLY_MODE:
        raise SkillConsumptionError("PROMPT_ONLY_HOST_MODE_REQUIRED")
    if str(handoff.get("EXECUTION_AUTHORIZED") or "NO").upper() != "NO":
        raise SkillConsumptionError("PROMPT_ONLY_MUST_NOT_AUTHORIZE_EXECUTION")
    _validate_prompt_only_frozen_selection(handoff, check)

    actual_repo = _canonical_repo_binding(project_root)
    actual_revision = _current_repo_revision(project_root)
    if actual_repo is None:
        raise SkillConsumptionError("HOST_CANONICAL_REPO_BINDING_UNAVAILABLE")
    if actual_revision is None:
        raise SkillConsumptionError("HOST_CANONICAL_REPO_REVISION_UNAVAILABLE")
    claimed_repo = str(handoff.get("REPOSITORY") or "").strip().lower()
    claimed_revision = str(handoff.get("REVISION") or "").strip().lower()
    if not _REPOSITORY_TOKEN_RE.fullmatch(claimed_repo):
        raise SkillConsumptionError("PROMPT_ONLY_REPOSITORY_INVALID")
    if not re.fullmatch(r"[0-9a-f]{40}", claimed_revision):
        raise SkillConsumptionError("PROMPT_ONLY_REVISION_INVALID")
    if claimed_repo != actual_repo:
        raise SkillConsumptionError("PROMPT_ONLY_REPOSITORY_MISMATCH")
    if claimed_revision != actual_revision:
        raise SkillConsumptionError("PROMPT_ONLY_REVISION_MISMATCH")

    requested_host = _destination_host_token(host)
    frozen_host = _destination_host_token(handoff.get("DESTINATION_HOST") or "")
    if not requested_host or not frozen_host:
        raise SkillConsumptionError("PROMPT_ONLY_DESTINATION_HOST_REQUIRED")
    if frozen_host != requested_host:
        raise SkillConsumptionError("PROMPT_ONLY_DESTINATION_HOST_MISMATCH")

    if check == "PREPARED":
        selected = tuple(str(v) for v in (handoff.get("SKILLS_SELECTED") or ()))
        loaded = load_selected_skills(project_root, selected)
        binding_error = _source_binding_error(loaded, project_root)
        if binding_error is not None:
            raise SkillConsumptionError(binding_error)
        expected_hashes = dict(handoff.get("SKILL_SOURCE_HASHES") or {})
        expected_paths = dict(handoff.get("SKILL_SOURCE_PATHS") or {})
        for item in loaded:
            if item.relative_path != expected_paths.get(item.capability_id):
                raise SkillConsumptionError(
                    f"SKILL_SOURCE_PATH_INVALID:{item.capability_id}"
                )
            if item.sha256 != expected_hashes.get(item.capability_id):
                raise SkillConsumptionError(
                    f"SKILL_ENTRYPOINT_HASH_MISMATCH:{item.capability_id}"
                )

    budget = (
        PROMPT_ONLY_MAX_PROMPT_CHARS
        if max_prompt_chars is None
        else int(max_prompt_chars)
    )
    if budget < 1:
        raise SkillConsumptionError("PROMPT_ONLY_BUDGET_INVALID")
    lines = [
        "P2P_DELEGATED_WORK_PROMPT:",
        "OPERATION=PREPARE",
        "DELIVERY_CAPABILITY=PROMPT_ONLY",
        "EXECUTION_AUTHORIZED=NO",
        "AUTOMATIC_START=NO",
        f"DESTINATION_HOST={requested_host}",
        f"REPOSITORY={actual_repo}",
        f"REVISION={actual_revision}",
        f"SOURCE_VALIDATION={handoff.get('SOURCE_VALIDATION', check)}",
        f"RECIPIENT_CONSUMPTION={handoff.get('RECIPIENT_CONSUMPTION', 'UNVERIFIED')}",
        "EXTERNAL_ACTOR_READ=NOT_VERIFIED",
        "",
        "TASK:",
        str(request_text or "").strip(),
        "",
        *skill_handoff_prompt_lines(handoff),
        "",
        "Return schema p2p-skill-consumption-receipt/1 after reading the exact selected skills.",
        "Do not treat this prompt as an authorized Control Tower execution session.",
    ]
    if allow_inline_skill_content and check == "PREPARED":
        selected = tuple(str(v) for v in (handoff.get("SKILLS_SELECTED") or ()))
        loaded = load_selected_skills(project_root, selected)
        expected_hashes = dict(handoff.get("SKILL_SOURCE_HASHES") or {})
        expected_paths = dict(handoff.get("SKILL_SOURCE_PATHS") or {})
        inline_block: list[str] = []
        for item in loaded:
            forbidden = _inline_skill_forbidden_reason(
                project_root, item.capability_id
            )
            if forbidden is not None:
                raise SkillConsumptionError(forbidden)
            if item.sha256 != expected_hashes.get(item.capability_id):
                raise SkillConsumptionError(
                    f"SKILL_ENTRYPOINT_HASH_MISMATCH:{item.capability_id}"
                )
            if item.relative_path != expected_paths.get(item.capability_id):
                raise SkillConsumptionError(
                    f"SKILL_SOURCE_PATH_INVALID:{item.capability_id}"
                )
            inline_block.extend((
                f"BEGIN_INLINE_SKILL={item.capability_id}|SHA256={item.sha256}",
                item.content,
                f"END_INLINE_SKILL={item.capability_id}",
            ))
        lines.extend(("", "INLINE_SKILL_CONTENT=EXACT_SELECTED_ONLY", *inline_block))
    prompt = "\n".join(lines)
    if len(prompt) > budget:
        raise SkillConsumptionError("INLINE_SKILL_CONTENT_EXCEEDS_PROMPT_BUDGET")
    if "\x00" in prompt:
        raise SkillConsumptionError("PROMPT_ONLY_CONTENT_INVALID")
    return prompt


TRUSTED_GENERIC_REPO_READ_WORKFLOW_PATH = (
    ".github/workflows/p2p-shield-ci-slice.yml"
)
GENERIC_DISCOVERY_MAX_AGE_SECONDS = 3600
GENERIC_DISCOVERY_MAX_FUTURE_SKEW_SECONDS = 300


def prompt_only_task_sha256(request_text: str) -> str:
    task = str(request_text or "").strip()
    if not task:
        raise SkillConsumptionError("PROMPT_ONLY_TASK_REQUIRED")
    return hashlib.sha256(task.encode("utf-8")).hexdigest()


def prompt_only_handoff_fingerprint(
    handoff: Mapping[str, Any],
    *,
    request_text: str,
    host: str,
) -> str:
    """Bind the exact PREPARED handoff to one bounded task and host."""
    check = str(handoff.get("SKILL_CHECK") or "")
    if check != "PREPARED":
        raise SkillConsumptionError("PROMPT_ONLY_HANDOFF_NOT_PREPARED")
    _validate_prompt_only_frozen_selection(handoff, check)
    host_name = _destination_host_token(host)
    if not host_name or host_name != _destination_host_token(
        handoff.get("DESTINATION_HOST") or ""
    ):
        raise SkillConsumptionError("PROMPT_ONLY_DESTINATION_HOST_MISMATCH")
    payload = {
        "schema": str(handoff.get("schema") or ""),
        "SKILL_CHECK": check,
        "REQUIRED_SKILLS": list(handoff.get("REQUIRED_SKILLS") or ()),
        "SKILLS_SELECTED": list(handoff.get("SKILLS_SELECTED") or ()),
        "SKILL_LOAD_STAGE": str(handoff.get("SKILL_LOAD_STAGE") or ""),
        "SKILL_SOURCE_HASHES": dict(handoff.get("SKILL_SOURCE_HASHES") or {}),
        "SKILL_SOURCE_PATHS": dict(handoff.get("SKILL_SOURCE_PATHS") or {}),
        "SKILL_HOST_MODE": str(handoff.get("SKILL_HOST_MODE") or ""),
        "SKILL_CONSUMPTION": str(handoff.get("SKILL_CONSUMPTION") or ""),
        "PERMISSION_WIDENED": str(handoff.get("PERMISSION_WIDENED") or ""),
        "SOURCE_VALIDATION": str(handoff.get("SOURCE_VALIDATION") or ""),
        "RECIPIENT_CONSUMPTION": str(
            handoff.get("RECIPIENT_CONSUMPTION") or ""
        ),
        "EXECUTION_AUTHORIZED": str(
            handoff.get("EXECUTION_AUTHORIZED") or ""
        ),
        "OPERATION": str(handoff.get("OPERATION") or ""),
        "DELIVERY_CAPABILITY": str(
            handoff.get("DELIVERY_CAPABILITY") or ""
        ),
        "DESTINATION_HOST": host_name,
        "REPOSITORY": str(handoff.get("REPOSITORY") or "").lower(),
        "REVISION": str(handoff.get("REVISION") or "").lower(),
        "TASK_SHA256": prompt_only_task_sha256(request_text),
    }
    return hashlib.sha256(json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()


def _coerce_generic_host_discovery_record(
    value: HostDiscoveryRecord | Mapping[str, Any] | None,
) -> HostDiscoveryRecord:
    if isinstance(value, HostDiscoveryRecord):
        record = value
    else:
        if not isinstance(value, Mapping):
            raise SkillConsumptionError("HOST_DISCOVERY_RECORD_REQUIRED")
        if value.get("schema") != DISCOVERY_SCHEMA:
            raise SkillConsumptionError("HOST_DISCOVERY_RECORD_SCHEMA_INVALID")
        profile_raw = value.get("profile")
        if not isinstance(profile_raw, Mapping):
            raise SkillConsumptionError("HOST_DISCOVERY_PROFILE_INVALID")
        active = value.get("active")
        transport = value.get("execution_transport_available")
        if not isinstance(active, bool):
            raise SkillConsumptionError("HOST_DISCOVERY_ACTIVE_TYPE_INVALID")
        if not isinstance(transport, bool):
            raise SkillConsumptionError("HOST_DISCOVERY_TRANSPORT_TYPE_INVALID")
        try:
            profile = HostCapabilityProfile.from_mapping(profile_raw)
            record = HostDiscoveryRecord(
                host_id=str(value.get("host_id") or ""),
                profile=profile,
                availability=str(value.get("availability") or ""),
                observed_at=str(value.get("observed_at") or ""),
                provenance=str(value.get("provenance") or ""),
                environment_binding=value.get("environment_binding"),
                project_binding=value.get("project_binding"),
                profile_version=str(value.get("profile_version") or "1"),
                active=active,
                reconciliation_burden=int(
                    value.get("reconciliation_burden") or 0
                ),
                execution_transport_available=transport,
            )
        except (HostExecutorContractError, ValueError, TypeError) as exc:
            raise SkillConsumptionError(
                f"HOST_DISCOVERY_RECORD_INVALID:{exc}"
            ) from exc
    if not isinstance(record.active, bool):
        raise SkillConsumptionError("HOST_DISCOVERY_ACTIVE_TYPE_INVALID")
    if not isinstance(record.execution_transport_available, bool):
        raise SkillConsumptionError("HOST_DISCOVERY_TRANSPORT_TYPE_INVALID")
    return record


def _validate_generic_host_discovery_record(
    root: Path,
    host: str,
    value: HostDiscoveryRecord | Mapping[str, Any] | None,
) -> HostDiscoveryRecord:
    record = _coerce_generic_host_discovery_record(value)
    host_name = _destination_host_token(host)
    record_host = _destination_host_token(record.host_id)
    profile_host = _destination_host_token(record.profile.host_label or "")
    if not host_name or record_host != host_name or profile_host != host_name:
        raise SkillConsumptionError("HOST_DISCOVERY_RECORD_HOST_MISMATCH")
    if record.availability != AVAILABLE:
        raise SkillConsumptionError("HOST_DISCOVERY_HOST_NOT_AVAILABLE")
    if record.active is not True:
        raise SkillConsumptionError("HOST_DISCOVERY_RECORD_INACTIVE")
    if record.execution_transport_available is not True:
        raise SkillConsumptionError("HOST_DISCOVERY_TRANSPORT_UNAVAILABLE")
    if record.profile.state("can_read_files") != SUPPORTED:
        raise SkillConsumptionError("HOST_DISCOVERY_REPO_READ_UNSUPPORTED")
    if record.profile.environment not in {
        "REMOTE_REPOSITORY",
        "CLOUD_SANDBOX",
    }:
        raise SkillConsumptionError(
            "HOST_DISCOVERY_ENVIRONMENT_NOT_REPO_BOUND"
        )
    if record.environment_binding != record.profile.environment:
        raise SkillConsumptionError("HOST_DISCOVERY_ENVIRONMENT_MISMATCH")
    repository = _canonical_repo_binding(root)
    if repository is None:
        raise SkillConsumptionError(
            "HOST_CANONICAL_REPO_BINDING_UNAVAILABLE"
        )
    if str(record.project_binding or "").strip().lower() != repository:
        raise SkillConsumptionError("HOST_DISCOVERY_PROJECT_MISMATCH")
    if str(record.provenance or "").strip().upper() == "DECLARED_PROFILE":
        raise SkillConsumptionError("HOST_DISCOVERY_DECLARATIVE_ONLY")
    try:
        observed = datetime.fromisoformat(
            str(record.observed_at).replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise SkillConsumptionError(
            "HOST_DISCOVERY_TIMESTAMP_INVALID"
        ) from exc
    if observed.tzinfo is None:
        raise SkillConsumptionError(
            "HOST_DISCOVERY_TIMESTAMP_TIMEZONE_REQUIRED"
        )
    age = (
        datetime.now(timezone.utc)
        - observed.astimezone(timezone.utc)
    ).total_seconds()
    if age < -GENERIC_DISCOVERY_MAX_FUTURE_SKEW_SECONDS:
        raise SkillConsumptionError(
            "HOST_DISCOVERY_EVIDENCE_FROM_FUTURE"
        )
    if age > GENERIC_DISCOVERY_MAX_AGE_SECONDS:
        raise SkillConsumptionError("HOST_DISCOVERY_EVIDENCE_STALE")
    return record


def authorize_prompt_only_skill_handoff(
    root: str | Path,
    handoff: Mapping[str, Any],
    *,
    request_text: str,
    host: str,
    host_discovery_record: HostDiscoveryRecord | Mapping[str, Any] | None,
    trusted_evidence_bytes: bytes,
    trusted_oidc_token: str,
) -> dict[str, Any]:
    """Upgrade one exact PREPARED handoff after trusted external read proof."""
    project_root = Path(root).resolve()
    build_prompt_only_delegated_prompt(
        project_root,
        handoff,
        request_text=request_text,
        host=host,
        allow_inline_skill_content=False,
    )
    repository = _canonical_repo_binding(project_root)
    revision = _current_repo_revision(project_root)
    if repository is None:
        raise SkillConsumptionError(
            "HOST_CANONICAL_REPO_BINDING_UNAVAILABLE"
        )
    if revision is None:
        raise SkillConsumptionError(
            "HOST_CANONICAL_REPO_REVISION_UNAVAILABLE"
        )
    host_name = _destination_host_token(host)
    if host_name in HOST_MODES:
        raise SkillConsumptionError(
            "GENERIC_REPO_READ_NATIVE_HOST_FORBIDDEN"
        )
    _validate_generic_host_discovery_record(
        project_root,
        host_name,
        host_discovery_record,
    )
    task_sha = prompt_only_task_sha256(request_text)
    handoff_fingerprint = prompt_only_handoff_fingerprint(
        handoff,
        request_text=request_text,
        host=host_name,
    )
    try:
        trust = verify_github_oidc_repo_read_evidence(
            trusted_evidence_bytes,
            trusted_oidc_token,
            expected_repository=repository,
            expected_revision=revision,
            expected_workflow_path=(
                TRUSTED_GENERIC_REPO_READ_WORKFLOW_PATH
            ),
            expected_host=host_name,
            expected_task_sha256=task_sha,
            expected_handoff_fingerprint=handoff_fingerprint,
            expected_skill_paths=dict(
                handoff.get("SKILL_SOURCE_PATHS") or {}
            ),
            expected_skill_hashes=dict(
                handoff.get("SKILL_SOURCE_HASHES") or {}
            ),
        )
    except TrustedRepoReadEvidenceError as exc:
        raise SkillConsumptionError(str(exc)) from exc

    authorized = dict(handoff)
    authorized.update({
        "SKILL_CHECK": "PASS",
        "SKILL_HOST_MODE": GENERIC_REPO_READ_MODE,
        "SKILL_CONSUMPTION": "CONSUMED",
        "SOURCE_VALIDATION": "PASS",
        "RECIPIENT_CONSUMPTION": "VERIFIED",
        "EXECUTION_AUTHORIZED": "YES",
        "OPERATION": "EXECUTE",
        "DELIVERY_CAPABILITY": GENERIC_REPO_READ_MODE,
        "PERMISSION_WIDENED": "NO",
        "SINGLE_ROUTER_REUSED": "YES",
        "TRUST_EVIDENCE_CLASS": trust["evidence_class"],
        "TRUST_EVIDENCE_SHA256": trust["evidence_sha256"],
        "TRUST_EVIDENCE_RUN_ID": trust["run_id"],
        "TRUST_EVIDENCE_JTI": trust["jti"],
        "TASK_SHA256": task_sha,
        "PROMPT_ONLY_HANDOFF_FINGERPRINT": handoff_fingerprint,
    })
    return authorized


def prepare_prompt_only_skill_handoff(
    root: str | Path,
    request_text: str,
    *,
    host: str,
    explicit_requests: Iterable[str] = (),
    required_skills: Iterable[str] = (),
    allow_inline_skill_content: bool = False,
    max_prompt_chars: int | None = None,
) -> dict[str, Any]:
    """Prepare a generic source-bound prompt without starting execution."""
    project_root = Path(root).resolve()

    def blocked(reason: str, required: Sequence[str] = ()) -> dict[str, Any]:
        handoff = {
            "schema": HANDOFF_SCHEMA,
            "SKILL_CHECK": "BLOCKED",
            "REQUIRED_SKILLS": list(required),
            "SKILLS_CONSIDERED_METADATA_COUNT": 0,
            "SKILLS_SELECTED": [],
            "SKILL_LOAD_STAGE": "DISCOVERY",
            "SKILL_SOURCE_HASHES": {},
            "SKILL_SOURCE_PATHS": {},
            "SKILL_CONSUMPTION": "BLOCKED",
            "SKILL_HOST_MODE": GENERIC_PROMPT_ONLY_MODE,
            "MATERIAL_ALTERNATIVES_REJECTED": [],
            "REJECTION_REASON": [reason],
            "PERMISSION_WIDENED": "NO",
            "SINGLE_ROUTER_REUSED": "YES",
            "SOURCE_VALIDATION": "BLOCKED",
            "RECIPIENT_CONSUMPTION": "NOT_ATTESTED",
            "EXECUTION_AUTHORIZED": "NO",
            "OPERATION": "PREPARE",
            "DELIVERY_CAPABILITY": PROMPT_ONLY_CAPABILITY,
        }
        return {
            "status": "BLOCKED",
            "operation": "PREPARE",
            "execution_authorized": False,
            "automatic_start": False,
            "delivery_capability": PROMPT_ONLY_CAPABILITY,
            "skill_handoff": handoff,
            "prompt": None,
            "source_validation": "BLOCKED",
            "recipient_consumption": "NOT_ATTESTED",
            "external_actor_read": "NOT_VERIFIED",
        }

    try:
        host_name = _destination_host_token(host)
    except SkillConsumptionError as exc:
        return blocked(str(exc))
    if not host_name:
        return blocked("HOST_REQUIRED")
    if host_name in HOST_MODES:
        return blocked("PROMPT_ONLY_NATIVE_HOST_FORBIDDEN")

    actual_repo = _canonical_repo_binding(project_root)
    actual_revision = _current_repo_revision(project_root)
    if actual_repo is None:
        return blocked("HOST_CANONICAL_REPO_BINDING_UNAVAILABLE")
    if actual_revision is None:
        return blocked("HOST_CANONICAL_REPO_REVISION_UNAVAILABLE")

    try:
        required_ids = _resolve_required_skill_ids(
            project_root, required_skills
        )
    except SkillConsumptionError as exc:
        return blocked(str(exc))

    selection = select_skills_for_task(
        project_root,
        request_text,
        explicit_requests=tuple(explicit_requests) + required_ids,
    )
    missing_required = tuple(
        skill_id for skill_id in required_ids
        if skill_id not in selection.selected
    )
    if missing_required:
        return blocked(
            "REQUIRED_SKILL_NOT_SELECTED:" + ",".join(missing_required),
            required_ids,
        )

    if not selection.selected:
        handoff = {
            "schema": HANDOFF_SCHEMA,
            "SKILL_CHECK": "NO_MATCH",
            "REQUIRED_SKILLS": [],
            "SKILLS_CONSIDERED_METADATA_COUNT": selection.considered_metadata_count,
            "SKILLS_SELECTED": [],
            "SKILL_LOAD_STAGE": "DISCOVERY",
            "SKILL_SOURCE_HASHES": {},
            "SKILL_SOURCE_PATHS": {},
            "SKILL_CONSUMPTION": "NO_SKILL_NEEDED",
            "SKILL_HOST_MODE": GENERIC_PROMPT_ONLY_MODE,
            "MATERIAL_ALTERNATIVES_REJECTED": list(selection.rejected),
            "REJECTION_REASON": list(selection.rejection_reasons),
            "PERMISSION_WIDENED": "NO",
            "SINGLE_ROUTER_REUSED": "YES",
            "SOURCE_VALIDATION": "NO_MATCH",
            "RECIPIENT_CONSUMPTION": "NOT_REQUIRED",
            "EXECUTION_AUTHORIZED": "NO",
            "OPERATION": "PREPARE",
            "DELIVERY_CAPABILITY": PROMPT_ONLY_CAPABILITY,
            "DESTINATION_HOST": host_name,
            "REPOSITORY": actual_repo,
            "REVISION": actual_revision,
        }
    else:
        try:
            loaded = load_selected_skills(project_root, selection.selected)
        except SkillConsumptionError as exc:
            return blocked(str(exc), required_ids)
        binding_error = _source_binding_error(loaded, project_root)
        if binding_error is not None:
            return blocked(binding_error, required_ids)
        handoff = {
            "schema": HANDOFF_SCHEMA,
            "SKILL_CHECK": "PREPARED",
            "REQUIRED_SKILLS": list(required_ids),
            "SKILLS_CONSIDERED_METADATA_COUNT": selection.considered_metadata_count,
            "SKILLS_SELECTED": [item.capability_id for item in loaded],
            "SKILL_LOAD_STAGE": "LOAD",
            "SKILL_SOURCE_HASHES": {
                item.capability_id: item.sha256 for item in loaded
            },
            "SKILL_SOURCE_PATHS": {
                item.capability_id: item.relative_path for item in loaded
            },
            "SKILL_CONSUMPTION": "EXPECTED_AFTER_RECIPIENT_READ",
            "SKILL_HOST_MODE": GENERIC_PROMPT_ONLY_MODE,
            "MATERIAL_ALTERNATIVES_REJECTED": list(selection.rejected),
            "REJECTION_REASON": list(selection.rejection_reasons),
            "PERMISSION_WIDENED": "NO",
            "SINGLE_ROUTER_REUSED": "YES",
            "SOURCE_VALIDATION": "PASS",
            "RECIPIENT_CONSUMPTION": "UNVERIFIED",
            "EXECUTION_AUTHORIZED": "NO",
            "OPERATION": "PREPARE",
            "DELIVERY_CAPABILITY": PROMPT_ONLY_CAPABILITY,
            "DESTINATION_HOST": host_name,
            "REPOSITORY": actual_repo,
            "REVISION": actual_revision,
        }

    try:
        prompt = build_prompt_only_delegated_prompt(
            project_root,
            handoff,
            request_text=request_text,
            host=host,
            allow_inline_skill_content=allow_inline_skill_content,
            max_prompt_chars=max_prompt_chars,
        )
    except SkillConsumptionError as exc:
        return blocked(str(exc), required_ids)

    status = str(handoff["SKILL_CHECK"])
    return {
        "status": status,
        "operation": "PREPARE",
        "execution_authorized": False,
        "automatic_start": False,
        "delivery_capability": PROMPT_ONLY_CAPABILITY,
        "skill_handoff": handoff,
        "prompt": prompt,
        "source_validation": str(handoff["SOURCE_VALIDATION"]),
        "recipient_consumption": str(handoff["RECIPIENT_CONSUMPTION"]),
        "external_actor_read": "NOT_VERIFIED",
    }


def validate_consumption_receipt(
    handoff: Mapping[str, Any],
    receipt: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Validate executor self-report against the frozen source-bound handoff."""
    if not isinstance(receipt, Mapping):
        return {"valid": False, "reason_codes": ["SKILL_CONSUMPTION_RECEIPT_MISSING"]}
    reasons: list[str] = []
    if receipt.get("schema") not in (None, RECEIPT_SCHEMA):
        reasons.append("SKILL_CONSUMPTION_RECEIPT_SCHEMA_INVALID")
    expected_check = str(handoff.get("SKILL_CHECK") or "BLOCKED")
    expected_ids = tuple(str(v) for v in (handoff.get("SKILLS_SELECTED") or ()))
    required_ids = tuple(str(v) for v in (handoff.get("REQUIRED_SKILLS") or ()))
    actual_ids = tuple(str(v) for v in (receipt.get("SKILLS_SELECTED") or ()))
    if any(skill_id not in expected_ids for skill_id in required_ids):
        reasons.append("REQUIRED_SKILL_SET_NOT_SELECTED")
    if actual_ids != expected_ids:
        reasons.append("SKILL_SELECTED_SET_MISMATCH")
    if dict(receipt.get("SKILL_SOURCE_HASHES") or {}) != dict(
        handoff.get("SKILL_SOURCE_HASHES") or {}
    ):
        reasons.append("SKILL_SOURCE_HASH_MISMATCH")
    if str(receipt.get("SKILL_HOST_MODE") or "") != str(
        handoff.get("SKILL_HOST_MODE") or ""
    ):
        reasons.append("SKILL_HOST_MODE_MISMATCH")
    if str(receipt.get("PERMISSION_WIDENED") or "UNKNOWN").upper() != "NO":
        reasons.append("SKILL_PERMISSION_WIDENING_REJECTED")
    if expected_check == "PASS":
        if str(receipt.get("SKILL_LOAD_STAGE") or "") != "LOAD":
            reasons.append("SKILL_LOAD_STAGE_MISMATCH")
        if str(receipt.get("SKILL_CONSUMPTION") or "") != "CONSUMED":
            reasons.append("SKILL_NOT_CONSUMED")
    elif expected_check == "NO_MATCH":
        if str(receipt.get("SKILL_CONSUMPTION") or "") != "NO_SKILL_NEEDED":
            reasons.append("SKILL_NO_MATCH_RECEIPT_INVALID")
    else:
        reasons.append("SKILL_HANDOFF_WAS_BLOCKED")
    return {"valid": not reasons, "reason_codes": reasons}


__all__ = [
    "HANDOFF_SCHEMA", "RECEIPT_SCHEMA", "FANOUT_INHERITANCE_SCHEMA",
    "MAX_SELECTED_SKILLS",
    "HOST_MODES", "GENERIC_PROMPT_ONLY_MODE", "GENERIC_REPO_READ_MODE",
    "PROMPT_ONLY_CAPABILITY", "PROMPT_ONLY_MAX_PROMPT_CHARS",
    "TRUSTED_GENERIC_REPO_READ_WORKFLOW_PATH", "SkillConsumptionError",
    "SkillSelection", "LoadedSkill",
    "RepoSkillMetadata",
    "select_skills_for_task", "load_selected_skills", "prepare_skill_handoff",
    "prepare_prompt_only_skill_handoff", "build_prompt_only_delegated_prompt",
    "prompt_only_task_sha256", "prompt_only_handoff_fingerprint",
    "authorize_prompt_only_skill_handoff",
    "freeze_skill_handoff_for_orca_candidates",
    "validate_orca_skill_inheritance",
    "skill_handoff_prompt_lines", "validate_consumption_receipt",
]
