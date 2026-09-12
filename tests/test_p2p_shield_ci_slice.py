"""Focused tests for P2P Shield v0.2b CI workflow slice.

Proves:
- CI control contract exists and stays provider-neutral
- Zizmor provider mapping pins exact repository/version and integrity rule
- Version extraction is exact semver only
- Checksum verification is exact
- PASS/FAIL/BLOCKED mapping via stub provider
- 3-control profile composition PASS/FAIL/BLOCKED with no overclaim
- FAIL-CLOSED verify_executable: mandatory receipt, binary hash binding, source identity
"""

from __future__ import annotations

import copy
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
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shield import zizmor_acquire as ziz
from shield import ci as shield_ci
from shield.profile import evaluate, PROFILE

CONTROL_ID = "SHIELD-CI-01"
PINNED_VERSION = "1.29.0"
REPO = "zizmorcore/zizmor"

# Stub provider emulating zizmor CLI: version prints semver, scan prints JSON based on STUB_MODE
STUB_SCRIPT = """#!/usr/bin/env python3
import sys, json, pathlib
argv = sys.argv[1:]
# version mode: any arg == --version
if "--version" in argv:
    mode = "NORMAL"
    for p in argv:
        if p.startswith("--version-mode="):
            mode = p.split("=",1)[1]
            break
    try:
        mfile = pathlib.Path("Z_VERSION_MODE")
        if mfile.is_file():
            mode = mfile.read_text().strip()
    except Exception:
        pass
    for cand in argv:
        try:
            mp = pathlib.Path(cand) / "STUB_MODE"
            if mp.is_file():
                mode = mp.read_text().strip()
                if mode.startswith("VERSION_"):
                    break
        except Exception:
            continue
    if mode == "VERSION_MISMATCH":
        print("zizmor 1.28.0")
    elif mode == "VERSION_NEAR":
        print("zizmor v1.29.00")
    elif mode == "VERSION_EXTRA_SUFFIX":
        print("zizmor 1.29.0-extra")
    else:
        print("zizmor 1.29.0")
    sys.exit(0)

# scan mode: first positional arg that is a directory is the target
target = None
for cand in argv:
    if not cand.startswith("-") and pathlib.Path(cand).is_dir():
        target = cand
        break
mode = "CLEAN"
if target:
    mf = pathlib.Path(target) / "STUB_MODE"
    if mf.is_file():
        mode = mf.read_text().strip()
    if mode.startswith("VERSION_"):
        mode = "CLEAN"

def write_json(obj, code):
    sys.stdout.write(json.dumps(obj))
    sys.stdout.flush()
    sys.exit(code)

if mode == "CLEAN":
    write_json([], 0)
elif mode == "UNPINNED":
    finding = {
        "ident": "unpinned-uses",
        "desc": "unpinned action reference",
        "url": "https://docs.zizmor.sh/audits/#unpinned-uses",
        "determinations": {"confidence": "High", "severity": "High", "persona": "Regular"},
        "locations": [
            {
                "symbolic": {"key": {"Local": {"verbatim_path": ".github/workflows/ci.yml"}}, "kind": "Primary", "annotation": "action is not pinned", "route": {"route": [{"Key": "jobs"}, {"Key": "build"}, {"Key": "steps"}, {"Index": 0}, {"Key": "uses"}]}, "feature_kind": "Normal"},
                "concrete": {"location": {"start_point": {"row": 10, "column": 15}, "end_point": {"row": 10, "column": 33}, "offset_span": {"start": 100, "end": 130}}, "feature": "uses: actions/checkout@v4", "comments": []}
            }
        ],
        "ignored": False,
        "fixes": []
    }
    write_json([finding], 14)
elif mode == "UNPINNED_MANY":
    f = {
        "ident": "unpinned-uses",
        "desc": "unpinned action reference",
        "url": "https://docs.zizmor.sh/audits/#unpinned-uses",
        "determinations": {"confidence": "High", "severity": "High", "persona": "Regular"},
        "locations": [{"symbolic": {"key": {"Local": {"verbatim_path": ".github/workflows/ci.yml"}}, "kind": "Primary"}, "concrete": {"location": {"start_point": {"row": 5, "column": 0}, "end_point": {"row": 5, "column": 10}}, "feature": "uses", "comments": []}}],
        "ignored": False,
        "fixes": []
    }
    write_json([f]*5, 14)
elif mode == "BAD_JSON":
    sys.stdout.write("not-json")
    sys.exit(0)
elif mode == "NO_INPUTS":
    sys.stderr.write("error: no inputs collected")
    sys.exit(3)
elif mode == "PROVIDER_ERROR":
    sys.stderr.write("fatal: no audit was performed")
    sys.exit(1)
else:
    write_json([], 0)
"""

