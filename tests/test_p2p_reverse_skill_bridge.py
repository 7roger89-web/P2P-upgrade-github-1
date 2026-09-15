from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.reverse_skill_bridge import (  # noqa: E402
    REVERSE_SKILL_ROUTE_CLASSIFICATION,
    REVERSE_SKILL_UPSTREAM_COMMIT,
    ReverseSkillBoundaryError,
    ReverseSkillBridge,
    ReverseSkillProvenanceError,
)


class ReverseSkillBridgeTests(unittest.TestCase):
    def _fixture(self, root: Path) -> Path:
        package = root / "reverse-skill"
        (package / "skills" / "scripts" / "lib").mkdir(parents=True)
        (package / "skills" / "config").mkdir(parents=True)
        (package / "skills" / "sample").mkdir(parents=True)
        (package / "skills" / "scripts" / "master-route.sh").write_text(
            "#!/usr/bin/env bash\n", encoding="utf-8"
        )
        (package / "skills" / "scripts" / "master-route.ps1").write_text(
            "# fixture\n", encoding="utf-8"
        )
        (package / "skills" / "scripts" / "lib" / "WorkRoot.ps1").write_text(
            "# fixture\n", encoding="utf-8"
        )
        (package / "skills" / "MASTER-ROUTING.md").write_text(
            "# fixture\n", encoding="utf-8"
        )
        (package / "skills" / "sample" / "SKILL.md").write_text(
            "# sample\n", encoding="utf-8"
        )
        (package / "skills" / "config" / "routing.json").write_text(
            json.dumps(
                {
                    "meta": {"fallbackId": "R0"},
                    "priority": ["R0"],
                    "routes": {
                        "R0": {
                            "label": "Sample",
                            "skill": "sample/SKILL.md",
                            "keywords": [],
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        return package

    @staticmethod
    def _which(name: str) -> str | None:
        return {
            "git": "/fake/git",
            "bash": "/fake/bash",
            "powershell": "/fake/powershell",
            "pwsh": "/fake/pwsh",
        }.get(name)

    def _route_runner(self, artifact_dir: Path, *, primary_skill: str = "skills/sample/SKILL.md"):
        calls = []

        def runner(invocation):
            calls.append(invocation)
            argv = invocation.argv
            if "rev-parse" in argv:
                return subprocess.CompletedProcess(argv, 0, REVERSE_SKILL_UPSTREAM_COMMIT + "\n", "")
            if "status" in argv:
                return subprocess.CompletedProcess(argv, 0, "", "")
            artifact_dir.mkdir(parents=True, exist_ok=True)
            (artifact_dir / "route-scope.md").write_text(
                "\n".join(
                    [
                        "# reverse-skill Master route (PRIMARY)",
                        "- primary: R0",
                        "- primary_label: Sample",
                        f"- primary_skill: {primary_skill}",
                        "- confidence: high",
                        "- secondary: (none)",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            return subprocess.CompletedProcess(argv, 0, "PRIMARY -> sample\n", "")

        return runner, calls

    def test_route_is_subordinate_non_authoritative_and_never_bootstraps(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self._fixture(root)
            project = root / "project"
            project.mkdir()
            marker = project / "marker.txt"
            marker.write_text("unchanged", encoding="utf-8")
            marker_before = hashlib.sha256(marker.read_bytes()).hexdigest()
            artifact_dir = root / "evidence" / "route"
            artifact_dir.parent.mkdir()

            runner, calls = self._route_runner(artifact_dir)
            bridge = ReverseSkillBridge(
                package_root=package,
                runner=runner,
                which=self._which,
                platform_name="posix",
            )
            result = bridge.route(
                task_hint="analyze an APK for reverse engineering",
                project_root=project,
                artifact_dir=artifact_dir,
            )

            self.assertEqual(result["classification"], REVERSE_SKILL_ROUTE_CLASSIFICATION)
            self.assertFalse(result["authoritative_state"])
            self.assertTrue(result["p2p_router_authority_unchanged"])
            self.assertEqual(result["upstream_router_scope"], "SUBORDINATE_METHOD_SELECTOR_ONLY")
            self.assertEqual(result["execution_class"], "ANALYSIS_LOCAL")
            self.assertTrue(result["security_execution"]["allowed"])
            self.assertEqual(result["route"]["primary_skill"], "skills/sample/SKILL.md")
            self.assertTrue(result["artifact"]["ephemeral"])
            self.assertTrue(result["artifact"]["contains_task_hint"])
            self.assertEqual(result["command"][result["command"].index("--hint") + 1], "<task_hint>")
            joined = " ".join(result["command"]).lower()
            self.assertNotIn("bootstrap", joined)
            self.assertNotIn("case-init", joined)
            self.assertNotIn("mcp", joined)
            self.assertNotIn("executionpolicy", joined)
            self.assertFalse(result["boundary"]["auto_install"])
            self.assertFalse(result["boundary"]["auto_bootstrap"])
            self.assertFalse(result["boundary"]["permission_grant"])
            self.assertFalse(result["boundary"]["target_act"])
            self.assertEqual(hashlib.sha256(marker.read_bytes()).hexdigest(), marker_before)
            self.assertEqual(len(calls), 3)

    def test_exact_commit_mismatch_fails_closed_before_router(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self._fixture(root)
            project = root / "project"
            project.mkdir()
            artifact_dir = root / "evidence" / "route"
            artifact_dir.parent.mkdir()
            calls = []

            def runner(invocation):
                calls.append(invocation)
                if "rev-parse" in invocation.argv:
                    return subprocess.CompletedProcess(invocation.argv, 0, "0" * 40 + "\n", "")
                raise AssertionError("router/status must not run after commit mismatch")

            bridge = ReverseSkillBridge(
                package_root=package,
                runner=runner,
                which=self._which,
                platform_name="posix",
            )
            with self.assertRaisesRegex(ReverseSkillProvenanceError, "UPSTREAM_COMMIT_MISMATCH"):
                bridge.route(
                    task_hint="reverse binary",
                    project_root=project,
                    artifact_dir=artifact_dir,
                )
            self.assertEqual(len(calls), 1)

    def test_dirty_tracked_checkout_fails_closed_before_router(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self._fixture(root)
            calls = []

            def runner(invocation):
                calls.append(invocation)
                if "rev-parse" in invocation.argv:
                    return subprocess.CompletedProcess(
                        invocation.argv, 0, REVERSE_SKILL_UPSTREAM_COMMIT + "\n", ""
                    )
                if "status" in invocation.argv:
                    return subprocess.CompletedProcess(
                        invocation.argv, 0, " M skills/scripts/master-route.sh\n", ""
                    )
                raise AssertionError("router must not run for a dirty checkout")

            bridge = ReverseSkillBridge(
                package_root=package,
                runner=runner,
                which=self._which,
                platform_name="posix",
            )
            with self.assertRaisesRegex(ReverseSkillProvenanceError, "UPSTREAM_TRACKED_WORKTREE_DIRTY"):
                bridge.verify_checkout()
            self.assertEqual(len(calls), 2)

    def test_artifact_output_inside_project_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self._fixture(root)
            project = root / "project"
            project.mkdir()
            bridge = ReverseSkillBridge(
                package_root=package,
                runner=lambda invocation: subprocess.CompletedProcess(invocation.argv, 0, "", ""),
                which=self._which,
                platform_name="posix",
            )
            with self.assertRaisesRegex(ReverseSkillBoundaryError, "OUTSIDE_PROJECT"):
                bridge.build_route_invocation(
                    task_hint="reverse binary",
                    project_root=project,
                    artifact_dir=project / "work" / "route",
                )

    def test_upstream_skill_path_escape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self._fixture(root)
            project = root / "project"
            project.mkdir()
            artifact_dir = root / "evidence" / "route"
            artifact_dir.parent.mkdir()
            runner, _ = self._route_runner(artifact_dir, primary_skill="skills/../escape/SKILL.md")
            bridge = ReverseSkillBridge(
                package_root=package,
                runner=runner,
                which=self._which,
                platform_name="posix",
            )
            with self.assertRaisesRegex(ReverseSkillBoundaryError, "SKILL_REF_ESCAPE"):
                bridge.route(
                    task_hint="reverse binary",
                    project_root=project,
                    artifact_dir=artifact_dir,
                )

    def test_windows_command_respects_host_execution_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = self._fixture(root)
            project = root / "project"
            project.mkdir()
            artifact_dir = root / "evidence" / "route"
            artifact_dir.parent.mkdir()
            bridge = ReverseSkillBridge(
                package_root=package,
                runner=lambda invocation: subprocess.CompletedProcess(invocation.argv, 0, "", ""),
                which=self._which,
                platform_name="windows",
            )
            invocation = bridge.build_route_invocation(
                task_hint="analyze PE binary",
                project_root=project,
                artifact_dir=artifact_dir,
            )
            self.assertEqual(invocation.argv[0], "/fake/powershell")
            self.assertIn("-NoProfile", invocation.argv)
            self.assertIn("-File", invocation.argv)
            self.assertNotIn("-ExecutionPolicy", invocation.argv)
            self.assertNotIn("Bypass", invocation.argv)


if __name__ == "__main__":
    unittest.main()
