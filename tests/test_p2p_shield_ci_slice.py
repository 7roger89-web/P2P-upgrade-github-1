"""Focused tests for P2P Shield v0.2b CI workflow slice.

Proves:
- CI control contract exists and stays provider-neutral
- Zizmor provider mapping pins exact repository/version and integrity rule
- Version extraction is exact semver only
- Checksum verification is exact
- PASS/FAIL/BLOCKED mapping via stub provider
- 3-control profile composition PASS/FAIL/BLOCKED with no overclaim
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
if \"--version\" in argv:
    # Check for version override file next to stub or in target
    mode = \"NORMAL\"
    for p in argv:
        if p.startswith(\"--version-mode=\"):
            mode = p.split(\"=\",1)[1]
            break
    # also check file Z_VERSION_MODE in cwd
    try:
        mfile = pathlib.Path(\"Z_VERSION_MODE\")
        if mfile.is_file():
            mode = mfile.read_text().strip()
    except Exception:
        pass
    # Try to find STUB_MODE in any arg that looks like a path containing file
    for cand in argv:
        try:
            mp = pathlib.Path(cand) / \"STUB_MODE\"
            if mp.is_file():
                mode = mp.read_text().strip()
                if mode.startswith(\"VERSION_\"):
                    break
        except Exception:
            continue
    if mode == \"VERSION_MISMATCH\":
        print(\"zizmor 1.28.0\")
    elif mode == \"VERSION_NEAR\":
        print(\"zizmor v1.29.00\")
    elif mode == \"VERSION_EXTRA_SUFFIX\":
        print(\"zizmor 1.29.0-extra\")
    else:
        print(\"zizmor 1.29.0\")
    sys.exit(0)

# scan mode: first positional arg that is a directory is the target
target = None
for cand in argv:
    if not cand.startswith(\"-\") and pathlib.Path(cand).is_dir():
        target = cand
        break
mode = \"CLEAN\"
if target:
    mf = pathlib.Path(target) / \"STUB_MODE\"
    if mf.is_file():
        mode = mf.read_text().strip()
    # also support version mismatch via target mode
    if mode.startswith(\"VERSION_\"):
        # for scan we still treat as clean but version check would have failed earlier
        mode = \"CLEAN\"

def write_json(obj, code):
    sys.stdout.write(json.dumps(obj))
    sys.stdout.flush()
    sys.exit(code)

if mode == \"CLEAN\":
    write_json([], 0)
elif mode == \"UNPINNED\":
    finding = {
        \"ident\": \"unpinned-uses\",
        \"desc\": \"unpinned action reference\",
        \"url\": \"https://docs.zizmor.sh/audits/#unpinned-uses\",
        \"determinations\": {\"confidence\": \"High\", \"severity\": \"High\", \"persona\": \"Regular\"},
        \"locations\": [
            {
                \"symbolic\": {\"key\": {\"Local\": {\"verbatim_path\": \".github/workflows/ci.yml\"}}, \"kind\": \"Primary\", \"annotation\": \"action is not pinned\", \"route\": {\"route\": [{\"Key\": \"jobs\"}, {\"Key\": \"build\"}, {\"Key\": \"steps\"}, {\"Index\": 0}, {\"Key\": \"uses\"}]}, \"feature_kind\": \"Normal\"},
                \"concrete\": {\"location\": {\"start_point\": {\"row\": 10, \"column\": 15}, \"end_point\": {\"row\": 10, \"column\": 33}, \"offset_span\": {\"start\": 100, \"end\": 130}}, \"feature\": \"uses: actions/checkout@v4\", \"comments\": []}
            }
        ],
        \"ignored\": False,
        \"fixes\": []
    }
    write_json([finding], 14)
elif mode == \"UNPINNED_MANY\":
    f = {
        \"ident\": \"unpinned-uses\",
        \"desc\": \"unpinned action reference\",
        \"url\": \"https://docs.zizmor.sh/audits/#unpinned-uses\",
        \"determinations\": {\"confidence\": \"High\", \"severity\": \"High\", \"persona\": \"Regular\"},
        \"locations\": [{\"symbolic\": {\"key\": {\"Local\": {\"verbatim_path\": \".github/workflows/ci.yml\"}}, \"kind\": \"Primary\"}, \"concrete\": {\"location\": {\"start_point\": {\"row\": 5, \"column\": 0}, \"end_point\": {\"row\": 5, \"column\": 10}}, \"feature\": \"uses\", \"comments\": []}}],
        \"ignored\": False,
        \"fixes\": []
    }
    write_json([f]*5, 14)
elif mode == \"BAD_JSON\":
    sys.stdout.write(\"not-json\")
    sys.exit(0)
elif mode == \"NO_INPUTS\":
    sys.stderr.write(\"error: no inputs collected\")
    sys.exit(3)
elif mode == \"PROVIDER_ERROR\":
    sys.stderr.write(\"fatal: no audit was performed\")
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

class CiSliceTest(unittest.TestCase):
    def setUp(self):
        self.work_dir = Path(tempfile.mkdtemp(prefix="p2p-shield-ci-test-"))
        self.addCleanup(shutil.rmtree, self.work_dir, True)
        self.stub = self.work_dir / "stub-zizmor"
        self.stub.write_text(STUB_SCRIPT, encoding="utf-8")
        self.stub.chmod(self.stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        self._counter = 0

    def _new_repo(self, mode="CLEAN", workflow_content=None):
        self._counter += 1
        repo = self.work_dir / f"repo-{self._counter}"
        repo.mkdir(parents=True)
        # minimal workflow file
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
        # ensure STUB_MODE persists after commit? need to re-create after commit as it is untracked? Let's keep it untracked but file exists
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
        # check no overclaim: objective mentions provider and coverage
        self.assertIn("GitHub Actions", control["objective"])
        # profile must now have 3 controls
        self.assertEqual(set(PROFILE["required_controls"].keys()), {"SHIELD-SECRET-01", "SHIELD-DEPENDENCY-01", "SHIELD-CI-01"})
        self.assertEqual(PROFILE["profile_version"], "0.2.0")

    def test_source_and_version_pins(self):
        original = ziz.mapping()
        # provider version/name mismatch should be blocked
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
        # integrity rule must contain sha256
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
        # version command failure also blocked
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
        # also verify data mismatch
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
        # finding should preserve audit identifier and file
        self.assertTrue(any(f.get("audit") == "unpinned-uses" for f in evidence["findings"]))
        self.assertTrue(any(".github/workflows/ci.yml" in f.get("file","") for f in evidence["findings"]))
        # severity/confidence preserved
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
        # plain directory, not a git repo
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

    def test_profile_3_control_pass(self):
        # Build evidence for all required scopes, all PASS => PROFILE PASS
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

    def test_profile_3_control_fail(self):
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
        # Change only CI evidence to FAIL
        for rec in records:
            if rec["control_id"] == "SHIELD-CI-01":
                rec["status"] = "FAIL"
                rec["findings_count"] = 1
                break
        result = evaluate(records, "/fixture", "a"*40)
        self.assertEqual(result["PROFILE_REQUIREMENTS_STATUS"], "FAIL")
        self.assertEqual(result["SYSTEM_SECURITY_VERDICT"], "NOT_EVALUATED")

    def test_profile_3_control_blocked(self):
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

    def test_no_system_security_overclaim(self):
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


if __name__ == "__main__":
    unittest.main()
