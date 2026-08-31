// P2P-IMG2THREEJS-MATERIAL-DEFAULT-NONFINITE-01 / P2P-IMG2THREEJS-MATERIAL-DEFAULT-USERDATA-01
// — material snapshot semantics.
//
// Unit-tests the standalone material snapshot module WITHOUT a real THREE
// runtime. The module is intentionally free of `process.exit` and only needs a
// material-object-shaped value carrying a real runtime-default constructor, so
// a bounded fake class with the same own-property surface (and a constructor
// that yields the class's own runtime defaults) is a faithful stand-in for the
// real class. No external runtime proof is claimed here.
//
//   EXTERNAL_IMG2THREEJS_RUNTIME_PROVEN=NO
//   (runtime smoke belongs to the later Owner-side run against the verified
//    runtime profile)

import { test } from "node:test";
import assert from "node:assert/strict";

import {
  materialSnapshot,
  SUPPORTED_MATERIAL_TYPES,
  PROJECTED_MATERIAL_KEYS,
} from "../img2threejs_material_snapshot.mjs";

class FakeColor {
  constructor(r = 1, g = 1, b = 1) {
    this.isColor = true;
    this.r = r;
    this.g = g;
    this.b = b;
  }

  getHex() {
    return Math.round(this.r * 255) * 0x10000 + Math.round(this.g * 255) * 0x100 + Math.round(this.b * 255);
  }
}

// Stand-in for THREE.Euler (r169 default: (0, 0, 0, "XYZ")).
class FakeEuler {
  constructor(x = 0, y = 0, z = 0, order = "XYZ") {
    this.isEuler = true;
    this.x = x;
    this.y = y;
    this.z = z;
    this.order = order;
  }
}

class FakeStandardMaterial {
  constructor() {
    this.type = "MeshStandardMaterial";
    this.color = new FakeColor(1, 1, 1);
    this.opacity = 1.0;
    this.metalness = 0.0;
    this.roughness = 1.0;
    // three's base Material constructor allocates a fresh empty record per
    // instance; the snapshot baseline is an independently allocated instance.
    this.userData = {};
    // r169 runtime surface: Material bookkeeping + standard-level env fields.
    this.version = 0;
    this.envMap = null;
    this.envMapRotation = new FakeEuler();
    this.envMapIntensity = 1.0;
    this.defines = { STANDARD: "" };
  }
}

class FakeBasicMaterial {
  constructor() {
    this.type = "MeshBasicMaterial";
    this.color = new FakeColor(1, 1, 1);
    this.opacity = 1.0;
    this.userData = {};
  }
}

class FakePhysicalMaterial {
  constructor() {
    this.type = "MeshPhysicalMaterial";
    this.color = new FakeColor(1, 1, 1);
    this.opacity = 1.0;
    this.metalness = 0.0;
    this.roughness = 1.0;
    this.userData = {};
    // r169 Material bookkeeping + standard/physical runtime surface. These
    // independently allocated defaults (version counter, defines record,
    // envMap Euler, iridescence range, inactive-feature companions) must be
    // semantically normalized and never create identity-only drift.
    this.version = 0;
    this.envMap = null;
    this.envMapRotation = new FakeEuler();
    this.envMapIntensity = 1.0;
    this.defines = { STANDARD: "", PHYSICAL: "" };
    // runtime defaults (three r169 MeshPhysicalMaterial)
    this.transmission = 0.0;
    this.clearcoat = 0.0;
    this.clearcoatRoughness = 0.0;
    this.sheen = 0.0;
    this.sheenColor = new FakeColor(0, 0, 0);
    this.iridescence = 0.0;
    this.iridescenceThicknessRange = [100, 400];
    this.thickness = 0.0;
    this.specularIntensity = 1.0;
    this.attenuationDistance = Infinity;
    this.attenuationColor = new FakeColor(1, 1, 1);
  }
}

function hasDrift(snapshot, key) {
  return snapshot.drift.some((entry) => entry[0] === key);
}

test("supported material types and projected key set are not expanded", () => {
  assert.deepEqual(
    [...SUPPORTED_MATERIAL_TYPES].sort(),
    [
      "MeshBasicMaterial",
      "MeshLambertMaterial",
      "MeshPhongMaterial",
      "MeshStandardMaterial",
      "MeshPhysicalMaterial",
    ].sort(),
  );
  assert.deepEqual([...PROJECTED_MATERIAL_KEYS].sort(), ["color", "metalness", "opacity", "roughness"]);
});

