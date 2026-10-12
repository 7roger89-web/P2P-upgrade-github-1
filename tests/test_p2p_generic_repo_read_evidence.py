"""Focused tests for Issue #333 signed generic repo-read evidence."""
from __future__ import annotations

import base64
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities import generic_repo_read_evidence as gre  # noqa: E402


def _b64(value: dict) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


class GenericRepoReadEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.now = 1_800_000_000
        self.repo = "7roger89-web/p2p-upgrade-github-1"
        self.revision = "a" * 40
        self.host = "GITHUB_COPILOT_CLI_ACTIONS"
        self.probe_path = ".agents/skills/scope-reality-check/SKILL.md"
        self.probe_sha = "b" * 64
        self.workflow_ref = (
            self.repo
            + "/.github/workflows/p2p-b1-real-generic-read-canary.yml"
            + "@refs/heads/feat/issue-333-signed-generic-read-admission"
        )
        self.evidence = {
            "schema": gre.EVIDENCE_SCHEMA,
            "actor": self.host,
            "repository": self.repo,
            "revision": self.revision,
            "workflow_ref": self.workflow_ref,
            "run_id": "38229163912",
            "run_attempt": 1,
            "runner_environment": "github-hosted",
            "probe_path": self.probe_path,
            "probe_sha256": self.probe_sha,
            "result_sha256": "c" * 64,
            "transcript_sha256": "d" * 64,
            "permission_widened": "NO",
        }

    def _claims(self, **updates):
        value = {
            "iss": gre.OIDC_ISSUER,
            "aud": gre.OIDC_AUDIENCE_PREFIX + gre.evidence_sha256(self.evidence),
            "repository": self.repo,
            "run_id": "38229163912",
            "run_attempt": "1",
            "workflow_ref": self.workflow_ref,
            "workflow_sha": self.revision,
            "ref": "refs/heads/feat/issue-333-signed-generic-read-admission",
            "event_name": "push",
            "runner_environment": "github-hosted",
            "iat": self.now - 5,
            "nbf": self.now - 5,
            "exp": self.now + 300,
        }
        value.update(updates)
        return value

    def _token(self, claims=None):
        header = {"alg": "RS256", "kid": "test-kid", "typ": "JWT"}
        return _b64(header) + "." + _b64(claims or self._claims()) + ".AA"

    @staticmethod
    def _fetch(url):
        if url == gre.OIDC_DISCOVERY_URL:
            return {
                "issuer": gre.OIDC_ISSUER,
                "jwks_uri": gre.OIDC_ISSUER + "/.well-known/jwks",
            }
        return {
            "keys": [{
                "kid": "test-kid",
                "kty": "RSA",
                "use": "sig",
                "n": "AQAB",
                "e": "AQAB",
            }]
        }

    def _verify(self, *, evidence=None, token=None, signature_error=None):
        patches = [
            mock.patch.object(gre, "_fetch_json", side_effect=self._fetch),
        ]
        if signature_error is None:
            patches.append(mock.patch.object(gre, "_verify_rs256", return_value=None))
        else:
            patches.append(
                mock.patch.object(
                    gre,
                    "_verify_rs256",
                    side_effect=gre.GenericRepoReadEvidenceError(signature_error),
                )
            )
        with patches[0], patches[1]:
            return gre.verify_generic_repo_read_evidence(
                self.evidence if evidence is None else evidence,
                self._token() if token is None else token,
                expected_host=self.host,
                expected_repo=self.repo,
                expected_revision=self.revision,
                expected_probe_path=self.probe_path,
                expected_probe_sha256=self.probe_sha,
                now_epoch=self.now,
            )

    def test_valid_signed_claim_binding_passes(self):
        result = self._verify()
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["workflow_sha"], self.revision)

    def test_signature_failure_fails_closed(self):
        result = self._verify(signature_error="GITHUB_OIDC_SIGNATURE_INVALID")
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "GITHUB_OIDC_SIGNATURE_INVALID")

    def test_wrong_audience_fails_closed(self):
        result = self._verify(token=self._token(self._claims(aud="wrong")))
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "GITHUB_OIDC_AUDIENCE_MISMATCH")

    def test_self_hosted_runner_fails_closed(self):
        result = self._verify(
            token=self._token(self._claims(runner_environment="self-hosted"))
        )
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "GITHUB_OIDC_SELF_HOSTED_REJECTED")

    def test_stale_token_fails_closed(self):
        result = self._verify(
            token=self._token(
                self._claims(iat=self.now - 3601, nbf=self.now - 3601)
            )
        )
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "GITHUB_OIDC_EVIDENCE_STALE")

    def test_wrong_workflow_is_rejected(self):
        forged = dict(self.evidence)
        forged["workflow_ref"] = (
            self.repo + "/.github/workflows/other.yml@refs/heads/main"
        )
        result = self._verify(evidence=forged)
        self.assertFalse(result["valid"])
        self.assertEqual(
            result["reason"], "GENERIC_READ_EVIDENCE_WORKFLOW_UNTRUSTED"
        )

    def test_wrong_probe_hash_is_rejected(self):
        forged = dict(self.evidence)
        forged["probe_sha256"] = "0" * 64
        result = self._verify(evidence=forged)
        self.assertFalse(result["valid"])
        self.assertEqual(
            result["reason"], "GENERIC_READ_EVIDENCE_PROBE_HASH_MISMATCH"
        )

    def test_missing_token_is_rejected(self):
        result = self._verify(token="")
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "GITHUB_OIDC_TOKEN_REQUIRED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
