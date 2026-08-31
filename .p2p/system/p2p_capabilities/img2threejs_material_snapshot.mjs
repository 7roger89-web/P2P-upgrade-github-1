// P2P img2threejs material snapshot.
//
// Owns exactly one job: snapshot a THREE material object into the bounded
// drift form consumed by the static projection seam. It knows nothing about
// geometry, scaling, or units; it only describes appearance drift relative to
// the material class's own runtime constructor defaults, and only for the
// canonical standardizer subset. It never claims equivalence it did not
// prove and never invents a supported feature.
//
// Fail-closed by construction. The property comparison order IS the fix the
// seam relies on:
//
//   1. runtime-default comparison runs BEFORE generic non-finite rejection
//   2. an exact runtime default `Infinity` (e.g. MeshPhysicalMaterial
//      `.attenuationDistance`) is treated as DEFAULT -> no drift, no reject
//   3. NaN is NEVER accepted as a valid default: NaN !== base for every base,
//      including a NaN base, so it always reaches the finite-only rejection
//   4. supported projected numeric fields (color channels, opacity,
//      metalness, roughness) remain finite-only
//   5. an active / non-default `attenuationDistance` remains fail-closed
//   6. active transmission / clearcoat / etc. drift remains fail-closed
//   7. no material support expansion (no new types, no new projected keys)
//
// This file is P2P-owned code, not an upstream allowlisted entrypoint.
//
// The function throws an Error whose `code` property carries the failure code.
// The caller (the bake harness) translates a caught code into its own terminal
// fail line. This keeps the module free of `process.exit` and directly
// unit-testable under Node without a THREE runtime.

export const SUPPORTED_MATERIAL_TYPES = new Set([
  "MeshBasicMaterial",
  "MeshLambertMaterial",
  "MeshPhongMaterial",
  "MeshStandardMaterial",
  "MeshPhysicalMaterial",
]);

// Projected fields the canonical `p2p-static-glb-asset/1` standardizer can
// carry. Any runtime material property outside this set that differs from the
// material class's own runtime default is a hard rejection: the seam must not
// silently drop appearance (MeshPhysical transmission/clearcoat/sheen/
// iridescence/thickness, texture slots, emissive, Phong specular/shininess,
// flat shading, vertex colors, blending, and so on all fail closed here).
export const PROJECTED_MATERIAL_KEYS = new Set([
  "color",
  "opacity",
  "metalness",
  "roughness",
]);

function reject(code) {
  const error = new Error(code);
  error.code = code;
  throw error;
}

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

export function materialSnapshot(material) {
  if (Array.isArray(material)) reject("MATERIAL_MULTI_UNSUPPORTED");
  if (!material) return null;
  const type = material.type;
  if (!SUPPORTED_MATERIAL_TYPES.has(type)) reject(`MATERIAL_TYPE_UNSUPPORTED:${type}`);
  const reference = new material.constructor();
  if (reference.type !== type) reject("MATERIAL_SUBCLASS_UNSUPPORTED");
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
      // Runtime-default comparison BEFORE generic non-finite rejection.
      // An exact runtime default (=== base) is accepted as default, even when
      // that default is Infinity (e.g. attenuationDistance). NaN never equals
      // any base, so it can never be laundered into a "default" here.
      if (value === base) continue;
      // Non-default numeric value. Supported projected fields must remain
      // finite-only; an Infinity/NaN that is NOT the runtime default is a
      // hard rejection. A finite non-default is recorded as drift so the
      // downstream standardizer can fail closed on unsupported features.
      if (!Number.isFinite(value)) reject(`MATERIAL_NONFINITE:${key}`);
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
  if (!color || typeof color.r !== "number") reject("MATERIAL_COLOR_MISSING");
  for (const channel of [color.r, color.g, color.b]) {
    if (!Number.isFinite(channel)) reject("MATERIAL_COLOR_NONFINITE");
  }
  out.color = [color.r, color.g, color.b];
  out.opacity = isNumberValue(material.opacity) ? material.opacity : reject("MATERIAL_OPACITY_INVALID");
  if (typeof material.metalness === "number") out.metalness = material.metalness;
  if (typeof material.roughness === "number") out.roughness = material.roughness;
  out.drift = drift;
  return out;
}
