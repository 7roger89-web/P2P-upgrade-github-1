// P2P-IMG2THREEJS-GENERATOR-USERDATA-BOUNDARY-01 — static projection harness
// boundary tests.
//
// Exercises the REAL harness process (`img2threejs_static_projection_harness.mjs`)
// end to end: real module imports, real generator-metadata classification, real
// generic material snapshot, real bake manifest write.
//
// It does NOT use a real THREE runtime. The harness only reads
// `THREE.REVISION` and `THREE.Object3D.DEFAULT_UP`, so a two-field stub module
// is a faithful stand-in for the gate, and a stub factory returns plain
// Object3D/Mesh-shaped records carrying a real runtime-default material class.
// No dependency is installed and no external runtime proof is claimed.
//
//   EXTERNAL_IMG2THREEJS_RUNTIME_PROVEN=NO
//
// The stub THREE module and stub factory are written into a fresh temporary
// directory per run rather than committed as repo fixtures, so no stub can be
// mistaken for a THREE runtime pin.

import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import assert from "node:assert/strict";

const HARNESS = resolve(dirname(fileURLToPath(import.meta.url)), "..", "img2threejs_static_projection_harness.mjs");

const THREE_STUB = `export const REVISION = "169";
export const Object3D = { DEFAULT_UP: { x: 0, y: 1, z: 0 } };
`;

// A stub factory whose material carries exactly the eight generator-owned
// records the pinned generator writes inside `createSculptMaterial`.
const GENERATOR_USERDATA_LITERAL = `{
    sculptMaterial: { albedo: { base: "#4a3b2c" }, roughness: { base: 0.76 } },
    proceduralMapsIndependent: true,
    pbrConstraints: { albedoRange: [30, 240], binaryMetalness: true, f0Range: [0.02, 1], iorRange: [1, 2.5] },
    pbrTextureSource: "flat-fallback",
    referencePbr: null,
    referenceMaterialId: null,
    materialEvidence: null,
    validationViews: [],
  }`;

function factorySource({ userDataExpression, transmission = "0", clearcoat = "0", attenuationDistance = "Infinity", restoreMarker = null, extraMeshes = [] }) {
  const meshSpecs = [{ userDataExpression, transmission, clearcoat, attenuationDistance, restoreMarker }, ...extraMeshes];
  const meshBlocks = meshSpecs
    .map((spec) => {
      // When a restore marker is requested, `userData` becomes an accessor
      // AFTER the generator-shaped record is assigned, so the marker line is
      // emitted exactly when the harness's separation.restore() re-assigns
      // the ORIGINAL record (identified by its sculptMaterial key) — never at
      // setup and never for the detached empty record. Reading marker order
      // against the terminal fail line in stdout observes restore-before-exit.
      const observe = spec.restoreMarker
        ? `  {
    let live = material.userData;
    Object.defineProperty(material, "userData", {
      get() { return live; },
      set(value) {
        live = value;
        if (value && typeof value === "object" && "sculptMaterial" in value) {
          process.stdout.write(${JSON.stringify(spec.restoreMarker)} + "\\n");
        }
      },
    });
  }
`
        : "";
      return `  {
  const material = new StubPhysicalMaterial();
  material.transmission = ${spec.transmission ?? "0"};
  material.clearcoat = ${spec.clearcoat ?? "0"};
  material.attenuationDistance = ${spec.attenuationDistance ?? "Infinity"};
  material.userData = ${spec.userDataExpression};
${observe}  meshes.push(makeStubMesh(material));
  }
`;
    })
    .join("");
  return `class StubColor {
  constructor() {
    this.isColor = true;
    this.r = 1;
    this.g = 1;
    this.b = 1;
  }

  getHex() {
    return 0xffffff;
  }
}

class StubPhysicalMaterial {
  constructor() {
    this.type = "MeshPhysicalMaterial";
    this.color = new StubColor();
    this.opacity = 1;
    this.metalness = 0;
    this.roughness = 1;
    this.userData = {};
    this.transmission = 0;
    this.clearcoat = 0;
    this.sheen = 0;
    this.thickness = 0;
    this.iridescence = 0;
    this.specularIntensity = 1;
    this.attenuationDistance = Infinity;
    this.attenuationColor = new StubColor();
  }
}

const identity = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];

function makeStubMesh(material) {
  const geometry = {
    type: "BufferGeometry",
    morphAttributes: {},
    attributes: {},
    getAttribute(name) {
      if (name !== "position") return null;
      return { array: new Float32Array([0, 0, 0, 1, 0, 0, 0, 1, 0]), itemSize: 3 };
    },
    getIndex() {
      return null;
    },
  };
  return { isObject3D: true, isMesh: true, visible: true, matrix: { elements: identity }, geometry, material, children: [] };
}

export function createStubModel() {
  const meshes = [];
${meshBlocks}  return {
    isObject3D: true,
    isGroup: true,
    type: "Group",
    visible: true,
    matrix: { elements: identity },
    children: meshes,
    updateMatrixWorld() {},
  };
}
`;
}

