"""P2P-IMG2THREEJS-STATIC-PROJECTION-01 — static projection seam tests.

Repository-side contract and composition coverage only:

  COMPOSITION_TESTED=YES  (bounded synthetic bake-manifest fixtures, in-repo)
  EXTERNAL_IMG2THREEJS_RUNTIME_PROVEN=NO
  (no upstream checkout, Node/three runtime, browser, or weapon generation
  is executed here; production runtime smoke belongs to the later Owner-side
  run against the pre-provisioned verified runtime profile)
"""

from __future__ import annotations

import inspect
import json
import math
import shutil
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from p2p_capabilities import img2threejs_adapter as adapter
from p2p_capabilities.static_glb_standardizer import (
    StaticGlbError,
    standardize_static_glb,
    validate_static_glb_output,
)


def _transform_matrix(translation=(0.0, 0.0, 0.0), scale=1.0):
    tx, ty, tz = translation
    return [scale, 0.0, 0.0, 0.0, 0.0, scale, 0.0, 0.0, 0.0, 0.0, scale, 0.0, tx, ty, tz, 1.0]


def _material(**overrides):
    material = {
        "type": "MeshStandardMaterial",
        "color": [0.5, 0.5, 0.5],
        "opacity": 1.0,
        "metalness": 0.0,
        "roughness": 1.0,
        "drift": [],
    }
    material.update(overrides)
    return material


def _mesh_node(node_id, parent, *, matrix=None, positions, indices=None, material="default", geometry_type="BufferGeometry"):
    node = {
        "id": node_id,
        "parent": parent,
        "kind": "mesh",
        "matrix": matrix if matrix is not None else _transform_matrix(),
        "mesh": {
            "geometry": {
                "type": geometry_type,
                "position": list(positions),
                "index": list(indices) if indices is not None else None,
            },
            "material": _material() if material == "default" else material,
        },
    }
    return node


def _group_node(node_id, parent, *, matrix=None):
    return {"id": node_id, "parent": parent, "kind": "group", "matrix": matrix if matrix is not None else _transform_matrix()}


def _manifest(nodes, **overrides):
    manifest = {
        "schema": adapter.RUNTIME_BAKE_SCHEMA,
        "status": "BAKED",
        "up_axis": "Y",
        "runtime": {"node": adapter.VERIFIED_NODE_VERSION, "three": adapter.VERIFIED_THREE_REVISION},
        "factory_sha256": "0" * 64,
        "factory_export": "createFixtureModel",
        "aggregate": {
            "nodes": len(nodes),
            "skinned_meshes": 0,
            "bones": 0,
            "animations": 0,
            "skeletons": 0,
            "maximum_depth": 1,
        },
        "nodes": nodes,
    }
    manifest.update(overrides)
    return manifest


def _project(manifest, *, asset_name="fixture_prop", target=1.0):
    return adapter.bake_static_projection(manifest, asset_name=asset_name, target_major_extent_meters=target)


