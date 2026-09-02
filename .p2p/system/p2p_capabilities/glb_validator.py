"""Structural, provenance-bound validation for a rigged glTF 2.0 GLB."""

from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any, Mapping

from .asset_provenance import (
    AssetProvenanceError,
    sha256_file,
    validate_asset_provenance,
    validate_recipe_asset_binding,
)
from .character_recipe import CharacterRecipeError, recipe_sha256, validate_recipe


class GlbStructuralError(ValueError):
    """Raised when a GLB is not a structurally valid rigged asset."""


def _read_glb(path: Path) -> tuple[dict[str, Any], bytes | None]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise GlbStructuralError(f"GLB unreadable: {path}") from exc
    if len(data) < 20:
        raise GlbStructuralError("GLB_HEADER_INVALID")
    magic, version, total_length = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF" or version != 2 or total_length != len(data):
        raise GlbStructuralError("GLB_HEADER_INVALID")
    offset = 12
    document: dict[str, Any] | None = None
    binary: bytes | None = None
    while offset < total_length:
        if offset + 8 > total_length:
            raise GlbStructuralError("GLB_CHUNK_HEADER_INVALID")
        chunk_length, chunk_type = struct.unpack_from("<I4s", data, offset)
        offset += 8
        end = offset + chunk_length
        if end > total_length or chunk_length % 4 != 0:
            raise GlbStructuralError("GLB_CHUNK_INVALID")
        payload = data[offset:end]
        offset = end
        if chunk_type == b"JSON":
            if document is not None:
                raise GlbStructuralError("GLB_MULTIPLE_JSON_CHUNKS")
            try:
                parsed = json.loads(payload.rstrip(b" \t\r\n\x00").decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise GlbStructuralError("GLB_JSON_INVALID") from exc
            if not isinstance(parsed, dict):
                raise GlbStructuralError("GLB_JSON_ROOT_INVALID")
            document = parsed
        elif chunk_type == b"BIN\x00":
            if binary is not None:
                raise GlbStructuralError("GLB_MULTIPLE_BIN_CHUNKS")
            binary = payload
    if document is None:
        raise GlbStructuralError("GLB_JSON_CHUNK_MISSING")
    return document, binary


def _array(document: Mapping[str, Any], key: str, *, required: bool = True) -> list[Any]:
    value = document.get(key)
    if not isinstance(value, list) or (required and not value):
        raise GlbStructuralError(f"GLB_{key.upper()}_INVALID")
    return value


def _index(value: object, size: int, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < size:
        raise GlbStructuralError(f"{field}: index invalid")
    return value


def _reachable_scene_nodes(document: Mapping[str, Any], nodes: list[Any]) -> tuple[set[int], dict[int, int]]:
    scenes = _array(document, "scenes")
    scene_index = _index(document.get("scene"), len(scenes), "GLB_scene")
    scene = scenes[scene_index]
    if not isinstance(scene, dict) or not isinstance(scene.get("nodes"), list) or not scene["nodes"]:
        raise GlbStructuralError("GLB_SCENE_ROOTS_INVALID")
    parents: dict[int, int] = {}
    for node_index, raw_node in enumerate(nodes):
        if not isinstance(raw_node, dict):
            raise GlbStructuralError("GLB_NODE_INVALID")
        children = raw_node.get("children", [])
        if not isinstance(children, list):
            raise GlbStructuralError("GLB_NODE_CHILDREN_INVALID")
        for child in children:
            child_index = _index(child, len(nodes), "GLB_child")
            if child_index in parents and parents[child_index] != node_index:
                raise GlbStructuralError("GLB_NODE_MULTIPLE_PARENTS")
            parents[child_index] = node_index

    reachable: set[int] = set()
    visiting: set[int] = set()

    def visit(node_index: int) -> None:
        if node_index in visiting:
            raise GlbStructuralError("GLB_NODE_CYCLE")
        if node_index in reachable:
            return
        visiting.add(node_index)
        node = nodes[node_index]
        for child in node.get("children", []):
            visit(_index(child, len(nodes), "GLB_child"))
        visiting.remove(node_index)
        reachable.add(node_index)

    for root in scene["nodes"]:
        visit(_index(root, len(nodes), "GLB_scene_root"))
    return reachable, parents


def _validate_mesh_skin(document: Mapping[str, Any], reachable: set[int], parents: Mapping[int, int]) -> None:
    nodes = _array(document, "nodes")
    meshes = _array(document, "meshes")
    skins = _array(document, "skins")
    accessors = _array(document, "accessors")
    mesh_nodes = [node for node in reachable if isinstance(nodes[node], dict) and "mesh" in nodes[node]]
    if not mesh_nodes:
        raise GlbStructuralError("GLB_SCENE_MESH_MISSING")
    skinned_nodes = [node for node in mesh_nodes if "skin" in nodes[node]]
    if not skinned_nodes:
        raise GlbStructuralError("GLB_SCENE_SKIN_MISSING")

    for node_index in skinned_nodes:
        node = nodes[node_index]
        mesh = meshes[_index(node["mesh"], len(meshes), "GLB_mesh")]
        skin = skins[_index(node["skin"], len(skins), "GLB_skin")]
        if not isinstance(mesh, dict) or not isinstance(mesh.get("primitives"), list) or not mesh["primitives"]:
            raise GlbStructuralError("GLB_MESH_PRIMITIVES_INVALID")
        if not isinstance(skin, dict):
            raise GlbStructuralError("GLB_SKIN_INVALID")
        joints = skin.get("joints")
        if not isinstance(joints, list) or not joints:
            raise GlbStructuralError("GLB_SKIN_JOINTS_INVALID")
        joint_indices = {_index(joint, len(nodes), "GLB_joint") for joint in joints}
        if "skeleton" in skin:
            skeleton = _index(skin["skeleton"], len(nodes), "GLB_skeleton")
        else:
            joint_roots = {joint for joint in joint_indices if parents.get(joint) not in joint_indices}
            if len(joint_roots) != 1:
                raise GlbStructuralError("GLB_ROOTED_SKELETON_INVALID")
            skeleton = next(iter(joint_roots))
        if skeleton not in joint_indices or parents.get(skeleton) in joint_indices:
            raise GlbStructuralError("GLB_ROOTED_SKELETON_INVALID")

        connected: set[int] = set()
        pending = [skeleton]
        while pending:
            current = pending.pop()
            if current in connected:
                continue
            connected.add(current)
            current_node = nodes[current]
            if isinstance(current_node, dict):
                pending.extend(_index(child, len(nodes), "GLB_skeleton_child") for child in current_node.get("children", []))
        if not joint_indices.issubset(connected):
            raise GlbStructuralError("GLB_JOINTS_NOT_ROOTED")

        for primitive in mesh["primitives"]:
            if not isinstance(primitive, dict) or not isinstance(primitive.get("attributes"), dict):
                raise GlbStructuralError("GLB_PRIMITIVE_ATTRIBUTES_INVALID")
            attributes = primitive["attributes"]
            for semantic in ("JOINTS_0", "WEIGHTS_0"):
                accessor_index = _index(attributes.get(semantic), len(accessors), f"GLB_{semantic}")
                accessor = accessors[accessor_index]
                if not isinstance(accessor, dict) or accessor.get("type") != "VEC4":
                    raise GlbStructuralError(f"GLB_{semantic}_ACCESSOR_INVALID")
            joints_accessor = accessors[attributes["JOINTS_0"]]
            if joints_accessor.get("componentType") not in {5121, 5123, 5125}:
                raise GlbStructuralError("GLB_JOINTS_COMPONENT_INVALID")
            weights_accessor = accessors[attributes["WEIGHTS_0"]]
            if weights_accessor.get("componentType") not in {5121, 5123, 5126}:
                raise GlbStructuralError("GLB_WEIGHTS_COMPONENT_INVALID")
            if weights_accessor.get("componentType") != 5126 and weights_accessor.get("normalized") is not True:
                raise GlbStructuralError("GLB_WEIGHTS_NORMALIZATION_INVALID")


def _validate_resources(document: Mapping[str, Any], resources: list[Mapping[str, object]], binary: bytes | None) -> None:
    resource_uris = {resource["uri"] for resource in resources}
    buffers = _array(document, "buffers")
    if binary is None and any(not isinstance(buffer, dict) or "uri" not in buffer for buffer in buffers):
        raise GlbStructuralError("GLB_EMBEDDED_BIN_MISSING")
    for buffer in buffers:
        if not isinstance(buffer, dict):
            raise GlbStructuralError("GLB_BUFFER_INVALID")
        uri = buffer.get("uri")
        if uri is None:
            if binary is None or not isinstance(buffer.get("byteLength"), int) or buffer["byteLength"] > len(binary):
                raise GlbStructuralError("GLB_BUFFER_EMBEDDING_INVALID")
        elif not isinstance(uri, str) or (not uri.startswith("data:") and uri not in resource_uris):
            raise GlbStructuralError("GLB_EXTERNAL_BUFFER_UNBOUND")
    for image in document.get("images", []):
        if isinstance(image, dict) and isinstance(image.get("uri"), str) and not image["uri"].startswith("data:") and image["uri"] not in resource_uris:
            raise GlbStructuralError("GLB_EXTERNAL_IMAGE_UNBOUND")


def validate_glb_output(
    glb_path: str | Path,
    provenance_path: str | Path,
    recipe: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Validate GLB structure, exact output naming, and rights provenance."""

    glb = Path(glb_path)
    provenance_file = Path(provenance_path)
    if glb.suffix.lower() != ".glb" or provenance_file.name != f"{glb.stem}.asset-provenance.json":
        raise GlbStructuralError("OUTPUT_NAMING_INVALID")
    try:
        provenance_document = json.loads(provenance_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GlbStructuralError("PROVENANCE_UNREADABLE") from exc
    try:
        provenance = validate_asset_provenance(provenance_document)
    except AssetProvenanceError as exc:
        raise GlbStructuralError(str(exc)) from exc
    if sha256_file(glb) != provenance["glb_sha256"]:
        raise GlbStructuralError("GLB_PROVENANCE_HASH_MISMATCH")
    if recipe is not None:
        try:
            normalized_recipe = validate_recipe(recipe)
            if provenance["character_id"] != normalized_recipe["character_id"] or provenance["recipe_sha256"] != recipe_sha256(normalized_recipe):
                raise GlbStructuralError("RECIPE_PROVENANCE_BINDING_MISMATCH")
            validate_recipe_asset_binding(normalized_recipe, provenance)
        except (CharacterRecipeError, AssetProvenanceError) as exc:
            raise GlbStructuralError(str(exc)) from exc

    document, binary = _read_glb(glb)
    if document.get("asset", {}).get("version") != "2.0":
        raise GlbStructuralError("GLB_GLTF_VERSION_INVALID")
    nodes = _array(document, "nodes")
    reachable, parents = _reachable_scene_nodes(document, nodes)
    _validate_mesh_skin(document, reachable, parents)
    _validate_resources(document, provenance["resources"], binary)
    return {
        "status": "STRUCTURALLY_VALID",
        "gltf_version": "2.0",
        "character_id": provenance["character_id"],
        "glb_sha256": provenance["glb_sha256"],
        "rig_preset": provenance["rigging"]["rig_preset"],
        "skinning": provenance["rigging"]["skinning"],
        "scene_reachable_nodes": len(reachable),
    }


__all__ = ["GlbStructuralError", "validate_glb_output"]
