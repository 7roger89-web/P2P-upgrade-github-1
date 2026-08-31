import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from p2p_capabilities.model import load_registry
from p2p_capabilities.static_glb_standardizer import StaticGlbError, standardize_static_glb, validate_static_glb_output, _parse, _encode

ASSET = {
    "name": "golden_sword_static", "units": "meters", "up_axis": "Y",
    "transform": {"position": [0, 0, 0], "rotation": [0, 0, 0], "scale": [1, 1, 1]},
    "meshes": [{"name": "blade", "positions": [-1, 0, 0, 1, 0, 0, 0, 2, 0], "indices": [0, 1, 2],
                "material": {"type": "MeshStandardMaterial", "color": [0.7, 0.7, 0.8], "metalness": 0.8, "roughness": 0.25}}],
}

class StaticGlbStandardizerTests(unittest.TestCase):
    def test_export_is_parseable_and_provenance_bound(self):
        with TemporaryDirectory() as directory:
            result = standardize_static_glb(ASSET, Path(directory) / "golden_sword_static.glb", generating_capability="img2threejs", run_id="forge-run-001")
            self.assertFalse(result["validation"]["skin"])
            self.assertEqual(result["validation"]["vertex_count"], 3)
            parsed = validate_static_glb_output(result["glb_path"], result["provenance_path"], expected_asset_name="golden_sword_static", expected_generating_capability="img2threejs", expected_run_id="forge-run-001")
            self.assertEqual(parsed["status"], "STRUCTURALLY_VALID")
            self.assertEqual(parsed["provenance"]["generating_capability"], "img2threejs")

    def test_rejects_empty_or_rigged_input(self):
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(StaticGlbError, "MESH_GEOMETRY_MISSING"):
                standardize_static_glb({**ASSET, "meshes": []}, Path(directory) / "x.glb", generating_capability="img2threejs", run_id="r")
            with self.assertRaisesRegex(StaticGlbError, "STATIC_ASSET_MUST_NOT_REQUIRE_SKIN"):
                standardize_static_glb({**ASSET, "skeleton": {"name": "root"}}, Path(directory) / "x.glb", generating_capability="img2threejs", run_id="r")

    def test_rejects_unsupported_material(self):
        asset = {**ASSET, "meshes": [{**ASSET["meshes"][0], "material": {"type": "ShaderMaterial"}}]}
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(StaticGlbError, "MATERIAL_UNSUPPORTED"):
                standardize_static_glb(asset, Path(directory) / "x.glb", generating_capability="img2threejs", run_id="r")

    def test_json_uses_space_padding_and_registry_loads(self):
        with TemporaryDirectory() as directory:
            result = standardize_static_glb(ASSET, Path(directory) / "x.glb", generating_capability="img2threejs", run_id="r")
            data = Path(result["glb_path"]).read_bytes(); length = int.from_bytes(data[12:16], "little")
            self.assertEqual(data[20 + length - 1:20 + length], b" ")
        load_registry(Path(__file__).parents[1] / "capabilities.json")

    def _mutated_result(self, directory, mutation):
        result = standardize_static_glb(ASSET, Path(directory) / "x.glb", generating_capability="img2threejs", run_id="r")
        data, doc, binary = _parse(Path(result["glb_path"])); mutation(doc)
        Path(result["glb_path"]).write_bytes(_encode(doc, binary))
        manifest = json.loads(Path(result["provenance_path"]).read_text())
        manifest["glb_sha256"] = hashlib.sha256(Path(result["glb_path"]).read_bytes()).hexdigest()
        Path(result["provenance_path"]).write_text(json.dumps(manifest))
        return result

    def test_structural_reference_and_geometry_failures(self):
        with TemporaryDirectory() as directory:
            for mutation, error in ((lambda d: d["nodes"][0].update(mesh=99), "node.mesh"), (lambda d: d["scenes"][0].update(nodes=[]), "GLB_SCENE_ROOTS_INVALID"), (lambda d: d["bufferViews"][0].update(byteLength=999999), "GLB_BUFFERVIEW_BOUNDS_INVALID")):
                result = self._mutated_result(directory, mutation)
                with self.assertRaisesRegex(StaticGlbError, error): validate_static_glb_output(result["glb_path"], result["provenance_path"], expected_asset_name="golden_sword_static", expected_generating_capability="img2threejs", expected_run_id="r")
            with self.assertRaisesRegex(StaticGlbError, "TRIANGLE_INDEX_COUNT_INVALID"):
                standardize_static_glb({**ASSET, "meshes":[{**ASSET["meshes"][0], "indices":[0,1]}]}, Path(directory)/"bad.glb", generating_capability="img2threejs", run_id="r")
            with self.assertRaisesRegex(StaticGlbError, "MESH_INDICES_INVALID"):
                standardize_static_glb({**ASSET, "meshes":[{**ASSET["meshes"][0], "indices":[0,1,9]}]}, Path(directory)/"bad.glb", generating_capability="img2threejs", run_id="r")

    def test_provenance_and_transform_fail_closed(self):
        with TemporaryDirectory() as directory:
            result = standardize_static_glb(ASSET, Path(directory) / "x.glb", generating_capability="img2threejs", run_id="r")
            with self.assertRaisesRegex(StaticGlbError, "PROVENANCE_EVIDENCE_MISMATCH"):
                validate_static_glb_output(result["glb_path"], result["provenance_path"], expected_asset_name="other", expected_generating_capability="img2threejs", expected_run_id="r")
            with self.assertRaisesRegex(StaticGlbError, "PROVENANCE_EVIDENCE_MISMATCH"):
                validate_static_glb_output(result["glb_path"], result["provenance_path"], expected_asset_name="golden_sword_static", expected_generating_capability="other", expected_run_id="r")
            with self.assertRaisesRegex(StaticGlbError, "PROVENANCE_HASH_MISMATCH"):
                data = bytearray(Path(result["glb_path"]).read_bytes()); data[-1] = 1; Path(result["glb_path"]).write_bytes(data)
                validate_static_glb_output(result["glb_path"], result["provenance_path"], expected_asset_name="golden_sword_static", expected_generating_capability="img2threejs", expected_run_id="r")
            with self.assertRaisesRegex(StaticGlbError, "TRANSFORM_REQUIRED"):
                standardize_static_glb({k:v for k,v in ASSET.items() if k != "transform"}, Path(directory)/"bad.glb", generating_capability="x", run_id="r")
            with self.assertRaisesRegex(StaticGlbError, "MATERIAL_FACTOR_OUT_OF_RANGE"):
                standardize_static_glb({**ASSET, "meshes":[{**ASSET["meshes"][0], "material": {"type":"MeshStandardMaterial", "color":[2,0,0]}}]}, Path(directory)/"bad.glb", generating_capability="x", run_id="r")

if __name__ == "__main__":
    unittest.main()