class ProjectionCoreTests(unittest.TestCase):
    def test_single_component_projection_is_flat_meters_and_deterministic(self):
        manifest = _manifest([
            _group_node("root", None),
            _mesh_node("n0001", "root", positions=[0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 2.0, 0.0], indices=[0, 1, 2]),
        ])
        asset, evidence = _project(manifest, target=0.5)
        self.assertEqual(asset["units"], "meters")
        self.assertEqual(asset["up_axis"], "Y")
        self.assertEqual(asset["transform"], {"space": "flat", "position": [0.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0], "scale": [1.0, 1.0, 1.0]})
        self.assertEqual(asset["name"], "fixture_prop")
        mesh = asset["meshes"][0]
        self.assertEqual(mesh["name"], "mesh_00")
        # relative extents (x=1, y=2) -> major 2 -> scale 0.25 for target 0.5
        self.assertEqual(evidence["relative_to_meter_scale"], 0.25)
        self.assertEqual(mesh["positions"], [0.0, 0.0, 0.0, 0.25, 0.0, 0.0, 0.0, 0.5, 0.0])
        self.assertEqual(mesh["indices"], [0, 1, 2])
        # no unresolved hierarchy may remain in the output
        for forbidden in ("children", "parent", "matrix", "skin", "skeleton", "bones", "animations"):
            self.assertNotIn(forbidden, asset)
        again, again_evidence = _project(manifest, target=0.5)
        self.assertEqual(json.dumps(asset, sort_keys=True), json.dumps(again, sort_keys=True))
        self.assertEqual(json.dumps(evidence, sort_keys=True), json.dumps(again_evidence, sort_keys=True))

    def test_parent_child_hierarchy_is_baked_including_rotation_scale(self):
        parent = _transform_matrix(translation=(2.0, 0.0, 0.0), scale=2.0)
        child = _transform_matrix(translation=(0.0, 1.0, 0.0))
        manifest = _manifest([
            _group_node("root", None),
            _group_node("pivot", "root", matrix=parent),
            _mesh_node("blade", "pivot", matrix=child, positions=[0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]),
        ])
        asset, evidence = _project(manifest, target=1.0)
        # baked points: (2,2,0), (4,2,0), (2,2,2); extents x=2, y=0, z=2 -> major 2 -> scale 0.5
        positions = asset["meshes"][0]["positions"]
        self.assertEqual(positions, [1.0, 1.0, 0.0, 2.0, 1.0, 0.0, 1.0, 1.0, 1.0])
        self.assertEqual(evidence["relative_to_meter_scale"], 0.5)
        self.assertEqual(evidence["hierarchy_nodes"], 3)
        self.assertEqual(evidence["mesh_count"], 1)

    def test_multiple_meshes_use_one_aggregate_extent_scale(self):
        small = _mesh_node("small", "root", positions=[0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0], indices=[0, 1, 2])
        large = _mesh_node("large", "root", positions=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 8.0])
        asset, evidence = _project(_manifest([_group_node("root", None), small, large]), target=2.0)
        self.assertEqual(evidence["relative_to_meter_scale"], 0.25)  # 2 / 8 aggregate, not per-mesh
        self.assertEqual(len(asset["meshes"]), 2)
        self.assertEqual(asset["meshes"][0]["positions"][3], 0.25)
        self.assertEqual(asset["meshes"][1]["positions"][8], 2.0)

    def test_physical_material_narrows_only_when_all_physical_features_are_default(self):
        manifest = _manifest([
            _group_node("root", None),
            _mesh_node("hilt", "root", positions=[0, 0, 0, 1, 0, 0, 0, 1, 0], material=_material(type="MeshPhysicalMaterial", drift=[])),
        ])
        asset, evidence = _project(manifest)
        self.assertEqual(asset["meshes"][0]["material"]["type"], "MeshStandardMaterial")
        self.assertEqual(evidence["material_narrowing"], {"physical_to_standard": 1})

    def test_unsupported_material_semantics_fail_closed(self):
        for key, material in (
            ("transmission", _material(type="MeshPhysicalMaterial", drift=[["transmission", 0.4]])),
            ("clearcoat", _material(type="MeshPhysicalMaterial", drift=[["clearcoat", 1.0]])),
            ("map", _material(drift=[["map", "texture"]])),
            ("emissive", _material(drift=[["emissive", "color"]])),
            ("flatShading", _material(type="MeshBasicMaterial", drift=[["flatShading", True]])),
            ("transparent", _material(drift=[["transparent", True]])),  # opacity is 1 -> alpha-only pass not allowed
        ):
            with self.subTest(feature=key):
                manifest = _manifest([_group_node("root", None), _mesh_node("m", "root", positions=[0, 0, 0, 1, 0, 0, 0, 1, 0], material=material)])
                with self.assertRaisesRegex(adapter.Img2ThreeJSAdapterError, f"UNSUPPORTED_MATERIAL_FEATURE:{key}"):
                    _project(manifest)
        manifest = _manifest([_group_node("root", None), _mesh_node("m", "root", positions=[0, 0, 0, 1, 0, 0, 0, 1, 0], material=_material(type="ShaderMaterial"))])
        with self.assertRaises(adapter.Img2ThreeJSAdapterError):
            _project(manifest)
        # transparent WITH sub-1 opacity rides on the surviving opacity factor
        manifest = _manifest([_group_node("root", None), _mesh_node("m", "root", positions=[0, 0, 0, 1, 0, 0, 0, 1, 0], material=_material(opacity=0.5, drift=[["transparent", True], ["opacity", 0.5]]))])
        asset, _ = _project(manifest)
        self.assertEqual(asset["meshes"][0]["material"]["opacity"], 0.5)

    def test_static_only_and_graph_rejections(self):
        base_nodes = [_group_node("root", None), _mesh_node("m", "root", positions=[0, 0, 0, 1, 0, 0, 0, 1, 0])]
        cases = (
            ("skinned aggregate", _manifest(base_nodes, aggregate={"nodes": 2, "skinned_meshes": 1, "bones": 0, "animations": 0, "skeletons": 0, "maximum_depth": 1}), "STATIC_ASSET_MUST_NOT_REQUIRE_SKIN"),
            ("animations aggregate", _manifest(base_nodes, aggregate={"nodes": 2, "skinned_meshes": 0, "bones": 0, "animations": 3, "skeletons": 0, "maximum_depth": 1}), "ANIMATIONS_UNSUPPORTED"),
            ("missing parent", _manifest([_group_node("root", None), _mesh_node("m", "ghost", positions=[0, 0, 0, 1, 0, 0, 0, 1, 0])]), "HIERARCHY_CYCLE_OR_MISSING_PARENT"),
            ("cycle via forward reference", _manifest([_mesh_node("a", "b", positions=[0, 0, 0, 1, 0, 0, 0, 1, 0]), _mesh_node("b", "a", positions=[0, 0, 0, 1, 0, 0, 0, 1, 0])]), "HIERARCHY_CYCLE_OR_MISSING_PARENT"),
            ("duplicate identity", _manifest([_group_node("root", None), _mesh_node("m", "root", positions=[0, 0, 0, 1, 0, 0, 0, 1, 0]), _mesh_node("m", "root", positions=[0, 0, 0, 1, 0, 0, 0, 1, 0])]), "BAKE_NODE_ID_INVALID"),
            ("unsupported node kind", _manifest([_group_node("root", None), {"id": "line", "parent": "root", "kind": "line", "matrix": _transform_matrix()}]), "BAKE_NODE_KIND_UNSUPPORTED"),
            ("unsupported geometry", _manifest([_group_node("root", None), _mesh_node("m", "root", positions=[0, 0, 0, 1, 0, 0, 0, 1, 0], geometry_type="Geometry")]), "GEOMETRY_UNSUPPORTED"),
            ("empty geometry", _manifest([_group_node("root", None), _mesh_node("m", "root", positions=[])]), "GEOMETRY_POSITIONS_INVALID"),
            ("non-finite position", _manifest([_group_node("root", None), _mesh_node("m", "root", positions=[0, 0, 0, math.nan, 0, 0, 0, 1, 0])]), "GEOMETRY_NONFINITE"),
            ("non-finite matrix", _manifest([_group_node("root", None), _mesh_node("m", "root", matrix=[math.inf] + [0.0] * 15, positions=[0, 0, 0, 1, 0, 0, 0, 1, 0])]), "BAKE_NODE_MATRIX_INVALID"),
            ("index out of range", _manifest([_group_node("root", None), _mesh_node("m", "root", positions=[0, 0, 0, 1, 0, 0, 0, 1, 0], indices=[0, 1, 9])]), "GEOMETRY_INDEX_INVALID"),
            ("non-triangle index count", _manifest([_group_node("root", None), _mesh_node("m", "root", positions=[0, 0, 0, 1, 0, 0, 0, 1, 0], indices=[0, 1])]), "GEOMETRY_INDEX_INVALID"),
            ("non-indexed vertex count not divisible by three", _manifest([_group_node("root", None), _mesh_node("m", "root", positions=[0, 0, 0, 1, 0, 0])]), "GEOMETRY_TRIANGLE_COUNT_INVALID"),
            ("groups only", _manifest([_group_node("root", None), _group_node("empty", "root")]), "GEOMETRY_EMPTY"),
            ("up axis mismatch", _manifest(base_nodes, up_axis="Z"), "UP_AXIS_UNSUPPORTED"),
            ("unknown units semantics via bad runtime identity", _manifest(base_nodes, runtime={"node": "v20.0.0", "three": "150"}), "RUNTIME_PROFILE_MISMATCH"),
            ("bad schema", _manifest(base_nodes, schema="p2p-other/1"), "BAKE_MANIFEST_SCHEMA_INVALID"),
            ("bad status", _manifest(base_nodes, status="PARTIAL"), "BAKE_MANIFEST_STATUS_INVALID"),
        )
        for label, manifest, code in cases:
            with self.subTest(case=label):
                with self.assertRaisesRegex(adapter.Img2ThreeJSAdapterError, code):
                    _project(manifest)
        for bad_manifest in (None, [], {}):
            with self.subTest(manifest=bad_manifest):
                with self.assertRaises(adapter.Img2ThreeJSAdapterError):
                    _project(bad_manifest)

    def test_physical_anchor_contract(self):
        manifest = _manifest([_group_node("root", None), _mesh_node("m", "root", positions=[0, 0, 0, 1, 0, 0, 0, 1, 0])])
        with self.assertRaises(TypeError):
            adapter.bake_static_projection(manifest, asset_name="fixture_prop")  # target is a REQUIRED keyword
        for value, code in ((None, "TARGET_MAJOR_EXTENT_METERS_REQUIRED"), (0.0, "TARGET_MAJOR_EXTENT_METERS_INVALID"), (-2.0, "TARGET_MAJOR_EXTENT_METERS_INVALID"), (True, "TARGET_MAJOR_EXTENT_METERS_INVALID"), (math.nan, "TARGET_MAJOR_EXTENT_METERS_INVALID"), (math.inf, "TARGET_MAJOR_EXTENT_METERS_INVALID"), ("1.0", "TARGET_MAJOR_EXTENT_METERS_INVALID")):
            with self.subTest(target=value):
                with self.assertRaisesRegex(adapter.Img2ThreeJSAdapterError, code):
                    adapter.bake_static_projection(manifest, asset_name="fixture_prop", target_major_extent_meters=value)
        with self.assertRaisesRegex(adapter.Img2ThreeJSAdapterError, "ASSET_NAME_INVALID"):
            adapter.bake_static_projection(manifest, asset_name="Fixture", target_major_extent_meters=1.0)
        # degenerate geometry: zero aggregate extent can never yield a scale
        degenerate = _manifest([_group_node("root", None), _mesh_node("m", "root", positions=[0, 0, 0, 0, 0, 0, 0, 0, 0])])
        with self.assertRaisesRegex(adapter.Img2ThreeJSAdapterError, "BAKED_EXTENT_INVALID"):
            _project(degenerate)

    def test_projection_is_accepted_by_static_glb_standardizer(self):
        manifest = _manifest([
            _group_node("root", None),
            _group_node("pivot", "root", matrix=_transform_matrix(translation=(1.0, 0.0, 0.0), scale=2.0)),
            _mesh_node("blade", "pivot", positions=[0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 2.0, 0.0], indices=[0, 1, 2]),
            _mesh_node("hilt", "root", positions=[0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, -0.5], material=_material(type="MeshPhysicalMaterial")),
        ])
        asset, evidence = _project(manifest, asset_name="golden_probe_prop", target=0.4)
        with TemporaryDirectory() as directory:
            result = standardize_static_glb(asset, Path(directory) / "golden_probe_prop.glb", generating_capability="img2threejs", run_id="projection-composition-001")
            parsed = validate_static_glb_output(
                result["glb_path"],
                result["provenance_path"],
                expected_asset_name="golden_probe_prop",
                expected_generating_capability="img2threejs",
                expected_run_id="projection-composition-001",
            )
        self.assertEqual(parsed["status"], "STRUCTURALLY_VALID")
        self.assertEqual(result["validation"]["mesh_count"], 2)
        self.assertEqual(result["validation"]["vertex_count"], evidence["vertex_count"])
        self.assertFalse(result["validation"]["skin"])
        self.assertFalse(result["validation"]["skeleton"])
        self.assertEqual(parsed["provenance"]["contract"], adapter.STATIC_PROJECTION_CONTRACT)


