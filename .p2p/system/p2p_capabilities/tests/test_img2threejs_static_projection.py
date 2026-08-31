"""P2P-IMG2THREEJS-STATIC-PROJECTION-01 — static projection seam tests.

Repository-side contract and composition coverage only:

  COMPOSITION_TESTED=YES  (bounded synthetic bake-manifest fixtures, in-repo)
  EXTERNAL_IMG2THREEJS_RUNTIME_PROVEN=NO
  (no upstream checkout, Node/three runtime, browser, or weapon generation
  is executed here; production runtime smoke belongs to the later Owner-side
  run against the pre-provisioned verified runtime profile)
"""

from __future__ import annotations

import hashlib
import inspect
import json
import math
import shutil
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import mock

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


class MaterialDefaultNonfiniteTests(unittest.TestCase):
    """P2P-IMG2THREEJS-MATERIAL-DEFAULT-NONFINITE-01.

    Bounded material runtime-default / non-finite fix. The corrected snapshot
    (``img2threejs_material_snapshot.mjs``) compares a numeric property against
    the material class's runtime default BEFORE the generic non-finite
    rejection, so:

      1. an exact runtime-default ``Infinity`` attenuationDistance on a
         physical material is accepted as DEFAULT (the snapshot emits no drift
         and the projection narrows to the canonical Standard subset accepted
         by the standardizer);
      2. an active / non-default attenuationDistance fails closed;
      3. NaN attenuationDistance fails closed;
      4. supported projected numeric fields (color channels, opacity,
         metalness, roughness) remain finite-only.

    These are adapter-boundary behaviors: the snapshot itself is exercised in
    ``tests/img2threejs_material_snapshot.node_test.mjs``.
    """

    def test_runtime_default_physical_material_is_accepted_and_narrows(self):
        manifest = _manifest([
            _group_node("root", None),
            _mesh_node(
                "hilt",
                "root",
                positions=[0, 0, 0, 1, 0, 0, 0, 1, 0],
                material=_material(type="MeshPhysicalMaterial", drift=[]),
            ),
        ])
        asset, evidence = _project(manifest, target=0.5)
        self.assertEqual(asset["meshes"][0]["material"]["type"], "MeshStandardMaterial")
        self.assertEqual(evidence["material_narrowing"], {"physical_to_standard": 1})
        # the corrected snapshot records no drift for a default-Infinity
        # attenuationDistance, so the projection is accepted by the standardizer
        with TemporaryDirectory() as directory:
            result = standardize_static_glb(
                asset,
                Path(directory) / "fixture_prop.glb",
                generating_capability="img2threejs",
                run_id="material-default-001",
            )
            parsed = validate_static_glb_output(
                result["glb_path"],
                result["provenance_path"],
                expected_asset_name="fixture_prop",
                expected_generating_capability="img2threejs",
                expected_run_id="material-default-001",
            )
        self.assertEqual(parsed["status"], "STRUCTURALLY_VALID")
        self.assertFalse(result["validation"]["skin"])
        self.assertFalse(result["validation"]["skeleton"])

    def test_active_attenuation_distance_fails_closed(self):
        for value in (2.5, float("nan"), float("inf")):
            with self.subTest(value=value):
                manifest = _manifest([
                    _group_node("root", None),
                    _mesh_node(
                        "m",
                        "root",
                        positions=[0, 0, 0, 1, 0, 0, 0, 1, 0],
                        material=_material(type="MeshPhysicalMaterial", drift=[["attenuationDistance", value]]),
                    ),
                ])
                with self.assertRaisesRegex(adapter.Img2ThreeJSAdapterError, "UNSUPPORTED_MATERIAL_FEATURE:attenuationDistance"):
                    _project(manifest)

    def test_supported_projected_field_nonfinite_fails_closed(self):
        cases = (
            ("opacity", dict(opacity=float("inf")), r"MATERIAL\.OPACITY"),
            ("metalness", dict(metalness=float("nan")), r"MATERIAL\.METALNESS"),
            ("roughness", dict(roughness=float("inf")), r"MATERIAL\.ROUGHNESS"),
            ("color", dict(color=[float("nan"), 0.5, 0.5]), r"MATERIAL\.COLOR\[0\]"),
        )
        for label, overrides, code in cases:
            with self.subTest(field=label):
                manifest = _manifest([
                    _group_node("root", None),
                    _mesh_node(
                        "m",
                        "root",
                        positions=[0, 0, 0, 1, 0, 0, 0, 1, 0],
                        material=_material(**overrides),
                    ),
                ])
                with self.assertRaisesRegex(adapter.Img2ThreeJSAdapterError, code):
                    _project(manifest)


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


