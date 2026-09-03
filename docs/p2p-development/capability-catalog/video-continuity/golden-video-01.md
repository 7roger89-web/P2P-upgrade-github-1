# GOLDEN VIDEO #1 — Pilot Contract

Status: CANDIDATE — awaiting manual pilot (Owner-facilitated) before any Video
Studio bootstrap
Date: 2026-09-03
Workstream: P2P-VIDEO-CONTINUITY-01
Issue: #72

The next proof is a **single Golden Path** executed manually with Arena Video /
DesignArena. This is not a broad Video Studio readiness claim. It is one
concrete, manually executable contract that closes the loop:
`canonical -> one approved keyframe -> one provider-ready prompt -> manual
render -> manual continuity verdict`.

## Golden Path

1. **Canonical asset** — pick one canonical identity asset (a still face / look
   reference for the character) and record it in the canonical visual contract
   (`p2p-canonical-visual-contract/1`).
2. **Approved start keyframe** — choose exactly one approved start keyframe for
   the shot (no alternate candidates yet).
3. **Provider-ready prompt** — project the master director spec into one
   provider-specific shot prompt via `project_provider_shot(...)`. The shot prompt
   must preserve mandatory constraints (anchor/reference, identity, canonical
   refs, action, camera, negative) intact. If mandatory constraints cannot fit
   the provider's declared limit, the projection **fails closed** with an
   explicit reason; do not proceed with a truncated prompt.
4. **Manual Arena/DesignArena render** — run the prompt through Arena Video /
   DesignArena manually. This is real render invocation, but it happens outside
   this codebase and is **manually performed** by the operator. No renderer API
   is called by this foundation.
5. **Manual continuity verdict** — a human inspects the resulting frame(s) and
   supplies the PASS/FAIL evidence per dimension (identity, hair/body, costume,
   prop, environment/style, start/end state, action/camera). `evaluate_continuity_gate`
   only consumes these externally supplied judgments; it does not inspect media.

## Re-anchor rule

The manual verdict feeds `ReanchorCycle`. A final frame with detected drift (or an
un-approved frame) is **not** allowed to become canonical input for the next shot.
`safe_to_reanchor` requires `gate_passed AND NOT drift_detected`; otherwise
`next_start()` raises `RE_ANCHOR_BLOCKED`.

## Deliverable of the pilot

- One canonical asset id + one approved keyframe id + one provider-ready prompt +
  the operator's manual continuity verdict (PASS/FAIL per dimension) for a single
  shot.
- This document is the executable contract. It requires a human render step; the
  foundation never invokes a renderer.

## Explicit bounds

- Continuity QA is **manual / external evidence**; no automatic vision QA.
- Best-of-N is **candidate-planning / state semantics**; no actual Arena /
  DesignArena rendering or take scoring.
- No renderer API, model, framework, service, infrastructure, paid generation, or
  credential is added.