test("default MeshStandardMaterial is written with empty drift", () => {
  const snapshot = materialSnapshot(new FakeStandardMaterial());
  assert.equal(snapshot.type, "MeshStandardMaterial");
  assert.deepEqual(snapshot.color, [1.0, 1.0, 1.0]);
  assert.equal(snapshot.opacity, 1.0);
  assert.equal(snapshot.metalness, 0.0);
  assert.equal(snapshot.roughness, 1.0);
  assert.deepEqual(snapshot.drift, []);
  // the per-instance empty userData record is not a drift entry
  assert.equal(hasDrift(snapshot, "userData"), false);
});

test("default MeshBasicMaterial omits metalness/roughness projected fields", () => {
  const snapshot = materialSnapshot(new FakeBasicMaterial());
  assert.equal(snapshot.type, "MeshBasicMaterial");
  assert.deepEqual(snapshot.color, [1.0, 1.0, 1.0]);
  assert.equal(snapshot.opacity, 1.0);
  assert.equal("metalness" in snapshot, false);
  assert.equal("roughness" in snapshot, false);
  assert.deepEqual(snapshot.drift, []);
});

test("non-default color is recorded as drift", () => {
  const material = new FakeStandardMaterial();
  material.color = new FakeColor(1, 0, 0);
  const snapshot = materialSnapshot(material);
  assert.deepEqual(snapshot.color, [1.0, 0.0, 0.0]);
  assert.equal(hasDrift(snapshot, "color"), true);
});

test("default-Infinity attenuationDistance is accepted as DEFAULT with no drift or non-finite entry", () => {
  // regression: the numeric default-Infinity must be compared against the
  // runtime default BEFORE the generic non-finite rejection, so a MeshPhysical
  // material whose only physical semantics are its own defaults survives.
  const material = new FakePhysicalMaterial();
  material.userData = {}; // reallocate: two independently created empty records
  const snapshot = materialSnapshot(material);
  assert.equal(snapshot.type, "MeshPhysicalMaterial");
  assert.deepEqual(snapshot.drift, []);
  assert.equal(hasDrift(snapshot, "attenuationDistance"), false);
  assert.equal(hasDrift(snapshot, "userData"), false);
  // a sanitized, default-Infinity runtime value is never laundered into a
  // MaterialNonFinite failure and never leaks into the drift list.
  const nonFiniteEntries = snapshot.drift.filter((entry) => entry[1] === Infinity);
  assert.deepEqual(nonFiniteEntries, []);
});

test("two separately allocated empty default userData records never create drift", () => {
  // regression: `value !== base` identity comparison used to classify two
  // independently created empty `userData = {}` objects as drift even though
  // no material appearance feature is active.
  const material = new FakeStandardMaterial();
  material.userData = {}; // distinct object identity from the constructor baseline
  const snapshot = materialSnapshot(material);
  assert.deepEqual(snapshot.drift, []);
  assert.equal(hasDrift(snapshot, "userData"), false);
});

test("non-empty runtime userData while baseline is empty remains drift (fail-closed)", () => {
  const material = new FakeStandardMaterial();
  material.userData = { customTag: "unique-id" };
  const snapshot = materialSnapshot(material);
  assert.deepEqual(snapshot.drift, [["userData", "object"]]);
});

test("same non-empty userData identity still emits drift (fail-closed)", () => {
  // Regression: the DEFAULT exception is strictly "two empty plain records".
  // If the live material and the constructor baseline happen to share the
  // SAME non-empty userData object, reference equality must not silence the
  // drift — non-empty metadata remains fail-closed either way.
  const shared = { customTag: "shared-id" };
  class SharedUserDataMaterial extends FakeStandardMaterial {
    constructor() {
      super();
      this.userData = shared;
    }
  }
  const snapshot = materialSnapshot(new SharedUserDataMaterial());
  assert.deepEqual(snapshot.drift, [["userData", "object"]]);
});

test("non-plain or hidden-key userData remains drift (fail-closed)", () => {
  const variants = [
    ["Map", new Map([["k", "v"]])],
    ["class instance", new (class Wrapper {})()],
    ["symbol key", (() => { const value = {}; value[Symbol("k")] = 1; return value; })()],
    ["non-enumerable key", (() => { const value = {}; Object.defineProperty(value, "hidden", { value: 1 }); return value; })()],
  ];
  for (const [label, userData] of variants) {
    const material = new FakeStandardMaterial();
    material.userData = userData;
    const snapshot = materialSnapshot(material);
    assert.equal(hasDrift(snapshot, "userData"), true, label);
  }
});

