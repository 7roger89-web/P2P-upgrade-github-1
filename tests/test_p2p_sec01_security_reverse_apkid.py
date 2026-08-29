from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities import (  # noqa: E402
    ACTIVE_TEST_AUTHORIZED,
    ANALYSIS_LOCAL,
    DECOMPILED_OUTPUT,
    DESTRUCTIVE_OR_INTRUSIVE,
    OFFENSIVE_HIGH_RISK,
    RECONSTRUCTED_SEMANTICS,
    SAFE_READONLY,
    SEMANTIC_KINDS,
    SECURITY_EXECUTION_CLASSES,
    ApkidAdapter,
    ReverseEvidence,
    SecurityContractError,
    classify_capabilities,
    load_registry,
)
from p2p_capabilities.model import validate_registry  # noqa: E402
from p2p_capabilities.orchestration_policy import (  # noqa: E402
    BLOCKED,
    CRITICAL,
    FAST,
    OrchestrationPolicyError,
    STANDARD,
    derive_requirement,
)


class P2PSec01SecurityReverseApkidTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry_path = SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json"
        cls.registry = load_registry(cls.registry_path)
        cls.capabilities = cls.registry["parsed"]
        cls.test_tmp_root = REPO_ROOT / ".tmp"
        cls.test_tmp_root.mkdir(exist_ok=True)

    def test_semantic_kind_vocabulary_is_orthogonal_to_six_type_classes(self) -> None:
        self.assertEqual(
            SEMANTIC_KINDS,
            ("SKILL", "TOOL", "ADAPTER", "VENDOR", "EXTERNAL_RUNTIME", "KNOWLEDGE_SOURCE"),
        )
        self.assertEqual(
            SECURITY_EXECUTION_CLASSES,
            (
                SAFE_READONLY,
                ANALYSIS_LOCAL,
                ACTIVE_TEST_AUTHORIZED,
                OFFENSIVE_HIGH_RISK,
                DESTRUCTIVE_OR_INTRUSIVE,
            ),
        )
        raw = json.loads(self.registry_path.read_text(encoding="utf-8"))["capabilities"]
        broken = [dict(item) for item in raw]
        broken[-1]["SEMANTIC_KIND"] = "SECOND_ROUTER"
        result = validate_registry(broken)
        self.assertFalse(result["valid"])
        self.assertIn("SEMANTIC_KIND_INVALID", {item["code"] for item in result["errors"]})

    def test_requested_ids_are_unique_and_apkid_is_one_adapter_capability(self) -> None:
        desired = {
            "android.protection.detect",
            "android.artifact.decode",
            "artifact.android.bundle.normalize",
            "security.mobile.static.assess",
            "android.runtime.instrument",
            "android.network.inspect",
            "reverse.identify",
            "reverse.decompile.managed",
            "reverse.decompile.native",
            "reverse.deobfuscate",
            "reverse.callgraph",
            "reverse.semantic_reconstruct",
        }
        self.assertEqual(len(self.registry["identities"]), len(set(self.registry["identities"])))
        selected = {item.capability_id: item for item in self.capabilities if item.capability_id in desired}
        self.assertEqual(set(selected), desired)
        self.assertEqual(selected["android.protection.detect"].type, "BACKEND_PROVIDER")
        self.assertEqual(selected["android.protection.detect"].semantic_kind, "ADAPTER")
        self.assertEqual(self.registry["canonical_denominator"], 8)
        self.assertEqual(self.registry["full_quorum"], "8/8")

        catalog = json.loads((REPO_ROOT / "manifest" / "external-sources.json").read_text(encoding="utf-8"))
        entries = catalog["external_tool_catalog"]
        self.assertEqual(len(entries), 10)
        self.assertEqual({entry["name"] for entry in entries}, {
            "APKiD", "Apktool", "JADX", "bundletool", "MobSF", "Frida",
            "Ghidra", "Detect It Easy / LIEF", "ILSpy / Vineflower", "OWASP MASVS / MASTG",
        })
        for entry in entries:
            self.assertFalse(entry["vendored"])
            self.assertFalse(entry["network_runtime"])
            self.assertFalse(entry["credentials"])
            self.assertEqual(entry["install_mode"], "DISABLED")
            self.assertEqual(entry["execution_status"], "NOT_EXECUTED")

    def test_existing_single_router_selects_apkid_for_static_protection_request(self) -> None:
        result = classify_capabilities(
            "Use APKiD to detect APK protection and android packers.",
            self.capabilities,
        )
        self.assertTrue(result["single_router"])
        apkid = next(item for item in result["results"] if item["capability_id"] == "android.protection.detect")
        self.assertEqual(apkid["classification"], "PRIMARY")
        self.assertIn("android.protection.detect", result["selected"])
        self.assertNotIn("router-agent", json.dumps(result))

    def test_execution_classes_bind_to_existing_eff01_and_fail_closed(self) -> None:
        safe = derive_requirement({"execution_class": SAFE_READONLY})
        self.assertEqual(safe["execution_lane"], FAST)
        self.assertEqual(safe["status"], "READY")
        self.assertTrue(safe["security_execution"]["allowed"])

        local = derive_requirement({"execution_class": ANALYSIS_LOCAL})
        self.assertEqual(local["execution_lane"], STANDARD)
        self.assertTrue(local["security_execution"]["allowed"])

        active_blocked = derive_requirement({"execution_class": ACTIVE_TEST_AUTHORIZED})
        self.assertEqual(active_blocked["execution_lane"], CRITICAL)
        self.assertEqual(active_blocked["worker_strategy"], BLOCKED)
        self.assertEqual(active_blocked["status"], "BLOCKED")
        self.assertIn("TARGET_AUTHORIZATION_REQUIRED", active_blocked["security_execution"]["reason_codes"])

        active_allowed = derive_requirement({
            "execution_class": ACTIVE_TEST_AUTHORIZED,
            "target_authorized": True,
            "controlled_test_environment": True,
        })
        self.assertEqual(active_allowed["status"], "READY")
        self.assertTrue(active_allowed["security_execution"]["allowed"])

        offensive_blocked = derive_requirement({
            "execution_class": OFFENSIVE_HIGH_RISK,
            "target_authorized": True,
            "controlled_test_environment": True,
        })
        self.assertEqual(offensive_blocked["status"], "BLOCKED")
        self.assertIn("EXPLICIT_TASK_AUTHORITY_REQUIRED", offensive_blocked["security_execution"]["reason_codes"])

        destructive = derive_requirement({
            "execution_class": DESTRUCTIVE_OR_INTRUSIVE,
            "target_authorized": True,
            "controlled_test_environment": True,
            "explicit_task_authority": True,
        })
        self.assertEqual(destructive["status"], "BLOCKED")
        self.assertIn(
            "DESTRUCTIVE_OR_INTRUSIVE_DENIED_BY_DEFAULT",
            destructive["security_execution"]["reason_codes"],
        )
        with self.assertRaises(OrchestrationPolicyError):
            derive_requirement({"execution_class": "IMPLICIT_PERMISSION"})

    def test_reverse_evidence_distinguishes_decompile_and_semantic_reconstruction(self) -> None:
        decompiled = ReverseEvidence(
            output_kind=DECOMPILED_OUTPUT,
            source_evidence_refs=(),
            tool_backend_identity={"tool": "future-managed-decompiler"},
            inferred_semantic_label="NOT_INFERRED",
            confidence="UNKNOWN",
            uncertainty_state="UNKNOWN",
        ).to_dict()
        self.assertFalse(decompiled["decompiled_output_is_reconstructed_source"])
        self.assertEqual(decompiled["original_source_recovery"], "NOT_CLAIMED")

        reconstructed = ReverseEvidence(
            output_kind=RECONSTRUCTED_SEMANTICS,
            source_evidence_refs=("artifact:method:001",),
            tool_backend_identity={"tool": "bounded-analysis-adapter", "version": "1"},
            inferred_semantic_label="validates signed payload",
            confidence="MEDIUM",
            uncertainty_state="NONE",
        )
        self.assertEqual(reconstructed.to_dict()["output_kind"], RECONSTRUCTED_SEMANTICS)
        unknown = ReverseEvidence.unknown(evidence_refs=("artifact:method:unknown",))
        self.assertEqual(unknown.confidence, "UNKNOWN")
        self.assertEqual(unknown.uncertainty_state, "INSUFFICIENT_EVIDENCE")
        with self.assertRaises(SecurityContractError):
            ReverseEvidence(
                output_kind=RECONSTRUCTED_SEMANTICS,
                source_evidence_refs=("artifact:method:001",),
                tool_backend_identity={"tool": "unknown"},
                inferred_semantic_label="ORIGINAL_SOURCE_RECOVERED",
                confidence="HIGH",
                uncertainty_state="NONE",
            )

    def test_apkid_missing_dependency_is_unavailable_and_hash_bound(self) -> None:
        with tempfile.TemporaryDirectory(dir=str(self.test_tmp_root)) as temp_root:
            apk = Path(temp_root) / "sample.apk"
            apk.write_bytes(b"safe readonly apk fixture")
            before = apk.read_bytes()
            result = ApkidAdapter(executable="p2p-sec01-apkid-not-installed").analyze(apk)
            self.assertEqual(result.status, "UNAVAILABLE")
            self.assertNotEqual(result.status, "PASS")
            self.assertEqual(result.error_code, "DEPENDENCY_UNAVAILABLE")
            self.assertEqual(result.artifact_identity.sha256, hashlib.sha256(before).hexdigest())
            self.assertFalse(result.mutation_observed)

    def test_apkid_normalizes_supported_findings_and_preserves_readonly_artifact(self) -> None:
        calls: list[tuple[list[str], dict[str, object]]] = []

        class Completed:
            returncode = 0
            stdout = "[+] APKiD 3.0.0\nPackers: Bangcle, DexProtector\nProtector: AppSealing\nCompiler: r8\nObfuscator: r8\n"
            stderr = ""

        def fake_runner(command: list[str], **kwargs: object) -> Completed:
            calls.append((command, kwargs))
            return Completed()

        with tempfile.TemporaryDirectory(dir=str(self.test_tmp_root)) as temp_root:
            apk = Path(temp_root) / "sample.apk"
            apk.write_bytes(b"unchanged apk fixture")
            before_bytes = apk.read_bytes()
            before_stat = apk.stat()
            result = ApkidAdapter(executable=sys.executable, runner=fake_runner).analyze(apk)
            self.assertEqual(result.status, "VERIFIED")
            self.assertIsNone(result.error_code)
            self.assertEqual(
                {(item.category, item.label) for item in result.findings},
                {
                    ("PACKER", "Bangcle"),
                    ("PACKER", "DexProtector"),
                    ("PROTECTOR", "AppSealing"),
                    ("COMPILER", "r8"),
                    ("OBFUSCATOR", "r8"),
                },
            )
            self.assertTrue(all(item.confidence == "UNKNOWN" for item in result.findings))
            self.assertEqual(result.artifact_identity.sha256, hashlib.sha256(before_bytes).hexdigest())
            self.assertEqual(apk.read_bytes(), before_bytes)
            self.assertEqual(apk.stat().st_mtime_ns, before_stat.st_mtime_ns)
            self.assertEqual(len(calls), 1)
            command, kwargs = calls[0]
            self.assertEqual(command[0], str(Path(sys.executable).resolve()))
            self.assertEqual(command[1], str(apk.resolve()))
            self.assertNotIn("shell", kwargs)
            self.assertEqual(result.to_dict()["execution_class"], SAFE_READONLY)
            self.assertFalse(result.external_interaction)

    def test_apkid_rejects_nonlocal_or_mutated_artifact(self) -> None:
        calls = 0

        def fake_runner(command: list[str], **kwargs: object) -> object:
            nonlocal calls
            calls += 1
            Path(command[1]).write_bytes(b"mutated by test fixture")
            return type("Completed", (), {"returncode": 0, "stdout": "Compiler: r8", "stderr": ""})()

        rejected = ApkidAdapter(executable=sys.executable, runner=fake_runner).analyze("https://example.invalid/app.apk")
        self.assertEqual(rejected.status, "REJECTED")
        self.assertEqual(rejected.error_code, "LOCAL_APK_REQUIRED")
        self.assertEqual(calls, 0)
        remote_share = ApkidAdapter(executable=sys.executable, runner=fake_runner).analyze(r"\\server\share\app.apk")
        self.assertEqual(remote_share.status, "REJECTED")
        self.assertEqual(remote_share.error_code, "LOCAL_APK_REQUIRED")
        self.assertEqual(calls, 0)

        with tempfile.TemporaryDirectory(dir=str(self.test_tmp_root)) as temp_root:
            apk = Path(temp_root) / "sample.apk"
            apk.write_bytes(b"mutable apk fixture")
            result = ApkidAdapter(executable=sys.executable, runner=fake_runner).analyze(apk)
            self.assertEqual(result.status, "REJECTED")
            self.assertEqual(result.error_code, "ARTIFACT_MUTATED_DURING_ANALYSIS")
            self.assertTrue(result.mutation_observed)
            self.assertEqual(result.findings, ())


if __name__ == "__main__":
    unittest.main()
