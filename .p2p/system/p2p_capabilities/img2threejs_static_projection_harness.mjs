// P2P img2threejs static-projection bake harness.
//
// Owns exactly one job: import a generated ObjectSculptSpec factory module,
// instantiate the returned THREE.Group, and serialize the static scene graph
// as a `p2p-img2threejs-runtime-bake/1` JSON manifest (local matrices, raw
// positions/indices, material drift snapshot). It performs no scaling and no
// unit interpretation; world-space baking and the physical-meter anchor are
// owned by the deterministic Python projection seam.
//
// Fail-closed by construction: any non-Object3D return, non-Y-up runtime,
// cycle, non-static subtree, morph/skin data, non-finite number, material
// array, or unusable geometry terminates the process with an error code on
// the last stdout line and a non-zero exit status.
//
// This file is P2P-owned code, not an upstream allowlisted entrypoint.

import { createHash } from "node:crypto";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const BAKE_SCHEMA = "p2p-img2threejs-runtime-bake/1";
const MAX_NODES = 8192;
const MAX_POSITION_FLOATS = 3_000_000;
const MAX_HIERARCHY_DEPTH = 512;
const SUPPORTED_MATERIAL_TYPES = new Set([
  "MeshBasicMaterial",
  "MeshLambertMaterial",
  "MeshPhongMaterial",
  "MeshStandardMaterial",
  "MeshPhysicalMaterial",
]);

function fail(code) {
  const line = `P2P_IMG2THREEJS_BAKE_FAIL ${code}`;
  process.stdout.write(line + "\n");
  process.stderr.write(line + "\n");
  process.exit(1);
}

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === "--factory") out.factory = argv[(i += 1)];
    else if (argv[i] === "--out") out.out = argv[(i += 1)];
    else fail("HARNESS_ARGUMENT_INVALID");
  }
  if (!out.factory || !out.out) fail("HARNESS_ARGUMENT_REQUIRED");
  if (!existsSync(out.factory)) fail("FACTORY_MODULE_MISSING");
  return out;
}

const args = parseArgs(process.argv.slice(2));
let THREE;
try {
  THREE = await import("three");
} catch (error) {
  fail("THREE_RUNTIME_UNAVAILABLE");
}

const up = THREE.Object3D.DEFAULT_UP ?? THREE.Object3D.DefaultUp;
if (!up || up.x !== 0 || up.y !== 1 || up.z !== 0) fail("Y_UP_RUNTIME_CONTRACT_FAILED");

const factoryUrl = pathToFileURL(args.factory).href;
let namespace;
try {
  namespace = await import(factoryUrl);
} catch (error) {
  fail("FACTORY_MODULE_IMPORT_FAILED");
}

const candidateNames = Object.keys(namespace)
  .filter((key) => /^create[A-Za-z0-9_]*Model$/.test(key) && typeof namespace[key] === "function")
  .sort();
if (candidateNames.length !== 1) fail("FACTORY_EXPORT_AMBIGUOUS");
const factory = namespace[candidateNames[0]];

let root;
try {
  root = factory({});
} catch (error) {
  fail("FACTORY_INVOCATION_FAILED");
}
if (!root || root instanceof Promise || !root.isObject3D) fail("FACTORY_RETURN_NOT_OBJECT3D");

if (Array.isArray(root.animations) && root.animations.length > 0) fail("ANIMATIONS_UNSUPPORTED");

root.updateMatrixWorld(true);

function isNumberValue(value) {
  return typeof value === "number" && Number.isFinite(value);
}

function sameVectorish(a, b) {
  const av = a.isVector2 || a.isVector3 || a.isVector4 ? a.toArray() : null;
  const bv = b.isVector2 || b.isVector3 || b.isVector4 ? b.toArray() : null;
  if (!av || !bv || av.length !== bv.length) return false;
  return av.every((value, index) => Object.is(value, bv[index]));
}