test("active finite attenuationDistance is recorded as drift (fail-closed downstream)", () => {
  const material = new FakePhysicalMaterial();
  material.attenuationDistance = 2.5;
  const snapshot = materialSnapshot(material);
  assert.equal(hasDrift(snapshot, "attenuationDistance"), true);
  assert.deepEqual(
    snapshot.drift.find((entry) => entry[0] === "attenuationDistance"),
    ["attenuationDistance", 2.5],
  );
});

test("NaN attenuationDistance is a hard reject (never a valid default)", () => {
  const material = new FakePhysicalMaterial();
  material.attenuationDistance = NaN;
  assert.throws(
    () => materialSnapshot(material),
    (error) => error.code === "MATERIAL_NONFINITE:attenuationDistance",
  );
});

test("non-default -Infinity attenuationDistance is a hard reject", () => {
  // only the exact runtime default (+Infinity) may pass as DEFAULT; any other
  // non-finite value must still hit the finite-only rejection.
  const material = new FakePhysicalMaterial();
  material.attenuationDistance = -Infinity;
  assert.throws(
    () => materialSnapshot(material),
    (error) => error.code === "MATERIAL_NONFINITE:attenuationDistance",
  );
});

test("supported projected field NaN is a hard reject", () => {
  const material = new FakeStandardMaterial();
  material.opacity = NaN;
  assert.throws(
    () => materialSnapshot(material),
    (error) => error.code === "MATERIAL_NONFINITE:opacity",
  );
});

test("supported projected field Infinity is a hard reject", () => {
  const material = new FakeStandardMaterial();
  material.metalness = Infinity;
  assert.throws(
    () => materialSnapshot(material),
    (error) => error.code === "MATERIAL_NONFINITE:metalness",
  );
});

test("non-finite color channel is a hard reject", () => {
  const material = new FakeStandardMaterial();
  material.color = new FakeColor(NaN, 1, 1);
  assert.throws(
    () => materialSnapshot(material),
    (error) => error.code === "MATERIAL_COLOR_NONFINITE",
  );
});

test("active transmission/clearcoat remain recorded as drift (fail-closed downstream)", () => {
  const transmissionMaterial = new FakePhysicalMaterial();
  transmissionMaterial.transmission = 0.4;
  const transmissionSnapshot = materialSnapshot(transmissionMaterial);
  assert.equal(hasDrift(transmissionSnapshot, "transmission"), true);

  const clearcoatMaterial = new FakePhysicalMaterial();
  clearcoatMaterial.clearcoat = 1.0;
  const clearcoatSnapshot = materialSnapshot(clearcoatMaterial);
  assert.equal(hasDrift(clearcoatSnapshot, "clearcoat"), true);
});

// ---------------------------------------------------------------------------
// P2P-IMG2THREEJS-MATERIAL-SEMANTIC-DRIFT-01 — bounded semantic normalization.
//
// These tests cover the exact production PR39 material drift inventory. The
// fix classifies identity-only bookkeeping and inactive-feature companions as
// default-equivalent WITHOUT expanding material support or PROJECTED keys:
// color/roughness stay projected drift; every other active feature still
// fails closed through the ordinary appearance/texture gates.
// ---------------------------------------------------------------------------

test("full production inventory: only color and roughness survive normalization", () => {
  // Exact representative positive material state from the live PR39 smoke:
  // version bumped by needsUpdate; independently allocated default defines /
  // envMapRotation / iridescenceThicknessRange; envMapIntensity/
  // clearcoatRoughness/sheenColor non-default while their controlling
  // features are inactive; color non-white and roughness non-default are the
  // ONLY supported projected appearance drift.
  const material = new FakePhysicalMaterial();
  material.version = 1; // needsUpdate invalidation counter
  material.defines = { STANDARD: "", PHYSICAL: "" }; // fresh allocation, same content
  material.color = new FakeColor(0.5, 0.55, 0.6); // non-white appearance
  material.roughness = 0.75;
  material.envMap = null;
  material.envMapRotation = new FakeEuler(0, 0, 0, "XYZ"); // fresh allocation
  material.envMapIntensity = 0.8; // no envMap -> inactive companion
  material.clearcoat = 0.0;
  material.clearcoatRoughness = 0.25; // clearcoat off -> inactive companion
  material.sheen = 0.0;
  material.sheenColor = new FakeColor(1, 1, 1); // white, sheen off -> inactive companion
  material.iridescenceThicknessRange = [100, 400]; // fresh allocation, same content

  const snapshot = materialSnapshot(material);
  assert.equal(snapshot.type, "MeshPhysicalMaterial");
  assert.equal(snapshot.roughness, 0.75);
  // EXACT positive-fixture post-normalization drift — order-sensitive.
  assert.deepEqual(snapshot.drift, [
    ["color", "color"],
    ["roughness", 0.75],
  ]);
});

