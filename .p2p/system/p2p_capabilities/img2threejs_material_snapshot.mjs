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
//   8. `userData` is a special runtime-default metadata comparison: three's
//      Material constructor allocates a fresh empty `{}` per instance, so the
//      live value and the constructor baseline are two independently allocated
//      empty plain records that are default-equivalent (identity differs,
//      appearance semantics identical). Two empty plain records -> DEFAULT ->
//      no drift. Non-empty or non-plain userData stays fail-closed drift.
//   9. semantic normalization (P2P-IMG2THREEJS-MATERIAL-SEMANTIC-DRIFT-01)
//      classifies exactly the bounded set of production properties whose
//      drift is identity-only bookkeeping or an inactive-feature companion,
//      and nothing else:
//        - `version` is the THREE material invalidation counter: a finite
//          non-negative safe integer on BOTH sides is valid runtime
//          bookkeeping -> ignored; any malformed value fails closed hard.
//        - `defines`, `envMapRotation`, `iridescenceThicknessRange` are
//          value-equivalent runtime defaults: identity differs between the
//          live and baseline allocations but an EXACT narrow semantic
//          comparison (plain record key/value equality; Euler
//          x/y/z/order; fixed-length bounded numeric array) proves equal
//          content -> default. Any content difference stays drift.
//        - `envMapIntensity`, `clearcoatRoughness`, `sheenColor` are
//          inactive appearance companions: a non-default companion value is
//          ignored ONLY when its controlling feature is proven inactive
//          (envMap null; clearcoat === 0; sheen === 0). An active feature
//          fails closed through the normal appearance/texture gates.
//      These are narrow per-property semantic classifiers, NOT a generic
//      deep-equality engine, and they add NO projected material key.
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

// A plain record-like object with no own properties of any kind (string,
// symbol, enumerable or not). This deliberately excludes arrays, class
// instances, Maps, and other exotic objects so the userData special case can
// never launder a non-default metadata carrier.
function isEmptyPlainRecord(value) {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return false;
  const prototype = Object.getPrototypeOf(value);
  if (prototype !== Object.prototype && prototype !== null) return false;
  return Reflect.ownKeys(value).length === 0;
}

// A. Runtime bookkeeping: `version` is THREE's material invalidation counter
// (Material.version, incremented on needsUpdate). It is pure bookkeeping with
// zero appearance content, so a sane counter is ignored for appearance. The
// validity rule is deliberately conservative and applies to BOTH the live
// value and the constructor baseline: a finite non-negative safe integer.
// Anything else (NaN, Infinity, negative, fractional, non-number, beyond the
// safe-integer range) is a corrupted runtime invariant and fails closed hard
// rather than being laundered as drift or default.
function isRuntimeVersionCounter(value) {
  return typeof value === "number"
    && Number.isSafeInteger(value)
    && value >= 0;
}

// B. Value-equivalent runtime defaults — narrow, per-property semantic
// comparisons only. There is deliberately NO generic deep-equality engine:
// each classifier knows the exact bounded shape three's runtime allocates.

// `defines`: three's ShaderMaterial-style defines record (MeshPhysical gets
// {"STANDARD":"","PHYSICAL":""}; MeshStandard gets {"STANDARD":""}). The live
// material and the constructor baseline hold independently allocated records,
// so identity differs although content is identical. Default-equivalent only
// when BOTH sides are plain safe records (Object.prototype or null prototype;
// never arrays/class instances/Map-like objects) carrying the EXACT same own
// key universe (strings AND symbols) and shallow-equal safe primitive values
// (string / finite number / boolean; NaN rejected). Any nested object value,
// extra/missing key, or value difference is NOT default-equivalent.
function isDefineRecordValue(value) {
  return typeof value === "string"
    || (typeof value === "number" && Number.isFinite(value))
    || typeof value === "boolean";
}

function sameDefines(a, b) {
  const plain = (value) => {
    if (typeof value !== "object" || value === null || Array.isArray(value)) return false;
    const prototype = Object.getPrototypeOf(value);
    return prototype === Object.prototype || prototype === null;
  };
  if (!plain(a) || !plain(b)) return false;
  const keys = Reflect.ownKeys(a);
  const otherKeys = Reflect.ownKeys(b);
  if (keys.length !== otherKeys.length) return false;
  for (const key of keys) {
    if (!Object.prototype.hasOwnProperty.call(b, key)) return false;
    const av = a[key];
    const bv = b[key];
    if (!isDefineRecordValue(av) || !isDefineRecordValue(bv) || !Object.is(av, bv)) return false;
  }
  return true;
}

