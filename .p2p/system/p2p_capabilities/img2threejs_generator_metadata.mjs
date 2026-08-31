// P2P img2threejs generator-owned material-metadata separation.
//
// Owns exactly one job: decide whether a live THREE `Material.userData` value
// is the verified pinned generator's OWN non-appearance metadata, and — only
// then — separate it from the generic appearance projection so the generic
// material snapshot keeps seeing the runtime default.
//
// Why this module exists (P2P-IMG2THREEJS-GENERATOR-USERDATA-BOUNDARY-01):
//
// The pinned generator `forge/stage3_build/generate_threejs_factory.py`
// (upstream `dede5909be4e494b228c801a55dda47439143932`, tree
// `25bcd4e1f1a487b9a61d69ade257342a3da767e3`) emits, unconditionally, inside
// `createSculptMaterial`:
//
//     material.userData.sculptMaterial = spec;
//     material.userData.proceduralMapsIndependent = true;
//     material.userData.pbrConstraints = { albedoRange: [30, 240], ... };
//     material.userData.pbrTextureSource = textures?.source ?? 'flat-fallback';
//     material.userData.referencePbr = spec.referencePbr ?? null;
//     material.userData.referenceMaterialId = spec.referenceMaterialId ?? ...;
//     material.userData.materialEvidence = spec.materialEvidence ?? null;
//     material.userData.validationViews = spec.materialReference?.validationViews ?? [];
//
// So EVERY material a verified factory produces carries non-empty userData.
// The generic appearance authority
// (`img2threejs_material_snapshot.mjs`) is correct to fail that closed: it
// cannot know that those eight records are bookkeeping rather than appearance.
// The fix therefore does NOT live in the generic module. It lives here, at the
// verified generator/harness boundary, which DOES know the factory was
// produced by the pinned verified generator entrypoint.
//
// Boundary guarantees:
//
//   1. `img2threejs_material_snapshot.mjs` is untouched. Two default-
//      equivalent empty plain userData records -> DEFAULT; ANY arbitrary or
//      non-empty userData that reaches it -> drift -> fail closed. That
//      invariant is unchanged and unweakened.
//   2. `userData` is NOT added to PROJECTED_MATERIAL_KEYS and never enters
//      the static GLB material contract. Separated metadata is never
//      projected; it is only attested in the bake manifest.
//   3. Separation is NOT laundering. `userData.sculptMaterial` describes the
//      authored spec; it is not the live appearance. The live appearance
//      properties the same generator also sets (`color`, `roughness`,
//      `metalness`, `transmission`, `clearcoat`, `sheen`, `iridescence`,
//      `attenuationDistance`, textures, `emissive`, ...) are still snapshotted
//      and still fail closed. Separating userData therefore cannot suppress
//      real appearance drift.
//   4. Classification is allowlist-only and inert-data-only. An unknown
//      additional key, a symbol or non-enumerable key, a non-plain carrier
//      (Map/Set/class instance/array), a function/bigint/symbol/undefined
//      value, NaN/Infinity, a prototype-exotic value, or a cycle all fail
//      closed here with an explicit code. Nothing is turned into DEFAULT.
//   5. No caller escape hatch: there is no parameter, flag, or environment
//      route that disables this classification.
//
// The bounds are deliberately small and are NOT a serialization framework:
// they exist only so a pathological or hostile structure cannot recurse
// without limit before the fail-closed verdict. The real generator metadata is
// a JSON literal emitted by `json_literal`/`json.dumps` from the strict-
// validated spec, so it is shallow, acyclic, and inert by construction; the
// bounds are a safety net, not a target.
//
// This file is P2P-owned code, not an upstream allowlisted entrypoint.
//
// Like the material snapshot module, this module throws an Error whose `code`
// property carries the failure code and never calls `process.exit`; the
// harness translates a caught code into its own terminal fail line.

// The exact key universe of the verified pinned generator contract. Every own
// key of a candidate userData must be a member; an unknown additional key is
// an immediate fail-closed rejection.
export const GENERATOR_MATERIAL_METADATA_KEYS = new Set([
  "materialEvidence",
  "pbrConstraints",
  "pbrTextureSource",
  "proceduralMapsIndependent",
  "referenceMaterialId",
  "referencePbr",
  "sculptMaterial",
  "validationViews",
]);

export const GENERATOR_NON_APPEARANCE_METADATA = "GENERATOR_NON_APPEARANCE_METADATA";

const MAX_METADATA_DEPTH = 16;
const MAX_METADATA_NODES = 16384;
const MAX_METADATA_STRING_LENGTH = 65536;

function reject(code) {
  const error = new Error(code);
  error.code = code;
  throw error;
}

// A fail code may embed an offending own key for diagnosability, but the
// harness writes that code as a single stdout/stderr line. Anything that is
// not a safe ASCII identifier character is replaced, so no key value can
// forge an extra `P2P_IMG2THREEJS_BAKE_FAIL` line.
function safeLabel(key) {
  if (typeof key === "symbol") return "SYMBOL";
  const label = String(key).replace(/[^A-Za-z0-9_]/g, "_").slice(0, 32);
  return label === "" ? "UNSAFE" : label;
}

