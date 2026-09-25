"""Issue #252 regression tests for evidence-gated native language admission."""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / ".p2p" / "system" / "p2p_capabilities" / "performance_language_gate.py"
DEV_CLI = ROOT / "scripts" / "p2p_performance_language_gate.py"
RUNTIME_CLI = ROOT / ".p2p" / "system" / "scripts" / "p2p_performance_language_gate.py"
FIXTURE = ROOT / "tests" / "fixtures" / "p2p_performance_language_gate" / "ziwei_518400_canary.json"
NOTEBOOK = ROOT / "docs" / "p2p-development" / "P2P-OPERATIONS-NOTEBOOK.md"
BOOTSTRAP = ROOT / "docs" / "p2p-development" / "P2P-PROJECT-BOOTSTRAP.md"
INSTALL = ROOT / "docs" / "p2p-development" / "P2P-AGENTS-INSTALL.md"
PACKAGE = ROOT / "scripts" / "package_release.py"
LEDGER = ROOT / "governance" / "research-adoption-ledger.json"

spec = importlib.util.spec_from_file_location("performance_language_gate", MODULE)
assert spec is not None and spec.loader is not None
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def packet(**updates):
    value = {
        "SCENARIO": "representative batch",
        "CURRENT_STACK": "Python",
        "ACCEPTANCE_TARGET": {"metric": "duration_seconds", "operator": "<=", "value": 5},
        "BASELINE": {"metric": "duration_seconds", "value": 20},
        "BOTTLENECK": "CPU_ALGORITHM",
        "HOT_PATH": "calculate_all",
        "HOT_PATH_SHARE": 0.8,
        "CURRENT_STACK_OPTIMIZED": True,
        "CURRENT_STACK_RESULT": {"metric": "duration_seconds", "value": 12},
    }
    value.update(updates)
    return value


class PerformanceLanguageAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.notebook = NOTEBOOK.read_text(encoding="utf-8")
        cls.bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
        cls.install = INSTALL.read_text(encoding="utf-8")
        cls.package = PACKAGE.read_text(encoding="utf-8")
        cls.ledger = json.loads(LEDGER.read_text(encoding="utf-8"))

    def evaluate(self, **updates):
        return gate.evaluate_performance_language_admission(packet(**updates))

    def test_missing_target_does_not_activate_native(self):
        result = self.evaluate(ACCEPTANCE_TARGET=None)
        self.assertEqual(result["VERDICT"], "INSUFFICIENT_EVIDENCE")
        self.assertFalse(result["NATIVE_CANDIDATE"])

    def test_current_stack_that_meets_target_stays(self):
        result = self.evaluate(BASELINE={"metric": "duration_seconds", "value": 4})
        self.assertEqual(result["VERDICT"], "KEEP_CURRENT_STACK")

    def test_non_cpu_bottlenecks_route_away_from_native(self):
        for bottleneck in ("DB", "NETWORK", "IO", "SERIALIZATION", "EXTERNAL_SERVICE", "MEMORY"):
            with self.subTest(bottleneck=bottleneck):
                result = self.evaluate(BOTTLENECK=bottleneck)
                self.assertEqual(result["VERDICT"], "FIX_NON_CPU_BOTTLENECK")
                self.assertFalse(result["NATIVE_CANDIDATE"])

    def test_cpu_path_requires_current_stack_optimization_first(self):
        result = self.evaluate(CURRENT_STACK_OPTIMIZED=False)
        self.assertEqual(result["VERDICT"], "OPTIMIZE_CURRENT_STACK_FIRST")

    def test_measured_cpu_hot_path_can_open_bounded_spike_only(self):
        result = self.evaluate()
        self.assertEqual(result["VERDICT"], "RUN_BOUNDED_NATIVE_SPIKE")
        self.assertTrue(result["NATIVE_CANDIDATE"])
        self.assertEqual(result["PERMISSION_EFFECT"], "NONE")

    def test_native_spike_must_be_same_workload_and_meet_target(self):
        different = self.evaluate(NATIVE_SPIKE={
            "performed": True,
            "same_workload": False,
            "result": {"metric": "duration_seconds", "value": 2},
        })
        self.assertEqual(different["VERDICT"], "INSUFFICIENT_EVIDENCE")
        slow = self.evaluate(NATIVE_SPIKE={
            "performed": True,
            "same_workload": True,
            "result": {"metric": "duration_seconds", "value": 8},
        })
        self.assertEqual(slow["VERDICT"], "REJECT_NATIVE_SPIKE")

    def test_adoption_requires_boundary_cost_and_rollback(self):
        spike = {
            "performed": True,
            "same_workload": True,
            "result": {"metric": "duration_seconds", "value": 2},
        }
        incomplete = self.evaluate(NATIVE_SPIKE=spike, SMALLEST_BOUNDARY="one module")
        self.assertEqual(incomplete["VERDICT"], "INSUFFICIENT_EVIDENCE")
        complete = self.evaluate(
            NATIVE_SPIKE=spike,
            SMALLEST_BOUNDARY="one module",
            OPERATIONS_COST="cargo build plus binding maintenance",
            ROLLBACK_PATH="remove binding and restore current implementation",
        )
        self.assertEqual(complete["VERDICT"], "ADOPT_BOUNDED_NATIVE_COMPONENT")
        self.assertEqual(complete["PERMISSION_EFFECT"], "NONE")

    def test_real_ziwei_canary_proves_scale_is_not_rust_need(self):
        value = json.loads(FIXTURE.read_text(encoding="utf-8"))
        expected_verdict = value.pop("EXPECTED_VERDICT")
        expected_candidate = value.pop("EXPECTED_NATIVE_CANDIDATE")
        value.pop("WHY")
        result = gate.evaluate_performance_language_admission(value)
        self.assertEqual(result["VERDICT"], expected_verdict)
        self.assertEqual(result["NATIVE_CANDIDATE"], expected_candidate)
        self.assertEqual(value["DATASET_PROVENANCE"]["records"], 518400)
        self.assertEqual(value["DATASET_PROVENANCE"]["bytes"], 5878228608)

    def test_cli_executes_real_canary(self):
        proc = subprocess.run(
            [sys.executable, str(DEV_CLI), "evaluate", "--file", str(FIXTURE)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["VERDICT"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(result["PERMISSION_EFFECT"], "NONE")

    def test_rule19_packaging_ledger_and_no_forced_rust(self):
        heading = "#### PERFORMANCE_LANGUAGE_ADMISSION_V1"
        self.assertIn(heading, self.notebook)
        self.assertLess(
            self.notebook.index("### RULE 19 — REALITY_FIRST_CAPABILITY_PROBE"),
            self.notebook.index(heading),
        )
        self.assertLess(
            self.notebook.index(heading),
            self.notebook.index("### RULE 20 — OWNER_EXECUTOR_SELECTION"),
        )
        self.assertNotIn("### RULE 22", self.notebook)
        self.assertIn("p2p_performance_language_gate.py", self.bootstrap)
        self.assertIn("PERFORMANCE_LANGUAGE_ADMISSION_V1", self.install)
        self.assertIn('"performance_language_gate.py"', self.package)
        self.assertIn('"p2p_performance_language_gate.py"', self.package)
        self.assertEqual(DEV_CLI.read_bytes(), RUNTIME_CLI.read_bytes())
        records = [r for r in self.ledger["records"] if r.get("research_id") == "RA-EXT-103"]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["canonical_capability_ids"], [])
        self.assertEqual(
            records[0]["owner_decision_status"],
            "OWNER_SELECTED_IMPLEMENTED_AND_RULE_ASSIMILATION_VERIFIED",
        )
        self.assertIn("BACKLOG_K flipped to VERIFIED", records[0]["notes"])
        self.assertEqual(list(ROOT.rglob("Cargo.toml")), [])
        self.assertEqual(list(ROOT.rglob("*.rs")), [])
        match = re.search(r"\`\`\`json\n(.*?)\n\`\`\`", self.notebook, re.DOTALL)
        self.assertIsNotNone(match)
        assimilation = json.loads(match.group(1))
        backlog = [r for r in assimilation["entries"] if r["id"] == "BACKLOG_K"]
        self.assertEqual(len(backlog), 1)
        self.assertEqual(backlog[0]["item"], "PERFORMANCE_LANGUAGE_ADMISSION_V1")
        self.assertIn(backlog[0]["status"], {"PENDING", "VERIFIED"})


if __name__ == "__main__":
    unittest.main()