// `envMapRotation`: a THREE.Euler instance (x, y, z, order). Default-equivalent
// only when BOTH sides are Euler-like objects with identical x/y/z (finite,
// Object.is-exact) and identical rotation order. A different angle or order is
// a real appearance change and stays drift; a NaN component is never accepted.
const EULER_ORDERS = new Set(["XYZ", "YXZ", "ZXY", "ZYX", "YZX", "XZY"]);

function sameEuler(a, b) {
  const euler = (value) =>
    value
    && typeof value === "object"
    && value.isEuler === true
    && isNumberValue(value.x)
    && isNumberValue(value.y)
    && isNumberValue(value.z)
    && EULER_ORDERS.has(value.order);
  if (!euler(a) || !euler(b)) return false;
  return Object.is(a.x, b.x) && Object.is(a.y, b.y) && Object.is(a.z, b.z) && a.order === b.order;
}

// `iridescenceThicknessRange`: a plain two-element numeric array
// ([min,max] nanometers; three's default is [100, 400]). The live and baseline
// arrays are independently allocated, so identity differs. Default-equivalent
// only when BOTH sides are real (non-typed) length-2 arrays whose two entries
// are finite and Object.is-exact. A different range stays drift.
function sameIridescenceThicknessRange(a, b) {
  const boundedRange = (value) =>
    Array.isArray(value)
    && value.length === 2
    && Object.getPrototypeOf(value) === Array.prototype
    && isNumberValue(value[0])
    && isNumberValue(value[1]);
  if (!boundedRange(a) || !boundedRange(b)) return false;
  return Object.is(a[0], b[0]) && Object.is(a[1], b[1]);
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
    // A. Runtime bookkeeping: the THREE material invalidation counter. A
    // finite non-negative safe integer on both sides is valid runtime state
    // (a fresh baseline legitimately starts at 0; a rendered live material
    // legitimately counts upward) with zero appearance content -> ignored.
    // Any malformed value is a corrupted invariant -> fail closed hard.
    if (key === "version") {
      if (!isRuntimeVersionCounter(value) || !isRuntimeVersionCounter(base)) {
        reject("MATERIAL_VERSION_INVALID");
      }
      continue;
    }
    if (value && value.isTexture) {
      if (base && base.isTexture) continue;
      drift.push([key, "texture"]);
      continue;
    }
    // C. Inactive appearance companion: `sheenColor` is semantically inert
    // only while the sheen feature is proven inactive (sheen === 0). An
    // active sheen (sheen > 0 or any non-0 value) keeps the normal color
    // comparison, whose drift the seam rejects: sheen stays unsupported /
    // fail-closed and never enters the projected key set.
    if (key === "sheenColor" && material.sheen === 0) {
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
      // C. Inactive appearance companions (numeric). A non-default companion
      // scalar is ignored ONLY while its controlling feature is proven
      // inactive AND the value itself is finite (NaN/Infinity can never be
      // laundered through an inactive feature). If the feature is active,
      // the fall-through below treats the value as ordinary appearance drift:
      // envMap intensity rides on an actual envMap texture slot (already
      // rejected as a texture above), and clearcoat/sheen are unsupported
      // physical features the static seam rejects via the drift list.
      if (key === "envMapIntensity" && (material.envMap === null || material.envMap === undefined) && isNumberValue(value)) {
        continue;
      }
      if (key === "clearcoatRoughness" && material.clearcoat === 0 && isNumberValue(value)) {
        continue;
      }
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
    // B. Value-equivalent runtime defaults (identity differs, content equal).
    // Each gate accepts ONLY an exact narrow semantic match; every other shape
    // or any content difference falls through to fail-closed drift.
    if (key === "envMapRotation") {
      if (sameEuler(value, base)) continue;
      drift.push([key, "object"]);
      continue;
    }
    if (key === "defines") {
      if (sameDefines(value, base)) continue;
      drift.push([key, "object"]);
      continue;
    }
    if (key === "iridescenceThicknessRange") {
      if (sameIridescenceThicknessRange(value, base)) continue;
      drift.push([key, "object"]);
      continue;
    }
    if (key === "userData") {
      // Runtime-default metadata special case (NOT a material support
      // expansion): the live material and the constructor baseline each carry
      // their own freshly allocated empty `userData = {}`, so distinct object
      // identity alone must not create drift for two empty plain records.
      // ONLY two empty plain records are DEFAULT. Every other userData value
      // is fail-closed drift regardless of reference equality, so even a
      // non-empty object shared by the live material and the constructor
      // baseline cannot be laundered through `value === base`.
      if (isEmptyPlainRecord(value) && isEmptyPlainRecord(base)) continue;
      drift.push([key, "object"]);
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