test("version: a valid non-negative runtime counter is ignored for appearance", () => {
  for (const version of [0, 1, 42, Number.MAX_SAFE_INTEGER]) {
    const material = new FakePhysicalMaterial();
    material.version = version;
    const snapshot = materialSnapshot(material);
    assert.deepEqual(snapshot.drift, [], `version ${version} must not drift`);
    assert.equal(hasDrift(snapshot, "version"), false);
  }
});

test("version: malformed/invalid counters fail closed hard", () => {
  const malformed = [NaN, Infinity, -Infinity, -1, 1.5, "1", null, {}, true, Number.MAX_SAFE_INTEGER + 1];
  for (const bad of malformed) {
    const material = new FakePhysicalMaterial();
    material.version = bad;
    assert.throws(
      () => materialSnapshot(material),
      (error) => error.code === "MATERIAL_VERSION_INVALID",
      `version ${String(bad)} must reject`,
    );
  }
});

test("defines: independently allocated records with identical content are default-equivalent", () => {
  const material = new FakePhysicalMaterial();
  material.defines = { STANDARD: "", PHYSICAL: "" }; // fresh object, identical content
  const snapshot = materialSnapshot(material);
  assert.deepEqual(snapshot.drift, []);
  assert.equal(hasDrift(snapshot, "defines"), false);
});

test("defines: changed content (value, extra key, missing key, non-primitive, non-plain) stays drift", () => {
  const variants = [
    ["changed value", { STANDARD: "DIFFERENT", PHYSICAL: "" }],
    ["extra key", { STANDARD: "", PHYSICAL: "", EXTRA: "" }],
    ["missing key", { STANDARD: "" }],
    ["nested object value", { STANDARD: "", PHYSICAL: { nested: true } }],
    ["symbol extra key", (() => { const d = { STANDARD: "", PHYSICAL: "" }; d[Symbol("k")] = 1; return d; })()],
    ["array", ["STANDARD", "PHYSICAL"]],
    ["class instance", new (class Defines {})()],
  ];
  for (const [label, defines] of variants) {
    const material = new FakePhysicalMaterial();
    material.defines = defines;
    const snapshot = materialSnapshot(material);
    assert.deepEqual(snapshot.drift, [["defines", "object"]], label);
  }
});

test("envMapRotation: independently allocated equal Euler is default-equivalent", () => {
  const material = new FakePhysicalMaterial();
  material.envMapRotation = new FakeEuler(0, 0, 0, "XYZ");
  const snapshot = materialSnapshot(material);
  assert.deepEqual(snapshot.drift, []);
  assert.equal(hasDrift(snapshot, "envMapRotation"), false);
});

test("envMapRotation: changed angle, order, NaN component, or non-Euler stays drift", () => {
  const variants = [
    ["rotated y", new FakeEuler(0, 0.5, 0, "XYZ")],
    ["different order", new FakeEuler(0, 0, 0, "YXZ")],
    ["NaN component", new FakeEuler(NaN, 0, 0, "XYZ")],
    ["plain object", { x: 0, y: 0, z: 0, order: "XYZ" }],
  ];
  for (const [label, rotation] of variants) {
    const material = new FakePhysicalMaterial();
    material.envMapRotation = rotation;
    const snapshot = materialSnapshot(material);
    assert.deepEqual(snapshot.drift, [["envMapRotation", "object"]], label);
  }
});

test("iridescenceThicknessRange: independently allocated equal range is default-equivalent", () => {
  const material = new FakePhysicalMaterial();
  material.iridescenceThicknessRange = [100, 400]; // fresh array, identical content
  const snapshot = materialSnapshot(material);
  assert.deepEqual(snapshot.drift, []);
  assert.equal(hasDrift(snapshot, "iridescenceThicknessRange"), false);
});

test("iridescenceThicknessRange: changed, malformed, or non-array ranges stay drift", () => {
  const variants = [
    ["changed max", [100, 401]],
    ["changed min", [101, 400]],
    ["wrong length", [100]],
    ["NaN element", [100, NaN]],
    ["non-numeric", [100, "400"]],
    ["typed array", Float32Array.from([100, 400])],
  ];
  for (const [label, range] of variants) {
    const material = new FakePhysicalMaterial();
    material.iridescenceThicknessRange = range;
    const snapshot = materialSnapshot(material);
    assert.deepEqual(snapshot.drift, [["iridescenceThicknessRange", "object"]], label);
  }
});