function sameColor(a, b) {
  if (typeof a?.getHex === "function" && typeof b?.getHex === "function") {
    return a.getHex() === b.getHex();
  }
  return false;
}

function materialSnapshot(material) {
  if (Array.isArray(material)) fail("MATERIAL_MULTI_UNSUPPORTED");
  if (!material) return null;
  const type = material.type;
  if (!SUPPORTED_MATERIAL_TYPES.has(type)) fail(`MATERIAL_TYPE_UNSUPPORTED:${type}`);
  const reference = new material.constructor();
  if (reference.type !== type) fail("MATERIAL_SUBCLASS_UNSUPPORTED");
  const ownKeys = Object.keys(material);
  const out = { type };
  const drift = [];
  for (const key of ownKeys) {
    if (key === "type" || key === "uuid" || key === "name") continue;
    const value = material[key];
    const base = reference[key];
    if (value === undefined) continue;
    if (value && value.isTexture) {
      if (base && base.isTexture) continue;
      drift.push([key, "texture"]);
      continue;
    }
    if (value && (value.isColor || base && base.isColor)) {
      if (!sameColor(value, base)) drift.push([key, "color"]);
      continue;
    }
    if (typeof value === "number") {
      if (!Number.isFinite(value)) fail(`MATERIAL_NONFINITE:${key}`);
      if (value !== base) drift.push([key, value]);
      continue;
    }
    if (typeof value === "boolean" || typeof value === "string") {
      if (value !== base) drift.push([key, value]);
      continue;
    }
    if (value && (value.isVector2 || value.isVector3 || value.isVector4)) {
      if (!sameVectorish(value, base)) drift.push([key, "vector"]);
      continue;
    }
    if (typeof value === "function") continue;
    if (value === null && (base === null || base === undefined)) continue;
    if (value !== base) drift.push([key, "object"]);
  }
  const color = material.color;
  if (!color || typeof color.r !== "number") fail("MATERIAL_COLOR_MISSING");
  for (const channel of [color.r, color.g, color.b]) {
    if (!Number.isFinite(channel)) fail("MATERIAL_COLOR_NONFINITE");
  }
  out.color = [color.r, color.g, color.b];
  out.opacity = isNumberValue(material.opacity) ? material.opacity : fail("MATERIAL_OPACITY_INVALID");
  if (typeof material.metalness === "number") out.metalness = material.metalness;
  if (typeof material.roughness === "number") out.roughness = material.roughness;
  out.drift = drift;
  return out;
}

function geometrySnapshot(geometry) {
  if (!geometry) fail("GEOMETRY_MISSING");
  if (geometry.type !== "BufferGeometry") fail(`GEOMETRY_TYPE_UNSUPPORTED:${geometry.type}`);
  if (geometry.morphAttributes && Object.keys(geometry.morphAttributes).length > 0) fail("GEOMETRY_MORPH_UNSUPPORTED");
  const position = geometry.getAttribute("position");
  if (!position || !position.array || position.itemSize !== 3) fail("GEOMETRY_POSITION_INVALID");
  const floats = Array.from(position.array);
  if (floats.length === 0 || floats.length % 3 !== 0 || floats.length > MAX_POSITION_FLOATS) fail("GEOMETRY_POSITION_INVALID");
  for (const value of floats) if (!Number.isFinite(value)) fail("GEOMETRY_POSITION_NONFINITE");
  let index = null;
  const indexAttribute = geometry.getIndex();
  if (indexAttribute) {
    index = Array.from(indexAttribute.array);
    if (index.length % 3 !== 0) fail("GEOMETRY_INDEX_INVALID");
    for (const value of index) {
      if (!Number.isInteger(value) || value < 0 || value >= floats.length / 3) fail("GEOMETRY_INDEX_INVALID");
    }
  } else if (floats.length / 3 % 3 !== 0) {
    fail("GEOMETRY_TRIANGLE_COUNT_INVALID");
  }
  return { type: "BufferGeometry", position: floats, index, count: floats.length / 3 };
}