function runHarness({ userDataExpression, transmission = "0", clearcoat = "0", attenuationDistance = "Infinity", restoreMarker = null, extraMeshes = [] }) {
  const directory = mkdtempSync(join(tmpdir(), "p2p-generator-userdata-"));
  try {
    const factory = join(directory, "factory.mjs");
    const three = join(directory, "three.module.js");
    const out = join(directory, "bake-manifest.json");
    writeFileSync(three, THREE_STUB, "utf8");
    writeFileSync(factory, factorySource({ userDataExpression, transmission, clearcoat, attenuationDistance, restoreMarker, extraMeshes }), "utf8");
    const result = spawnSync(
      process.execPath,
      [HARNESS, "--factory", factory, "--out", out, "--three-entry", three],
      { encoding: "utf8" },
    );
    let manifest = null;
    try {
      manifest = JSON.parse(readFileSync(out, "utf8"));
    } catch {
      manifest = null;
    }
    return {
      status: result.status,
      stdout: result.stdout || "",
      stderr: result.stderr || "",
      manifest,
    };
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
}

const EXPECTED_KEYS = [
  "materialEvidence",
  "pbrConstraints",
  "pbrTextureSource",
  "proceduralMapsIndependent",
  "referenceMaterialId",
  "referencePbr",
  "sculptMaterial",
  "validationViews",
].sort();

// --- 3. generated-metadata separation records bake attestation ------------

test("verified-generator metadata is separated and attested in the bake manifest", () => {
  const run = runHarness({ userDataExpression: GENERATOR_USERDATA_LITERAL });
  assert.equal(run.status, 0, run.stderr);
  assert.match(run.stdout, /P2P_IMG2THREEJS_BAKE_OK nodes=2/);

  const attestation = run.manifest.generator_material_metadata;
  assert.equal(attestation.present, true);
  assert.deepEqual(attestation.keys, EXPECTED_KEYS);

  // the separation let a default-appearance material through untouched
  const material = run.manifest.nodes.find((node) => node.kind === "mesh").mesh.material;
  assert.equal(material.type, "MeshPhysicalMaterial");
  assert.deepEqual(material.drift, []);
  // separated metadata is attested, never projected into the material contract
  assert.equal("userData" in material, false);
  assert.equal(JSON.stringify(material).includes("sculptMaterial"), false);
  // the factory SHA binding still anchors the manifest
  assert.match(run.manifest.factory_sha256, /^[0-9a-f]{64}$/);
});

// --- 4. arbitrary non-empty userData still fails closed through the harness

test("arbitrary {customTag:\"x\"} userData fails the bake closed with an explicit code", () => {
  const run = runHarness({ userDataExpression: '{ customTag: "x" }' });
  assert.equal(run.status, 1);
  assert.match(run.stdout, /P2P_IMG2THREEJS_BAKE_FAIL GENERATOR_MATERIAL_METADATA_UNKNOWN_KEY:customTag/);
  assert.equal(run.manifest, null);
});

// --- 5. expected keys + one unknown key fails closed ----------------------

test("expected generator keys plus one unknown key fails the bake closed", () => {
  const run = runHarness({
    userDataExpression: `{ ...(${GENERATOR_USERDATA_LITERAL}), customTag: "x" }`,
  });
  assert.equal(run.status, 1);
  assert.match(run.stdout, /P2P_IMG2THREEJS_BAKE_FAIL GENERATOR_MATERIAL_METADATA_UNKNOWN_KEY:customTag/);
});

// --- 6. non-plain / hidden / cyclic / non-finite metadata fails closed -----

test("non-plain, hidden-key, cyclic and non-finite metadata fail the bake closed", () => {
  const cases = [
    ['new Map([["sculptMaterial", {}]])', "GENERATOR_MATERIAL_METADATA_NOT_PLAIN_RECORD"],
    ["[{ sculptMaterial: {} }]", "GENERATOR_MATERIAL_METADATA_NOT_PLAIN_RECORD"],
    ["(() => { const value = {}; value[Symbol(\"k\")] = 1; return value; })()", "GENERATOR_MATERIAL_METADATA_UNKNOWN_KEY:SYMBOL"],
    ["(() => { const value = { sculptMaterial: {} }; Object.defineProperty(value, \"materialEvidence\", { value: 1 }); return value; })()", "GENERATOR_MATERIAL_METADATA_HIDDEN_KEY:materialEvidence"],
    ["(() => { const value = {}; value.sculptMaterial = { self: value }; return value; })()", "GENERATOR_MATERIAL_METADATA_CYCLIC"],
    ['{ sculptMaterial: () => 1 }', "GENERATOR_MATERIAL_METADATA_NON_INERT_VALUE:sculptMaterial"],
    ["{ sculptMaterial: { base: NaN } }", "GENERATOR_MATERIAL_METADATA_NON_INERT_VALUE:sculptMaterial"],
    ["{ sculptMaterial: { base: Infinity } }", "GENERATOR_MATERIAL_METADATA_NON_INERT_VALUE:sculptMaterial"],
    ["{ sculptMaterial: { set: new Set([1]) } }", "GENERATOR_MATERIAL_METADATA_NON_INERT_VALUE:sculptMaterial"],
  ];
  for (const [expression, expected] of cases) {
    const run = runHarness({ userDataExpression: expression });
    assert.equal(run.status, 1, expression);
    assert.ok(
      run.stdout.includes(`P2P_IMG2THREEJS_BAKE_FAIL ${expected}`),
      `${expression} -> expected ${expected}, got ${JSON.stringify(run.stdout)}`,
    );
    assert.equal(run.manifest, null, expression);
  }
});

// --- empty default userData keeps the generic rule and attests absent ------

test("empty default userData attests absent and still bakes", () => {
  const run = runHarness({ userDataExpression: "{}" });
  assert.equal(run.status, 0, run.stderr);
  const attestation = run.manifest.generator_material_metadata;
  assert.equal(attestation.present, false);
  assert.deepEqual(attestation.keys, []);
  const material = run.manifest.nodes.find((node) => node.kind === "mesh").mesh.material;
  assert.deepEqual(material.drift, []);
});

// --- 7/8/9. appearance safety survives the separation ----------------------

test("active transmission is still recorded as drift after separation", () => {
  const run = runHarness({ userDataExpression: GENERATOR_USERDATA_LITERAL, transmission: "0.4" });
  assert.equal(run.status, 0, run.stderr);
  const material = run.manifest.nodes.find((node) => node.kind === "mesh").mesh.material;
  assert.deepEqual(
    material.drift.find((entry) => entry[0] === "transmission"),
    ["transmission", 0.4],
  );
  // userData separation did not suppress the live appearance drift
  assert.equal(material.drift.some((entry) => entry[0] === "userData"), false);
});

test("active clearcoat is still recorded as drift after separation", () => {
  const run = runHarness({ userDataExpression: GENERATOR_USERDATA_LITERAL, clearcoat: "1.0" });
  assert.equal(run.status, 0, run.stderr);
  const material = run.manifest.nodes.find((node) => node.kind === "mesh").mesh.material;
  assert.deepEqual(
    material.drift.find((entry) => entry[0] === "clearcoat"),
    ["clearcoat", 1.0],
  );
  assert.equal(material.drift.some((entry) => entry[0] === "userData"), false);
});

test("default attenuationDistance=Infinity still bakes clean with metadata separated", () => {
  const run = runHarness({ userDataExpression: GENERATOR_USERDATA_LITERAL });
  assert.equal(run.status, 0, run.stderr);
  const material = run.manifest.nodes.find((node) => node.kind === "mesh").mesh.material;
  // the runtime-default Infinity is classified DEFAULT: no drift entry at all,
  // and nothing non-finite leaks into the baked material record
  assert.deepEqual(material.drift, []);
  assert.equal(JSON.stringify(material).includes("Infinity"), false);
});

// --- 10. restore is guaranteed BEFORE the terminal fail line ----------------
//
// Regression for the snapshotMaterial control-flow defect: fail() exits the
// process synchronously (process.exit does not unwind `finally`), so a
// materialSnapshot rejection used to terminate the process with the generator
// metadata still detached. These tests observe separation.restore() through a
// userData accessor in the stub factory that prints a marker line exactly when
// the ORIGINAL generator record is re-assigned, and compare stdout ordering
// against the terminal fail line.

test("materialSnapshot rejection restores generator userData BEFORE the terminal fail line", () => {
  const run = runHarness({
    userDataExpression: GENERATOR_USERDATA_LITERAL,
    attenuationDistance: "NaN",
    restoreMarker: "P2P_TEST_USERDATA_RESTORED_M0",
  });
  // terminal process exit is still a failure with the unchanged fail code
  assert.equal(run.status, 1);
  const restoreIndex = run.stdout.indexOf("P2P_TEST_USERDATA_RESTORED_M0");
  const failIndex = run.stdout.indexOf("P2P_IMG2THREEJS_BAKE_FAIL MATERIAL_NONFINITE:attenuationDistance");
  assert.notEqual(restoreIndex, -1, `restore marker missing: ${JSON.stringify(run.stdout)}`);
  assert.notEqual(failIndex, -1, `fail line missing: ${JSON.stringify(run.stdout)}`);
  // RESTORE_EXECUTED_BEFORE_TERMINAL_FAILURE
  assert.ok(restoreIndex < failIndex, `restore must precede terminal failure: ${JSON.stringify(run.stdout)}`);
  // fail-closed: no bake manifest is written
  assert.equal(run.manifest, null);
});

test("success path still restores the original generator userData", () => {
  const run = runHarness({
    userDataExpression: GENERATOR_USERDATA_LITERAL,
    restoreMarker: "P2P_TEST_USERDATA_RESTORED_M0",
  });
  assert.equal(run.status, 0, run.stderr);
  const restoreIndex = run.stdout.indexOf("P2P_TEST_USERDATA_RESTORED_M0");
  const okIndex = run.stdout.indexOf("P2P_IMG2THREEJS_BAKE_OK");
  assert.notEqual(restoreIndex, -1);
  assert.ok(restoreIndex < okIndex);
  // attestation and manifest are unchanged by the observability hook
  assert.equal(run.manifest.generator_material_metadata.present, true);
  assert.deepEqual(run.manifest.generator_material_metadata.keys, EXPECTED_KEYS);
});

test("multiple materials: earlier material restored on success, failing material restored before terminal failure", () => {
  const run = runHarness({
    userDataExpression: GENERATOR_USERDATA_LITERAL,
    restoreMarker: "P2P_TEST_USERDATA_RESTORED_M0",
    extraMeshes: [
      {
        userDataExpression: GENERATOR_USERDATA_LITERAL,
        attenuationDistance: "NaN",
        restoreMarker: "P2P_TEST_USERDATA_RESTORED_M1",
      },
    ],
  });
  assert.equal(run.status, 1);
  const firstRestore = run.stdout.indexOf("P2P_TEST_USERDATA_RESTORED_M0");
  const secondRestore = run.stdout.indexOf("P2P_TEST_USERDATA_RESTORED_M1");
  const failIndex = run.stdout.indexOf("P2P_IMG2THREEJS_BAKE_FAIL MATERIAL_NONFINITE:attenuationDistance");
  assert.notEqual(firstRestore, -1, `first restore marker missing: ${JSON.stringify(run.stdout)}`);
  assert.notEqual(secondRestore, -1, `second restore marker missing: ${JSON.stringify(run.stdout)}`);
  assert.notEqual(failIndex, -1);
  // both materials were restored, and the failing one before the terminal line
  assert.ok(firstRestore < secondRestore);
  assert.ok(secondRestore < failIndex);
  assert.equal(run.manifest, null);
});
