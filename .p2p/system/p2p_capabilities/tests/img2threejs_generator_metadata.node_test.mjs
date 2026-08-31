// P2P-IMG2THREEJS-GENERATOR-USERDATA-BOUNDARY-01 — generator-owned
// non-appearance Material.userData separation.
//
// Unit-tests the generator/harness boundary classifier WITHOUT a real THREE
// runtime, plus its composition with the UNCHANGED generic material snapshot
// module. A bounded fake material class carrying a real runtime-default
// constructor is the same faithful stand-in the existing material snapshot
// suite already uses. No external runtime proof is claimed here.
//
//   EXTERNAL_IMG2THREEJS_RUNTIME_PROVEN=NO

import { test } from "node:test";
import assert from "node:assert/strict";

import {
  GENERATOR_MATERIAL_METADATA_KEYS,
  GENERATOR_NON_APPEARANCE_METADATA,
  separateGeneratorMaterialMetadata,
} from "../img2threejs_generator_metadata.mjs";
import {
  materialSnapshot,
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

// three's base Material constructor allocates a fresh empty `userData = {}`
// per instance, so the snapshot baseline is an independently allocated one.
class FakePhysicalMaterial {
  constructor() {
    this.type = "MeshPhysicalMaterial";
    this.color = new FakeColor(1, 1, 1);
    this.opacity = 1.0;
    this.metalness = 0.0;
    this.roughness = 1.0;
    this.userData = {};
    this.transmission = 0.0;
    this.clearcoat = 0.0;
    this.sheen = 0.0;
    this.thickness = 0.0;
    this.iridescence = 0.0;
    this.specularIntensity = 1.0;
    this.attenuationDistance = Infinity;
    this.attenuationColor = new FakeColor(1, 1, 1);
  }
}

// Exactly the eight records the pinned generator
// (`forge/stage3_build/generate_threejs_factory.py` @ dede5909be4e494b228c801a55dda47439143932)
// writes unconditionally inside `createSculptMaterial`.
function generatorMaterialUserData() {
  return {
    sculptMaterial: {
      albedo: { base: "#4a3b2c" },
      roughness: { base: 0.76 },
      metalness: { base: 0.0 },
      textureless: { declared: false },
    },
    proceduralMapsIndependent: true,
    pbrConstraints: { albedoRange: [30, 240], binaryMetalness: true, f0Range: [0.02, 1], iorRange: [1, 2.5] },
    pbrTextureSource: "flat-fallback",
    referencePbr: null,
    referenceMaterialId: null,
    materialEvidence: null,
    validationViews: [],
  };
}

function codeOf(thunk) {
  try {
    thunk();
  } catch (error) {
    return error.code;
  }
  return null;
}

// --- the verified pinned generator key universe itself --------------------

test("generator metadata key universe is exactly the pinned contract", () => {
  assert.deepEqual(
    [...GENERATOR_MATERIAL_METADATA_KEYS].sort(),
    [
      "materialEvidence",
      "pbrConstraints",
      "pbrTextureSource",
      "proceduralMapsIndependent",
      "referenceMaterialId",
      "referencePbr",
      "sculptMaterial",
      "validationViews",
    ].sort(),
  );
  // separation must never expand the generic projected surface
  assert.deepEqual([...PROJECTED_MATERIAL_KEYS].sort(), ["color", "metalness", "opacity", "roughness"]);
  assert.equal(PROJECTED_MATERIAL_KEYS.has("userData"), false);
});

// --- 2. expected keys separated before materialSnapshot ------------------

test("verified-generator metadata is separated and a default appearance material passes", () => {
  const material = new FakePhysicalMaterial();
  material.userData = generatorMaterialUserData();

  const separation = separateGeneratorMaterialMetadata(material);
  assert.equal(separation.present, true);
  assert.equal(separation.classification, GENERATOR_NON_APPEARANCE_METADATA);
  assert.deepEqual(separation.keys, [...GENERATOR_MATERIAL_METADATA_KEYS].sort());
  // detached, so the generic appearance snapshot provably never observes it
  assert.deepEqual(Reflect.ownKeys(material.userData), []);

  const snapshot = materialSnapshot(material);
  assert.equal(snapshot.type, "MeshPhysicalMaterial");
  assert.deepEqual(snapshot.drift, []);
  assert.equal(snapshot.drift.some((entry) => entry[0] === "userData"), false);

  // reversible: separation is evidence-backed, never a silent mutation
  separation.restore();
  assert.deepEqual(Reflect.ownKeys(material.userData).sort(), separation.keys);
});

test("a subset of the expected generator keys is also separated", () => {
  const material = new FakePhysicalMaterial();
  material.userData = { proceduralMapsIndependent: true, pbrTextureSource: "procedural" };
  const separation = separateGeneratorMaterialMetadata(material);
  assert.equal(separation.present, true);
  assert.deepEqual(separation.keys, ["pbrTextureSource", "proceduralMapsIndependent"]);
  assert.deepEqual(materialSnapshot(material).drift, []);
});

// --- empty default userData stays the generic module's own decision -------

test("empty default userData is left for the generic snapshot to classify", () => {
  const material = new FakePhysicalMaterial();
  const separation = separateGeneratorMaterialMetadata(material);
  assert.equal(separation.present, false);
  assert.equal(separation.classification, null);
  assert.deepEqual(separation.keys, []);
  // nothing detached: the generic two-empty-plain-records DEFAULT rule still
  // owns this case, exactly as before this boundary existed
  assert.equal(typeof material.userData, "object");
  assert.deepEqual(materialSnapshot(material).drift, []);
});

// --- 1/4. arbitrary non-empty userData ------------------------------------

test("standalone materialSnapshot still rejects arbitrary non-empty userData", () => {
  // the generic authority is UNCHANGED: no separation applied, the fail-closed
  // rule for arbitrary non-empty userData still holds on its own
  const material = new FakePhysicalMaterial();
  material.userData = { customTag: "x" };
  const snapshot = materialSnapshot(material);
  assert.deepEqual(snapshot.drift, [["userData", "object"]]);
});

test("arbitrary {customTag:\"x\"} fails closed at the classifier", () => {
  const material = new FakePhysicalMaterial();
  material.userData = { customTag: "x" };
  assert.equal(
    codeOf(() => separateGeneratorMaterialMetadata(material)),
    "GENERATOR_MATERIAL_METADATA_UNKNOWN_KEY:customTag",
  );
  // and it was NOT turned into a default
  assert.deepEqual(Reflect.ownKeys(material.userData), ["customTag"]);
});

// --- 5. known generator keys + one unknown extra key ----------------------

test("expected generator keys plus one unknown key fails closed", () => {
  const material = new FakePhysicalMaterial();
  material.userData = { ...generatorMaterialUserData(), customTag: "x" };
  assert.equal(
    codeOf(() => separateGeneratorMaterialMetadata(material)),
    "GENERATOR_MATERIAL_METADATA_UNKNOWN_KEY:customTag",
  );
});

// --- 6. symbol / hidden / non-plain / cyclic / non-finite -----------------

test("symbol-key and hidden-key metadata fail closed", () => {
  const symbolKeyed = { sculptMaterial: {} };
  symbolKeyed[Symbol("k")] = 1;
  assert.equal(
    codeOf(() => separateGeneratorMaterialMetadata({ userData: symbolKeyed })),
    "GENERATOR_MATERIAL_METADATA_UNKNOWN_KEY:SYMBOL",
  );

  const hiddenKeyed = { sculptMaterial: {} };
  Object.defineProperty(hiddenKeyed, "materialEvidence", { value: { nested: 1 }, enumerable: false });
  assert.equal(
    codeOf(() => separateGeneratorMaterialMetadata({ userData: hiddenKeyed })),
    "GENERATOR_MATERIAL_METADATA_HIDDEN_KEY:materialEvidence",
  );

  // a symbol key nested inside an otherwise valid value fails closed too
  const nestedSymbol = {};
  nestedSymbol[Symbol("deep")] = 1;
  assert.equal(
    codeOf(() => separateGeneratorMaterialMetadata({ userData: { sculptMaterial: nestedSymbol } })),
    "GENERATOR_MATERIAL_METADATA_NON_INERT_VALUE:sculptMaterial",
  );
});

test("Map / class instance / array / function top-level userData fails closed", () => {
  const variants = [
    ["Map", new Map([["sculptMaterial", {}]])],
    ["class instance", new (class Wrapper { constructor() { this.sculptMaterial = {}; } })()],
    ["array", [{ sculptMaterial: {} }]],
    ["function", () => {}],
  ];
  for (const [label, userData] of variants) {
    assert.equal(
      codeOf(() => separateGeneratorMaterialMetadata({ userData })),
      "GENERATOR_MATERIAL_METADATA_NOT_PLAIN_RECORD",
      label,
    );
  }
});

test("cyclic / function / non-finite / bigint / undefined metadata fails closed", () => {
  const cyclic = {};
  cyclic.sculptMaterial = { self: cyclic };
  assert.equal(
    codeOf(() => separateGeneratorMaterialMetadata({ userData: cyclic })),
    "GENERATOR_MATERIAL_METADATA_CYCLIC",
  );

  assert.equal(
    codeOf(() => separateGeneratorMaterialMetadata({ userData: { sculptMaterial: () => 1 } })),
    "GENERATOR_MATERIAL_METADATA_NON_INERT_VALUE:sculptMaterial",
  );

  for (const value of [NaN, Infinity, -Infinity]) {
    assert.equal(
      codeOf(() => separateGeneratorMaterialMetadata({ userData: { sculptMaterial: { base: value } } })),
      "GENERATOR_MATERIAL_METADATA_NON_INERT_VALUE:sculptMaterial",
      String(value),
    );
  }

  assert.equal(
    codeOf(() => separateGeneratorMaterialMetadata({ userData: { sculptMaterial: { base: 10n } } })),
    "GENERATOR_MATERIAL_METADATA_NON_INERT_VALUE:sculptMaterial",
  );

  assert.equal(
    codeOf(() => separateGeneratorMaterialMetadata({ userData: { referencePbr: undefined } })),
    "GENERATOR_MATERIAL_METADATA_NON_INERT_VALUE:referencePbr",
  );

  // prototype-exotic carriers inside an otherwise valid value
  assert.equal(
    codeOf(() => separateGeneratorMaterialMetadata({ userData: { sculptMaterial: { set: new Set([1]) } } })),
    "GENERATOR_MATERIAL_METADATA_NON_INERT_VALUE:sculptMaterial",
  );
  assert.equal(
    codeOf(() => separateGeneratorMaterialMetadata({ userData: { sculptMaterial: { when: new Date(0) } } })),
    "GENERATOR_MATERIAL_METADATA_NON_INERT_VALUE:sculptMaterial",
  );
});

test("metadata deeper than the bound fails closed", () => {
  let deep = { leaf: 1 };
  for (let depth = 0; depth < 40; depth += 1) deep = { next: deep };
  assert.equal(
    codeOf(() => separateGeneratorMaterialMetadata({ userData: { sculptMaterial: deep } })),
    "GENERATOR_MATERIAL_METADATA_BOUNDS_EXCEEDED",
  );
});

// --- 7/8. appearance safety is unchanged by the separation ----------------

test("active transmission still fails closed after generator metadata separation", () => {
  const material = new FakePhysicalMaterial();
  material.userData = generatorMaterialUserData();
  material.transmission = 0.4;
  const separation = separateGeneratorMaterialMetadata(material);
  assert.equal(separation.present, true);
  const snapshot = materialSnapshot(material);
  // separating userData provably does NOT launder live appearance drift
  assert.deepEqual(
    snapshot.drift.find((entry) => entry[0] === "transmission"),
    ["transmission", 0.4],
  );
  assert.equal(snapshot.drift.some((entry) => entry[0] === "userData"), false);
});

test("active clearcoat still fails closed after generator metadata separation", () => {
  const material = new FakePhysicalMaterial();
  material.userData = generatorMaterialUserData();
  material.clearcoat = 1.0;
  separateGeneratorMaterialMetadata(material);
  const snapshot = materialSnapshot(material);
  assert.deepEqual(
    snapshot.drift.find((entry) => entry[0] === "clearcoat"),
    ["clearcoat", 1.0],
  );
});

// --- 9. default Infinity behaviour preserved ------------------------------

test("default attenuationDistance=Infinity remains PASS with generator metadata separated", () => {
  const material = new FakePhysicalMaterial();
  material.userData = generatorMaterialUserData();
  assert.equal(material.attenuationDistance, Infinity);
  separateGeneratorMaterialMetadata(material);
  const snapshot = materialSnapshot(material);
  assert.deepEqual(snapshot.drift, []);
  assert.deepEqual(snapshot.drift.filter((entry) => entry[1] === Infinity), []);
});

test("NaN attenuationDistance remains a hard reject even with valid generator metadata", () => {
  const material = new FakePhysicalMaterial();
  material.userData = generatorMaterialUserData();
  material.attenuationDistance = NaN;
  separateGeneratorMaterialMetadata(material);
  assert.equal(
    codeOf(() => materialSnapshot(material)),
    "MATERIAL_NONFINITE:attenuationDistance",
  );
});

test("non-default -Infinity attenuationDistance remains a hard reject", () => {
  const material = new FakePhysicalMaterial();
  material.userData = generatorMaterialUserData();
  material.attenuationDistance = -Infinity;
  separateGeneratorMaterialMetadata(material);
  assert.equal(
    codeOf(() => materialSnapshot(material)),
    "MATERIAL_NONFINITE:attenuationDistance",
  );
});

// --- no escape hatch ------------------------------------------------------

test("the classifier exposes no bypass surface", () => {
  assert.equal(separateGeneratorMaterialMetadata.length, 1);
});
