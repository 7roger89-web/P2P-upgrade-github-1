"""Issue #333 trusted generic repo-read admission tests."""
from __future__ import annotations

import base64
import hashlib
import json
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.host_executor import SUPPORTED, HostCapabilityProfile  # noqa: E402
from p2p_capabilities.host_selection import AVAILABLE, HostDiscoveryRecord  # noqa: E402
from p2p_capabilities.skill_consumption import (  # noqa: E402
    GENERIC_REPO_READ_MODE,
    TRUSTED_GENERIC_REPO_READ_WORKFLOW_PATH,
    SkillConsumptionError,
    authorize_prompt_only_skill_handoff,
    prepare_prompt_only_skill_handoff,
    prompt_only_handoff_fingerprint,
    prompt_only_task_sha256,
)
from p2p_capabilities import trusted_repo_read_evidence as trust  # noqa: E402

RSA_N = 19491853073119284460730953428560264402647294265593683603120167715152617813812081877413172380836698487002142476015909955044646366525447244057658134561151090017870316487477304760789816970655277782402948361529247634384164565888227873166278255580371335230163818927273281537461159724565505800182447343441447181442940296595168731357681677590929515384469892211198318515451615371777231845095699996348350908110689173375870594262487948630582591098250313221818358541901786200855893541220283514916451330373762388751733380843954615471842687932935979888351021384377109842785737959205197101505010578503490619612381678456932721705133
RSA_E = 65537
RSA_D = 2207333814857769242403398986256589341008092155695476679450643830598862910134865307640998128585527217770636954333654959026041530487557068978560499493945043864523768235722732657374131024467805767862437225127020861394140836776687945211850737550274235820475952151282174514302723251839678281688522972273798625177741056150744843475822101505416271076995342695141331667121025322391116558574511719134144457745454608142695217730886980785124559076133432041680833879333780171173461129150232749428738601075983402938541925115769406224662613446934344775103159927580792719128698015832250789699267689901148654560873460233227646393173
RSA_KID = "p2p-test-rsa-1"
NOW = 2_000_000_000
HOST = "GITHUB_COPILOT_CLI_ACTIONS"
TASK = "@Scope Reality Check xé claim B1 này ra"


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64_int(value: int) -> str:
    size = max(1, (value.bit_length() + 7) // 8)
    return _b64(value.to_bytes(size, "big"))


def _sign_rs256(claims: dict) -> str:
    header = {"alg": "RS256", "kid": RSA_KID, "typ": "JWT"}
    h64 = _b64(json.dumps(
        header, sort_keys=True, separators=(",", ":")
    ).encode())
    p64 = _b64(json.dumps(
        claims, sort_keys=True, separators=(",", ":")
    ).encode())
    signed = f"{h64}.{p64}".encode("ascii")
    digest = hashlib.sha256(signed).digest()
    digest_info = (
        bytes.fromhex("3031300d060960864801650304020105000420")
        + digest
    )
    key_bytes = (RSA_N.bit_length() + 7) // 8
    padding = (
        b"\x00\x01"
        + (b"\xff" * (key_bytes - len(digest_info) - 3))
        + b"\x00"
    )
    encoded = padding + digest_info
    signature = pow(
        int.from_bytes(encoded, "big"), RSA_D, RSA_N
    ).to_bytes(key_bytes, "big")
    return f"{h64}.{p64}.{_b64(signature)}"


class GenericRepoReadOidcTests(unittest.TestCase):
    def setUp(self):
        self.root = REPO_ROOT
        package = prepare_prompt_only_skill_handoff(
            self.root,
            TASK,
            host=HOST,
            required_skills=("scope-reality-check",),
        )
        self.assertEqual(package["status"], "PREPARED")
        self.handoff = package["skill_handoff"]
        self.repo = self.handoff["REPOSITORY"]
        self.revision = self.handoff["REVISION"]
        self.task_sha = prompt_only_task_sha256(TASK)
        self.handoff_fp = prompt_only_handoff_fingerprint(
            self.handoff, request_text=TASK, host=HOST
        )
        self.paths = dict(self.handoff["SKILL_SOURCE_PATHS"])
        self.hashes = dict(self.handoff["SKILL_SOURCE_HASHES"])
        self.workflow_ref = (
            f"{self.repo}/{TRUSTED_GENERIC_REPO_READ_WORKFLOW_PATH}"
            "@refs/heads/test"
        )
        profile = HostCapabilityProfile(
            adapter_class="GitHubCopilotCliActions",
            host_label=HOST,
            environment="CLOUD_SANDBOX",
            capabilities={"can_read_files": SUPPORTED},
        )
        self.discovery = HostDiscoveryRecord(
            host_id=HOST,
            profile=profile,
            availability=AVAILABLE,
            observed_at=datetime.now(timezone.utc).isoformat(),
            provenance="GITHUB_ACTIONS_OIDC_OBSERVED",
            environment_binding="CLOUD_SANDBOX",
            project_binding=self.repo,
            active=True,
            execution_transport_available=True,
        ).to_dict()

    @property
    def jwk(self):
        return {
            "kty": "RSA",
            "use": "sig",
            "alg": "RS256",
            "kid": RSA_KID,
            "n": _b64_int(RSA_N),
            "e": _b64_int(RSA_E),
        }

    def _evidence(self, **overrides):
        receipt = {
            "schema": "p2p-skill-consumption-receipt/1",
            "SKILLS_SELECTED": list(self.paths),
            "SKILL_SOURCE_HASHES": dict(self.hashes),
            "SKILL_SOURCE_PATHS": dict(self.paths),
            "SKILL_LOAD_STAGE": "LOAD",
            "SKILL_CONSUMPTION": "CONSUMED",
            "SKILL_HOST_MODE": GENERIC_REPO_READ_MODE,
            "PERMISSION_WIDENED": "NO",
        }
        value = {
            "schema": "p2p-generic-repo-read-evidence/1",
            "actor": HOST,
            "actor_runtime": "GitHub Copilot CLI",
            "arena": False,
            "codex": False,
            "repository": self.repo,
            "revision": self.revision,
            "workflow_ref": self.workflow_ref,
            "run_id": "12345",
            "run_attempt": 1,
            "runner_environment": "github-hosted",
            "skill_applied": True,
            "tool_trace_validated": True,
            "permission_widened": "NO",
            "task_sha256": self.task_sha,
            "handoff_fingerprint": self.handoff_fp,
            "result_sha256": "a" * 64,
            "transcript_sha256": "b" * 64,
            "skill_consumption_receipt": receipt,
        }
        for key, value_override in overrides.items():
            if key.startswith("receipt__"):
                receipt[key.split("__", 1)[1]] = value_override
            else:
                value[key] = value_override
        return value

    def _raw(self, **overrides):
        return (
            json.dumps(
                self._evidence(**overrides),
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode()

    def _claims(self, evidence_bytes: bytes, **overrides):
        evidence_sha = hashlib.sha256(evidence_bytes).hexdigest()
        value = {
            "iss": trust.OIDC_ISSUER,
            "aud": trust.OIDC_AUDIENCE_PREFIX + evidence_sha,
            "sub": f"repo:{self.repo}:ref:refs/heads/test",
            "repository": self.repo,
            "workflow_ref": self.workflow_ref,
            "workflow_sha": self.revision,
            "runner_environment": "github-hosted",
            "run_id": "12345",
            "run_attempt": "1",
            "jti": "jti-12345",
            "iat": NOW - 10,
            "nbf": NOW - 10,
            "exp": NOW + 600,
        }
        value.update(overrides)
        return value

    def _provider(self, url):
        if url == trust.OIDC_DISCOVERY_URL:
            return {
                "issuer": trust.OIDC_ISSUER,
                "jwks_uri": (
                    trust.OIDC_ISSUER + "/.well-known/jwks"
                ),
            }
        if url == trust.OIDC_ISSUER + "/.well-known/jwks":
            return {"keys": [self.jwk]}
        self.fail(f"unexpected provider URL: {url}")

    def _authorize(
        self,
        raw=None,
        claims=None,
        discovery=None,
        token=None,
    ):
        raw = raw if raw is not None else self._raw()
        claims = claims if claims is not None else self._claims(raw)
        token = token if token is not None else _sign_rs256(claims)
        with patch.object(
            trust, "_fetch_json", side_effect=self._provider
        ), patch.object(trust.time, "time", return_value=NOW):
            return authorize_prompt_only_skill_handoff(
                self.root,
                self.handoff,
                request_text=TASK,
                host=HOST,
                host_discovery_record=(
                    self.discovery if discovery is None else discovery
                ),
                trusted_evidence_bytes=raw,
                trusted_oidc_token=token,
            )

    def test_positive_oidc_evidence_authorizes_exact_generic_handoff(self):
        handoff = self._authorize()
        self.assertEqual(handoff["SKILL_CHECK"], "PASS")
        self.assertEqual(
            handoff["SKILL_HOST_MODE"], GENERIC_REPO_READ_MODE
        )
        self.assertEqual(handoff["EXECUTION_AUTHORIZED"], "YES")
        self.assertEqual(
            handoff["RECIPIENT_CONSUMPTION"], "VERIFIED"
        )
        self.assertEqual(handoff["PERMISSION_WIDENED"], "NO")
        self.assertEqual(handoff["SKILL_SOURCE_PATHS"], self.paths)
        self.assertEqual(handoff["SKILL_SOURCE_HASHES"], self.hashes)
        self.assertEqual(handoff["TASK_SHA256"], self.task_sha)
        self.assertEqual(
            handoff["PROMPT_ONLY_HANDOFF_FINGERPRINT"],
            self.handoff_fp,
        )
        self.assertEqual(
            handoff["TRUST_EVIDENCE_CLASS"],
            "GITHUB_OIDC_BOUND_EXTERNAL_REPO_READ",
        )

    def test_signature_and_oidc_claim_attacks_fail_closed(self):
        raw = self._raw()
        baseline = self._claims(raw)
        cases = {
            "wrong_audience": {
                **baseline,
                "aud": "p2p-generic-repo-read:" + "0" * 64,
            },
            "wrong_repository": {
                **baseline,
                "repository": "other/repo",
            },
            "wrong_revision": {
                **baseline,
                "workflow_sha": "0" * 40,
            },
            "wrong_workflow": {
                **baseline,
                "workflow_ref": (
                    f"{self.repo}/.github/workflows/evil.yml"
                    "@refs/heads/test"
                ),
            },
            "self_hosted": {
                **baseline,
                "runner_environment": "self-hosted",
            },
            "expired": {
                **baseline,
                "iat": NOW - 700,
                "nbf": NOW - 700,
                "exp": NOW - 100,
            },
            "future": {
                **baseline,
                "iat": NOW + 120,
                "nbf": NOW + 120,
                "exp": NOW + 600,
            },
        }
        for name, claims in cases.items():
            with self.subTest(name=name), self.assertRaises(
                SkillConsumptionError
            ):
                self._authorize(raw=raw, claims=claims)

        token = _sign_rs256(baseline)
        h64, p64, signature = token.split(".")
        broken = (
            ("A" if signature[0] != "A" else "B")
            + signature[1:]
        )
        with self.assertRaisesRegex(
            SkillConsumptionError,
            "TRUST_OIDC_SIGNATURE_INVALID",
        ):
            self._authorize(
                raw=raw,
                token=f"{h64}.{p64}.{broken}",
            )

    def test_evidence_task_handoff_skill_and_bytes_attacks_fail_closed(self):
        cases = [
            {"task_sha256": "0" * 64},
            {"handoff_fingerprint": "0" * 64},
            {"actor": "CLAUDE"},
            {"tool_trace_validated": False},
            {"permission_widened": "YES"},
            {
                "receipt__SKILL_SOURCE_HASHES": {
                    "scope-reality-check": "0" * 64
                }
            },
            {"receipt__SKILL_HOST_MODE": "GENERIC_PROMPT_ONLY"},
            {"receipt__PERMISSION_WIDENED": "YES"},
        ]
        for overrides in cases:
            raw = self._raw(**overrides)
            with self.subTest(
                overrides=overrides
            ), self.assertRaises(SkillConsumptionError):
                self._authorize(raw=raw)

        raw = self._raw()
        token = _sign_rs256(self._claims(raw))
        tampered = raw.replace(
            b'"permission_widened":"NO"',
            b'"permission_widened":"OK"',
            1,
        )
        with self.assertRaisesRegex(
            SkillConsumptionError,
            "TRUST_OIDC_AUDIENCE_MISMATCH",
        ):
            self._authorize(raw=tampered, token=token)

    def test_c21_discovery_is_cross_check_not_certification(self):
        stale = dict(self.discovery)
        stale["observed_at"] = (
            datetime.now(timezone.utc) - timedelta(hours=2)
        ).isoformat()
        wrong_project = dict(self.discovery)
        wrong_project["project_binding"] = "other/repo"
        string_false = dict(self.discovery)
        string_false["execution_transport_available"] = "false"
        wrong_host = json.loads(json.dumps(self.discovery))
        wrong_host["profile"]["host_label"] = "CLAUDE"
        declared = dict(self.discovery)
        declared["provenance"] = "DECLARED_PROFILE"
        for name, record in {
            "stale": stale,
            "wrong_project": wrong_project,
            "string_false": string_false,
            "wrong_host": wrong_host,
            "declarative_only": declared,
        }.items():
            with self.subTest(name=name), self.assertRaises(
                SkillConsumptionError
            ):
                self._authorize(discovery=record)

    def test_missing_or_unavailable_trust_provider_blocks(self):
        with self.assertRaisesRegex(
            SkillConsumptionError,
            "TRUST_OIDC_TOKEN_REQUIRED",
        ):
            self._authorize(token="")
        raw = self._raw()
        token = _sign_rs256(self._claims(raw))
        with patch.object(
            trust,
            "_fetch_json",
            side_effect=trust.TrustedRepoReadEvidenceError(
                "TRUST_OIDC_PROVIDER_UNAVAILABLE"
            ),
        ), patch.object(trust.time, "time", return_value=NOW):
            with self.assertRaisesRegex(
                SkillConsumptionError,
                "TRUST_OIDC_PROVIDER_UNAVAILABLE",
            ):
                authorize_prompt_only_skill_handoff(
                    self.root,
                    self.handoff,
                    request_text=TASK,
                    host=HOST,
                    host_discovery_record=self.discovery,
                    trusted_evidence_bytes=raw,
                    trusted_oidc_token=token,
                )

    def test_prompt_only_stays_non_authorizing_before_trust_evidence(self):
        self.assertEqual(self.handoff["SKILL_CHECK"], "PREPARED")
        self.assertEqual(
            self.handoff["EXECUTION_AUTHORIZED"], "NO"
        )
        self.assertEqual(
            self.handoff["SKILL_HOST_MODE"],
            "GENERIC_PROMPT_ONLY",
        )
        self.assertEqual(
            self.handoff["RECIPIENT_CONSUMPTION"],
            "UNVERIFIED",
        )


if __name__ == "__main__":
    unittest.main()
