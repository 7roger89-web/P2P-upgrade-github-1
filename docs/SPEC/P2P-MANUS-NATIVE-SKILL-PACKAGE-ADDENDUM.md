# P2P → Manus Native Skill Package Addendum

Status: IMPLEMENTATION CANDIDATE — bounded development-source addendum
Version: `p2p-manus-native-skill-package-addendum/1`
Parent authority: `docs/SPEC/P2P-HOST-SKILL-PROJECTION-SPEC.md`
Scope: local, repo-relative package planning and export only

## Purpose and boundary

This addendum defines the smallest provider-neutral extension required to represent the Manus filesystem Skill format without editing the approved Host Skill Projection V1 semantics. P2P remains the sole control plane, capability registry, provenance authority, and router. The addendum adds a separate package plan and a separate repo-local materializer; it does not add a router, registry, executor, Manus adapter, task-state writer, or runtime certification system.

The package boundary is intentionally split into four independently evidenced stages:

| Stage | Meaning | Permitted side effects |
|---|---|---|
| `MAPPING_PLANNED` | The Manus target is represented but package format is not yet proven. | None. |
| `PACKAGE_FORMAT_PROVEN` | A deterministic filesystem package and archive were materialized under the approved repository-local output directory. | Writes only below the caller-provided repo-relative output directory. |
| `MAPPING_SUPPORTED` | The package mapping is defined and safe for the two current local vendor capabilities. | No host or Manus mutation. |
| `RUNTIME_PROOF` | A real imported Skill was consumed by a bounded Manus task and evidence was returned. | Requires the separate Owner import/credential gate. |
| `HOST_RUNTIME_CERTIFIED` | P2P has independently certified the actual Manus runtime behavior. | Never inferred from package creation. |

`PACKAGE_FORMAT_PROVEN` and `MAPPING_SUPPORTED` are not runtime certification. The implementation reports `runtime_status: NOT_CERTIFIED` until a real Owner-approved import and bounded task proof exists.

## Current host mapping

The closed host kind is `manus`. The supported native representation is a filesystem Skill with a root `SKILL.md`. `SKILL.md` receives Manus-compatible YAML frontmatter generated from the canonical P2P capability ID, description, and invocation class, followed by the upstream entrypoint body. A deterministic `P2P-PROVENANCE.json` sidecar preserves the source snapshot hash, entrypoint hash, ownership classification, source path, license, declared references/assets/scripts, and disabled dependency/network constraints.

The package contains only content selected from the existing P2P vendor declaration. At `LOAD`, only `SKILL.md` and provenance metadata are materialized. At `DEEP_LOAD`, only explicitly requested and declared references, templates, assets, and script descriptors may be added. Script entries are non-executable descriptors with `executable: false`; the exporter never executes them or installs dependencies. Unrequested vendor files are never copied.

## Canonical input and safety rules

The input is an existing validated `CapabilityManifest`, an explicit project-scoped Manus target, and resolved content supplied by the existing vendor-skill boundary. The exporter reuses `vendor_skill_metadata` and `load_vendor_skill` for the two canonical capabilities: `creative.copywriting` and `media.whiteboard_animation`. It preserves the registry's `UPSTREAM_PROVENANCE`, snapshot hash, entrypoint hash, `APPROVAL_BOUNDARY`, trust level, declared context, and optional dependency state. Missing or stale hashes, malformed metadata, traversal, absolute paths, ownership conflict, ambiguous host evidence, and full-tree expansion fail closed with stable reason codes.

No package operation reads credentials, provider/model configuration, host-global settings, or Manus configuration. The exporter does not upload, import, create tasks, send messages, or call the network. Its only permitted writes are the package directory and deterministic `.skill` ZIP archive beneath the supplied repository-local output directory. Existing output is never overwritten.

## Upstream Manus evidence

The official [Manus Skills documentation](https://manus.im/docs/features/skills) describes file-system-based Skills, progressive disclosure, and upload of a local `.zip`, `.skill`, or folder, as well as GitHub import. The official [`skill.list` API reference](https://open.manus.ai/docs/v2/skill.list) describes listing global/project Skills and passing returned IDs to task controls. The official [`task.create` API reference](https://open.manus.ai/docs/v2/task.create) states that `message.enable_skills` controls available Skills and `message.force_skills` ensures invocation. These sources establish package/runtime compatibility requirements only; they do not substitute for real import or runtime evidence.

## Runtime gate

A package candidate must stop at `OWNER_ACTION_REQUIRED_MANUS_SKILL_IMPORT` before any real import. The Owner must import the produced `.skill` archive through Manus, report the resulting availability/name, and explicitly authorize any credentialed or task-running proof. Only after that gate may a separate runtime procedure verify `skill.list`, explicitly enable or force the actual imported Skill where supported, and inspect bounded task evidence. A package hash or local test result must never be reported as runtime proof.
