# Three.js Production Workflow & Look-Dev

Modern production workflow reconciling 3D asset preparation, baking decisions, color management, WebGPU/TSL pipeline, and measurement-first performance.

---

## 1. Blender & Web-3D Asset Preparation

High-performance web 3D begins in the DCC (Digital Content Creation) tool (Blender, Maya, Houdini).

### GLTF / GLB Export Rules
- **Apply Transforms**: Before export, always apply Object transforms (`Ctrl + A` -> Apply All Transforms in Blender). Unapplied scales cause distorted normals and physics bounding discrepancies.
- **Pivot / Origin**: Place the object origin at its logical center or base (feet for characters, center of mass for physics props).
- **Clean Modifiers**: Apply all modifiers (Subdivision Surface, Mirror, Boolean) before export unless handled by an explicit pipeline exporter. Remove loose geometry, zero-area faces, and non-manifold edges.
- **Hierarchy Cleanliness**: Flatten nested empties where possible to minimize scene graph traversal depth.

### Geometry Compression: Draco vs Uncompressed
- **Draco Compression**:
  - Compresses vertex positions, normals, colors, and UVs (often 80-90% reduction in download size).
  - *Trade-off*: Decompression happens on the CPU on the client main thread or web worker (`DRACOLoader`).
  - *Rule*: Use Draco for complex static meshes (> 2 MB GLB) where network bandwidth is the primary bottleneck. Avoid Draco for tiny meshes (< 200 KB) where decompression overhead exceeds network transfer savings, or heavily morphed/animated skinned meshes where decompression latency stutters initialization.

### Texture Compression: KTX2 / Basis Universal
- **GPU Texture Memory Footprint**: Uncompressed PNG/JPEG textures decompress into raw RGBA in GPU VRAM (e.g., a 2048x2048 PNG is only ~2 MB on disk, but occupies **16 MB** of VRAM uncompressed).
- **KTX2 with Basis Universal**:
  - Stays compressed *in GPU VRAM* (transcoded to ASTC, BC7, or ETC on target hardware).
  - Dramatically cuts VRAM usage by 70-80% and eliminates texture upload stutter.
  - Use `KTX2Loader` with `basis_universal` transcoders.

### Texture Channel Packing (ORM Workflow)
- Pack grayscale PBR maps into a single 3-channel RGB texture:
  - **R channel**: Ambient Occlusion (AO)
  - **G channel**: Roughness
  - **B channel**: Metalness
- Reduces texture sampling passes from 3 separate textures to 1 texture fetch, cutting memory bandwidth and draw state switches.

---

## 2. Baking vs Dynamic Lighting Decision Matrix

Lighting is the highest-cost runtime rendering feature in WebGL/WebGPU.

| Scene Element | Recommended Approach | Justification |
|---|---|---|
| **Static Architecture / Environment** | **Baked Lightmaps** (`uv2` + `material.lightMap`) | Zero runtime shadow cost; captures global illumination, soft bounce light, and ambient occlusion for near-zero GPU fill overhead. |
| **Hero Characters / Movable Props** | **Dynamic Lighting + Shadows** (`DirectionalLight` + Shadow Maps) | Dynamic interaction requires real-time shadow projection and specular highlight responsiveness. |
| **Secondary NPCs / Debris** | **Contact Shadows / Blob Shadows** (`ContactShadows` or decal plane) | Eliminates costly multi-pass shadow map rendering for secondary actors. |
| **Ambient / Fill Light** | **HDR Environment Map (IBL)** (`scene.environment`) | Physically based reflections without placing dozens of expensive runtime point/spot lights. |

### Baking Implementation Pattern
```javascript
// Load mesh with second UV set for lightmap
const loader = new GLTFLoader();
loader.load('environment.glb', (gltf) => {
  const lightmap = new THREE.TextureLoader().load('environment_lightmap.jpg');
  lightmap.channel = 1; // uv2 channel
  lightmap.flipY = false;

  gltf.scene.traverse((child) => {
    if (child.isMesh) {
      child.material.lightMap = lightmap;
      child.material.lightMapIntensity = 1.0;
      child.material.needsUpdate = true;
    }
  });
  scene.add(gltf.scene);
});
```

---

## 3. Color Management, PBR & Environment Workflow

Physically Plausible Rendering (PBR) requires strict adherence to linear workflow and correct color space conversions.

