"""Bounded, deterministic GLB standardization for static Three.js props.

This seam deliberately does not import Three.js or Blender.  A forge adapter may
project a Three.js Object3D/Scene into the small JSON-shaped input contract below;
the resulting GLB is self-contained and can be consumed by the existing
``game.three.asset`` route.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import struct
from pathlib import Path
from typing import Any, Mapping

CAPABILITY_ID = "game.three.asset.static_glb_standardize"
CAPABILITY_VERSION = "1.0.0"
STATIC_CONTRACT = "p2p-static-glb-asset/1"
SUPPORTED_MATERIALS = {"MeshBasicMaterial", "MeshLambertMaterial", "MeshPhongMaterial", "MeshStandardMaterial"}
_NAME = re.compile(r"^[a-z][a-z0-9_-]{1,63}$")

class StaticGlbError(ValueError):
    pass

def _finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise StaticGlbError(f"{field}: finite number required")
    return float(value)

def _vec(value: Any, field: str, expected: int = 3) -> list[float]:
    if not isinstance(value, (list, tuple)) or len(value) != expected:
        raise StaticGlbError(f"{field}: {expected} numbers required")
    return [_finite_number(item, field) for item in value]

def _align(data: bytes) -> bytes:
    return data + b"\0" * ((4 - len(data) % 4) % 4)

def _validate_input(asset: Mapping[str, Any]) -> tuple[str, list[Mapping[str, Any]]]:
    if not isinstance(asset, Mapping):
        raise StaticGlbError("INPUT_NOT_OBJECT")
    name = asset.get("name")
    if not isinstance(name, str) or not _NAME.fullmatch(name):
        raise StaticGlbError("ASSET_NAME_INVALID")
    if asset.get("units") != "meters" or asset.get("up_axis") != "Y":
        raise StaticGlbError("STATIC_CONVENTION_INVALID")
    transform = asset.get("transform", {})
    if not isinstance(transform, Mapping):
        raise StaticGlbError("TRANSFORM_INVALID")
    position = _vec(transform.get("position", [0, 0, 0]), "transform.position")
    rotation = _vec(transform.get("rotation", [0, 0, 0]), "transform.rotation")
    scale = _vec(transform.get("scale", [1, 1, 1]), "transform.scale")
    if any(abs(x) > 1e6 for x in position + rotation) or any(x <= 0 or x > 1e4 for x in scale):
        raise StaticGlbError("TRANSFORM_SANITY_FAILED")
    if any(key in asset for key in ("skin", "skeleton", "animations", "bones")) and any(asset.get(key) for key in ("skin", "skeleton", "animations", "bones")):
        raise StaticGlbError("STATIC_ASSET_MUST_NOT_REQUIRE_SKIN")
    meshes = asset.get("meshes")
    if not isinstance(meshes, list) or not meshes:
        raise StaticGlbError("MESH_GEOMETRY_MISSING")
    return name, meshes

def _make_document(name: str, meshes: list[Mapping[str, Any]], transform: Mapping[str, Any]) -> tuple[dict[str, Any], bytes, dict[str, Any]]:
    raw = bytearray(); views: list[dict[str, int]] = []; accessors: list[dict[str, Any]] = []
    gltf_meshes = []; materials = []; material_indices: dict[str, int] = {}
    vertex_total = index_total = 0
    for mesh_index, mesh in enumerate(meshes):
        if not isinstance(mesh, Mapping): raise StaticGlbError("MESH_INVALID")
        positions = mesh.get("positions")
        if not isinstance(positions, list) or not positions or len(positions) % 3: raise StaticGlbError("MESH_POSITIONS_INVALID")
        vals = [_finite_number(x, "positions") for x in positions]
        if not all(math.isfinite(x) for x in vals): raise StaticGlbError("MESH_POSITIONS_INVALID")
        indices = mesh.get("indices")
        if indices is None: indices = list(range(len(vals) // 3))
        if not isinstance(indices, list) or not indices or any(isinstance(x, bool) or not isinstance(x, int) or x < 0 or x >= len(vals)//3 for x in indices): raise StaticGlbError("MESH_INDICES_INVALID")
        material = mesh.get("material", {"type": "MeshStandardMaterial", "color": [1, 1, 1], "roughness": 1, "metalness": 0})
        if not isinstance(material, Mapping) or material.get("type") not in SUPPORTED_MATERIALS: raise StaticGlbError("MATERIAL_UNSUPPORTED")
        key = json.dumps(dict(material), sort_keys=True, separators=(",", ":"))
        if key not in material_indices:
            material_indices[key] = len(materials); materials.append({"name": f"material_{len(materials):02d}", "pbrMetallicRoughness": {"baseColorFactor": [*(_vec(material.get("color", [1, 1, 1]), "material.color")), _finite_number(material.get("opacity", 1), "material.opacity")], "metallicFactor": _finite_number(material.get("metalness", 0), "material.metalness"), "roughnessFactor": _finite_number(material.get("roughness", 1), "material.roughness")}})
        while len(raw) % 4: raw.append(0)
        pos_offset = len(raw); raw.extend(struct.pack("<%sf" % len(vals), *vals)); pos_view = len(views); views.append({"buffer": 0, "byteOffset": pos_offset, "byteLength": len(vals)*4})
        pos_acc = len(accessors); accessors.append({"bufferView": pos_view, "componentType": 5126, "count": len(vals)//3, "type": "VEC3", "min": [min(vals[i::3]) for i in range(3)], "max": [max(vals[i::3]) for i in range(3)]})
        while len(raw) % 4: raw.append(0)
        idx_offset = len(raw); raw.extend(struct.pack("<%sI" % len(indices), *indices)); idx_view = len(views); views.append({"buffer": 0, "byteOffset": idx_offset, "byteLength": len(indices)*4, "target": 34963})
        idx_acc = len(accessors); accessors.append({"bufferView": idx_view, "componentType": 5125, "count": len(indices), "type": "SCALAR", "min": [min(indices)], "max": [max(indices)]})
        gltf_meshes.append({"name": mesh.get("name", f"mesh_{mesh_index:02d}"), "primitives": [{"attributes": {"POSITION": pos_acc}, "indices": idx_acc, "material": material_indices[key], "mode": 4}]})
        vertex_total += len(vals)//3; index_total += len(indices)
    rx, ry, rz = [_finite_number(x, "transform.rotation") for x in _vec(transform.get("rotation", [0, 0, 0]), "transform.rotation")]
    cx, sx, cy, sy, cz, sz = (math.cos(rx / 2), math.sin(rx / 2), math.cos(ry / 2), math.sin(ry / 2), math.cos(rz / 2), math.sin(rz / 2))
    quaternion = [sx * cy * cz - cx * sy * sz, cx * sy * cz + sx * cy * sz, cx * cy * sz - sx * sy * cz, cx * cy * cz + sx * sy * sz]
    node_transform = {"translation": _vec(transform.get("position", [0, 0, 0]), "transform.position"), "rotation": quaternion, "scale": _vec(transform.get("scale", [1, 1, 1]), "transform.scale")}
    document = {"asset": {"version": "2.0", "generator": "P2P static GLB standardizer"}, "scene": 0, "scenes": [{"name": name, "nodes": list(range(len(gltf_meshes)))}], "nodes": [{"name": m["name"], "mesh": i, **node_transform} for i, m in enumerate(gltf_meshes)], "meshes": gltf_meshes, "materials": materials, "buffers": [{"byteLength": len(raw)}], "bufferViews": views, "accessors": accessors}
    evidence = {"status": "VALID", "contract": STATIC_CONTRACT, "asset_name": name, "mesh_count": len(gltf_meshes), "vertex_count": vertex_total, "index_count": index_total, "material_count": len(materials), "skin": False, "skeleton": False, "gltf_version": "2.0"}
    return document, bytes(raw), evidence

def _encode_glb(document: dict[str, Any], binary: bytes) -> bytes:
    json_chunk = _align(json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    binary = _align(binary)
    total = 12 + 8 + len(json_chunk) + 8 + len(binary)
    return struct.pack("<4sII", b"glTF", 2, total) + struct.pack("<I4s", len(json_chunk), b"JSON") + json_chunk + struct.pack("<I4s", len(binary), b"BIN\0") + binary

def standardize_static_glb(asset: Mapping[str, Any], output_path: str | Path, *, generating_capability: str, run_id: str) -> dict[str, Any]:
    """Export a bounded static asset and write a provenance-bound validation receipt."""
    if not isinstance(generating_capability, str) or not generating_capability or not isinstance(run_id, str) or not run_id:
        raise StaticGlbError("PROVENANCE_BINDING_INVALID")
    name, meshes = _validate_input(asset)
    document, binary, evidence = _make_document(name, meshes, asset["transform"])
    glb = _encode_glb(document, binary)
    destination = Path(output_path)
    if destination.suffix.lower() != ".glb": raise StaticGlbError("OUTPUT_MUST_BE_GLB")
    destination.parent.mkdir(parents=True, exist_ok=True); destination.write_bytes(glb)
    digest = hashlib.sha256(glb).hexdigest()
    provenance = {"schema": "p2p-static-asset-provenance/1", "capability_id": CAPABILITY_ID, "capability_version": CAPABILITY_VERSION, "generating_capability": generating_capability, "run_id": run_id, "asset_name": name, "glb_sha256": digest, "contract": STATIC_CONTRACT}
    provenance_path = destination.with_suffix(".asset-provenance.json"); provenance_path.write_text(json.dumps(provenance, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return {"status": "STANDARDIZED", "glb_path": str(destination), "provenance_path": str(provenance_path), "glb_sha256": digest, "validation": evidence, "provenance": provenance}

def validate_static_glb_output(glb_path: str | Path, provenance_path: str | Path) -> dict[str, Any]:
    glb = Path(glb_path); data = glb.read_bytes()
    if len(data) < 20: raise StaticGlbError("GLB_HEADER_INVALID")
    magic, version, total = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF" or version != 2 or total != len(data): raise StaticGlbError("GLB_HEADER_INVALID")
    offset = 12; document = None; bin_chunk = None
    while offset < total:
        if offset + 8 > total: raise StaticGlbError("GLB_CHUNK_HEADER_INVALID")
        length, chunk_type = struct.unpack_from("<I4s", data, offset); offset += 8
        if length % 4 or offset + length > total: raise StaticGlbError("GLB_CHUNK_INVALID")
        payload = data[offset:offset + length]; offset += length
        if chunk_type == b"JSON":
            if document is not None: raise StaticGlbError("GLB_MULTIPLE_JSON_CHUNKS")
            try: document = json.loads(payload.rstrip(b" \\t\\r\\n\\0").decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError) as exc: raise StaticGlbError("GLB_JSON_INVALID") from exc
        elif chunk_type == b"BIN\0": bin_chunk = payload
    if not isinstance(document, dict) or not isinstance(bin_chunk, bytes): raise StaticGlbError("GLB_LOADABILITY_INVALID")
    if document.get("asset", {}).get("version") != "2.0" or not document.get("meshes") or not document.get("buffers"): raise StaticGlbError("GLB_STATIC_CONTENT_INVALID")
    if Path(provenance_path).name != f"{glb.stem}.asset-provenance.json": raise StaticGlbError("PROVENANCE_NAMING_INVALID")
    provenance = json.loads(Path(provenance_path).read_text(encoding="utf-8"))
    if provenance.get("glb_sha256") != hashlib.sha256(data).hexdigest() or provenance.get("schema") != "p2p-static-asset-provenance/1": raise StaticGlbError("PROVENANCE_HASH_MISMATCH")
    return {"status": "PARSEABLE", "gltf_version": "2.0", "glb_sha256": provenance["glb_sha256"], "provenance": provenance}

__all__ = ["CAPABILITY_ID", "CAPABILITY_VERSION", "STATIC_CONTRACT", "StaticGlbError", "standardize_static_glb", "validate_static_glb_output"]