def init_test_repo(path: Path):
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "P2P Shield Test",
        "GIT_AUTHOR_EMAIL": "p2p-shield-test@example.invalid",
        "GIT_COMMITTER_NAME": "P2P Shield Test",
        "GIT_COMMITTER_EMAIL": "p2p-shield-test@example.invalid",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
    }
    for args in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "fixture"]):
        subprocess.run(
            ["git", "-c", "commit.gpgsign=false", *args],
            cwd=str(path),
            check=True,
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
        )

def _write_valid_receipt(binary: Path):
    """Create a valid synthetic receipt for a stub binary that reports 1.29.0."""
    binary = Path(binary)
    sha = hashlib.sha256(binary.read_bytes()).hexdigest()
    receipt = {
        "source": dict(ziz.SOURCE),
        "sha256": ziz.DIGEST,
        "binary_sha256": sha,
        "observed_version": ziz.VERSION,
        "provider": "Zizmor",
        "provider_version": ziz.VERSION,
        "repository": ziz.REPOSITORY,
        "tag": ziz.TAG,
    }
    receipt_path = binary.with_suffix('.verified.json')
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    return receipt_path, receipt

class CiSliceTest(unittest.TestCase):
    def setUp(self):
        self.work_dir = Path(tempfile.mkdtemp(prefix="p2p-shield-ci-test-"))
        self.addCleanup(shutil.rmtree, self.work_dir, True)
        self.stub = self.work_dir / "stub-zizmor"
        self.stub.write_text(STUB_SCRIPT, encoding="utf-8")
        self.stub.chmod(self.stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        self._counter = 0
        # Create valid receipt for stub so existing PASS/FAIL tests that rely on stub can reach provider logic
        _write_valid_receipt(self.stub)

    def _new_repo(self, mode="CLEAN", workflow_content=None):
        self._counter += 1
        repo = self.work_dir / f"repo-{self._counter}"
        repo.mkdir(parents=True)
        wf_dir = repo / ".github/workflows"
        wf_dir.mkdir(parents=True)
        if workflow_content is None:
            workflow_content = """name: ci
on: push
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - run: echo hello\n"""
        (wf_dir / "ci.yml").write_text(workflow_content, encoding="utf-8")
        (repo / "STUB_MODE").write_text(mode, encoding="utf-8")
        (repo / "README.md").write_text("# fixture\n", encoding="utf-8")
        init_test_repo(repo)
        (repo / "STUB_MODE").write_text(mode, encoding="utf-8")
        return repo

    def test_control_contract(self):
        control_path = REPO_ROOT / "shield/controls/SHIELD-CI-01.json"
        control = json.loads(control_path.read_text())
        for field in ("control_id", "control_version", "objective", "applies_to", "required_scope", "required_evidence", "status_semantics", "limitations"):
            self.assertTrue(control.get(field), f"missing {field}")
        self.assertEqual(control["control_id"], CONTROL_ID)
        self.assertEqual(control["control_version"], "0.1.0")
        self.assertIn("github_actions_workflow_scan", str(control["required_scope"]))
        self.assertEqual(set(control["status_semantics"].keys()), {"PASS", "FAIL", "BLOCKED"})
        self.assertIn("GitHub Actions", control["objective"])
        self.assertEqual(set(PROFILE["required_controls"].keys()), {"SHIELD-SECRET-01", "SHIELD-DEPENDENCY-01", "SHIELD-CI-01"})
        self.assertEqual(PROFILE["profile_version"], "0.2.1")

    def test_source_and_version_pins(self):
        original = ziz.mapping()
        for key, val in [("provider_version", "1.28.0"), ("provider_version", "1.29.1"), ("provider_version", "latest"), ("provider_name", "Other"), ("provider_version", "1.30.0-rc1")]:
            m = copy.deepcopy(original)
            m[key] = val
            with patch.object(Path, "read_text", return_value=json.dumps(m)):
                with self.assertRaises(ValueError, msg=f"{key}={val} should fail"):
                    ziz.mapping()
        for key, val in [("repository", "mirror/zizmor"), ("tag", "v1.28.0"), ("asset", "elsewhere.tar.gz"), ("asset_digest_value", "0"*64)]:
            m = copy.deepcopy(original)
            m["source"][key] = val
            with patch.object(Path, "read_text", return_value=json.dumps(m)):
                with self.assertRaises(ValueError):
                    ziz.mapping()
        m = copy.deepcopy(original)
        m["source"]["integrity_rule"] = "no hash here"
        with patch.object(Path, "read_text", return_value=json.dumps(m)):
            with self.assertRaises(ValueError):
                ziz.mapping()

    def test_exact_observed_version(self):
        for text, valid in [
            ("zizmor 1.29.0\n", True),
            ("zizmor v1.29.0", True),
            ("zizmor 1.29.00", False),
            ("1.29.0-dev", False),
            ("zizmor 1.28.0", False),
            ("zizmor 1.29.0-extra", False),
            ("zizmor v1.29.0-dirty", False),
        ]:
            with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0, text, "")):
                if valid:
                    self.assertEqual(ziz.version("binary"), "1.29.0")
                else:
                    with self.assertRaises(ValueError):
                        ziz.version("binary")
        with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 1, "zizmor 1.29.0", "")):
            with self.assertRaises(ValueError):
                ziz.version("binary")

    def test_checksum(self):
        data = b"unit-test-only"
        digest = hashlib.sha256(data).hexdigest()
        self.assertEqual(ziz.verify_checksum(data, digest), digest)
        for bad in ["0"*64, digest + "00", "", "abcd"]:
            with self.assertRaises(ValueError):
                ziz.verify_checksum(data, bad)
        with self.assertRaises(ValueError):
            ziz.verify_checksum(b"other", digest)

    def test_pass_mapping(self):
        repo = self._new_repo(mode="CLEAN")
        evidence = shield_ci.assess(repo, self.stub, "test-pass")
        self.assertEqual(evidence["status"], "PASS")
        self.assertEqual(evidence["control_id"], CONTROL_ID)
        self.assertEqual(evidence["scope"], "github_actions_workflow_scan")
        self.assertEqual(evidence["findings_count"], 0)
        self.assertTrue(evidence["coverage"])
        self.assertNotIn("NONE_ESTABLISHED", evidence["coverage"])
        self.assertEqual(evidence["provider"], "Zizmor")
        self.assertEqual(evidence["provider_version"], "1.29.0")
        self.assertIn("zizmorcore/zizmor@v1.29.0", evidence["provider_source"])

    def test_fail_mapping(self):
        repo = self._new_repo(mode="UNPINNED")
        evidence = shield_ci.assess(repo, self.stub, "test-fail")
        self.assertEqual(evidence["status"], "FAIL")
        self.assertGreaterEqual(evidence["findings_count"], 1)
        self.assertTrue(any(f.get("audit") == "unpinned-uses" for f in evidence["findings"]))
        self.assertTrue(any(".github/workflows/ci.yml" in f.get("file","") for f in evidence["findings"]))
        self.assertTrue(any(f.get("severity") == "High" for f in evidence["findings"]))

    def test_blocked_unavailable_provider(self):
        repo = self._new_repo(mode="CLEAN")
        missing = self.work_dir / "absent-zizmor"
        evidence = shield_ci.assess(repo, missing, "test-blocked-missing")
        self.assertEqual(evidence["status"], "BLOCKED")
        self.assertEqual(evidence["coverage"], ["NONE_ESTABLISHED"])
        self.assertEqual(evidence["findings_count"], 0)

    def test_blocked_malformed_output(self):
        repo = self._new_repo(mode="BAD_JSON")
        evidence = shield_ci.assess(repo, self.stub, "test-bad-json")
        self.assertEqual(evidence["status"], "BLOCKED")

    def test_blocked_no_workflow_inventory(self):
        repo = self._new_repo(mode="NO_INPUTS")
        evidence = shield_ci.assess(repo, self.stub, "test-no-inputs")
        self.assertEqual(evidence["status"], "BLOCKED")
        self.assertIn("WORKFLOW_INVENTORY", evidence["reason"])

    def test_blocked_target_not_git_repository(self):
        plain = self.work_dir / "plain-dir"
        plain.mkdir()
        (plain / ".github" / "workflows").mkdir(parents=True)
        (plain / ".github/workflows/ci.yml").write_text("name: ci\non: push\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps: []\n")
        (plain / "STUB_MODE").write_text("CLEAN")
        evidence = shield_ci.assess(plain, self.stub, "test-not-git")
        self.assertEqual(evidence["status"], "BLOCKED")
        self.assertIn("TARGET_REF", evidence["reason"])

    def test_blocked_provider_error(self):
        repo = self._new_repo(mode="PROVIDER_ERROR")
        evidence = shield_ci.assess(repo, self.stub, "test-provider-error")
        self.assertEqual(evidence["status"], "BLOCKED")

    @patch("shield.profile.resolve_target_ref", return_value="a"*40)
    def test_profile_3_control_pass(self, _resolve_ref):
        records = []
        for cid, rule in PROFILE["required_controls"].items():
            for scope in rule["required_scopes"]:
                rec = dict(
                    schema="p2p-shield-evidence/1",
                    control_id=cid,
                    control_version="0.1.0",
                    scope=scope,
                    target="/fixture",
                    target_ref="a"*40,
                    timestamp="2026-09-12T00:00:00Z",
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
                records.append(rec)
        result = evaluate(records, "/fixture", "a"*40)
        self.assertEqual(result["PROFILE_REQUIREMENTS_STATUS"], "PASS")
        self.assertEqual(result["SYSTEM_SECURITY_VERDICT"], "NOT_EVALUATED")

    @patch("shield.profile.resolve_target_ref", return_value="a"*40)
    def test_profile_3_control_fail(self, _resolve_ref):
        records = []
        for cid, rule in PROFILE["required_controls"].items():
            for scope in rule["required_scopes"]:
                rec = dict(
                    schema="p2p-shield-evidence/1",
                    control_id=cid,
                    control_version="0.1.0",
                    scope=scope,
                    target="/fixture",
                    target_ref="a"*40,
                    timestamp="2026-09-12T00:00:00Z",
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
                records.append(rec)
        for rec in records:
            if rec["control_id"] == "SHIELD-CI-01":
                rec["status"] = "FAIL"
                rec["findings_count"] = 1
                break
        result = evaluate(records, "/fixture", "a"*40)
        self.assertEqual(result["PROFILE_REQUIREMENTS_STATUS"], "FAIL")
        self.assertEqual(result["SYSTEM_SECURITY_VERDICT"], "NOT_EVALUATED")

    @patch("shield.profile.resolve_target_ref", return_value="a"*40)
    def test_profile_3_control_blocked(self, _resolve_ref):
        records = []
        for cid, rule in PROFILE["required_controls"].items():
            for scope in rule["required_scopes"]:
                rec = dict(
                    schema="p2p-shield-evidence/1",
                    control_id=cid,
                    control_version="0.1.0",
                    scope=scope,
                    target="/fixture",
                    target_ref="a"*40,
                    timestamp="2026-09-12T00:00:00Z",
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
                records.append(rec)
        for rec in records:
            if rec["control_id"] == "SHIELD-CI-01":
                rec["status"] = "BLOCKED"
                rec["coverage"] = ["NONE_ESTABLISHED"]
                break
        result = evaluate(records, "/fixture", "a"*40)
        self.assertEqual(result["PROFILE_REQUIREMENTS_STATUS"], "BLOCKED")
        self.assertEqual(result["SYSTEM_SECURITY_VERDICT"], "NOT_EVALUATED")

    @patch("shield.profile.resolve_target_ref", return_value="a"*40)
    def test_no_system_security_overclaim(self, _resolve_ref):
        records = []
        for cid, rule in PROFILE["required_controls"].items():
            for scope in rule["required_scopes"]:
                rec = dict(
                    schema="p2p-shield-evidence/1",
                    control_id=cid,
                    control_version="0.1.0",
                    scope=scope,
                    target="/fixture",
                    target_ref="a"*40,
                    timestamp="2026-09-12T00:00:00Z",
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
                records.append(rec)
        result = evaluate(records, "/fixture", "a"*40)
        self.assertNotIn("SYSTEM_SECURE", str(result))
        self.assertNotIn("P2P_SECURE", str(result))
        self.assertEqual(result["SYSTEM_SECURITY_VERDICT"], "NOT_EVALUATED")
        self.assertNotIn("SECURE", result.get("reason",""))


class ZizmorVerifyTests(unittest.TestCase):
    """FAIL-CLOSED receipt + binary hash binding."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="p2p-ziz-verify-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.bin = self.tmp / "zizmor"
        self.bin.write_text(STUB_SCRIPT, encoding="utf-8")
        self.bin.chmod(self.bin.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    def _valid_receipt(self):
        _, receipt = _write_valid_receipt(self.bin)
        return receipt

    def test_missing_receipt_blocked(self):
        # exact-version binary but no receipt => BLOCKED
        # ensure no receipt file
        receipt_path = self.bin.with_suffix('.verified.json')
        if receipt_path.is_file():
            receipt_path.unlink()
        with self.assertRaises(ValueError) as ctx:
            ziz.verify_executable(self.bin)
        self.assertIn("ZIZMOR_RECEIPT_MISSING", str(ctx.exception))
        # also via assess -> BLOCKED
        repo = self.tmp / "repo"
        repo.mkdir()
        wf = repo / ".github/workflows"
        wf.mkdir(parents=True)
        (wf / "ci.yml").write_text("name: ci\non: push\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps: [{run: echo hi}]\n")
        (repo / "STUB_MODE").write_text("CLEAN")
        (repo / "README.md").write_text("hi")
        init_test_repo(repo)
        (repo / "STUB_MODE").write_text("CLEAN")
        evid = shield_ci.assess(repo, self.bin, "ref")
        self.assertEqual(evid["status"], "BLOCKED")

    def test_forged_receipt_blocked(self):
        self._valid_receipt()
        receipt_path = self.bin.with_suffix('.verified.json')
        data = json.loads(receipt_path.read_text())
        data["binary_sha256"] = "0"*64  # forged hash
        receipt_path.write_text(json.dumps(data))
        with self.assertRaises(ValueError) as ctx:
            ziz.verify_executable(self.bin)
        self.assertIn("ZIZMOR_BINARY_TAMPERED", str(ctx.exception))

    def test_tampered_binary_blocked(self):
        self._valid_receipt()
        # tamper binary after receipt
        self.bin.write_text(self.bin.read_text() + "\n# tampered\n", encoding="utf-8")
        self.bin.chmod(self.bin.stat().st_mode | stat.S_IEXEC)
        with self.assertRaises(ValueError) as ctx:
            ziz.verify_executable(self.bin)
        self.assertIn("ZIZMOR_BINARY_TAMPERED", str(ctx.exception))

    def test_valid_receipt_pass(self):
        self._valid_receipt()
        # should PASS
        observed = ziz.verify_executable(self.bin)
        self.assertEqual(observed, "1.29.0")
        # and assess should PASS with clean workflow
        repo = self.tmp / "repo2"
        repo.mkdir()
        wf = repo / ".github/workflows"
        wf.mkdir(parents=True)
        (wf / "ci.yml").write_text("name: ci\non: push\npermissions:\n  contents: read\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps: [{run: echo hi}]\n")
        (repo / "STUB_MODE").write_text("CLEAN")
        (repo / "README.md").write_text("hi")
        init_test_repo(repo)
        (repo / "STUB_MODE").write_text("CLEAN")
        evid = shield_ci.assess(repo, self.bin, "ref")
        self.assertEqual(evid["status"], "PASS")

    def test_wrong_download_base_blocked(self):
        self._valid_receipt()
        receipt_path = self.bin.with_suffix('.verified.json')
        data = json.loads(receipt_path.read_text())
        data["source"]["download_base"] = "https://evil.example/zizmor"
        receipt_path.write_text(json.dumps(data))
        with self.assertRaises(ValueError) as ctx:
            ziz.verify_executable(self.bin)
        self.assertIn("ZIZMOR_SOURCE_IDENTITY_MISMATCH", str(ctx.exception))
        self.assertIn("download_base", str(ctx.exception))

    def test_wrong_asset_digest_blocked(self):
        self._valid_receipt()
        receipt_path = self.bin.with_suffix('.verified.json')
        data = json.loads(receipt_path.read_text())
        data["source"]["asset_digest"] = "sha256:" + "0"*64
        receipt_path.write_text(json.dumps(data))
        with self.assertRaises(ValueError) as ctx:
            ziz.verify_executable(self.bin)
        self.assertIn("ZIZMOR_SOURCE_IDENTITY_MISMATCH", str(ctx.exception))
        self.assertIn("asset_digest", str(ctx.exception))
        # also top-level sha256 mismatch should be caught
        data = json.loads(receipt_path.read_text())
        data["source"]["asset_digest"] = ziz.SOURCE["asset_digest"]
        data["sha256"] = "0"*64
        receipt_path.write_text(json.dumps(data))
        with self.assertRaises(ValueError) as ctx2:
            ziz.verify_executable(self.bin)
        self.assertIn("ZIZMOR_DIGEST_MISMATCH", str(ctx2.exception))

    def test_wrong_extracted_binary_blocked(self):
        self._valid_receipt()
        receipt_path = self.bin.with_suffix('.verified.json')
        data = json.loads(receipt_path.read_text())
        data["source"]["extracted_binary"] = "evil"
        receipt_path.write_text(json.dumps(data))
        with self.assertRaises(ValueError) as ctx:
            ziz.verify_executable(self.bin)
        self.assertIn("ZIZMOR_SOURCE_IDENTITY_MISMATCH", str(ctx.exception))
        self.assertIn("extracted_binary", str(ctx.exception))

    def test_malformed_receipt_blocked(self):
        # not json
        receipt_path = self.bin.with_suffix('.verified.json')
        receipt_path.write_text("not-json", encoding="utf-8")
        with self.assertRaises(ValueError) as ctx:
            ziz.verify_executable(self.bin)
        self.assertIn("ZIZMOR_RECEIPT_MALFORMED", str(ctx.exception))
        # missing binary_sha256
        self._valid_receipt()
        data = json.loads(receipt_path.read_text())
        del data["binary_sha256"]
        receipt_path.write_text(json.dumps(data))
        with self.assertRaises(ValueError) as ctx2:
            ziz.verify_executable(self.bin)
        self.assertIn("ZIZMOR_BINARY_SHA256_MISSING", str(ctx2.exception))


class DurableWorkflowRoutingContractTest(unittest.TestCase):
    """Contract for the single durable BASE acceptance workflow.

    Proves promotion-ready routing with no Arena session branch residue:
    NO_ARENA_BRANCH_TRIGGER=YES, exact push/pull_request branch lists, no
    pull_request_target/schedule/workflow_run/repository_dispatch, and the
    read-only permissions + immutable pinned checkout security properties.
    """

    WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
    WORKFLOW = WORKFLOWS_DIR / "p2p-shield-ci-slice.yml"

    def test_durable_base_acceptance_routing_contract(self):
        shield_workflows = sorted(
            p.name for p in self.WORKFLOWS_DIR.glob("p2p-shield-*.yml")
        )
        # Historical session harnesses removed; exactly one durable workflow.
        self.assertEqual(shield_workflows, ["p2p-shield-ci-slice.yml"])
        # NO_ARENA_BRANCH_TRIGGER=YES — nowhere in any Shield workflow.
        for name in shield_workflows:
            self.assertNotIn(
                "arena/", (self.WORKFLOWS_DIR / name).read_text(encoding="utf-8")
            )
        text = self.WORKFLOW.read_text(encoding="utf-8")
        on_block = self._trigger_block(text)
        self.assertEqual(
            self._branches(on_block, "push"), ["docs/p2p-shield-plan", "main"]
        )
        self.assertEqual(
            self._branches(on_block, "pull_request"), ["docs/p2p-shield-plan", "main"]
        )
        for forbidden in (
            "pull_request_target",
            "schedule:",
            "workflow_run",
            "repository_dispatch",
        ):
            self.assertNotIn(forbidden, on_block)
        # Security properties must remain.
        self.assertIn("permissions:", text)
        self.assertIn("contents: read", text)
        self.assertIn(
            "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803", text
        )
        self.assertIn("fetch-depth: 0", text)
        self.assertIn("persist-credentials: false", text)

    def _trigger_block(self, text):
        lines = text.splitlines()
        start = None
        for i, line in enumerate(lines):
            if line == "on:":
                start = i + 1
                break
        self.assertIsNotNone(start, "workflow has no on: block")
        block = []
        for line in lines[start:]:
            if line and not line[0].isspace():
                break
            block.append(line)
        return "\n".join(block)

    def _branches(self, block, trigger):
        lines = block.splitlines()
        try:
            i = lines.index("  " + trigger + ":")
        except ValueError:
            self.fail("missing trigger: " + trigger)
        branches = []
        in_branches = False
        for line in lines[i + 1:]:
            if in_branches:
                stripped = line.strip()
                if stripped.startswith("- "):
                    branches.append(stripped[2:].strip())
                    continue
                break
            if line.strip() == "branches:":
                in_branches = True
        return branches


if __name__ == "__main__":
    unittest.main()