### Renderer Color Space (Three.js r152+)
```javascript
// Modern standard: SRGBColorSpace (NOT deprecated sRGBEncoding)
renderer.outputColorSpace = THREE.SRGBColorSpace;
```

### Texture Color Space Conventions
- **Color Textures** (Diffuse / Albedo / BaseColor, Emissive):
  ```javascript
  diffuseMap.colorSpace = THREE.SRGBColorSpace;
  ```
- **Data Textures** (Normal, Roughness, Metalness, AO, Height):
  ```javascript
  normalMap.colorSpace = THREE.NoColorSpace; // Linear data!
  roughnessMap.colorSpace = THREE.NoColorSpace;
  ```

### Tone Mapping & Exposure
To prevent blown-out highlights and reproduce high dynamic range contrast:
```javascript
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0; // Tune to scene aesthetic
```

### Image-Based Lighting (IBL) with PMREM
```javascript
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js';

const pmremGenerator = new THREE.PMREMGenerator(renderer);
pmremGenerator.compileEquirectangularShader();

new RGBELoader().load('textures/studio_small_08_1k.hdr', (hdrTexture) => {
  const envMap = pmremGenerator.fromEquirectangular(hdrTexture).texture;
  scene.environment = envMap; // PBR ambient reflections
  scene.background = envMap;  // Optional visible background
  hdrTexture.dispose();
  pmremGenerator.dispose();
});
```

---

## 4. Modern WebGL vs WebGPU / TSL / RenderPipeline Path

Web graphics is transitioning from WebGL/GLSL to WebGPU/WGSL. Applications should adopt a progressive enhancement architecture.

### Progressive Enhancement Pattern
```javascript
import WebGPU from 'three/addons/capabilities/WebGPU.js';
import WebGPURenderer from 'three/addons/renderers/webgpu/WebGPURenderer.js';

let renderer;
if (WebGPU.isAvailable()) {
  renderer = new WebGPURenderer({ antialias: true });
} else {
  // Graceful fallback to WebGL
  renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
}
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setAnimationLoop(renderLoop);
```

### Three Shading Language (TSL) vs Raw GLSL
- **Why TSL?**
  Raw GLSL shaders do not execute natively under WebGPU (which requires WGSL).
  TSL (Three Shading Language) uses a node-based functional syntax that compiles automatically to **both WGSL (WebGPU) and GLSL (WebGL)**.
- **TSL Shader Node Example**:
```javascript
import { MeshStandardNodeMaterial, color, timerLocal, positionLocal, sin } from 'three/tsl';

// Node material that compiles to both WebGL and WebGPU
const material = new MeshStandardNodeMaterial();
const t = timerLocal(1.0);
material.colorNode = color(0.2, 0.6, 1.0).add(sin(t).mul(0.2));
material.positionNode = positionLocal.add(sin(positionLocal.y.mul(4.0).add(t)).mul(0.1));
```

---

## 5. Measurement-First Performance Guidance

### Rejection of Brittle Magic Numbers
Do **NOT** rely on rigid, untested assertions (e.g. "always limit scenes to 50k triangles" or "tier 3 GPU guarantees 60 FPS").
Real performance is bounded by multiple independent bottlenecks:
1. **CPU Draw Call Bottleneck**: Exceeding 150-200 draw calls stalls the JS main thread and WebGL submission.
2. **GPU Fill Rate Bottleneck**: High overdraw, multiple full-screen post-processing passes, or 4K canvas resolutions choke pixel shaders.
3. **Memory Bandwidth Bottleneck**: Large uncompressed textures saturating mobile GPU memory bus.

### Measurement-First Profiling Loop
Always measure real metrics before and after optimization:

```javascript
function logFrameMetrics(renderer) {
  const info = renderer.info;
  console.log({
    drawCalls: info.render.calls,
    triangles: info.render.triangles,
    points: info.render.points,
    geometries: info.memory.geometries,
    textures: info.memory.textures,
  });
}
```

### Performance Checklist
- [ ] Draw calls measured (`renderer.info.render.calls < 150`).
- [ ] Geometry batched (`InstancedMesh` or `BatchedMesh` for repeated objects).
- [ ] Pixel ratio capped (`Math.min(window.devicePixelRatio, 2.0)` — never allow 3x on mobile!).
- [ ] Unused textures and geometries explicitly disposed (`geometry.dispose()`, `texture.dispose()`).
- [ ] Color space configured (`SRGBColorSpace`) and ACES tone mapping enabled.
- [ ] Static lighting baked where dynamic shadows are unnecessary.
