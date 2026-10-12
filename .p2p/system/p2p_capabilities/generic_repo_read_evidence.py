"""Verified GitHub Actions OIDC evidence for generic repo-read admission.

This is a bounded evidence verifier, not a host router and not a permission
grant.  A valid result proves that the reviewed GitHub Actions workflow bound
an exact evidence subject to GitHub's signed OIDC identity for the current
repository revision.  Caller-authored JSON without a valid token never passes.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Mapping

EVIDENCE_SCHEMA = "p2p-generic-repo-read-evidence/1"
OIDC_ISSUER = "https://token.actions.githubusercontent.com"
OIDC_DISCOVERY_URL = OIDC_ISSUER + "/.well-known/openid-configuration"
OIDC_AUDIENCE_PREFIX = "p2p-generic-repo-read:"
TRUSTED_WORKFLOW_PATH = ".github/workflows/p2p-b1-real-generic-read-canary.yml"
MAX_EVIDENCE_AGE_SECONDS = 3600
MAX_FUTURE_SKEW_SECONDS = 300
MAX_NETWORK_BYTES = 1024 * 1024
MAX_TOKEN_CHARS = 32768
_HOST_TOKEN_RE = re.compile(r"[A-Z0-9][A-Z0-9_]{0,127}")
_REPO_RE = re.compile(r"[a-z0-9_.\-]+/[a-z0-9_.\-]+")
_SHA40_RE = re.compile(r"[0-9a-f]{40}")
_SHA64_RE = re.compile(r"[0-9a-f]{64}")


class GenericRepoReadEvidenceError(ValueError):
    """Fail-closed evidence verification error with a stable code."""


def canonical_evidence_bytes(evidence: Mapping[str, Any]) -> bytes:
    if not isinstance(evidence, Mapping):
        raise GenericRepoReadEvidenceError("GENERIC_READ_EVIDENCE_MUST_BE_OBJECT")
    try:
        payload = json.dumps(
            dict(evidence),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise GenericRepoReadEvidenceError(
            "GENERIC_READ_EVIDENCE_NOT_CANONICAL_JSON"
        ) from exc
    return (payload + "\n").encode("utf-8")


def evidence_sha256(evidence: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_evidence_bytes(evidence)).hexdigest()


def _required_text(
    evidence: Mapping[str, Any], field: str, *, max_length: int = 1024
) -> str:
    value = evidence.get(field)
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > max_length
        or any(ord(ch) < 32 or ord(ch) == 127 for ch in value)
    ):
        raise GenericRepoReadEvidenceError(
            f"GENERIC_READ_EVIDENCE_FIELD_INVALID:{field}"
        )
    return value.strip()


def _b64url_decode(value: str) -> bytes:
    try:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except Exception as exc:  # noqa: BLE001 - malformed token fails closed.
        raise GenericRepoReadEvidenceError(
            "GITHUB_OIDC_BASE64_INVALID"
        ) from exc


def _fetch_json(url: str) -> Mapping[str, Any]:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != "token.actions.githubusercontent.com":
        raise GenericRepoReadEvidenceError("GITHUB_OIDC_ENDPOINT_UNTRUSTED")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "p2p-generic-repo-read-evidence/1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read(MAX_NETWORK_BYTES + 1)
    except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
        raise GenericRepoReadEvidenceError(
            "GITHUB_OIDC_NETWORK_UNAVAILABLE"
        ) from exc
    if len(raw) > MAX_NETWORK_BYTES:
        raise GenericRepoReadEvidenceError("GITHUB_OIDC_RESPONSE_TOO_LARGE")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GenericRepoReadEvidenceError("GITHUB_OIDC_JSON_INVALID") from exc
    if not isinstance(value, Mapping):
        raise GenericRepoReadEvidenceError("GITHUB_OIDC_JSON_NOT_OBJECT")
    return value


def _verify_rs256(
    signing_input: bytes,
    signature: bytes,
    *,
    modulus_b64: str,
    exponent_b64: str,
) -> None:
    try:
        modulus = int.from_bytes(_b64url_decode(modulus_b64), "big")
        exponent = int.from_bytes(_b64url_decode(exponent_b64), "big")
    except GenericRepoReadEvidenceError:
        raise
    if modulus <= 0 or exponent <= 1 or exponent % 2 == 0:
        raise GenericRepoReadEvidenceError("GITHUB_OIDC_RSA_KEY_INVALID")
    key_bytes = (modulus.bit_length() + 7) // 8
    if key_bytes < 64 or len(signature) > key_bytes:
        raise GenericRepoReadEvidenceError("GITHUB_OIDC_SIGNATURE_INVALID")

    digest_info = (
        bytes.fromhex("3031300d060960864801650304020105000420")
        + hashlib.sha256(signing_input).digest()
    )
    padding_len = key_bytes - len(digest_info) - 3
    if padding_len < 8:
        raise GenericRepoReadEvidenceError("GITHUB_OIDC_RSA_KEY_INVALID")
    expected = b"\x00\x01" + (b"\xff" * padding_len) + b"\x00" + digest_info
    decoded = pow(
        int.from_bytes(signature, "big"), exponent, modulus
    ).to_bytes(key_bytes, "big")
    if not hmac.compare_digest(decoded, expected):
        raise GenericRepoReadEvidenceError("GITHUB_OIDC_SIGNATURE_INVALID")


def _verified_oidc_claims(token: str) -> Mapping[str, Any]:
    if not isinstance(token, str) or not token.strip():
        raise GenericRepoReadEvidenceError("GITHUB_OIDC_TOKEN_REQUIRED")
    compact = token.strip()
    if len(compact) > MAX_TOKEN_CHARS or compact.count(".") != 2:
        raise GenericRepoReadEvidenceError("GITHUB_OIDC_TOKEN_FORMAT_INVALID")
    header_b64, payload_b64, signature_b64 = compact.split(".")
    try:
        header = json.loads(_b64url_decode(header_b64).decode("utf-8"))
        claims = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GenericRepoReadEvidenceError(
            "GITHUB_OIDC_TOKEN_JSON_INVALID"
        ) from exc
    if not isinstance(header, Mapping) or not isinstance(claims, Mapping):
        raise GenericRepoReadEvidenceError("GITHUB_OIDC_TOKEN_JSON_INVALID")
    if header.get("alg") != "RS256":
        raise GenericRepoReadEvidenceError("GITHUB_OIDC_ALG_NOT_ALLOWED")
    kid = header.get("kid")
    if not isinstance(kid, str) or not kid:
        raise GenericRepoReadEvidenceError("GITHUB_OIDC_KID_REQUIRED")

    discovery = _fetch_json(OIDC_DISCOVERY_URL)
    if discovery.get("issuer") != OIDC_ISSUER:
        raise GenericRepoReadEvidenceError("GITHUB_OIDC_ISSUER_DISCOVERY_MISMATCH")
    jwks_uri = discovery.get("jwks_uri")
    if not isinstance(jwks_uri, str):
        raise GenericRepoReadEvidenceError("GITHUB_OIDC_JWKS_URI_MISSING")
    jwks = _fetch_json(jwks_uri)
    keys = jwks.get("keys")
    if not isinstance(keys, list):
        raise GenericRepoReadEvidenceError("GITHUB_OIDC_JWKS_INVALID")
    key = next(
        (
            item
            for item in keys
            if isinstance(item, Mapping)
            and item.get("kid") == kid
            and item.get("kty") == "RSA"
            and item.get("use") in (None, "sig")
        ),
        None,
    )
    if key is None:
        raise GenericRepoReadEvidenceError("GITHUB_OIDC_SIGNING_KEY_NOT_FOUND")
    modulus = key.get("n")
    exponent = key.get("e")
    if not isinstance(modulus, str) or not isinstance(exponent, str):
        raise GenericRepoReadEvidenceError("GITHUB_OIDC_RSA_KEY_INVALID")
    _verify_rs256(
        (header_b64 + "." + payload_b64).encode("ascii"),
        _b64url_decode(signature_b64),
        modulus_b64=modulus,
        exponent_b64=exponent,
    )
    return claims


def verify_generic_repo_read_evidence(
    evidence: Mapping[str, Any] | None,
    oidc_token: str | None,
    *,
    expected_host: str,
    expected_repo: str,
    expected_revision: str,
    expected_probe_path: str,
    expected_probe_sha256: str,
    now_epoch: int | None = None,
) -> dict[str, Any]:
    """Verify one actor-bound repo-read observation.

    The signed OIDC identity is trusted only for the exact reviewed canary
    workflow, exact repository/revision and exact canonical evidence digest.
    It authorizes only GENERIC_EXACT_REPO_READ skill handoff; it never widens
    P2P permissions or proves later skill consumption.
    """
    try:
        if not isinstance(evidence, Mapping):
            raise GenericRepoReadEvidenceError("GENERIC_READ_EVIDENCE_REQUIRED")
        if evidence.get("schema") != EVIDENCE_SCHEMA:
            raise GenericRepoReadEvidenceError(
                "GENERIC_READ_EVIDENCE_SCHEMA_INVALID"
            )

        host = _required_text(evidence, "actor", max_length=128).upper()
        if not _HOST_TOKEN_RE.fullmatch(host) or host != expected_host.upper():
            raise GenericRepoReadEvidenceError("GENERIC_READ_EVIDENCE_ACTOR_MISMATCH")

        repo = _required_text(evidence, "repository", max_length=256).lower()
        if not _REPO_RE.fullmatch(repo) or repo != expected_repo.lower():
            raise GenericRepoReadEvidenceError("GENERIC_READ_EVIDENCE_REPO_MISMATCH")

        revision = _required_text(evidence, "revision", max_length=40).lower()
        if not _SHA40_RE.fullmatch(revision) or revision != expected_revision.lower():
            raise GenericRepoReadEvidenceError(
                "GENERIC_READ_EVIDENCE_REVISION_MISMATCH"
            )

        probe_path = _required_text(evidence, "probe_path", max_length=512)
        if probe_path != expected_probe_path:
            raise GenericRepoReadEvidenceError(
                "GENERIC_READ_EVIDENCE_PROBE_PATH_MISMATCH"
            )
        probe_sha = _required_text(evidence, "probe_sha256", max_length=64).lower()
        if not _SHA64_RE.fullmatch(probe_sha) or probe_sha != expected_probe_sha256.lower():
            raise GenericRepoReadEvidenceError(
                "GENERIC_READ_EVIDENCE_PROBE_HASH_MISMATCH"
            )
        for field in ("result_sha256", "transcript_sha256"):
            digest = _required_text(evidence, field, max_length=64).lower()
            if not _SHA64_RE.fullmatch(digest):
                raise GenericRepoReadEvidenceError(
                    f"GENERIC_READ_EVIDENCE_DIGEST_INVALID:{field}"
                )

        if evidence.get("permission_widened") != "NO":
            raise GenericRepoReadEvidenceError(
                "GENERIC_READ_EVIDENCE_PERMISSION_WIDENING_REJECTED"
            )
        if evidence.get("runner_environment") != "github-hosted":
            raise GenericRepoReadEvidenceError(
                "GENERIC_READ_EVIDENCE_SELF_HOSTED_REJECTED"
            )
        run_id = _required_text(evidence, "run_id", max_length=64)
        run_attempt = evidence.get("run_attempt")
        if type(run_attempt) is not int or run_attempt < 1:
            raise GenericRepoReadEvidenceError(
                "GENERIC_READ_EVIDENCE_RUN_ATTEMPT_INVALID"
            )
        workflow_ref = _required_text(evidence, "workflow_ref", max_length=512)
        trusted_prefix = (
            f"{expected_repo.lower()}/{TRUSTED_WORKFLOW_PATH.lower()}@"
        )
        if not workflow_ref.lower().startswith(trusted_prefix):
            raise GenericRepoReadEvidenceError(
                "GENERIC_READ_EVIDENCE_WORKFLOW_UNTRUSTED"
            )

        claims = _verified_oidc_claims(str(oidc_token or ""))
        if claims.get("iss") != OIDC_ISSUER:
            raise GenericRepoReadEvidenceError("GITHUB_OIDC_ISSUER_MISMATCH")
        expected_audience = OIDC_AUDIENCE_PREFIX + evidence_sha256(evidence)
        audience = claims.get("aud")
        if not (
            audience == expected_audience
            or (isinstance(audience, list) and expected_audience in audience)
        ):
            raise GenericRepoReadEvidenceError("GITHUB_OIDC_AUDIENCE_MISMATCH")
        if str(claims.get("repository") or "").lower() != expected_repo.lower():
            raise GenericRepoReadEvidenceError("GITHUB_OIDC_REPO_MISMATCH")
        if str(claims.get("workflow_sha") or "").lower() != expected_revision.lower():
            raise GenericRepoReadEvidenceError("GITHUB_OIDC_WORKFLOW_SHA_MISMATCH")
        if str(claims.get("workflow_ref") or "") != workflow_ref:
            raise GenericRepoReadEvidenceError("GITHUB_OIDC_WORKFLOW_REF_MISMATCH")
        if str(claims.get("run_id") or "") != run_id:
            raise GenericRepoReadEvidenceError("GITHUB_OIDC_RUN_ID_MISMATCH")
        if str(claims.get("run_attempt") or "") != str(run_attempt):
            raise GenericRepoReadEvidenceError("GITHUB_OIDC_RUN_ATTEMPT_MISMATCH")
        if claims.get("runner_environment") != "github-hosted":
            raise GenericRepoReadEvidenceError("GITHUB_OIDC_SELF_HOSTED_REJECTED")
        if claims.get("event_name") != "push":
            raise GenericRepoReadEvidenceError("GITHUB_OIDC_EVENT_NOT_ALLOWED")
        ref = claims.get("ref")
        if not isinstance(ref, str) or not ref.startswith("refs/heads/"):
            raise GenericRepoReadEvidenceError("GITHUB_OIDC_REF_NOT_BRANCH")

        def claim_epoch(field: str) -> int:
            value = claims.get(field)
            if type(value) is not int:
                raise GenericRepoReadEvidenceError(
                    f"GITHUB_OIDC_TIME_CLAIM_INVALID:{field}"
                )
            return value

        now = int(time.time()) if now_epoch is None else int(now_epoch)
        issued = claim_epoch("iat")
        not_before = claim_epoch("nbf")
        expires = claim_epoch("exp")
        if issued > now + MAX_FUTURE_SKEW_SECONDS:
            raise GenericRepoReadEvidenceError("GITHUB_OIDC_ISSUED_IN_FUTURE")
        if now - issued > MAX_EVIDENCE_AGE_SECONDS:
            raise GenericRepoReadEvidenceError("GITHUB_OIDC_EVIDENCE_STALE")
        if not_before > now + MAX_FUTURE_SKEW_SECONDS:
            raise GenericRepoReadEvidenceError("GITHUB_OIDC_NOT_YET_VALID")
        if expires < now:
            raise GenericRepoReadEvidenceError("GITHUB_OIDC_TOKEN_EXPIRED")

        return {
            "valid": True,
            "reason": None,
            "evidence_sha256": evidence_sha256(evidence),
            "run_id": run_id,
            "workflow_ref": workflow_ref,
            "workflow_sha": expected_revision.lower(),
            "runner_environment": "github-hosted",
        }
    except GenericRepoReadEvidenceError as exc:
        return {"valid": False, "reason": str(exc)}
