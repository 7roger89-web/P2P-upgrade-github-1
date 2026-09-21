# Three.js Production Workflow & Look-Dev

Evidence-based production practices reconciling 3D asset preparation, baking decisions, color management, WebGPU/TSL pipeline, and measurement-first performance.

---

## 1. Blender & Web-3D Asset Preparation

Asset pipeline efficiency directly impacts GPU memory consumption, draw call frequency, and initialization latency.

### GLTF / GLB Export Hygiene
- **Apply Object Transforms**: Before export, apply transforms (`Ctrl + A` -> Apply All Transforms in Blender). Unapplied object scales result in distorted surface normals and incorrect bounding volumes.
- **Logical Origin / Pivot**: Set the pivot at the logical interaction point (grounded base for characters, center of mass for physics objects).
- **Geometry Cleanup**: Remove non-manifold geometry, duplicate vertices, and degenerate polygons prior to export.
- **Hierarchy Depth**: Avoid deeply nested empty object hierarchies that incur unnecessary scene-graph traversal overhead during matrix world updates.

### Geometry Compression (Draco Trade-offs)
- **Measurement-First Evaluation**: Draco geometry compression reduces network payload size over the wire. However, Draco decompression executes on the client CPU / web worker before geometry is uploaded to GPU memory.
- **Heuristic Guideline**: Measure whether the network bandwidth savings exceed the client-side decompression latency. For complex meshes on bandwidth-constrained networks, Draco can significantly speed up time-to-first-render. For lightweight meshes or heavily morphed skinned characters, decompression latency may induce frame hitches during initial loading.

### Texture Compression (GPU Memory Footprint)
- **VRAM vs Disk Size**: PNG and JPEG files are compressed for disk storage, but GPUs must decompress them into raw uncompressed texels in VRAM upon upload.
- **GPU-Native Compression (KTX2 / Basis Universal)**: Transcodes into native GPU formats (e.g. ASTC, BC7, ETC) directly in VRAM. This keeps memory footprint low and prevents mobile memory pressure crashes. Evaluate KTX2 for memory-intensive scenes using `KTX2Loader`.

### Channel Packing (ORM Workflow)
- Pack grayscale material maps into a single texture:
  - **Red Channel**: Ambient Occlusion (AO)
  - **Green Channel**: Roughness
  - **Blue Channel**: Metalness
- Combining multiple scalar channels reduces independent texture sampler bindings, minimizing state changes in the graphics driver.

---

## 2. Baking vs Dynamic Lighting Decision Matrix

Lighting and real-time shadow generation represent significant GPU compute and fill-rate loads.

| Scene Element | Strategy | Justification |
|---|---|---|
| **Static Geometry / Architecture** | **Baked Lightmaps** (`uv2` + `material.lightMap`) | Eliminates real-time shadow map render passes; captures indirect global illumination and ambient occlusion with minimal runtime overhead. |
| **Hero Characters / Interactive Objects** | **Dynamic Real-time Lighting** (`DirectionalLight` + Shadows) | Dynamic interactivity requires real-time cast shadows and responsive specular reflection. |
| **Secondary Objects / Ground Contact** | **Contact Shadows / Decal Shadows** | Simulates soft grounding shadows without paying the full cost of high-resolution cascaded shadow maps. |
| **Ambient / Diffuse Lighting** | **Image-Based Lighting (IBL)** (`scene.environment`) | Provides physically plausible ambient light and environment reflections without multiple dynamic fill lights. |

### Lightmap Implementation & Color Space
Lightmaps represent physical surface irradiance and must be handled in linear color space with non-overlapping second UV coordinates (`uv2`):

```javascript
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const textureLoader = new THREE.TextureLoader();
const lightmap = await textureLoader.loadAsync('baked_lightmap.png');

// Explicit linear color space for baked illuminance
lightmap.colorSpace = THREE.LinearSRGBColorSpace;
lightmap.channel = 1; // UV2 channel
lightmap.flipY = false; // Match glTF coordinate convention

const gltfLoader = new GLTFLoader();
gltfLoader.load('environment.glb', (gltf) => {
  gltf.scene.traverse((child) => {
    if (child.isMesh && child.material) {
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

PBR (Physically Based Rendering) requires consistent linear color space math across textures and framebuffers.

### Renderer Color Space (Three.js r152+)
```javascript
// Output color space for standard display rendering
renderer.outputColorSpace = THREE.SRGBColorSpace;
```

### Texture Color Space Conventions
- **Color Textures** (BaseColor / Albedo, Emissive):
  ```javascript
  texture.colorSpace = THREE.SRGBColorSpace;
  ```
- **Data Textures** (Normal maps, Roughness, Metalness, Ambient Occlusion):
  ```javascript
  dataTexture.colorSpace = THREE.NoColorSpace; // Pure linear numeric data
  ```

### Tone Mapping
Map high dynamic range values gracefully to monitor display gamut:
```javascript
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
```

### Environment Lighting via PMREM
```javascript
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js';

