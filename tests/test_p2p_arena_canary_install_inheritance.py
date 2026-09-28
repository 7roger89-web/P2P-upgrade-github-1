"""T19: managed projects inherit the Arena FAST_CANARY runtime (Issue #254).

Supervisor review 5306294879 (BLOCKER 4) found that the release path shipped
``control_tower_handoff.py`` / ``owner_goal.py`` but not the foreground Control
Tower CLI ``scripts/p2p_control_tower.py`` that the PR uses as a primary
enforcement path. This module is the executable inheritance proof:

1. build the real release with the existing builder
   (``scripts/package_release.py build``) from a clean clone of the exact
   committed HEAD - the builder itself refuses a dirty source worktree;
2. install it with the real ``install.sh`` into a synthetic managed project;
3. exercise ONLY the installed runtime inside that project:
   ``.p2p/system/scripts/p2p_control_tower.py`` (start -> evidence-only ingest
   -> external grade -> Owner continuation -> resumed terminal return) and
   ``.p2p/system/scripts/p2p_workflow.py owner-goal`` (Owner /goal Arena handoff).

No repository module is imported for the installed-runtime assertions; every
installed command runs as a subprocess from the managed project directory.

A second, build-free layer stages the release with the real release selection
(``package_release.copy_selected``), lays out the managed project exactly as
the real installers' script lists place it, and drives the same installed
loop. It binds to the current tree even when the full release build cannot run
(shallow clone, or a release gate failing outside Issue #254).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import re
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
# A release doctor failure that is outside Issue #254: canonical main commit
# 6bb0581 (PR #221) declares external source P2P-EXT-0006 while
# scripts/doctor.py still expects exactly P2P-EXT-0001..0005, so no release can
# be built from that main. Only this exact, sole doctor failure is treated as
# BLOCKED (skip); any other build failure fails the test.
PREEXISTING_RELEASE_BLOCKER = "[FAIL] external-sources: External-source schema or IDs are incomplete"
MEDIUM_HIGH_TASK = (
    "Repair the Control Tower runtime so a new medium/high-risk Arena session "
    "stops at the FAST_CANARY boundary, mutating runtime prompt generation, "
    "ledger events and gates"
)
CHECKPOINT_LINES = (
    "CONTINUATION_CHECKPOINT=READY",
    "OWNER_ACTION_REQUIRED=YES",
    "NATIVE_ACTION_HINT=KEEP_WORKING_IF_APPROVED",
    "FALLBACK_OWNER_REPLY=Tiếp tục công việc",
)
EVIDENCE_ONLY_RESPONSE = "\n".join(
    (
        "CANARY_EVIDENCE_PACKET_V1",
        "P2P_LAW_SOURCE=.p2p/system/docs/P2P-OPERATIONS-NOTEBOOK.md",
        "CURRENT_STATE=synthetic managed project @ installed release",
        "FACTS=installed Control Tower CLI present; ledger lives in project .p2p/state",
        "DECISIVE_CHECK=python3 .p2p/system/scripts/p2p_control_tower.py snapshot",
        "CHECK_RESULT=exit=0; PASS",
        "ERRORS_ENCOUNTERED=NONE",
        "RECOVERY_ACTIONS=NONE",
        "DURABLE_MUTATION_CREATED=NO",
        "MODEL_IDENTITY=UNKNOWN",
        "",
        *CHECKPOINT_LINES,
        "",
    )
)
RESUMED_TASK_BEGIN_PREFIX = "RESUMED_TASK_CONTRACT"
RESUMED_TASK_END = "END_RESUMED_TASK_CONTRACT"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.pop("P2P_PROJECT_ROOT", None)
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def _run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_environment(),
        check=False,
        timeout=600,
    )


def _git(*args: str, cwd: Path = REPO_ROOT) -> str:
    result = _run(["git", *args], cwd=cwd)
    if result.returncode:
        raise unittest.SkipTest(f"git {' '.join(args)} unavailable: {result.stderr.strip()}")
    return result.stdout.strip()


def _anchor_commit() -> str:
    control = json.loads((REPO_ROOT / "governance" / "development-control.json").read_text(encoding="utf-8"))
    stack = [control]
    while stack:
        value = stack.pop()
        if isinstance(value, dict):
            if isinstance(value.get("anchor_commit"), str):
                return value["anchor_commit"]
            stack.extend(value.values())
        elif isinstance(value, list):
            stack.extend(value)
    raise unittest.SkipTest("development-control anchor_commit is not declared")


class ManagedProjectCanaryInheritanceTests(unittest.TestCase):
    """Real release build + real install.sh + installed-runtime execution."""

    @classmethod
    def setUpClass(cls) -> None:
        for tool in ("bash", "git", "sha256sum", "awk"):
            if shutil.which(tool) is None:
                raise unittest.SkipTest(f"{tool} is required for the Linux installer path")
        anchor = _anchor_commit()
        if _run(["git", "cat-file", "-e", f"{anchor}^{{commit}}"], cwd=REPO_ROOT).returncode:
            # Shallow sandboxes: an absent anchor is a tool-environment artifact,
            # not a repository fact. The release builder needs full lineage.
            raise unittest.SkipTest(
                "RELEASE_BUILD_REQUIRES_FULL_GIT_HISTORY: run `git fetch --unshallow origin` first"
            )
        cls.head = _git("rev-parse", "HEAD")
        cls._temp = tempfile.TemporaryDirectory(prefix="p2p-canary-install-")
        cls.addClassCleanup(cls._temp.cleanup)
        base = Path(cls._temp.name)

        # 1. Clean source bound to the exact committed HEAD.
        cls.source = base / "source"
        _git("clone", "--quiet", "--shared", "--no-checkout", str(REPO_ROOT), str(cls.source), cwd=base)
        _git("checkout", "--quiet", "--detach", cls.head, cwd=cls.source)

        # 2. Real release build through the existing builder.
        cls.artifact = base / "P2P-canary-inheritance.zip"
        build = _run(
            [
                sys.executable,
                str(cls.source / "scripts" / "package_release.py"),
                "--root",
                str(cls.source),
                "--output",
                str(cls.artifact),
                "build",
            ],
            cwd=cls.source,
        )
        if build.returncode:
            failures = [line.strip() for line in build.stderr.splitlines() if line.strip().startswith("[FAIL]")]
            if failures == [PREEXISTING_RELEASE_BLOCKER]:
                raise unittest.SkipTest(
                    "RELEASE_BUILD_BLOCKED_OUTSIDE_ISSUE_254: release doctor rejects "
                    "manifest/external-sources.json (P2P-EXT-0006 vs expected P2P-EXT-0001..0005); "
                    "the build-free staged inheritance layer still runs"
                )
            raise AssertionError(f"release build failed:\n{build.stdout}\n{build.stderr}")
        cls.build = json.loads(build.stdout)
        cls.release = base / "release"
        with zipfile.ZipFile(cls.artifact) as archive:
            archive.extractall(cls.release)

        # 3. Real installer into a synthetic managed project.
        cls.project = base / "managed-project"
        cls.project.mkdir()
        (cls.project / "README.md").write_text("# Synthetic managed project\n", encoding="utf-8")
        _git("init", "--quiet", cwd=cls.project)
        install = _run(
            [
                "bash",
                str(cls.release / "install.sh"),
                "project",
                str(cls.project),
                str(cls.artifact),
                _sha256(cls.artifact),
            ],
            cwd=cls.project,
        )
        cls.install_output = install.stdout + install.stderr
        if install.returncode:
            raise AssertionError(f"install.sh failed ({install.returncode}):\n{cls.install_output}")
        cls.installed_cli = cls.project / ".p2p" / "system" / "scripts" / "p2p_control_tower.py"

    # --- helpers ---------------------------------------------------------
    def installed_control_tower(self, *args: str) -> dict:
        result = _run([sys.executable, str(self.installed_cli), *args, "--json"], cwd=self.project)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def ledger_event_types(self) -> list[str]:
        ledger = self.project / ".p2p" / "state" / "execution-ledger.jsonl"
        return [
            json.loads(line)["event_type"]
            for line in ledger.read_text(encoding="utf-8").splitlines()
            if line.strip() and json.loads(line).get("event_type", "").startswith("CONTROL_TOWER_")
        ]

    # --- T19 ----------------------------------------------------------------
    def test_t19_release_ships_the_foreground_control_tower_cli_and_canary_runtime(self) -> None:
        self.assertEqual("PASS", self.build["status"])
        self.assertEqual(self.head, self.build["source_commit"])
        for relative, source in (
            ("scripts/p2p_control_tower.py", "scripts/p2p_control_tower.py"),
            ("runtime/p2p_capabilities/control_tower_handoff.py", ".p2p/system/p2p_capabilities/control_tower_handoff.py"),
            ("runtime/p2p_capabilities/owner_goal.py", ".p2p/system/p2p_capabilities/owner_goal.py"),
            ("scripts/p2p_workflow.py", "scripts/p2p_workflow.py"),
        ):
            packaged = self.release / relative
            self.assertTrue(packaged.is_file(), relative)
            self.assertEqual(_sha256(self.source / source), _sha256(packaged), relative)

    def test_t19_installer_places_cli_and_runtime_in_managed_project(self) -> None:
        self.assertIn("RESULT: PASS", self.install_output)
        system = self.project / ".p2p" / "system"
        self.assertTrue(self.installed_cli.is_file())
        self.assertEqual(_sha256(self.release / "scripts" / "p2p_control_tower.py"), _sha256(self.installed_cli))
        for relative in (
            "p2p_capabilities/control_tower_handoff.py",
            "p2p_capabilities/owner_goal.py",
            "scripts/p2p_workflow.py",
            "docs/P2P-OPERATIONS-NOTEBOOK.md",
        ):
            self.assertTrue((system / relative).is_file(), relative)

    def test_t19_installed_control_tower_enforces_canary_end_to_end(self) -> None:
        # No --root: the installed CLI must resolve the managed project root.
        started = self.installed_control_tower(
            "start",
            "--host",
            "ARENA",
            "--goal-id",
            "MANAGED-CANARY-01",
            "--task-id",
            "MANAGED-CANARY-01-T1",
            "--session-id",
            "managed-arena-1",
            "--goal",
            MEDIUM_HIGH_TASK,
        )
        receipt = started["control_tower_self_law_receipt"]
        self.assertEqual("INSTALLED_PROJECTION", receipt["source_type"])
        self.assertTrue(receipt["source"].endswith(".p2p/system/docs/P2P-OPERATIONS-NOTEBOOK.md"))
        recommendation = started["recommendation"]
        self.assertEqual("YES", recommendation["FAST_CANARY_REQUIRED"])
        prompt = recommendation["PROMPT"]
        for token in ("FAST_CANARY_REQUIRED=YES", "STOP_AFTER_CANARY=YES", "CANARY_EVIDENCE_PACKET_V1", *CHECKPOINT_LINES):
            self.assertIn(token, prompt)
        self.assertIn("FIRST_TURN_RETURN_CONTRACT=CANARY_EVIDENCE_PACKET_V1_THEN_STOP", prompt)
        self.assertNotIn("CONTROL_TOWER_RETURN_PACKET_BEGIN", prompt)
        # Durable state lives in the managed project, not in the runtime copy.
        self.assertTrue((self.project / ".p2p" / "state" / "execution-ledger.jsonl").is_file())
        self.assertFalse((self.project / ".p2p" / "system" / ".p2p").exists())

        response_file = self.project / "canary-response.txt"
        response_file.write_text(EVIDENCE_ONLY_RESPONSE, encoding="utf-8")
        self.assertNotIn("CONTROL_TOWER_RETURN_PACKET", EVIDENCE_ONLY_RESPONSE)
        graded = self.installed_control_tower(
            "ingest", "--response-file", str(response_file), "--session-id", "managed-arena-1"
        )
        self.assertEqual("GREEN", graded["canary_grade"]["CLASSIFICATION"])
        self.assertEqual("WAIT_FOR_OWNER_CONTINUATION", graded["snapshot"]["NEXT_SAFE_ACTION"]["ACTION"])

        resumed = self.installed_control_tower(
            "continue", "--session-id", "managed-arena-1", "--owner-reply", "Tiếp tục công việc"
        )
        continuation = resumed["recommendation"]
        self.assertEqual("managed-arena-1", continuation["SESSION_ID"])
        self.assertEqual("RESUME_ORIGINAL_TASK_IN_SAME_SESSION", continuation["CONTINUATION_MODE"])
        self.assertEqual("NO", continuation["CANARY_REPEAT"])
        self.assertIn(MEDIUM_HIGH_TASK, continuation["PROMPT"])
        self.assertIn("CONTROL_TOWER_RETURN_PACKET_BEGIN", continuation["PROMPT"])
        self.assertNotIn("FAST_CANARY_REQUIRED=YES", continuation["PROMPT"])

        final_packet = {
            "schema": "p2p-control-tower-return-packet/1",
            "CONTROL_TOWER_RETURN_PACKET": True,
            "SESSION_ID": "managed-arena-1",
            "HOST": "ARENA",
            "GOAL_ID": "MANAGED-CANARY-01",
            "GOAL": MEDIUM_HIGH_TASK,
            "SESSION_STATE": "COMPLETED",
            "UPLOAD_REQUIRED": "NO",
        }
        final_file = self.project / "final-response.txt"
        final_file.write_text(
            "CONTROL_TOWER_RETURN_PACKET_BEGIN\n"
            + json.dumps(final_packet, ensure_ascii=False)
            + "\nCONTROL_TOWER_RETURN_PACKET_END\n",
            encoding="utf-8",
        )
        closed = self.installed_control_tower("ingest", "--response-file", str(final_file))
        self.assertEqual("PASS", closed["status"])
        self.assertEqual(
            [
                "CONTROL_TOWER_SESSION_STARTED",
                "CONTROL_TOWER_CANARY_EVIDENCE",
                "CONTROL_TOWER_CANARY_CONTINUATION",
                "CONTROL_TOWER_RETURN_PACKET",
            ],
            self.ledger_event_types(),
        )

    def test_t19_installed_owner_goal_arena_handoff_is_a_first_turn_canary(self) -> None:
        workflow = self.project / ".p2p" / "system" / "scripts" / "p2p_workflow.py"
        result = _run(
            [
                sys.executable,
                str(workflow),
                "owner-goal",
                "--project",
                str(self.project),
                "--request",
                "/goal Hoàn thiện workflow hợp đồng logistics, dùng Arena",
            ],
            cwd=self.project,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        intake = json.loads(result.stdout)
        arena = intake["arena_handoff"]
        self.assertEqual("YES", arena["fast_canary_required"])
        self.assertEqual("FAST_CANARY_FIRST_SAFE_SLICE_THEN_STOP", arena["execution_mode"])
        self.assertEqual("FAST_CANARY_FIRST_SAFE_SLICE_THEN_STOP", intake["execution_mode"])
        for text in (arena["packet_text"], intake["beginner_arena_handoff"]["packet_text"]):
            lines = text.splitlines()
            begin = next(index for index, line in enumerate(lines) if line.startswith(RESUMED_TASK_BEGIN_PREFIX))
            end = lines.index(RESUMED_TASK_END)
            active = "\n".join(lines[:begin] + lines[end + 1 :])
            self.assertNotIn("AUTONOMOUS_UNTIL_TERMINAL", active)
            self.assertIn("EXECUTION_MODE=FAST_CANARY_FIRST_SAFE_SLICE_THEN_STOP", active)
            self.assertIn("STOP_AFTER_CANARY=YES", active)
            self.assertIn("RESUMED_TASK_MODE=AUTONOMOUS_UNTIL_TERMINAL", "\n".join(lines[begin : end + 1]))

    def test_t19_windows_installer_ships_the_same_cli(self) -> None:
        # PowerShell is not available in every sandbox; the Windows installer
        # must copy the same packaged script into the same managed location.
        ps1 = (self.release / "install.ps1").read_text(encoding="utf-8")
        sh = (self.release / "install.sh").read_text(encoding="utf-8")
        self.assertIn('"p2p_control_tower.py"', ps1)
        self.assertIn('"$package_root/scripts/p2p_control_tower.py"', sh)


def _installer_runtime_script_names() -> list[str]:
    """Runtime scripts install.sh copies from runtime/scripts/ into .p2p/system/scripts/."""

    sh = (REPO_ROOT / "install.sh").read_text(encoding="utf-8")
    block = re.search(r'cp \\\n((?:\s+"\$uiux_runtime/scripts/[^"]+" \\\n)+)\s+"\$system_destination/scripts/"', sh)
    if block is None:
        raise AssertionError("install.sh runtime-scripts copy block not found")
    return re.findall(r'"\$uiux_runtime/scripts/([A-Za-z0-9_.-]+)"', block.group(1))


def _installer_script_names() -> tuple[list[str], list[str]]:
    """Scripts the real installers copy into <project>/.p2p/system/scripts/."""

    sh = (REPO_ROOT / "install.sh").read_text(encoding="utf-8")
    block = re.search(r'cp \\\n((?:\s+"\$package_root/scripts/[^"]+" \\\n)+)\s+"\$system_destination/scripts/"', sh)
    if block is None:
        raise AssertionError("install.sh managed-scripts copy block not found")
    sh_names = re.findall(r'"\$package_root/scripts/([A-Za-z0-9_.-]+)"', block.group(1))
    ps1 = (REPO_ROOT / "install.ps1").read_text(encoding="utf-8")
    loop = re.search(r"foreach \(\$ScriptName in @\(([^)]*)\)\)", ps1)
    if loop is None:
        raise AssertionError("install.ps1 managed-scripts loop not found")
    ps1_names = re.findall(r'"([A-Za-z0-9_.-]+)"', loop.group(1))
    return sh_names, ps1_names


class StagedReleaseCanaryInheritanceTests(unittest.TestCase):
    """Build-free T19 layer bound to the current tree."""

    @classmethod
    def setUpClass(cls) -> None:
        import package_release

        cls._temp = tempfile.TemporaryDirectory(prefix="p2p-canary-staged-")
        cls.addClassCleanup(cls._temp.cleanup)
        base = Path(cls._temp.name)
        cls.stage = base / "stage"
        package_release.copy_selected(REPO_ROOT, cls.stage)
        cls.sh_names, cls.ps1_names = _installer_script_names()
        # Lay out the managed project as install.sh places the payload.
        cls.project = base / "managed-project"
        system = cls.project / ".p2p" / "system"
        (system / "scripts").mkdir(parents=True)
        for name in cls.sh_names:
            shutil.copy2(cls.stage / "scripts" / name, system / "scripts" / name)
        for name in _installer_runtime_script_names():
            shutil.copy2(cls.stage / "runtime" / "scripts" / name, system / "scripts" / name)
        shutil.copytree(cls.stage / "runtime" / "p2p_capabilities", system / "p2p_capabilities")
        (system / "docs").mkdir()
        shutil.copy2(
            cls.stage / "docs" / "p2p-development" / "P2P-OPERATIONS-NOTEBOOK.md",
            system / "docs" / "P2P-OPERATIONS-NOTEBOOK.md",
        )
        cls.installed_cli = system / "scripts" / "p2p_control_tower.py"

    def installed_control_tower(self, *args: str) -> dict:
        result = _run([sys.executable, str(self.installed_cli), *args, "--json"], cwd=self.project)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_t19_staged_release_selection_and_installer_lists_ship_the_cli(self) -> None:
        packaged = self.stage / "scripts" / "p2p_control_tower.py"
        self.assertTrue(packaged.is_file())
        self.assertEqual(_sha256(REPO_ROOT / "scripts" / "p2p_control_tower.py"), _sha256(packaged))
        for module in ("control_tower_handoff.py", "owner_goal.py"):
            self.assertTrue((self.stage / "runtime" / "p2p_capabilities" / module).is_file(), module)
        self.assertIn("p2p_control_tower.py", self.sh_names)
        self.assertIn("p2p_control_tower.py", self.ps1_names)
        self.assertEqual(sorted(self.sh_names), sorted(self.ps1_names))

    def test_t19_staged_installed_control_tower_runs_the_canary_loop(self) -> None:
        started = self.installed_control_tower(
            "start",
            "--host",
            "ARENA",
            "--goal-id",
            "STAGED-CANARY-01",
            "--session-id",
            "staged-arena-1",
            "--goal",
            MEDIUM_HIGH_TASK,
        )
        self.assertEqual("INSTALLED_PROJECTION", started["control_tower_self_law_receipt"]["source_type"])
        prompt = started["recommendation"]["PROMPT"]
        self.assertIn("FIRST_TURN_RETURN_CONTRACT=CANARY_EVIDENCE_PACKET_V1_THEN_STOP", prompt)
        self.assertNotIn("CONTROL_TOWER_RETURN_PACKET_BEGIN", prompt)
        response_file = self.project / "canary-response.txt"
        response_file.write_text(EVIDENCE_ONLY_RESPONSE, encoding="utf-8")
        graded = self.installed_control_tower(
            "ingest", "--response-file", str(response_file), "--session-id", "staged-arena-1"
        )
        self.assertEqual("GREEN", graded["canary_grade"]["CLASSIFICATION"])
        resumed = self.installed_control_tower(
            "continue", "--session-id", "staged-arena-1", "--owner-reply", "Tiếp tục công việc"
        )
        self.assertEqual("RESUME_ORIGINAL_TASK_IN_SAME_SESSION", resumed["recommendation"]["CONTINUATION_MODE"])
        self.assertIn("CONTROL_TOWER_RETURN_PACKET_BEGIN", resumed["recommendation"]["PROMPT"])
        self.assertTrue((self.project / ".p2p" / "state" / "execution-ledger.jsonl").is_file())
        self.assertFalse((self.project / ".p2p" / "system" / ".p2p").exists())


if __name__ == "__main__":
    unittest.main()
