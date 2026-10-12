"""Trusted external repo-read evidence for Issue #333.

This module verifies a GitHub Actions OIDC token and binds it to the exact
canonical evidence bytes produced after an external non-Arena/non-Codex actor
read and applied one frozen repo-native skill handoff. It is deliberately
small: GitHub OIDC is the evidence issuer; C20/C21 remain discovery only.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import urllib.parse
import urllib.request
from typing import Any, Mapping

EVIDENCE_SCHEMA = "p2p-generic-repo-read-evidence/1"
OIDC_ISSUER = "https://token.actions.githubusercontent.com"
OIDC_DISCOVERY_URL = OIDC_ISSUER + "/.well-known/openid-configuration"
OIDC_AUDIENCE_PREFIX = "p2p-generic-repo-read:"
GENERIC_REPO_READ_MODE = "GENERIC_EXACT_REPO_READ"
MAX_EVIDENCE_BYTES = 128 * 1024
MAX_TOKEN_CHARS = 32 * 1024
MAX_CLOCK_SKEW_SECONDS = 60
MAX_TOKEN_LIFETIME_SECONDS = 20 * 60


class TrustedRepoReadEvidenceError(ValueError):
    """Fail-closed evidence validation error with one stable code."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise TrustedRepoReadEvidenceError("TRUST_EVIDENCE_JSON_DUPLICATE_KEY")
        result[key] = value
    return result


def _json_object(raw: bytes | str, code: str) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
        value = json.loads(text, object_pairs_hook=_reject_duplicates)
    except TrustedRepoReadEvidenceError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise TrustedRepoReadEvidenceError(code) from exc
    if not isinstance(value, dict):
        raise TrustedRepoReadEvidenceError(code)
    return value


def _b64url_decode(value: str, code: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise TrustedRepoReadEvidenceError(code)
    try:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, TypeError) as exc:
        raise TrustedRepoReadEvidenceError(code) from exc


def _b64url_int(value: Any, code: str) -> int:
    if not isinstance(value, str):
        raise TrustedRepoReadEvidenceError(code)
    raw = _b64url_decode(value, code)
    if not raw:
        raise TrustedRepoReadEvidenceError(code)
    return int.from_bytes(raw, "big")


def _hex64(value: Any, code: str) -> str:
    text = str(value or "").strip().lower()
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise TrustedRepoReadEvidenceError(code)
    return text


def _integer_claim(claims: Mapping[str, Any], name: str) -> int:
    value = claims.get(name)
    if isinstance(value, bool) or not isinstance(value, int):
        raise TrustedRepoReadEvidenceError(f"TRUST_OIDC_{name.upper()}_INVALID")
    return value


def _fetch_json(url: str) -> dict[str, Any]:
    parsed = urllib.parse.urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "token.actions.githubusercontent.com"
    ):
        raise TrustedRepoReadEvidenceError("TRUST_OIDC_ENDPOINT_INVALID")
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "p2p-issue-333/1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read(256 * 1024 + 1)
    except Exception as exc:
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_PROVIDER_UNAVAILABLE"
        ) from exc
    if len(raw) > 256 * 1024:
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_PROVIDER_RESPONSE_TOO_LARGE"
        )
    return _json_object(raw, "TRUST_OIDC_PROVIDER_JSON_INVALID")


