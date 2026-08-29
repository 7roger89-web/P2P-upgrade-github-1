# Coder Handoff — P2P-IMG2THREEJS-EXEC-01

## Result

Implementation is complete on the isolated branch
`workstream/p2p-img2threejs-exec-01`, based on fresh `origin/main`.
No push, promotion, release, deployment, or Thiên Hạ checkout mutation occurred.

The existing non-executable img2threejs provenance path was upgraded in place:
P2P now has one noncanonical, on-demand capability record, one P2P-authored
selective protocol snapshot, and one fail-closed adapter bound to an exact
external checkout. The upstream repository was not copied into P2P and was not
patched.

## Bound invariants implemented

- Provenance: img2threejs v1.5.1 at commit
  `dede5909be4e494b228c801a55dda47439143932`, tree
  `25bcd4e1f1a487b9a61d69ade257342a3da767e3`, Apache-2.0.
- Execution: exactly five allowlisted local/control-plane entrypoints; denied
  CS2 metadata, material-region, vision/plugin, and all unlisted routes.
- Network: `DENY` by default; CS2 metadata networking disabled; no caller
  network override.
- Filesystem: declared reconstruction workspace only; absolute paths, URLs,
  dot-dot, backslash traversal, symlink/reparse escape, and output-root escape
  are rejected.
- Process: explicit argv, `shell=False`, closed stdin, bounded timeout, and
  minimal environment without inherited credentials/secrets.
- Projection: existing pure host projection is reused; only the selected
  P2P-authored contract is projectable, not the full P2P runtime or upstream tree.
- Protocol: future Golden Character and separate Golden Weapon / Asset Forge
  protocols are documented with honest visual-browser and maturity gates.

## Changed surfaces

- `.p2p/system/p2p_capabilities/img2threejs_adapter.py`
- `.p2p/system/p2p_capabilities/capabilities.json`
- `.p2p/vendor/provenance/p2p-game-toolchain-02a.json`
- `.p2p/vendor/skill/img2threejs-safe-exec-1.5.1/SKILL.md`
- `manifest/external-sources.json`
- `docs/p2p-development/P2P-PROJECT-BOOTSTRAP.md`
- focused 02A/vendor/projection tests
- plan evidence, benchmark, and actual-status files

## Validation evidence

- `python -B -m unittest tests.test_p2p_img2threejs_exec_01 -v`: `6/6` PASS,
  including exact-checkout state/next/probe/factory smoke and hostile-input
  fail-closed cases.
- Focused suite (`img2threejs_exec_01`, `game_toolchain_02a`, vendor skill,
  visual vendor, projection contract, projection bundle): `84/84` PASS.
- Exact upstream adapter verification: PASS for commit/tree/license and all
  allowlisted entrypoints.
- Registry/provenance/manifest consistency and Python compilation: PASS.
- `git diff --check`: PASS.
- Anvien refresh: `1047` files scanned, `188` parsed, `0` parse failures;
  detect-changes was run before implementation commits.

## Validation limitation

`scripts/doctor.py --root . --role development` exits `FAIL` because the fresh
development checkout already has governance drift: six unlocked runtime files
and five protected runtime files changed, including the intentionally scoped
bootstrap documentation change. The package doctor role mismatch (`portable`
requested vs `development` detected) is also not a capability failure. No
unrelated governance/release repair was made.

Browser/Playwright visual evidence is intentionally not claimed: no Thiên Hạ
project or runtime is in scope. Full production auto-rig, general auto-rig,
Mixamo compatibility, complete facial rig, and production animation pipeline
remain unproven or not claimed.

## Handoff decision

`PASS_FOR_SUPERVISOR_REVIEW`

The candidate is technically ready for independent exact-subject supervisor
review. Owner approval, promotion, push, release, and deployment remain pending
and were not inferred.