// A plain record-like object: Object.prototype or null prototype only. Arrays,
// Maps, Sets, class instances, Dates, typed arrays, and every other
// prototype-exotic carrier are excluded.
function isPlainRecord(value) {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return false;
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

// Kept local (a duplicate of the material snapshot module's private
// predicate) on purpose: the generic appearance authority must stay byte-for-
// byte untouched so its invariant cannot regress as a side effect of this
// boundary.
function isEmptyPlainRecord(value) {
  return isPlainRecord(value) && Reflect.ownKeys(value).length === 0;
}

// Bounded JSON-like data contract. Accepts null / boolean / string / finite
// number / array / plain record and nothing else.
function assertInertValue(value, keyLabel, budget, depth, path) {
  budget.remaining -= 1;
  if (budget.remaining < 0) reject("GENERATOR_MATERIAL_METADATA_BOUNDS_EXCEEDED");
  if (value === null) return;
  const kind = typeof value;
  if (kind === "boolean") return;
  if (kind === "string") {
    if (value.length > MAX_METADATA_STRING_LENGTH) reject("GENERATOR_MATERIAL_METADATA_BOUNDS_EXCEEDED");
    return;
  }
  if (kind === "number") {
    // NaN and +/-Infinity are rejected: `json_literal` in the pinned generator
    // is a bare `json.dumps`, which emits `NaN`/`Infinity` as live JS
    // identifiers, so a non-finite spec value would really arrive here.
    if (!Number.isFinite(value)) reject(`GENERATOR_MATERIAL_METADATA_NON_INERT_VALUE:${keyLabel}`);
    return;
  }
  if (kind !== "object") {
    // function, bigint, symbol, undefined
    reject(`GENERATOR_MATERIAL_METADATA_NON_INERT_VALUE:${keyLabel}`);
  }
  if (path.has(value)) reject("GENERATOR_MATERIAL_METADATA_CYCLIC");
  if (depth >= MAX_METADATA_DEPTH) reject("GENERATOR_MATERIAL_METADATA_BOUNDS_EXCEEDED");
  path.add(value);
  try {
    if (Array.isArray(value)) {
      for (const item of value) assertInertValue(item, keyLabel, budget, depth + 1, path);
      return;
    }
    if (!isPlainRecord(value)) reject(`GENERATOR_MATERIAL_METADATA_NON_INERT_VALUE:${keyLabel}`);
    for (const ownKey of Reflect.ownKeys(value)) {
      // A nested symbol key or accessor is not inert JSON data either.
      if (typeof ownKey !== "string") reject(`GENERATOR_MATERIAL_METADATA_NON_INERT_VALUE:${keyLabel}`);
      const descriptor = Object.getOwnPropertyDescriptor(value, ownKey);
      if (!descriptor.enumerable || descriptor.get !== undefined || descriptor.set !== undefined) {
        reject(`GENERATOR_MATERIAL_METADATA_NON_INERT_VALUE:${keyLabel}`);
      }
      assertInertValue(descriptor.value, keyLabel, budget, depth + 1, path);
    }
  } finally {
    path.delete(value);
  }
}

/**
 * Separate verified-generator non-appearance metadata from a live material.
 *
 * Returns `{ present, keys, restore }`:
 *
 *   - `present: false` for the runtime-default empty plain userData record.
 *     Nothing is detached, so the generic material snapshot applies its own
 *     two-empty-plain-records DEFAULT rule exactly as before.
 *   - `present: true` once, and only once, every own key is an expected
 *     generator metadata key and every value is inert bounded JSON data. The
 *     userData is detached (replaced with an empty plain record) so the
 *     generic appearance snapshot provably never observes it, and `keys`
 *     carries the sorted exact key list for bake attestation.
 *
 * Throws an Error carrying `code` on every other input. `restore()` puts the
 * original record back, so the material is not left mutated.
 */
export function separateGeneratorMaterialMetadata(material) {
  const untouched = { present: false, classification: null, keys: [], restore() {} };
  if (!material || typeof material !== "object") return untouched;
  const userData = material.userData;
  if (isEmptyPlainRecord(userData)) return untouched;

  if (!isPlainRecord(userData)) reject("GENERATOR_MATERIAL_METADATA_NOT_PLAIN_RECORD");

  const budget = { remaining: MAX_METADATA_NODES };
  const path = new Set();
  for (const key of Reflect.ownKeys(userData)) {
    if (typeof key !== "string" || !GENERATOR_MATERIAL_METADATA_KEYS.has(key)) {
      reject(`GENERATOR_MATERIAL_METADATA_UNKNOWN_KEY:${safeLabel(key)}`);
    }
    const descriptor = Object.getOwnPropertyDescriptor(userData, key);
    if (!descriptor.enumerable || descriptor.get !== undefined || descriptor.set !== undefined) {
      reject(`GENERATOR_MATERIAL_METADATA_HIDDEN_KEY:${safeLabel(key)}`);
    }
    assertInertValue(descriptor.value, safeLabel(key), budget, 0, path);
  }

  const keys = [...Reflect.ownKeys(userData)].sort();
  const original = userData;
  material.userData = {};
  return {
    present: true,
    classification: GENERATOR_NON_APPEARANCE_METADATA,
    keys,
    restore() {
      material.userData = original;
    },
  };
}