def _verify_rs256(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise TrustedRepoReadEvidenceError("TRUST_OIDC_TOKEN_INVALID")
    header64, payload64, signature64 = parts
    header = _json_object(
        _b64url_decode(header64, "TRUST_OIDC_HEADER_INVALID"),
        "TRUST_OIDC_HEADER_INVALID",
    )
    claims = _json_object(
        _b64url_decode(payload64, "TRUST_OIDC_CLAIMS_INVALID"),
        "TRUST_OIDC_CLAIMS_INVALID",
    )
    if header.get("alg") != "RS256":
        raise TrustedRepoReadEvidenceError("TRUST_OIDC_ALG_INVALID")
    kid = header.get("kid")
    if not isinstance(kid, str) or not kid or len(kid) > 256:
        raise TrustedRepoReadEvidenceError("TRUST_OIDC_KID_INVALID")

    discovery = _fetch_json(OIDC_DISCOVERY_URL)
    if discovery.get("issuer") != OIDC_ISSUER:
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_ISSUER_DISCOVERY_MISMATCH"
        )
    jwks_uri = discovery.get("jwks_uri")
    if not isinstance(jwks_uri, str):
        raise TrustedRepoReadEvidenceError("TRUST_OIDC_JWKS_URI_INVALID")
    jwks = _fetch_json(jwks_uri)
    keys = jwks.get("keys")
    if not isinstance(keys, list):
        raise TrustedRepoReadEvidenceError("TRUST_OIDC_JWKS_INVALID")
    key = next(
        (
            candidate
            for candidate in keys
            if isinstance(candidate, Mapping) and candidate.get("kid") == kid
        ),
        None,
    )
    if key is None:
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_SIGNING_KEY_NOT_FOUND"
        )
    if key.get("kty") != "RSA" or key.get("use") not in (None, "sig"):
        raise TrustedRepoReadEvidenceError("TRUST_OIDC_SIGNING_KEY_INVALID")
    if key.get("alg") not in (None, "RS256"):
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_SIGNING_KEY_ALG_INVALID"
        )

    modulus = _b64url_int(
        key.get("n"), "TRUST_OIDC_RSA_MODULUS_INVALID"
    )
    exponent = _b64url_int(
        key.get("e"), "TRUST_OIDC_RSA_EXPONENT_INVALID"
    )
    if modulus.bit_length() < 2048 or exponent < 3 or exponent % 2 == 0:
        raise TrustedRepoReadEvidenceError("TRUST_OIDC_RSA_KEY_INVALID")
    signature = _b64url_decode(
        signature64, "TRUST_OIDC_SIGNATURE_INVALID"
    )
    key_bytes = (modulus.bit_length() + 7) // 8
    if len(signature) != key_bytes:
        raise TrustedRepoReadEvidenceError("TRUST_OIDC_SIGNATURE_INVALID")
    decoded = pow(
        int.from_bytes(signature, "big"), exponent, modulus
    ).to_bytes(key_bytes, "big")
    digest = hashlib.sha256(
        f"{header64}.{payload64}".encode("ascii")
    ).digest()
    digest_info = (
        bytes.fromhex("3031300d060960864801650304020105000420")
        + digest
    )
    padding_len = key_bytes - len(digest_info) - 3
    if padding_len < 8:
        raise TrustedRepoReadEvidenceError("TRUST_OIDC_SIGNATURE_INVALID")
    expected = (
        b"\x00\x01"
        + (b"\xff" * padding_len)
        + b"\x00"
        + digest_info
    )
    if not hmac.compare_digest(decoded, expected):
        raise TrustedRepoReadEvidenceError("TRUST_OIDC_SIGNATURE_INVALID")
    return claims


def _exact_string(value: Any, expected: str, code: str) -> None:
    if not isinstance(value, str) or value != expected:
        raise TrustedRepoReadEvidenceError(code)


