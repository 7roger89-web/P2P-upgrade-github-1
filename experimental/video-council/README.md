# VIDEO COUNCIL — sandbox video expert council (TASK=VIDEO-COUNCIL-01)

Scope: **sandbox only**. This directory does not touch P2P core, defines no runtime
dependency, installs nothing, downloads no weights, and runs no inference.

The seven cloned repositories under `sources/` (git-ignored) are **expert source
material**, read as text. Each expert is a bounded role that may only cite its own source.

## Layout
```
sources/            7 cloned repos (reference material, git-ignored)
experts/            7 expert charters (01..07)
council/
  brief.md          shared production brief
  round1/           independent recommendations (7 files)
  round2/           disagreements / risks / corrections (7 files)
  round3/           chairman synthesis
productions/GOLDEN_VIDEO_001/PRODUCTION_PLAN.md   <- final executable plan
```

## Workflow (file-mediated, max 3 rounds, no daemon, no framework)
1. R1 — each expert writes one recommendation grounded only in its source + brief.
2. R2 — each expert reads the other six R1 files and writes only material
   disagreements, risks, corrections. No replies to replies.
3. R3 — chairman writes ONE executable production plan. Council stops.

## Experts
| # | Role | Grounded in |
|---|------|-------------|
| 01 | DIRECTOR | jacob-ye-seedance-prompt |
| 02 | PROMPT_RESEARCHER | awesome-seedance-prompts |
| 03 | CHARACTER_CONSISTENCY | awesome-character-consistency |
| 04 | CAMERA_MOTION | ReCamMaster |
| 05 | REFERENCE_VIDEO_EDIT | VACE |
| 06 | VIDEO_MODEL | Wan2.2 |
| 07 | POST_PRODUCTION | MoneyPrinterTurbo |

## Reproduce the clones
`bash scripts/clone_sources.sh`
