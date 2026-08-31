// P2P-IMG2THREEJS-MATERIAL-DEFAULT-NONFINITE-01 — material snapshot semantics.
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

class FakeStandardMaterial {
  constructor() {
    this.type = "MeshStandardMaterial";
    this.color = new FakeColor(1, 1, 1);
    this.opacity = 1.0;
    this.metalness = 0.0;
    this.roughness = 1.0;
  }
}

class FakeBasicMaterial {
  constructor() {
    this.type = "MeshBasicMaterial";
    this.color = new FakeColor(1, 1, 1);
    this.opacity = 1.0;
  }
}

class FakePhysicalMaterial {
  constructor() {
    this.type = "MeshPhysicalMaterial";
    this.color = new FakeColor(1, 1, 1);
    this.opacity = 1.0;
    this.metalness = 0.0;
    this.roughness = 1.0;
    // runtime defaults (three r169 MeshPhysicalMaterial)
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
  const snapshot = materialSnapshot(new FakePhysicalMaterial());
  assert.equal(snapshot.type, "MeshPhysicalMaterial");
  assert.deepEqual(snapshot.drift, []);
  assert.equal(hasDrift(snapshot, "attenuationDistance"), false);
  // a sanitized, default-Infinity runtime value is never laundered into a
  // MaterialNonFinite failure and never leaks into the drift list.
  const nonFiniteEntries = snapshot.drift.filter((entry) => entry[1] === Infinity);
  assert.deepEqual(nonFiniteEntries, []);
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