const ids = new Map();
const nodes = [];
const seen = new Set();
let skinnedMeshes = 0;
let bones = 0;
let animations = 0;
let skeletonNodes = 0;
let maximumDepth = 0;

function visit(node, depth) {
  if (depth > MAX_HIERARCHY_DEPTH) fail("HIERARCHY_DEPTH_EXCEEDED");
  if (seen.has(node)) fail("OBJECT_GRAPH_CYCLE");
  seen.add(node);
  maximumDepth = Math.max(maximumDepth, depth);
  if (nodes.length >= MAX_NODES) fail("SCENE_NODE_LIMIT_EXCEEDED");
  const id = `n${String(nodes.length).padStart(4, "0")}`;
  ids.set(node, id);

  if (node.isBone) bones += 1;
  if (node.isSkinnedMesh) skinnedMeshes += 1;
  if (node.isSkeleton) skeletonNodes += 1;
  if (node.animations && node.animations.length > 0) animations += node.animations.length;
  if (bones || skinnedMeshes || animations || skeletonNodes) {
    fail(bones ? "STATIC_ASSET_MUST_NOT_REQUIRE_SKIN:BONE" : skinnedMeshes ? "STATIC_ASSET_MUST_NOT_REQUIRE_SKIN:SKINNED_MESH" : skeletonNodes ? "STATIC_ASSET_MUST_NOT_REQUIRE_SKIN:SKELETON" : "ANIMATIONS_UNSUPPORTED");
  }

  if (node.parent && !ids.has(node.parent)) fail("HIERARCHY_PARENT_UNVISITED");
  if (!node.visible) fail("INVISIBLE_NODE_REJECTED");

  let kind = "group";
  if (node.isSkinnedMesh) kind = "skinned";
  else if (node.isInstancedMesh) kind = "instanced";
  else if (node.isMesh) kind = "mesh";
  else if (node.isPoints || node.isLine || node.isLineSegments || node.isLineLoop || node.isSprite || node.isCamera || node.isLight) kind = "nonstatic";
  if (kind === "skinned") fail("STATIC_ASSET_MUST_NOT_REQUIRE_SKIN");
  if (kind === "instanced") fail("MESH_INSTANCED_UNSUPPORTED");
  if (kind === "nonstatic") fail("MESH_KIND_UNSUPPORTED");
  if (!node.isMesh && !node.isGroup && node.type !== "Group" && !node.isObject3D) fail("NODE_KIND_UNSUPPORTED");

  const matrix = Array.from(node.matrix.elements);
  for (const value of matrix) if (!Number.isFinite(value)) fail("TRANSFORM_NONFINITE");

  const record = { id, parent: node.parent ? ids.get(node.parent) : null, kind, matrix };
  if (kind === "mesh") {
    record.mesh = { geometry: geometrySnapshot(node.geometry), material: materialSnapshot(node.material) };
    if (node.geometry.attributes.skinIndex || node.geometry.attributes.skinWeight) fail("STATIC_ASSET_MUST_NOT_REQUIRE_SKIN");
  }
  nodes.push(record);
  for (const child of node.children) {
    visit(child, depth + 1);
  }
}

visit(root, 0);

const factoryDigest = createHash("sha256").update(readFileSync(args.factory)).digest("hex");
const manifest = {
  schema: BAKE_SCHEMA,
  status: "BAKED",
  up_axis: "Y",
  runtime: { node: process.version, three: THREE.REVISION },
  factory_sha256: factoryDigest,
  factory_export: candidateNames[0],
  aggregate: {
    nodes: nodes.length,
    skinned_meshes: skinnedMeshes,
    bones,
    animations,
    skeletons: skeletonNodes,
    maximum_depth: maximumDepth,
  },
  nodes,
};
writeFileSync(args.out, JSON.stringify(manifest), "utf8");
process.stdout.write(`P2P_IMG2THREEJS_BAKE_OK nodes=${nodes.length}\n`);
