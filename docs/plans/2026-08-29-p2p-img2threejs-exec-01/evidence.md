# P2P img2threejs executable projection Evidence Ledger

## Metadata

- Date: `2026-08-29`
- Plan: `docs/plans/2026-08-29-p2p-img2threejs-exec-01/plan.md`
- Evidence: `docs/plans/2026-08-29-p2p-img2threejs-exec-01/evidence.md`
- Benchmark: `docs/plans/2026-08-29-p2p-img2threejs-exec-01/benchmark.md`
- Actual status: `docs/plans/2026-08-29-p2p-img2threejs-exec-01/actual-status.md`

## Evidence Rules

This ledger records source facts, security decisions, implementation behavior,
validation commands, impact evidence, exact commit identity, and explicit limits.
No local test receipt substitutes for Owner approval, release, promotion, or browser
visual evidence.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-SRC1`: fresh P2P clone from the requested remote is on isolated branch
  `workstream/p2p-img2threejs-exec-01`, origin/main `29291dae1f3101f3ace9546fb2b27e3d514bca61`,
  tree `e5e01a1a2d4ddad207aaab2e25752b571bd5fb9e`.
- `E0-P0A-SRC2`: fresh upstream refs resolve release v1.5.1 to
  `dede5909be4e494b228c801a55dda47439143932`, tree
  `25bcd4e1f1a487b9a61d69ade257342a3da767e3`; upstream main resolves to
  `9fbd0ca5bbcc3b13bebe712745d6784d33db0b85`.
- `E0-P0A-SEC1`: pinned `forge/stage1_intake/fetch_cs2_metadata.py` calls
  `urllib.request.urlopen(index_url, timeout=30)` and retrieves `imageUrl`; no URL
  allowlist exists in upstream v1.5.1. P2P route is therefore deny-only.
- `E0-P0A-SEC2`: pinned `forge/stage1_intake/material_region_analysis.py` derives
  output names from `region_id.replace('/', '-')` and accepts unconstrained output
  roots/source paths; backslash, dot-dot, absolute, and root-escape cases remain
  applicable. P2P validates before invocation.
- `E0-P0A-SRC3`: fresh current registry has 39 capabilities and no img2threejs identity;
  provenance has `img2threejs_pending` at the old 02A pin and status
  `EXECUTABLE_REGISTRATION_PENDING_OWNER_GATE` / `NOT_EXECUTED`.
- `E0-P0A-SRC4`: existing `vendor_skill` and host projection are metadata/JIT/pure
  projection surfaces; they do not execute arbitrary scripts and must be reused,
  not redesigned.
- `E0-P0A-GRAPH1`: Anvien refresh on the fresh clone: 1042 files scanned, 187 code
  files parsed, 0 parse failures, graph 45,706 nodes / 52,841 relationships. The
  exact repo alias `p2p-img2threejs-exec-01` was used. `tests/test_p2p_game_toolchain_02a.py`
  file-detail: 38 symbols, 30 local relationships, 3 outbound, high graph warning;
  bootstrap doc: low-risk documentation surface with no code relationships.
- `E0-P0A-BOUNDARY1`: no Thiên Hạ checkout was opened or modified; no push, release,
  deploy, promotion, or Owner approval action was taken.

P0 decision: complete. P1-A can proceed, then P1-B can proceed after P1-A refresh.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

### P1-A

- `E1-P1A-SEC1`: adapter binds upstream repository, version `1.5.1`, exact commit
  `dede5909be4e494b228c801a55dda47439143932`, exact tree
  `25bcd4e1f1a487b9a61d69ade257342a3da767e3`, and Apache-2.0 provenance.
- `E1-P1A-SEC2`: execution allowlist contains exactly five local/control-plane
  entrypoints: `state`, `next`, local image probe, strict spec validation, and
  deterministic Three.js factory generation. Unsafe CS2, material-region, vision,
  and unlisted routes are denied.
- `E1-P1A-SEC3`: `NETWORK_POLICY=DENY` and `CS2_METADATA_NETWORK=DISABLED`; caller
  network override is rejected before source execution.
- `E1-P1A-SEC4`: relative path and identifier guards reject remote URL, absolute path,
  dot-dot, backslash traversal, symlink/reparse escape, and output-root escape.
- `E1-P1A-SEC5`: subprocess policy uses explicit argv, `shell=False`, closed stdin,
  bounded timeout, and a minimal environment without credentials/secrets.
- `E1-P1A-TEST1`: `python -B -m unittest tests.test_p2p_img2threejs_exec_01 -v`
  passed `6/6`, including real exact-checkout state/next/probe/factory smoke and
  fail-closed security cases.
- `E1-P1A-TEST2`: strict upstream quality gate was retained; a shallow fixture was
  rejected, then a bounded quality-complete fixture generated deterministic output.

P1-A decision: complete. The external unsafe routes remain unchanged and are
contained by adapter denial; no upstream patch or network sandbox was introduced.

### P1-B

- `E1-P1B-REG1`: registry validates with 40 entries, canonical identities unchanged,
  denominator `8`, and one noncanonical `img2threejs` capability using the existing
  single router and `LOCAL_VENDOR_SNAPSHOT` on-demand contract.
- `E1-P1B-REG2`: current v1.5.1 provenance and external-source candidate are recorded
  with the exact SHA/tree/license, adapter allowlist, deny policy, snapshot hash, and
  explicit predecessor pointer; the old 02A record remains unchanged.
- `E1-P1B-PROJ1`: explicit img2threejs route loads only `SKILL.md`; host projection is
  pure, selected-only, project-scoped, and emits only the projected skill plus host
  metadata. No upstream tree or full P2P runtime is copied.
- `E1-P1B-PROJ2`: canonical project bootstrap now documents the optional selective
  read order and required discovery fields without changing `P2P_REQUIRED`.
- `E1-P1B-TEST1`: focused compatibility/projection suites passed `84/84`, including
  existing vendor, projection, registry, routing, and unrelated-project behavior.

P1-B decision: complete. Final closure evidence is recorded below; the remaining
workflow action is independent exact-subject supervisor review.

## Closure Evidence

- `E1-CLOSE1`: final focused compatibility/projection suites remain `84/84` PASS;
  the dedicated adapter suite remains `6/6` PASS. Exact upstream verification,
  JSON/hash consistency, Python compilation, and `git diff --check` are PASS.
- `E1-CLOSE2`: Anvien was refreshed after implementation (`1047` files scanned,
  `188` parsed, `0` parse failures) and `detect-changes --scope all` was run
  before implementation commits. The report identified only the scoped registry,
  provenance, protocol, bootstrap, and focused-test surfaces; test files carry a
  HIGH blast-radius warning, treated as a scope warning.
- `E1-CLOSE3`: development doctor was run with the correct detected role. It
  exits `FAIL` only on existing governance drift in the fresh development
  checkout: six unlocked runtime additions and five protected runtime changes,
  including the intentionally scoped bootstrap documentation change. The package
  doctor portable-role mismatch is not applicable. No unrelated drift was repaired.
- `E1-CLOSE4`: candidate before supervisor report is
  `abc7a6b8a09f77dd25aa1f350e20a31e9510dfac`, tree
  `124c71141c5a54c2250fad8d162c2641b3196909`; worktree is clean and no push or
  promotion occurred. The exact source prerequisite is the separate clean
  v1.5.1 checkout at `dede5909be4e494b228c801a55dda47439143932` /
  `25bcd4e1f1a487b9a61d69ade257342a3da767e3`.
- `E1-CLOSE5`: coder handoff is recorded at
  `reports/coder/rp_coder_260830_0019_by_gpt-5-codex_p2p-img2threejs-exec-01.md`.
  Supervisor review and final report remain required before the Owner Gate.
