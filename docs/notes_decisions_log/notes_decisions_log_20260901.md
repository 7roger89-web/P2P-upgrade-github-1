# Notes and Decisions Log — 2026-09-01

## P2P-HUMANIZER-01 / Issue #51

- Initial fresh `origin/main` was bound to `d80934bc...` / tree `b2d5d03...`;
  a later remote check found unrelated PR #50 and advanced current main to
  `b65948b00ed2a8969fed70ab59f68b5d9b53858d` / tree
  `6553b9cb55990f66f6da5b2db83dc6f5ec7e393c`. The sole branch was rebased
  onto current main before push.
- Existing `creative.copywriting` was reconciled as marketing-only and kept
  unchanged. The new distinct ID is `creative.prose.humanize`.
- Exact upstream Humanizer subject:
  `e2e92e7b4b8229253ed5c8e81dc65463fdeddda5` /
  `b8a8804ed9210e539531fc26c2d84fdb603960f4`, version `2.11.2`, MIT;
  `SKILL.md` SHA-256 is
  `14fc8a965b6e0a8dc100ba4dffeab55cb94bbac112abbde7e014d5c15a35c202`.
- Integration reuses the existing single router and generic vendor loader;
  load is `ON_DEMAND`, selection is explicit/profile-selected, global default
  is disabled, and only exact upstream `SKILL.md` plus `LICENSE` are vendored.
- Focused direct test module passed 9/9; nearest vendor/host boundary passed
  61/61. Broad baseline/governance drift findings remain disclosed and are not
  silently repaired in this bounded workstream.
- Coder report: `reports/coder/rp_coder_260901_175535_by_gpt-5-codex_p2p-humanizer-01.md`.
- Handoff: `NEXT_STEP=INDEPENDENT_SUPERVISOR`; no merge/promotion performed.