const pmremGenerator = new THREE.PMREMGenerator(renderer);
pmremGenerator.compileEquirectangularShader();

new RGBELoader().load('environment_1k.hdr', (hdrTexture) => {
  const envMap = pmremGenerator.fromEquirectangular(hdrTexture).texture;
  scene.environment = envMap;
  scene.background = envMap;
  hdrTexture.dispose();
  pmremGenerator.dispose();
});
```

---

## 4. WebGL vs WebGPU & Three Shading Language (TSL) Path

Three.js supports both the mature, universally compatible `WebGLRenderer` and the evolving `WebGPURenderer`.

### WebGPURenderer Path (three/webgpu)
In current Three.js, `WebGPURenderer` (from `three/webgpu`) automatically attempts to initialize a WebGPU backend and **automatically falls back to a WebGL 2 backend** if WebGPU is unsupported by the browser or platform hardware:

```javascript
import { WebGPURenderer } from 'three/webgpu';
import * as THREE from 'three';

const renderer = new WebGPURenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// Async initialization establishes the WebGPU or fallback WebGL 2 backend
await renderer.init();

renderer.setAnimationLoop(() => {
  renderer.render(scene, camera);
});
```

*Note*: `WebGLRenderer` remains the stable, fully verified default for mission-critical web applications. `WebGPURenderer` is the forward-looking target for compute shaders, storage buffers, and next-generation pipelines.

### Three Shading Language (TSL)
TSL provides node-based shader authoring that cross-compiles to both WGSL (for WebGPU) and GLSL (for WebGL):

```javascript
import { MeshStandardNodeMaterial, color, positionLocal, time, sin } from 'three/tsl';

const material = new MeshStandardNodeMaterial();
// Use official current TSL time node
material.colorNode = color(0.2, 0.6, 1.0).add(sin(time).mul(0.2));
material.positionNode = positionLocal.add(sin(positionLocal.y.mul(4.0).add(time)).mul(0.05));
```

---

## 5. Measurement-First Performance Discipline

### Rejection of Brittle Magic Numbers
Do not treat arbitrary static numbers (e.g. fixed draw call counts, universal triangle ceilings, or rigid GPU tiers) as universal performance law. Real runtime performance is dictated by the specific hardware bottleneck on the user's device:

1. **CPU Draw-Call Bound**: High command submission overhead stalling the JavaScript main thread.
2. **GPU Vertex Bound**: High vertex shader execution time or complex skinning computations.
3. **GPU Fill-Rate / Rasterization Bound**: Excessive overdraw, transparent sorting, or expensive full-screen post-processing passes at high screen resolutions.
4. **Memory Bandwidth Bound**: Large uncompressed texture streaming saturating mobile memory bus.

### Measurement-First Profiling Loop
Always observe actual performance metrics in the target runtime environment before choosing optimizations:

```javascript
function inspectFrameMetrics(renderer) {
  const { render, memory } = renderer.info;
  return {
    drawCalls: render.calls,
    triangles: render.triangles,
    geometries: memory.geometries,
    textures: memory.textures,
  };
}
```

### Empirical Optimization Protocol
- Profile draw calls using `renderer.info.render.calls`. When profiling reveals CPU submission bottlenecks, batch repeated meshes using `InstancedMesh` or `BatchedMesh`.
- Monitor fill rate: on dense high-DPI displays, high pixel densities multiply fragment shader workload quadratically. Scale rendering resolution dynamically based on measured frame time rather than assuming static device pixel ratio caps.
- Explicitly dispose of unused GPU assets when scenes or components unload (`geometry.dispose()`, `material.dispose()`, `texture.dispose()`).