def _exact_bool(value: Any, expected: bool, code: str) -> None:
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
    """Verify one GitHub-signed external repo-read evidence subject."""
    if not isinstance(evidence_bytes, bytes) or not evidence_bytes:
        raise TrustedRepoReadEvidenceError("TRUST_EVIDENCE_REQUIRED")
    if len(evidence_bytes) > MAX_EVIDENCE_BYTES:
        raise TrustedRepoReadEvidenceError("TRUST_EVIDENCE_TOO_LARGE")
    if not isinstance(oidc_token, str) or not oidc_token.strip():
        raise TrustedRepoReadEvidenceError("TRUST_OIDC_TOKEN_REQUIRED")
    token = oidc_token.strip()
    if len(token) > MAX_TOKEN_CHARS:
        raise TrustedRepoReadEvidenceError("TRUST_OIDC_TOKEN_TOO_LARGE")

    repository = str(expected_repository or "").strip().lower()
    revision = str(expected_revision or "").strip().lower()
    host = str(expected_host or "").strip().upper()
    workflow_path = str(expected_workflow_path or "").strip()
    if not repository or "/" not in repository:
        raise TrustedRepoReadEvidenceError(
            "TRUST_EXPECTED_REPOSITORY_INVALID"
        )
    if (
        len(revision) != 40
        or any(ch not in "0123456789abcdef" for ch in revision)
    ):
        raise TrustedRepoReadEvidenceError(
            "TRUST_EXPECTED_REVISION_INVALID"
        )
    if (
        not workflow_path.startswith(".github/workflows/")
        or ".." in workflow_path.split("/")
    ):
        raise TrustedRepoReadEvidenceError(
            "TRUST_EXPECTED_WORKFLOW_INVALID"
        )
    if not host:
        raise TrustedRepoReadEvidenceError("TRUST_EXPECTED_HOST_INVALID")
    task_sha = _hex64(
        expected_task_sha256, "TRUST_EXPECTED_TASK_SHA_INVALID"
    )
    handoff_fp = _hex64(
        expected_handoff_fingerprint,
        "TRUST_EXPECTED_HANDOFF_FINGERPRINT_INVALID",
    )
    skill_paths = {
        str(key): str(value)
        for key, value in expected_skill_paths.items()
    }
    skill_hashes = {
        str(key): _hex64(
            value, f"TRUST_EXPECTED_SKILL_HASH_INVALID:{key}"
        )
        for key, value in expected_skill_hashes.items()
    }
    if not skill_paths or set(skill_paths) != set(skill_hashes):
        raise TrustedRepoReadEvidenceError(
            "TRUST_EXPECTED_SKILL_SET_INVALID"
        )

    evidence_sha = hashlib.sha256(evidence_bytes).hexdigest()
    evidence = _json_object(
        evidence_bytes, "TRUST_EVIDENCE_JSON_INVALID"
    )
    claims = _verify_rs256(token)

    expected_audience = OIDC_AUDIENCE_PREFIX + evidence_sha
    audience = claims.get("aud")
    audience_ok = audience == expected_audience or (
        isinstance(audience, list)
        and all(isinstance(item, str) for item in audience)
        and expected_audience in audience
    )
    if not audience_ok:
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_AUDIENCE_MISMATCH"
        )
    _exact_string(
        claims.get("iss"),
        OIDC_ISSUER,
        "TRUST_OIDC_ISSUER_MISMATCH",
    )
    _exact_string(
        str(claims.get("repository") or "").lower(),
        repository,
        "TRUST_OIDC_REPOSITORY_MISMATCH",
    )
    _exact_string(
        str(claims.get("workflow_sha") or "").lower(),
        revision,
        "TRUST_OIDC_WORKFLOW_SHA_MISMATCH",
    )
    _exact_string(
        claims.get("runner_environment"),
        "github-hosted",
        "TRUST_OIDC_RUNNER_ENVIRONMENT_INVALID",
    )
    subject = claims.get("sub")
    if (
        not isinstance(subject, str)
        or not subject.startswith(f"repo:{repository}:")
    ):
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_SUBJECT_MISMATCH"
        )
    workflow_ref = claims.get("workflow_ref")
    if not isinstance(workflow_ref, str):
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_WORKFLOW_REF_INVALID"
        )
    expected_workflow_prefix = f"{repository}/{workflow_path}@"
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
        raise TrustedRepoReadEvidenceError("TRUST_OIDC_JTI_INVALID")

    now = int(time.time())
    issued_at = _integer_claim(claims, "iat")
    not_before = _integer_claim(claims, "nbf")
    expires_at = _integer_claim(claims, "exp")
    if (
        issued_at > now + MAX_CLOCK_SKEW_SECONDS
        or not_before > now + MAX_CLOCK_SKEW_SECONDS
    ):
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_TOKEN_FROM_FUTURE"
        )
    if (
        expires_at < now - MAX_CLOCK_SKEW_SECONDS
        or expires_at <= issued_at
    ):
        raise TrustedRepoReadEvidenceError("TRUST_OIDC_TOKEN_EXPIRED")
    if expires_at - issued_at > MAX_TOKEN_LIFETIME_SECONDS:
        raise TrustedRepoReadEvidenceError(
            "TRUST_OIDC_TOKEN_LIFETIME_INVALID"
        )

    if evidence.get("schema") != EVIDENCE_SCHEMA:
        raise TrustedRepoReadEvidenceError(
            "TRUST_EVIDENCE_SCHEMA_INVALID"
        )
    _exact_string(
        str(evidence.get("repository") or "").lower(),
        repository,
        "TRUST_EVIDENCE_REPOSITORY_MISMATCH",
    )
    _exact_string(
        str(evidence.get("revision") or "").lower(),
        revision,
        "TRUST_EVIDENCE_REVISION_MISMATCH",
    )
    _exact_string(
        evidence.get("workflow_ref"),
        workflow_ref,
        "TRUST_EVIDENCE_WORKFLOW_MISMATCH",
    )
    _exact_string(
        str(evidence.get("run_id") or ""),
        str(claims.get("run_id") or ""),
        "TRUST_EVIDENCE_RUN_ID_MISMATCH",
    )
    run_attempt = evidence.get("run_attempt")
    claim_attempt = claims.get("run_attempt")
    if isinstance(run_attempt, bool) or not isinstance(run_attempt, int):
        raise TrustedRepoReadEvidenceError(
            "TRUST_EVIDENCE_RUN_ATTEMPT_INVALID"
        )
    if str(run_attempt) != str(claim_attempt or ""):
        raise TrustedRepoReadEvidenceError(
            "TRUST_EVIDENCE_RUN_ATTEMPT_MISMATCH"
        )
    _exact_string(
        evidence.get("runner_environment"),
        "github-hosted",
        "TRUST_EVIDENCE_RUNNER_ENVIRONMENT_INVALID",
    )
    _exact_string(
        str(evidence.get("actor") or "").upper(),
        host,
        "TRUST_EVIDENCE_HOST_MISMATCH",
    )
    _exact_bool(
        evidence.get("arena"),
        False,
        "TRUST_EVIDENCE_ARENA_INVALID",
    )
    _exact_bool(
        evidence.get("codex"),
        False,
        "TRUST_EVIDENCE_CODEX_INVALID",
    )
    _exact_bool(
        evidence.get("skill_applied"),
        True,
        "TRUST_EVIDENCE_SKILL_NOT_APPLIED",
    )
    _exact_bool(
        evidence.get("tool_trace_validated"),
        True,
        "TRUST_EVIDENCE_TOOL_TRACE_NOT_VALIDATED",
    )
    _exact_string(
        str(evidence.get("permission_widened") or "").upper(),
        "NO",
        "TRUST_EVIDENCE_PERMISSION_WIDENED",
    )
    _exact_string(
        str(evidence.get("task_sha256") or "").lower(),
        task_sha,
        "TRUST_EVIDENCE_TASK_MISMATCH",
    )
    _exact_string(
        str(evidence.get("handoff_fingerprint") or "").lower(),
        handoff_fp,
        "TRUST_EVIDENCE_HANDOFF_MISMATCH",
    )
    _hex64(
        evidence.get("result_sha256"),
        "TRUST_EVIDENCE_RESULT_SHA_INVALID",
    )
    _hex64(
        evidence.get("transcript_sha256"),
        "TRUST_EVIDENCE_TRANSCRIPT_SHA_INVALID",
    )

    receipt = evidence.get("skill_consumption_receipt")
    if not isinstance(receipt, Mapping):
        raise TrustedRepoReadEvidenceError(
            "TRUST_EVIDENCE_RECEIPT_MISSING"
        )
    if (
        receipt.get("schema")
        != "p2p-skill-consumption-receipt/1"
    ):
        raise TrustedRepoReadEvidenceError(
            "TRUST_EVIDENCE_RECEIPT_SCHEMA_INVALID"
        )
    selected = receipt.get("SKILLS_SELECTED")
    if not isinstance(selected, list) or selected != list(skill_paths):
        raise TrustedRepoReadEvidenceError(
            "TRUST_EVIDENCE_SKILL_SET_MISMATCH"
        )
    if dict(receipt.get("SKILL_SOURCE_PATHS") or {}) != skill_paths:
        raise TrustedRepoReadEvidenceError(
            "TRUST_EVIDENCE_SKILL_PATH_MISMATCH"
        )
    if {
        str(key): str(value).lower()
        for key, value in dict(
            receipt.get("SKILL_SOURCE_HASHES") or {}
        ).items()
    } != skill_hashes:
        raise TrustedRepoReadEvidenceError(
            "TRUST_EVIDENCE_SKILL_HASH_MISMATCH"
        )
    _exact_string(
        receipt.get("SKILL_LOAD_STAGE"),
        "LOAD",
        "TRUST_EVIDENCE_LOAD_STAGE_INVALID",
    )
    _exact_string(
        receipt.get("SKILL_CONSUMPTION"),
        "CONSUMED",
        "TRUST_EVIDENCE_CONSUMPTION_INVALID",
    )
    _exact_string(
        receipt.get("SKILL_HOST_MODE"),
        GENERIC_REPO_READ_MODE,
        "TRUST_EVIDENCE_HOST_MODE_INVALID",
    )
    _exact_string(
        str(receipt.get("PERMISSION_WIDENED") or "").upper(),
        "NO",
        "TRUST_EVIDENCE_RECEIPT_PERMISSION_WIDENED",
    )

    return {
        "valid": True,
        "evidence_class": "GITHUB_OIDC_BOUND_EXTERNAL_REPO_READ",
        "evidence_sha256": evidence_sha,
        "repository": repository,
        "revision": revision,
        "host": host,
        "run_id": str(claims.get("run_id")),
        "run_attempt": str(claims.get("run_attempt")),
        "workflow_ref": workflow_ref,
        "workflow_sha": revision,
        "runner_environment": "github-hosted",
        "jti": jti,
        "task_sha256": task_sha,
        "handoff_fingerprint": handoff_fp,
    }


__all__ = [
    "EVIDENCE_SCHEMA",
    "GENERIC_REPO_READ_MODE",
    "OIDC_AUDIENCE_PREFIX",
    "OIDC_ISSUER",
    "TrustedRepoReadEvidenceError",
    "verify_github_oidc_repo_read_evidence",
]