test("envMapIntensity: non-default with envMap=null is inactive/default-equivalent", () => {
  const material = new FakePhysicalMaterial();
  material.envMap = null;
  material.envMapIntensity = 0.8;
  const snapshot = materialSnapshot(material);
  assert.deepEqual(snapshot.drift, []);
  assert.equal(hasDrift(snapshot, "envMapIntensity"), false);
});

test("envMapIntensity: active envMap or non-finite intensity is never silently accepted", () => {
  // active envMap: the texture slot is rejected first AND the intensity is
  // recorded as numeric drift — both entries fail closed downstream.
  const active = new FakePhysicalMaterial();
  active.envMap = { isTexture: true };
  active.envMapIntensity = 0.8;
  const activeSnapshot = materialSnapshot(active);
  assert.equal(hasDrift(activeSnapshot, "envMap"), true);
  assert.equal(hasDrift(activeSnapshot, "envMapIntensity"), true);

  // a non-null non-texture envMap (malformed slot) also keeps the intensity
  // in the drift list rather than silently accepting it.
  const weird = new FakePhysicalMaterial();
  weird.envMap = { notATexture: true };
  weird.envMapIntensity = 0.8;
  assert.equal(hasDrift(materialSnapshot(weird), "envMapIntensity"), true);

  // NaN intensity can never be laundered through an inactive envMap.
  const nonFinite = new FakePhysicalMaterial();
  nonFinite.envMap = null;
  nonFinite.envMapIntensity = NaN;
  assert.throws(
    () => materialSnapshot(nonFinite),
    (error) => error.code === "MATERIAL_NONFINITE:envMapIntensity",
  );
});

test("clearcoatRoughness: non-default with clearcoat=0 is inactive/default-equivalent", () => {
  const material = new FakePhysicalMaterial();
  material.clearcoat = 0.0;
  material.clearcoatRoughness = 0.25;
  const snapshot = materialSnapshot(material);
  assert.deepEqual(snapshot.drift, []);
  assert.equal(hasDrift(snapshot, "clearcoatRoughness"), false);
});

test("clearcoatRoughness: active clearcoat keeps clearcoat and companion fail-closed drift", () => {
  const material = new FakePhysicalMaterial();
  material.clearcoat = 1.0;
  material.clearcoatRoughness = 0.25;
  const snapshot = materialSnapshot(material);
  assert.equal(hasDrift(snapshot, "clearcoat"), true);
  assert.equal(hasDrift(snapshot, "clearcoatRoughness"), true);

  // NaN companion value is never laundered through an inactive clearcoat.
  const nonFinite = new FakePhysicalMaterial();
  nonFinite.clearcoat = 0.0;
  nonFinite.clearcoatRoughness = NaN;
  assert.throws(
    () => materialSnapshot(nonFinite),
    (error) => error.code === "MATERIAL_NONFINITE:clearcoatRoughness",
  );
});

test("sheenColor: non-default color with sheen=0 is inactive/default-equivalent", () => {
  const material = new FakePhysicalMaterial();
  material.sheen = 0.0;
  material.sheenColor = new FakeColor(1, 1, 1); // white vs default black
  const snapshot = materialSnapshot(material);
  assert.deepEqual(snapshot.drift, []);
  assert.equal(hasDrift(snapshot, "sheenColor"), false);
});

test("sheenColor: active sheen keeps the color drift fail-closed", () => {
  const material = new FakePhysicalMaterial();
  material.sheen = 1.0;
  material.sheenColor = new FakeColor(1, 1, 1);
  const snapshot = materialSnapshot(material);
  assert.equal(hasDrift(snapshot, "sheen"), true);
  assert.deepEqual(
    snapshot.drift.find((entry) => entry[0] === "sheenColor"),
    ["sheenColor", "color"],
  );

  // a sheen color texture slot while sheen is off is still a texture drift
  // (texture gate precedes the inactive-companion skip).
  const textured = new FakePhysicalMaterial();
  textured.sheen = 0.0;
  textured.sheenColor = { isTexture: true };
  assert.equal(hasDrift(materialSnapshot(textured), "sheenColor"), true);
});

test("semantic normalization never expands the projected key set", () => {
  assert.deepEqual([...PROJECTED_MATERIAL_KEYS].sort(), ["color", "metalness", "opacity", "roughness"]);
  for (const normalizedKey of ["version", "defines", "envMapRotation", "envMapIntensity", "clearcoatRoughness", "sheenColor", "iridescenceThicknessRange"]) {
    assert.equal(PROJECTED_MATERIAL_KEYS.has(normalizedKey), false, `${normalizedKey} must not be projected`);
  }
});
