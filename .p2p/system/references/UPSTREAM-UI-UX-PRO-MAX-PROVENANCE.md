# Upstream UI UX Pro Max Provenance

Status: PINNED REFERENCE ADAPTER
Last verified: 2026-08-12
Recheck after: 2026-09-12

## Source

- Repository: [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)
- Pinned commit: `abb7f2fd5a083fa1ff55c326a963ff0d95c33f99`
- Observed tag at the pinned commit: `v2.14.1`
- Skill metadata version at the pinned commit: `2.13.0`
- License: MIT
- License text: [upstream LICENSE](https://raw.githubusercontent.com/nextlevelbuilder/ui-ux-pro-max-skill/main/LICENSE)

The metadata version and observed tag differ at this commit. P2P records both values and pins the full commit rather than treating either floating label as an update authority.

## What was researched

The repository structure, skill workflow, design-system generator, local CSV/JSON data, stack guidance, Python search/validation scripts, installation model, tests, Windows notes, and version/update mechanism were inspected from the upstream source. The inspected data inventory includes styles, palettes/colors, typography, products, UX guidelines, motion, icons, charts, app interfaces, landing patterns, React performance, and stack-specific guidance.

The upstream skill explicitly treats UI/UX work as a design-intelligence workflow, recommends local searchable data and a Design System, and provides accessibility, interaction, responsive, typography, and reduced-motion guidance. P2P adapts these concepts into a smaller deterministic local catalog and a project-safe artifact workflow.

## Integration decision

P2P does not clone, install, symlink, or fetch upstream at runtime. It does not vendor the upstream repository wholesale. The local adapter records the upstream taxonomy and derives a small attributed rule set for representative product types and stacks. This keeps project installs offline, reproducible, and version-auditable.

## Recheck procedure

1. Inspect upstream commit/tag/version/license and compare the recorded full commit.
2. Review upstream data/schema/script changes.
3. Run the P2P UI/UX evaluation and lifecycle gates.
4. Obtain release approval before changing the pinned commit in a future package.

No user project auto-updates from this source.
