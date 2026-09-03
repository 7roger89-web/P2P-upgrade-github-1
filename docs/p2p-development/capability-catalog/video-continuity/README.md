# Video Continuity Capability Catalog

Status: CANDIDATE — awaiting owner gate for any video-studio bootstrap
Date: 2026-09-03
Workstream: P2P-VIDEO-CONTINUITY-01
Parent: `docs/SPEC/P2P-CAPABILITY-FOUNDATION-ARCHITECTURE-SPEC.md`
Issue: #72

Provider-neutral video continuity foundation for consistency-controlled AI-video
production, before any standalone Video Studio project is bootstrapped.

This catalog **extends** the existing P2P capability foundation. It does **not**
create a second ontology, registry, router, projection, or profile system, and it
does **not** install a video model, framework, model weight, paid API, secret, or
infrastructure. Arena Video / DesignArena are treated as **random/candidate
renderers**, never as a canonical production backend.

## Architecture alignment

- `capabilities.json` — canonical capability registry (extended by one new entry).
- `p2p_uiux/router.py` — the only router (no second router created).
- `p2p_capabilities/model.py` — manifest + canonical safety (reused, unchanged).
- `p2p_capabilities/video_continuity.py` — provider-neutral contract surface
  (director spec, canonical visual contract, performance bible, keyframe
  re-anchor, continuity gate, provider projection, best-of-N candidate rendering).
- `protocols/video-continuity-protocol.md` — the reusable protocol.

## Invariants

1. **Consistency lives outside the renderer** — identity/appearance is carried by
   canonical assets and approved keyframes, not by trusting a random video model.
2. **A raw final frame containing drift never automatically becomes canonical
   input for the next shot.**
3. **A failed shot cannot become the source of truth for downstream shots.**
4. **Provider prompt limits are profile/config data**, not architectural constants.
5. **Single router / no orcheshestrator** — this catalog only supplies contract
   data, readiness facts, and referenced knowledge to the existing route.
6. **Knowledge-only sources stay knowledge-only**; no runtime adoption is forced.