class ProductionBoundaryTests(unittest.TestCase):
    def test_strict_quality_boundary_has_no_nonstrict_surface(self):
        source = inspect.getsource(adapter)
        # the flag may be *described* in prose but must never exist as a
        # constructible argv string on any production route
        self.assertNotIn('"--allow-nonstrict"', source)
        self.assertNotIn("'--allow-nonstrict'", source)
        signature = inspect.signature(adapter.project_static_asset)
        self.assertNotIn("allow_nonstrict", signature.parameters)
        self.assertNotIn("strict", signature.parameters)
        # _build_argv pins the strict gate for validation and cannot emit the hatch anywhere
        validate_argv = adapter._build_argv("forge/stage2_spec/validate_sculpt_spec.py", Path("/up"), state_path="s.json", reference_path=None, profile="generic", spec_path="spec.json", output_path=None, pass_id=None)
        self.assertIn("--strict-quality", validate_argv)
        for entrypoint in adapter.ALLOWED_ENTRYPOINTS:
            for pass_id in (None, "blockout", "material-pass"):
                try:
                    argv = adapter._build_argv(entrypoint, Path("/up"), state_path="s.json", reference_path="r.png", profile="generic", spec_path="spec.json", output_path="o.ts", pass_id=pass_id)
                except adapter.Img2ThreeJSAdapterError:
                    continue
                self.assertNotIn("--allow-nonstrict", argv)
                self.assertNotIn("--allow-nonstrict", " ".join(argv))
        combined = adapter._build_argv("forge/stage3_build/generate_threejs_factory.py", Path("/up"), state_path="s.json", reference_path=None, profile="generic", spec_path="spec.json", output_path="o.ts", pass_id="blockout")
        self.assertNotIn("--allow-nonstrict", combined)

    def test_runtime_profile_verification_fail_closed(self):
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(adapter.Img2ThreeJSAdapterError, "RUNTIME_ROOT_UNAVAILABLE|NODE_VERSION_UNVERIFIED|NODE_RUNTIME_MISSING"):
                adapter.verify_static_runtime_profile(Path(directory) / "missing-runtime")
            (Path(directory) / "node_modules" / "three" / "build").mkdir(parents=True)
            (Path(directory) / "node_modules" / "three" / "build" / "three.module.js").write_text("export {}", encoding="utf-8")
            (Path(directory) / "node_modules" / "three" / "package.json").write_text(json.dumps({"name": "three", "version": "0.168.0"}), encoding="utf-8")
            with self.assertRaisesRegex(adapter.Img2ThreeJSAdapterError, "NODE_VERSION_UNVERIFIED|NODE_RUNTIME_MISSING"):
                adapter.verify_static_runtime_profile(Path(directory))
        with self.assertRaisesRegex(adapter.Img2ThreeJSAdapterError, "NODE_EXECUTABLE_INVALID"):
            adapter.verify_static_runtime_profile("/tmp", node_executable="../evil node")

    def test_project_operation_fails_closed_before_any_execution(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            calls = []
            original_run = adapter.subprocess.run

            def recorded(command, *args, **kwargs):
                calls.append(command)
                return original_run(command, *args, **kwargs)

            adapter.subprocess.run = recorded
            try:
                common = dict(source_root=root / "upstream-missing", workspace_root=root, runtime_root=root / "runtime-missing", spec_path="spec.json", asset_name="fixture_prop", target_major_extent_meters=0.5, run_id="run-001")
                with self.assertRaises(adapter.Img2ThreeJSAdapterError):
                    adapter.project_static_asset(**common)
                with self.assertRaisesRegex(adapter.Img2ThreeJSAdapterError, "TARGET_MAJOR_EXTENT_METERS_REQUIRED"):
                    adapter.project_static_asset(**{**common, "target_major_extent_meters": None})
                with self.assertRaisesRegex(adapter.Img2ThreeJSAdapterError, "ASSET_NAME_INVALID"):
                    adapter.project_static_asset(**{**common, "asset_name": "BAD NAME"})
                with self.assertRaisesRegex(adapter.Img2ThreeJSAdapterError, "RUN_ID_PATH_TRAVERSAL"):
                    adapter.project_static_asset(**{**common, "run_id": "../escape"})
                with self.assertRaisesRegex(adapter.Img2ThreeJSAdapterError, "RUN_ID_INVALID"):
                    adapter.project_static_asset(**{**common, "run_id": "bad id"})
                self.assertEqual(calls, [], "no subprocess may start before every pin, path, and anchor gate passes")
            finally:
                adapter.subprocess.run = original_run

    def test_verified_runtime_profile_is_exact(self):
        self.assertEqual(adapter.VERIFIED_NODE_VERSION, "v25.2.1")
        self.assertEqual(adapter.VERIFIED_THREE_VERSION, "0.169.0")
        self.assertEqual(adapter.VERIFIED_THREE_REVISION, "169")
        if shutil.which("node"):
            # The sandbox node is intentionally NOT the verified profile: the
            # adapter must refuse it. This asserts fail-closed versioning,
            # not runtime proof.
            with self.assertRaisesRegex(adapter.Img2ThreeJSAdapterError, "NODE_VERSION_UNVERIFIED"):
                adapter.verify_static_runtime_profile(Path("/"))
        self.assertFalse(hasattr(adapter, "install"))


if __name__ == "__main__":
    unittest.main()
