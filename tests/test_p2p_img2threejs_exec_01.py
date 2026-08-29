from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_AUDIT_ROOT = Path(
    os.environ.get(
        "P2P_IMG2THREEJS_UPSTREAM_ROOT",
        str(REPO_ROOT.parent / "p2p-img2threejs-upstream-audit"),
    )
)
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities import img2threejs_adapter as adapter  # noqa: E402


@unittest.skipUnless(UPSTREAM_AUDIT_ROOT.is_dir(), "exact upstream audit checkout is unavailable")
class P2PImg2ThreeJSExec01Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(dir=REPO_ROOT, prefix=".tmp-img2threejs-exec-test-")
        self.workspace = Path(self.temp.name)
        reference = self.workspace / "references" / "front.png"
        reference.parent.mkdir(parents=True, exist_ok=True)
        reference.write_bytes(b"reference-fixture")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_strict_factory_spec(self) -> Path:
        """Prepare a bounded, quality-gated fixture without exposing upstream authoring routes."""

        assessment = self.workspace / "assessment.json"
        result = subprocess.run(
            [
                sys.executable,
                str(UPSTREAM_AUDIT_ROOT / "forge/stage2_spec/new_pre_spec_assessment.py"),
                "Oak",
                "--complexity",
                "simple",
                "--out",
                str(assessment),
            ],
            cwd=self.workspace,
            capture_output=True,
            text=True,
            check=False,
            shell=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        spec_path = self.workspace / "character-spec.json"
        result = subprocess.run(
            [
                sys.executable,
                str(UPSTREAM_AUDIT_ROOT / "forge/stage2_spec/new_sculpt_spec.py"),
                "Oak",
                "--assessment",
                str(assessment),
                "--out",
                str(spec_path),
            ],
            cwd=self.workspace,
            capture_output=True,
            text=True,
            check=False,
            shell=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        pre = spec["preSpecAssessment"]
        pre["objectClass"].update(
            {
                "primaryType": "object",
                "formLanguage": ["organic-solid"],
                "structureKind": ["single-body"],
                "motionPotential": ["static"],
                "materialFamilies": ["wood"],
            }
        )
        pre["complexity"]["tier"] = "simple"
        pre["specDepthDecision"]["requiredDepth"] = "simple"
        spec["qualityContract"]["qualityBar"] = "simple"
        spec["materials"][0]["localOverrides"] = [
            {"id": "edge-wear", "roughness": 0.28, "response": "subtle worn edge"},
        ]
        spec["componentTree"][0]["localFeatures"] = [
            {"id": "grain-lines", "description": "visible longitudinal grain"},
            {"id": "edge-bevel", "description": "small softened silhouette edge"},
            {"id": "knot", "description": "localized darker knot"},
        ]
        pre["detailInventory"]["details"] = [
            {"id": "grain-lines", "kind": "linework", "mapsTo": {"ref": "root/grain-lines"}},
            {"id": "edge-bevel", "kind": "bevel", "mapsTo": {"ref": "root/edge-bevel"}},
            {"id": "knot", "kind": "stain", "mapsTo": {"ref": "root/knot"}},
        ]
        spec["componentTree"][0]["colorMaterialRecipe"] = {
            "dominantAlbedo": "rgba(138, 122, 95, 1.0)",
            "secondaryAlbedo": "rgba(110, 97, 75, 1.0)",
            "materialClass": "wood",
            "materialClassConfidence": 0.8,
        }
        spec["lightingFromPhoto"] = [
            "key light: neutral front-left",
            "fill light: soft front-right",
            "rim light: low back edge; exposure 0; ACES tone mapping; contact shadow on ground",
        ]
        spec_path.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
        return spec_path

    def test_exact_upstream_identity_and_license_are_bound(self) -> None:
        result = adapter.verify_upstream_checkout(UPSTREAM_AUDIT_ROOT)
        self.assertEqual(result["version"], "1.5.1")
        self.assertEqual(result["commit"], "dede5909be4e494b228c801a55dda47439143932")
        self.assertEqual(result["tree"], "25bcd4e1f1a487b9a61d69ade257342a3da767e3")
        self.assertEqual(result["license"], "Apache-2.0")
        self.assertEqual(
            tuple(adapter.ALLOWED_ENTRYPOINTS),
            (
                "forge/state.py",
                "forge/next.py",
                "forge/stage1_intake/probe_image.py",
                "forge/stage2_spec/validate_sculpt_spec.py",
                "forge/stage3_build/generate_threejs_factory.py",
            ),
        )

    def test_state_init_and_next_execute_inside_workspace(self) -> None:
        init_receipt = adapter.execute(
            "forge/state.py",
            source_root=UPSTREAM_AUDIT_ROOT,
            workspace_root=self.workspace,
            reference_path="references/front.png",
            state_path=".img2threejs/state.json",
            profile="character",
            spec_path="character-spec.json",
        )
        self.assertEqual(init_receipt["status"], "EXECUTED")
        self.assertFalse(init_receipt["network_used"])
        self.assertFalse(init_receipt["secrets_inherited"])
        self.assertFalse(init_receipt["shell"])
        state_path = self.workspace / ".img2threejs" / "state.json"
        self.assertTrue(state_path.is_file())
        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(state["profile"], "character")
        self.assertEqual(state["artifacts"]["reference"], "references/front.png")

        next_receipt = adapter.execute(
            "forge/next.py",
            source_root=UPSTREAM_AUDIT_ROOT,
            workspace_root=self.workspace,
            state_path=".img2threejs/state.json",
        )
        self.assertEqual(next_receipt["status"], "EXECUTED")
        self.assertEqual(next_receipt["source"]["commit"], init_receipt["source"]["commit"])
        self.assertTrue(state_path.is_file())

    def test_local_probe_and_deterministic_factory_are_allowlisted(self) -> None:
        probe_receipt = adapter.execute(
            "forge/stage1_intake/probe_image.py",
            source_root=UPSTREAM_AUDIT_ROOT,
            workspace_root=self.workspace,
            reference_path="references/front.png",
        )
        self.assertEqual(probe_receipt["status"], "EXECUTED")
        spec = self._write_strict_factory_spec()
        output = self.workspace / "generated" / "character.ts"
        factory_receipt = adapter.execute(
            "forge/stage3_build/generate_threejs_factory.py",
            source_root=UPSTREAM_AUDIT_ROOT,
            workspace_root=self.workspace,
            spec_path="character-spec.json",
            output_path="generated/character.ts",
        )
        self.assertEqual(factory_receipt["status"], "EXECUTED")
        self.assertTrue(output.is_file())
        self.assertGreater(output.stat().st_size, 0)

    def test_network_and_unsafe_upstream_routes_fail_closed(self) -> None:
        cases = (
            ("forge/stage1_intake/fetch_cs2_metadata.py", {}),
            ("forge/stage1_intake/material_region_analysis.py", {}),
            ("forge/stage1_intake/run_vision_adapter.py", {}),
            ("forge/arbitrary.py", {}),
            ("forge/state.py", {"network_access": True}),
        )
        for entrypoint, options in cases:
            with self.subTest(entrypoint=entrypoint, options=options):
                with self.assertRaisesRegex(adapter.Img2ThreeJSAdapterError, "(ENTRYPOINT_NOT_ALLOWLISTED|NETWORK_NOT_PERMITTED)"):
                    adapter.execute(
                        entrypoint,
                        source_root=UPSTREAM_AUDIT_ROOT,
                        workspace_root=self.workspace,
                        reference_path="references/front.png",
                        **options,
                    )

    def test_remote_reference_identifier_and_output_escape_fail_closed(self) -> None:
        for value in ("https://example.invalid/reference.png", "../outside.png", r"references\outside.png", "C:outside.png", str(self.workspace / "absolute.png")):
            with self.subTest(reference=value):
                with self.assertRaises(adapter.Img2ThreeJSAdapterError):
                    adapter.execute(
                        "forge/state.py",
                        source_root=UPSTREAM_AUDIT_ROOT,
                        workspace_root=self.workspace,
                        reference_path=value,
                    )
        for value in ("../outside", r"regions\evil", ".."):  # region/component inputs are never path-like
            with self.subTest(identifier=value):
                with self.assertRaises(adapter.Img2ThreeJSAdapterError):
                    adapter.validate_identifier(value, field="region")
        for value in ("../outside.json", r"references\outside.json", "C:outside.json", str(self.workspace / "outside.json")):
            with self.subTest(path=value):
                with self.assertRaises(adapter.Img2ThreeJSAdapterError):
                    adapter.bounded_workspace_path(self.workspace, value, field="output")

    def test_invalid_source_pin_fails_closed(self) -> None:
        original_git = adapter._git
        calls = iter((str(UPSTREAM_AUDIT_ROOT), "0" * 40, adapter.UPSTREAM_TREE, ""))
        try:
            adapter._git = lambda _root, *_args: next(calls)
            with self.assertRaisesRegex(adapter.Img2ThreeJSAdapterError, "UPSTREAM_PIN_MISMATCH"):
                adapter.verify_upstream_checkout(UPSTREAM_AUDIT_ROOT)
        finally:
            adapter._git = original_git


if __name__ == "__main__":
    unittest.main()
