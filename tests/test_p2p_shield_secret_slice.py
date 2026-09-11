"""Focused tests for the P2P Shield v0.1 slice 1 contracts and runner.

These tests prove the deterministic, offline half of the slice:

- the control contract exists and stays provider-neutral;
- the provider mapping exists and pins the provider version and source;
- the runner converts provider outcomes into PASS / FAIL / BLOCKED evidence and
  never turns a provider failure into PASS;
- the evidence record carries the whole control evidence contract;
- swapping the provider mapping changes provider fields only, never the control.

Real provider execution is proven by the candidate acceptance workflow, which
runs this file and ``shield.acceptance`` on a GitHub-hosted runner.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shield import runner as shield_runner  # noqa: E402
from shield.acquire import (  # noqa: E402
    ProviderAcquisitionBlocked as BlockedProviderAcquisition,
    expected_checksum_from as acquire_expected,
    load_and_validate_mapping,
)
from shield.runner import (  # noqa: E402
    EXIT_BY_STATUS,
    STATUS_BLOCKED,
    STATUS_FAIL,
    STATUS_PASS,
    Blocked,
    assess,
    load_control,
    load_provider_mapping,
)

SHIELD_DIR = REPO_ROOT / "shield"
CONTROL_ID = "SHIELD-SECRET-01"
PINNED_PROVIDER_VERSION = "8.18.4"
SECRET_MARKER = "MUST-NOT-BE-COPIED"

STUB_SCRIPT = '''#!/usr/bin/env python3
"""Fake provider used only to prove Shield status mapping deterministically."""
import json
import pathlib
import sys

argv = sys.argv[1:]
target = report = None
for item in argv:
    if item.startswith("--target="):
        target = item.split("=", 1)[1]
    elif item.startswith("--report="):
        report = item.split("=", 1)[1]

mode = "CLEAN"
if target:
    mode_file = pathlib.Path(target) / "STUB_MODE"
    if mode_file.is_file():
        mode = mode_file.read_text(encoding="utf-8").strip()


def write(text):
    if report:
        pathlib.Path(report).write_text(text, encoding="utf-8")


if argv and argv[0] == "version":
    if mode == "VERSION_MISMATCH":
        print("9.9.9")
    elif mode == "VERSION_COMMAND_FAILED":
        print("version probe failed", file=sys.stderr)
        raise SystemExit(1)
    else:
        print("1.2.3")
    raise SystemExit(0)

finding = {
    "RuleID": "stub-fake-rule",
    "Description": "stub",
    "File": "config/service-settings.env",
    "StartLine": 3,
    "Commit": "0" * 40,
    "Secret": "%s",
    "Line": "SERVICE_TOKEN=%s",
}
if mode == "CLEAN":
    write("[]\\n")
    raise SystemExit(0)
if mode == "LEAK":
    write(json.dumps([finding], indent=1))
    raise SystemExit(1)
if mode == "LEAK_MANY":
    write(json.dumps([finding] * 30, indent=1))
    raise SystemExit(1)
if mode == "PARTIAL":
    write("[]\\n")
    sys.stderr.write("partial scan completed\\n")
    raise SystemExit(1)
if mode == "NO_REPORT":
    raise SystemExit(0)
if mode == "BAD_REPORT":
    write("this is not json\\n")
    raise SystemExit(0)
raise SystemExit(4)
''' % (SECRET_MARKER, SECRET_MARKER)


def _stub_mapping(path: Path, *, name: str = "StubScan", version: str = "1.2.3") -> Path:
    path.write_text(
        json.dumps(
            {
                "schema": "p2p-shield-provider-mapping/1",
                "control_id": CONTROL_ID,
                "provider_name": name,
                "provider_version": version,
                "source": {"kind": "test_stub", "repository": "local/stub", "tag": "none"},
                "invocation": {
                    "version_argv": ["{executable}", "version", "--target={target}"],
                    "version_expected_substring": "1.2.3",
                    "detect_argv": ["{executable}", "--target={target}", "--report={report}"],
                    "scan_mode_args": {
                        "git_history_scan": [],
                        "worktree_scan": ["--mode=worktree"],
                        "dependency_scan": ["--mode=dependency"],
                    },
                },
                "coverage": {
                    "git_history_scan": ["stub history coverage"],
                    "worktree_scan": ["stub worktree coverage"],
                },
                "limitations": ["stub provider has no real detection capability"],
                "failure_behavior": "BLOCKED",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


class ShieldSliceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.work_dir = Path(tempfile.mkdtemp(prefix="p2p-shield-test-"))
        self.addCleanup(shutil.rmtree, self.work_dir, True)
        self.stub = self.work_dir / "stub-provider"
        self.stub.write_text(STUB_SCRIPT, encoding="utf-8")
        self.stub.chmod(self.stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        self.stub_mapping = _stub_mapping(self.work_dir / "stub-mapping.json")

    def _target(self, mode: str) -> Path:
        target = self.work_dir / f"target-{mode}-{len(self.id())}"
        target.mkdir(parents=True, exist_ok=True)
        (target / "STUB_MODE").write_text(mode + "\n", encoding="utf-8")
        return target

    def _assess(self, mode: str, *, mapping: Path | None = None, executable: str | None = None):
        return assess(
            shield_dir=SHIELD_DIR,
            control_id=CONTROL_ID,
            scan_mode="git_history_scan",
            target=self._target(mode),
            executable=str(self.stub if executable is None else Path(executable)),
            provider_mapping=self.stub_mapping if mapping is None else mapping,
            timeout=60,
            reference="unit-test",
        )

    # --- contract shape -------------------------------------------------

    def test_control_contract_is_defined_and_provider_neutral(self) -> None:
        control_path = SHIELD_DIR / "controls" / f"{CONTROL_ID}.json"
        control, resolved = load_control(SHIELD_DIR, CONTROL_ID)
        self.assertEqual(resolved, control_path)
        self.assertEqual(control["control_id"], CONTROL_ID)
        self.assertTrue(control["objective"].strip())
        self.assertEqual(
            set(control["status_semantics"]), {STATUS_PASS, STATUS_FAIL, STATUS_BLOCKED}
        )
        self.assertTrue(
            control["non_negotiable"]["provider_failure_must_never_become_pass"] is True
        )
        for field in (
            "control_id",
            "control_version",
            "provider",
            "provider_version",
            "target_ref",
            "timestamp",
            "status",
            "scope",
            "findings_count",
            "limitations",
        ):
            self.assertIn(field, control["evidence_fields"])
        document = control_path.read_text(encoding="utf-8").lower()
        for provider_word in ("gitleaks", "trufflehog", "8.18.4", "zricethezav"):
            self.assertNotIn(provider_word, document)

    def test_provider_mapping_pins_official_pinned_provider(self) -> None:
        mapping, mapping_path = load_provider_mapping(SHIELD_DIR, CONTROL_ID, None)
        self.assertEqual(mapping["control_id"], CONTROL_ID)
        self.assertEqual(mapping["provider_name"], "Gitleaks")
        self.assertEqual(mapping["provider_version"], PINNED_PROVIDER_VERSION)
        self.assertEqual(mapping["failure_behavior"], STATUS_BLOCKED)
        self.assertTrue(mapping["coverage"]["git_history_scan"])
        self.assertTrue(mapping["coverage"]["worktree_scan"])
        self.assertTrue(mapping["limitations"])
        source = mapping["source"]
        self.assertEqual(source["kind"], "official_github_release")
        self.assertEqual(source["download_base"], f"https://github.com/gitleaks/gitleaks/releases/download/v{PINNED_PROVIDER_VERSION}")
        self.assertEqual(source["linux_x64_asset"], f"gitleaks_{PINNED_PROVIDER_VERSION}_linux_x64.tar.gz")
        self.assertEqual(source["checksums_asset"], f"gitleaks_{PINNED_PROVIDER_VERSION}_checksums.txt")
        self.assertNotIn("latest", json.dumps(source))
        self.assertIn("sha256", source["integrity_rule"])
        self.assertEqual(
            mapping_path.name, f"gitleaks-{PINNED_PROVIDER_VERSION}.json"
        )

    def test_control_and_provider_mapping_are_separate_documents(self) -> None:
        control, control_path = load_control(SHIELD_DIR, CONTROL_ID)
        mapping, mapping_path = load_provider_mapping(SHIELD_DIR, CONTROL_ID, None)
        self.assertNotEqual(control_path, mapping_path)
        # The mapping binds to the control by id only; it does not redefine it.
        self.assertEqual(set(mapping) & set(control), {"schema", "control_id"})
        for provider_field in ("invocation", "source", "provider_name"):
            self.assertNotIn(provider_field, control)
        for control_field in ("objective", "status_semantics", "evidence_fields"):
            self.assertNotIn(control_field, mapping)

    # --- runner status mapping -----------------------------------------

    def test_clean_provider_result_is_pass(self) -> None:
        evidence = self._assess("CLEAN")
        self.assertEqual(evidence["status"], STATUS_PASS)
        self.assertEqual(evidence["findings_count"], 0)
        self.assertEqual(evidence["reason"], "PROVIDER_COMPLETED_WITHOUT_FINDINGS")
        self.assertEqual(EXIT_BY_STATUS[evidence["status"]], 0)

    def test_provider_findings_are_fail_not_pass(self) -> None:
        evidence = self._assess("LEAK")
        self.assertEqual(evidence["status"], STATUS_FAIL)
        self.assertGreaterEqual(evidence["findings_count"], 1)
        self.assertEqual(EXIT_BY_STATUS[evidence["status"]], 10)
        self.assertEqual(evidence["findings"][0]["rule_id"], "stub-fake-rule")
        self.assertEqual(evidence["findings"][0]["file"], "config/service-settings.env")

    def test_finding_reference_limit_never_understates_the_count(self) -> None:
        evidence = self._assess("LEAK_MANY")
        self.assertEqual(evidence["status"], STATUS_FAIL)
        self.assertEqual(evidence["findings_count"], 30)
        self.assertEqual(len(evidence["findings"]), shield_runner.MAX_FINDING_REFERENCES)
        self.assertTrue(evidence["findings_truncated"])

    def test_evidence_never_carries_provider_secret_values(self) -> None:
        evidence = self._assess("LEAK")
        serialised = json.dumps(evidence)
        self.assertNotIn(SECRET_MARKER, serialised)
        for finding in evidence["findings"]:
            self.assertEqual(set(finding), {"rule_id", "file", "line", "commit"})

    def test_provider_failures_are_blocked_never_pass(self) -> None:
        cases = {
            "PARTIAL": "PROVIDER_INCOMPLETE",
            "NO_REPORT": "PROVIDER_REPORT_MISSING",
            "BAD_REPORT": "PROVIDER_REPORT_UNREADABLE",
            "VERSION_MISMATCH": "PROVIDER_VERSION_MISMATCH",
            "VERSION_COMMAND_FAILED": "PROVIDER_VERSION_COMMAND_FAILED",
        }
        for mode, expected_reason in cases.items():
            with self.subTest(mode=mode):
                evidence = self._assess(mode)
                self.assertEqual(evidence["status"], STATUS_BLOCKED)
                self.assertTrue(
                    evidence["reason"].startswith(expected_reason),
                    f"{mode}: {evidence['reason']}",
                )
                self.assertEqual(evidence["findings_count"], 0)
                self.assertEqual(EXIT_BY_STATUS[evidence["status"]], 20)

    def test_unavailable_provider_executable_is_blocked(self) -> None:
        missing = self.work_dir / "no-such-provider"
        evidence = self._assess("CLEAN", executable=str(missing))
        self.assertEqual(evidence["status"], STATUS_BLOCKED)
        self.assertTrue(evidence["reason"].startswith("PROVIDER_EXECUTABLE_MISSING"))
        self.assertEqual(evidence["coverage"], ["NONE_ESTABLISHED"])

    def test_unusable_provider_executable_is_blocked(self) -> None:
        not_executable = self.work_dir / "plain-file"
        not_executable.write_text("not a program\n", encoding="utf-8")
        os.chmod(not_executable, 0o644)
        evidence = self._assess("CLEAN", executable=str(not_executable))
        self.assertEqual(evidence["status"], STATUS_BLOCKED)
        self.assertIn(
            evidence["reason"].split(":")[0],
            {"PROVIDER_EXECUTABLE_NOT_EXECUTABLE", "PROVIDER_SPAWN_FAILED"},
        )

    def test_scan_mode_must_be_required_by_the_control(self) -> None:
        # The stub mapping can assess a scope the control does not require; the
        # control contract, not the provider, decides which scopes count.
        evidence = assess(
            shield_dir=SHIELD_DIR,
            control_id=CONTROL_ID,
            scan_mode="dependency_scan",
            target=self._target("CLEAN"),
            executable=str(self.stub),
            provider_mapping=self.stub_mapping,
            timeout=60,
            reference="unit-test",
        )
        self.assertEqual(evidence["status"], STATUS_BLOCKED)
        self.assertEqual(evidence["reason"], "SCAN_MODE_NOT_REQUIRED_BY_CONTROL:dependency_scan")
        self.assertEqual(evidence["coverage"], ["NONE_ESTABLISHED"])

    # --- evidence contract ---------------------------------------------

    def test_evidence_record_carries_the_full_control_contract(self) -> None:
        control, _ = load_control(SHIELD_DIR, CONTROL_ID)
        evidence = self._assess("CLEAN")
        for field in control["evidence_fields"]:
            self.assertIn(field, evidence)
            self.assertNotIn(evidence[field], (None, ""))
        self.assertEqual(evidence["schema"], "p2p-shield-evidence/1")
        self.assertEqual(evidence["control_id"], CONTROL_ID)
        self.assertEqual(evidence["control_version"], control["control_version"])
        self.assertEqual(evidence["scope"], "git_history_scan")
        self.assertEqual(evidence["provider"], "StubScan")
        self.assertEqual(evidence["provider_version"], "1.2.3")
        self.assertEqual(len(evidence["limitations"]), 2)
        self.assertTrue(evidence["limitations"][0].startswith("stub provider"))
        self.assertIn("worktree_scan", evidence["limitations"][1])
        self.assertRegex(evidence["timestamp"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    # --- provider replaceability ---------------------------------------

    def test_provider_swap_changes_provider_fields_only(self) -> None:
        other = _stub_mapping(
            self.work_dir / "other-mapping.json", name="ReplacementScan", version="4.5.6"
        )
        first = self._assess("CLEAN")
        second = self._assess("CLEAN", mapping=other)
        self.assertEqual(first["provider"], "StubScan")
        self.assertEqual(second["provider"], "ReplacementScan")
        self.assertEqual(second["provider_version"], "4.5.6")
        for field in ("control_id", "control_version", "status", "scope"):
            self.assertEqual(first[field], second[field], field)
        # The control contract binding is unchanged; the provider binding moved.
        self.assertEqual(
            first["contract_binding"]["control_sha256"],
            second["contract_binding"]["control_sha256"],
        )
        self.assertNotEqual(
            first["contract_binding"]["provider_mapping_sha256"],
            second["contract_binding"]["provider_mapping_sha256"],
        )

    def test_mapping_selection_is_fail_closed_without_a_registry(self) -> None:
        shield_dir = self.work_dir / "shield"
        (shield_dir / "controls").mkdir(parents=True)
        shutil.copy(SHIELD_DIR / "controls" / f"{CONTROL_ID}.json", shield_dir / "controls")
        (shield_dir / "providers").mkdir(parents=True)
        with self.assertRaises(Blocked) as none:
            load_provider_mapping(shield_dir, CONTROL_ID, None)
        self.assertIn("PROVIDER_MAPPING_NOT_UNIQUE", none.exception.reason)
        _stub_mapping(shield_dir / "providers" / "a.json")
        _stub_mapping(shield_dir / "providers" / "b.json", name="OtherStub")
        with self.assertRaises(Blocked) as many:
            load_provider_mapping(shield_dir, CONTROL_ID, None)
        self.assertIn("matches=2", many.exception.reason)

    def test_control_with_a_broken_fail_closed_rule_is_blocked(self) -> None:
        shield_dir = self.work_dir / "broken-shield"
        (shield_dir / "controls").mkdir(parents=True)
        control = json.loads(
            (SHIELD_DIR / "controls" / f"{CONTROL_ID}.json").read_text(encoding="utf-8")
        )
        control["non_negotiable"]["provider_failure_must_never_become_pass"] = False
        (shield_dir / "controls" / f"{CONTROL_ID}.json").write_text(
            json.dumps(control), encoding="utf-8"
        )
        evidence = assess(
            shield_dir=shield_dir,
            control_id=CONTROL_ID,
            scan_mode="git_history_scan",
            target=self._target("CLEAN"),
            executable=str(self.stub),
            provider_mapping=self.stub_mapping,
            timeout=60,
            reference="unit-test",
        )
        self.assertEqual(evidence["status"], STATUS_BLOCKED)
        self.assertEqual(evidence["reason"], "CONTROL_FAIL_CLOSED_RULE_ABSENT")
        self.assertEqual(evidence["control_version"], "UNRESOLVED")


class ProviderAcquireTests(unittest.TestCase):
    """The harness must refuse to install a provider it cannot verify."""

    def setUp(self) -> None:
        self.work_dir = Path(tempfile.mkdtemp(prefix="p2p-shield-acquire-"))
        self.addCleanup(shutil.rmtree, self.work_dir, True)
        self.asset = "gitleaks_8.18.4_linux_x64.tar.gz"
        self.checksums = "gitleaks_8.18.4_checksums.txt"

    def _official_mapping(self, **overrides) -> Path:
        source = {
            "kind": "official_github_release",
            "repository": "gitleaks/gitleaks",
            "tag": "v8.18.4",
            "download_base": "https://github.com/gitleaks/gitleaks/releases/download/v8.18.4",
            "linux_x64_asset": self.asset,
            "checksums_asset": self.checksums,
            "extracted_binary": "gitleaks",
            "integrity_rule": "sha256 of the downloaded archive must match the official checksums asset",
        }
        source.update(overrides.pop("source", {}))
        mapping = {
            "schema": "p2p-shield-provider-mapping/1",
            "control_id": CONTROL_ID,
            "provider_name": "Gitleaks",
            "provider_version": "8.18.4",
            "source": source,
            "invocation": {"version_argv": ["{executable}", "version"]},
            "coverage": {"git_history_scan": ["x"], "worktree_scan": ["y"]},
            "limitations": ["stub"],
            "failure_behavior": "BLOCKED",
        }
        mapping.update(overrides)
        path = self.work_dir / f"mapping-{abs(hash(json.dumps(mapping, sort_keys=True)))}.json"
        path.write_text(json.dumps(mapping, indent=2), encoding="utf-8")
        return path

    def _release_files(self, *, tamper: bool = False) -> Path:
        staging = self.work_dir / "release"
        package = staging / "pkg"
        package.mkdir(parents=True)
        (package / "gitleaks").write_text('#!/bin/sh\nprintf "8.18.4\\n"\n', encoding="utf-8")
        (package / "gitleaks").chmod(0o755)
        archive = staging / self.asset
        subprocess.run(
            ["tar", "-czf", str(archive), "-C", str(package), "gitleaks"],
            check=True,
            capture_output=True,
            timeout=60,
        )
        # The official checksums entry describes the untampered archive.
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        if tamper:
            with archive.open("ab") as handle:
                handle.write(b"tampered")
        (staging / self.checksums).write_text(
            f"{'0' * 64}  gitleaks_8.18.4_darwin_x64.tar.gz\n{digest}  {self.asset}\n",
            encoding="utf-8",
        )
        return staging

    def _acquire(self, mapping: Path, staging: Path, provider_dir: Path):
        from shield import acquire as acquire_module

        def fake_download(url: str, destination: Path) -> None:
            shutil.copyfile(staging / Path(url).name, destination)

        original = acquire_module.download
        acquire_module.download = fake_download
        self.addCleanup(setattr, acquire_module, "download", original)
        return acquire_module.acquire(
            mapping_path=mapping,
            provider_dir=provider_dir,
            expected_version="8.18.4",
            offline=False,
        )

    def test_official_checksum_entry_is_selected_for_the_right_asset(self) -> None:
        staging = self._release_files()
        text = (staging / self.checksums).read_text(encoding="utf-8")
        digest = acquire_expected(text, self.asset)
        self.assertEqual(digest, hashlib.sha256((staging / self.asset).read_bytes()).hexdigest())
        self.assertNotEqual(digest, "0" * 64)
        with self.assertRaises(BlockedProviderAcquisition) as missing:
            acquire_expected(text, "gitleaks_9.9.9_linux_x64.tar.gz")
        self.assertIn("PROVIDER_CHECKSUM_ENTRY_MISSING", missing.exception.reason)

    def test_verified_provider_is_installed_and_version_checked(self) -> None:
        provider_dir = self.work_dir / "provider"
        summary = self._acquire(
            self._official_mapping(), self._release_files(), provider_dir
        )
        self.assertEqual(summary["PROVIDER_ACQUIRE"], "VERIFIED_SHA256_VERSION_PINNED")
        executable = Path(summary["PROVIDER_EXECUTABLE"])
        self.assertEqual(executable.name, "gitleaks")
        self.assertTrue(os.access(executable, os.X_OK))

    def test_tampered_archive_is_blocked_and_not_installed(self) -> None:
        provider_dir = self.work_dir / "provider-tampered"
        with self.assertRaises(BlockedProviderAcquisition) as raised:
            self._acquire(self._official_mapping(), self._release_files(tamper=True), provider_dir)
        self.assertTrue(raised.exception.reason.startswith("PROVIDER_CHECKSUM_MISMATCH"))
        self.assertFalse((provider_dir / "gitleaks").exists())

    def test_provider_member_is_found_under_a_directory_prefix(self) -> None:
        # An official archive may carry one top-level directory; the binary must
        # still be located instead of silently producing a missing provider.
        staging = self.work_dir / "nested-release"
        package = staging / "pkg" / "gitleaks_8.18.4_linux_x64"
        package.mkdir(parents=True)
        (package / "gitleaks").write_text('#!/bin/sh\nprintf "8.18.4\\n"\n', encoding="utf-8")
        (package / "gitleaks").chmod(0o755)
        (package / "LICENSE").write_text("license\n", encoding="utf-8")
        archive = staging / self.asset
        subprocess.run(
            ["tar", "-czf", str(archive), "-C", str(staging / "pkg"), "gitleaks_8.18.4_linux_x64"],
            check=True,
            capture_output=True,
            timeout=60,
        )
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        (staging / self.checksums).write_text(f"{digest}  {self.asset}\n", encoding="utf-8")
        summary = self._acquire(self._official_mapping(), staging, self.work_dir / "provider-nested")
        self.assertEqual(summary["PROVIDER_ACQUIRE"], "VERIFIED_SHA256_VERSION_PINNED")
        self.assertTrue(Path(summary["PROVIDER_EXECUTABLE"]).is_file())

    def test_unpinned_or_mirrored_mapping_is_refused(self) -> None:
        for overrides, expected in (
            ({"provider_version": "8.28.0"}, "MAPPING_PROVIDER_VERSION_NOT_PINNED"),
            ({"source": {"download_base": "https://mirror.example/v8.18.4"}}, "MAPPING_DOWNLOAD_BASE_UNEXPECTED"),
            ({"source": {"kind": "package_manager"}}, "MAPPING_SOURCE_UNSUPPORTED"),
            ({"failure_behavior": "IGNORE"}, "MAPPING_FAILURE_BEHAVIOR_UNSUPPORTED"),
        ):
            with self.subTest(expected=expected):
                with self.assertRaises(BlockedProviderAcquisition) as raised:
                    load_and_validate_mapping(self._official_mapping(**overrides), "8.18.4")
                self.assertIn(expected, raised.exception.reason)


class ShieldRunnerCliTests(unittest.TestCase):
    """The runner CLI returns the Shield status, not a boolean 'passed'."""

    def test_cli_exit_codes_encode_the_shield_status(self) -> None:
        work_dir = Path(tempfile.mkdtemp(prefix="p2p-shield-cli-"))
        self.addCleanup(shutil.rmtree, work_dir, True)
        stub = work_dir / "stub-provider"
        stub.write_text(STUB_SCRIPT, encoding="utf-8")
        stub.chmod(stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        mapping = _stub_mapping(work_dir / "stub-mapping.json")
        target = work_dir / "target"
        evidence_path = work_dir / "evidence.json"
        exit_codes = {}
        for mode, expected in (
            ("CLEAN", 0),
            ("LEAK", 10),
            ("PARTIAL", 20),
        ):
            target.mkdir(parents=True, exist_ok=True)
            (target / "STUB_MODE").write_text(mode + "\n", encoding="utf-8")
            process = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "shield.runner",
                    "--control",
                    CONTROL_ID,
                    "--scan-mode",
                    "git_history_scan",
                    "--target",
                    str(target),
                    "--executable",
                    str(stub),
                    "--provider-mapping",
                    str(mapping),
                    "--evidence-out",
                    str(evidence_path),
                    "--timeout-seconds",
                    "60",
                ],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            exit_codes[mode] = process.returncode
            self.assertIn("SHIELD_STATUS=", process.stderr)
            self.assertTrue(evidence_path.is_file(), process.stderr)
        self.assertEqual(exit_codes, {"CLEAN": 0, "LEAK": 10, "PARTIAL": 20})


if __name__ == "__main__":
    unittest.main()