VALIDATE_ENTRYPOINT = "forge/stage2_spec/validate_sculpt_spec.py"
GENERATE_ENTRYPOINT = "forge/stage3_build/generate_threejs_factory.py"


class SpecToctouTests(unittest.TestCase):
    """SPEC_VALIDATION_GENERATION_TOCTOU remediation.

    Fully offline dry run: the pinned-upstream and runtime-profile verifiers,
    the execution boundary, and the Node bake step are replaced by fakes so
    the test proves only the adapter's own capture/hash-binding contract.
    No external runtime proof is claimed.
    """

    SPEC = b'{"name": "Oak", "componentTree": []}'

    def _run_seam(self, workspace: Path, *, on_validate=None):
        spec_path = workspace / "input" / "character-spec.json"
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path.write_bytes(self.SPEC)
        runtime_root = workspace / "runtime"
        (runtime_root / "node_modules" / "three" / "build").mkdir(parents=True)
        (runtime_root / "node_modules" / "three" / "build" / "three.module.js").write_text("export {}", encoding="utf-8")
        (runtime_root / "node_modules" / "three" / "package.json").write_text(json.dumps({"version": adapter.VERIFIED_THREE_VERSION}), encoding="utf-8")
        calls: list[tuple[str, dict]] = []

        def fake_execute(entrypoint, **kwargs):
            calls.append((entrypoint, kwargs))
            if entrypoint == VALIDATE_ENTRYPOINT and on_validate is not None:
                on_validate(workspace, kwargs)
            if entrypoint == GENERATE_ENTRYPOINT:
                (workspace / kwargs["output_path"]).write_bytes(b"export function createFixtureModel() { throw 0; }\n")
            return {"status": "EXECUTED", "entrypoint": entrypoint}

        def fake_copytree(_src, dst, **_kwargs):
            Path(dst).mkdir(parents=True, exist_ok=True)

        def fake_run(argv, *args, **kwargs):
            factory = Path(argv[argv.index("--factory") + 1])
            out = Path(argv[argv.index("--out") + 1])
            manifest = {
                "schema": adapter.RUNTIME_BAKE_SCHEMA,
                "status": "BAKED",
                "up_axis": "Y",
                "runtime": {"node": adapter.VERIFIED_NODE_VERSION, "three": adapter.VERIFIED_THREE_REVISION},
                "factory_sha256": hashlib.sha256(factory.read_bytes()).hexdigest(),
                "aggregate": {"nodes": 2, "skinned_meshes": 0, "bones": 0, "animations": 0, "skeletons": 0, "maximum_depth": 1},
                "nodes": [
                    _group_node("root", None),
                    _mesh_node("n0001", "root", positions=[0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]),
                ],
            }
            out.write_text(json.dumps(manifest), encoding="utf-8")
            return SimpleNamespace(returncode=0, stdout="P2P_IMG2THREEJS_BAKE_OK nodes=2\n", stderr="")

        with (
            mock.patch.object(adapter, "verify_upstream_checkout", lambda _root: {"commit": adapter.UPSTREAM_SHA, "tree": adapter.UPSTREAM_TREE}),
            mock.patch.object(adapter, "verify_static_runtime_profile", lambda _root, *, node_executable="node": {
                "node_executable": "node-fake",
                "node_version": adapter.VERIFIED_NODE_VERSION,
                "three_version": adapter.VERIFIED_THREE_VERSION,
                "three_revision": adapter.VERIFIED_THREE_REVISION,
                "three_entrypoint": "fake",
                "runtime_root": str(runtime_root),
            }),
            mock.patch.object(adapter.shutil, "copytree", fake_copytree),
            mock.patch.object(adapter, "execute", fake_execute),
            mock.patch.object(adapter.subprocess, "run", fake_run),
        ):
            receipt = adapter.project_static_asset(
                source_root=workspace / "pinned-upstream",
                workspace_root=workspace,
                runtime_root=runtime_root,
                spec_path="input/character-spec.json",
                asset_name="fixture_prop",
                target_major_extent_meters=1.0,
                run_id="run-toctou-01",
            )
        return receipt, calls

    def test_A_success_binds_captured_bytes_to_owned_copy(self):
        with TemporaryDirectory() as directory:
            workspace = Path(directory)
            receipt, calls = self._run_seam(workspace)
            expected_sha = hashlib.sha256(self.SPEC).hexdigest()
            owned_relative = "static-projection/run-toctou-01/input-spec.json"
            self.assertEqual(receipt["status"], "PROJECTED")
            self.assertEqual(receipt["spec_sha256"], expected_sha)
            self.assertEqual(receipt["spec"]["sha256"], expected_sha)
            self.assertEqual(receipt["spec"]["workspace_relative_path"], owned_relative)
            self.assertEqual(receipt["spec"]["source_workspace_relative_path"], "input/character-spec.json")
            self.assertEqual([entrypoint for entrypoint, _ in calls], [VALIDATE_ENTRYPOINT, GENERATE_ENTRYPOINT])
            for _, kwargs in calls:
                # both upstream subprocesses receive ONLY the owned path
                self.assertEqual(kwargs["spec_path"], owned_relative)
            self.assertEqual((workspace / owned_relative).read_bytes(), self.SPEC)
            self.assertTrue((workspace / Path(owned_relative).parent / "projection.json").is_file())

    def test_B_caller_mutation_after_capture_cannot_reach_generation(self):
        def mutate_source(workspace, _kwargs):
            (workspace / "input" / "character-spec.json").write_bytes(b'{"name": "Evil", "componentTree": []}')

        with TemporaryDirectory() as directory:
            workspace = Path(directory)
            receipt, calls = self._run_seam(workspace, on_validate=mutate_source)
            owned_relative = "static-projection/run-toctou-01/input-spec.json"
            # caller source really did change after capture
            self.assertNotEqual((workspace / "input" / "character-spec.json").read_bytes(), self.SPEC)
            # generation still operated on the captured owned bytes
            self.assertEqual((workspace / owned_relative).read_bytes(), self.SPEC)
            self.assertEqual(calls[1][1]["spec_path"], owned_relative)
            self.assertEqual(receipt["spec_sha256"], hashlib.sha256(self.SPEC).hexdigest())

    def test_C_owned_copy_tamper_before_generation_fails_closed(self):
        def tamper_owned(workspace, kwargs):
            (workspace / kwargs["spec_path"]).write_bytes(b'{"tampered": true}')

        with TemporaryDirectory() as directory:
            workspace = Path(directory)
            with self.assertRaisesRegex(adapter.Img2ThreeJSAdapterError, "SPEC_CONTENT_CHANGED"):
                self._run_seam(workspace, on_validate=tamper_owned)
            # after a failed pre-generation hash re-bind, generation never starts
            receipt_dir = workspace / "static-projection" / "run-toctou-01"
            self.assertFalse((receipt_dir / "factory.ts").exists())

    def test_D_bounded_capture_rejects_oversize_and_missing(self):
        with TemporaryDirectory() as directory:
            workspace = Path(directory)
            spec_path = workspace / "input" / "character-spec.json"
            spec_path.parent.mkdir(parents=True, exist_ok=True)
            spec_path.write_bytes(b"x" * (adapter.MAX_SPEC_BYTES + 1))
            with mock.patch.object(adapter, "verify_upstream_checkout", lambda _root: {}), mock.patch.object(
                adapter, "verify_static_runtime_profile", lambda _root, **_kw: {"runtime_root": str(workspace)}
            ):
                with self.assertRaisesRegex(adapter.Img2ThreeJSAdapterError, "SPEC_INPUT_TOO_LARGE"):
                    adapter.project_static_asset(
                        source_root=workspace, workspace_root=workspace, runtime_root=workspace,
                        spec_path="input/character-spec.json", asset_name="fixture_prop",
                        target_major_extent_meters=1.0, run_id="run-toctou-02",
                    )

    def test_existing_receipt_records_do_not_inline_the_spec(self):
        with TemporaryDirectory() as directory:
            workspace = Path(directory)
            receipt, _calls = self._run_seam(workspace)
            serialized = json.dumps(receipt, sort_keys=True)
            self.assertNotIn('"name": "Oak"', serialized)
            self.assertNotIn("componentTree", serialized)


if __name__ == "__main__":
    unittest.main()
