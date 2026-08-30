import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from p2p_capabilities.static_glb_standardizer import StaticGlbError, standardize_static_glb, validate_static_glb_output

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
            parsed = validate_static_glb_output(result["glb_path"], result["provenance_path"])
            self.assertEqual(parsed["status"], "PARSEABLE")
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

if __name__ == "__main__":
    unittest.main()
