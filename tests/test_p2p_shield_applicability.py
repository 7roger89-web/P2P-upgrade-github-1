import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from shield import ci
from shield.profile import evaluate, PROFILE
from shield.runner import resolve_target_ref


def init(root):
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "fixture",
        "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
        "GIT_COMMITTER_NAME": "fixture",
        "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
    }
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, env=env)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, env=env)
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "commit", "-qm", "fixture"],
        cwd=root,
        check=True,
        env=env,
    )


class ApplicabilityTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def repo(self, workflow=False):
        root = self.root / ("with-workflow" if workflow else "empty")
        root.mkdir()
        (root / "README.md").write_text("fixture\n")
        if workflow:
            workflow_dir = root / ".github" / "workflows"
            workflow_dir.mkdir(parents=True)
            (workflow_dir / "ci.yml").write_text(
                "name: ci\non: push\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps: []\n"
            )
        init(root)
        return root

    def records(self, target, ci_evidence):
        target_ref = resolve_target_ref(target)
        records = []
        for control_id, rule in PROFILE["required_controls"].items():
            for scope in rule["required_scopes"]:
                if control_id == "SHIELD-CI-01":
                    records.append(ci_evidence)
                    continue
                records.append(
                    dict(
                        schema="p2p-shield-evidence/1",
                        control_id=control_id,
                        control_version=rule["control_version"],
                        scope=scope,
                        target=str(target),
                        target_ref=target_ref,
                        timestamp="2026-09-15T00:00:00Z",
                        status="PASS",
                        findings_count=0,
                        coverage=["assessed"],
                        limitations=[],
                        provider="provider",
                        provider_version="1",
                        provider_source="upstream@tag",
                        reason="assessed",
                        artifact_or_reference="run",
                    )
                )
        return records

    def test_na_passes_profile_only_for_empty_inventory(self):
        target = self.repo()
        with patch(
            "shield.ci.zizmor_acquire.verify_executable",
            side_effect=AssertionError("provider must not run"),
        ):
            evidence = ci.assess(target, self.root / "missing-zizmor", "run")
        self.assertEqual(evidence["status"], "NOT_APPLICABLE")
        self.assertEqual(evidence["coverage"], ["NOT_APPLICABLE_BY_TARGET_SHAPE"])
        self.assertEqual(
            evidence["applicability"]["basis"],
            "DETERMINISTIC_EMPTY_WORKFLOW_INVENTORY",
        )
        result = evaluate(self.records(target, evidence), target, resolve_target_ref(target))
        self.assertEqual(result["PROFILE_REQUIREMENTS_STATUS"], "PASS")
        self.assertEqual(result["NOT_APPLICABLE_CONTROLS"], ["SHIELD-CI-01"])
        self.assertEqual(result["SYSTEM_SECURITY_VERDICT"], "NOT_EVALUATED")

    def test_cli_not_applicable_exits_zero(self):
        target = self.repo()
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "shield.ci",
                "--target",
                str(target),
                "--executable",
                str(self.root / "missing-zizmor"),
                "--reference",
                "run",
            ],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        evidence = json.loads(proc.stdout)
        self.assertEqual(evidence["status"], "NOT_APPLICABLE")
        self.assertEqual(evidence["applicability"]["workflow_count"], 0)

    def test_forged_na_blocked(self):
        target = self.repo()
        evidence = ci.assess(target, self.root / "missing-zizmor", "run")
        for mutation in (
            {"coverage": ["assessed"]},
            {"findings_count": 1},
            {"reason": "forged"},
            {
                "applicability": {
                    "basis": "SELF_DECLARED",
                    "path": ".github/workflows",
                    "workflow_count": 0,
                }
            },
        ):
            forged = copy.deepcopy(evidence)
            forged.update(mutation)
            result = evaluate(self.records(target, forged), target, resolve_target_ref(target))
            self.assertEqual(result["PROFILE_REQUIREMENTS_STATUS"], "BLOCKED")

    def test_applicable_missing_provider_stays_blocked(self):
        target = self.repo(workflow=True)
        evidence = ci.assess(target, self.root / "missing-zizmor", "run")
        self.assertEqual(evidence["status"], "BLOCKED")
        self.assertEqual(evidence["applicability"]["basis"], "WORKFLOW_INVENTORY_PRESENT")
        self.assertEqual(evidence["applicability"]["workflow_count"], 1)
        result = evaluate(self.records(target, evidence), target, resolve_target_ref(target))
        self.assertEqual(result["PROFILE_REQUIREMENTS_STATUS"], "BLOCKED")

    def test_symlinked_github_root_is_blocked_not_na(self):
        external = self.root / "outside"
        (external / "workflows").mkdir(parents=True)
        target = self.root / "symlink-target"
        target.mkdir()
        (target / "README.md").write_text("fixture\n")
        (target / ".github").symlink_to(external, target_is_directory=True)
        init(target)
        evidence = ci.assess(target, self.root / "missing-zizmor", "run")
        self.assertEqual(evidence["status"], "BLOCKED")
        self.assertIn("github_root_symlink", evidence["reason"])
        self.assertEqual(evidence["applicability"]["basis"], "NOT_ESTABLISHED")


if __name__ == "__main__":
    unittest.main()
