# Supervisor Report: P2P MPFB2 Addon Init 01

Verdict: PASS

## Metadata

- Report file: `reports/supervisor/rp_supervisor_260901_184112_by_gpt-5-codex_p2p-mpfb2-addon-init-01.md`
- Review time: `260901 184112 +07:00`
- Reviewer: `gpt-5-codex`
- Repo/project: `7roger89-web/P2P-upgrade-github-1`
- Scope reviewed: bounded addon-init source fix, real Blender child proof,
  one-character stop-law evidence, current candidate worktree
- Claim reviewed: the MPFB2 addon-initialization blocker is closed through the
  supported Blender extension lifecycle, and the first new downstream blocker
  is recorded without a second repair
- Authority used: current user request, repository instructions, plan and
  acceptance boundaries, source/runtime contracts, current source/diff, and
  fresh command evidence
- Related artifacts: coder report, plan/evidence/benchmark/actual-status
  ledgers, runtime manifest, Blender child logs, result JSON, GLB, provenance
  sidecar, source commit `0e3cc85d3b8ea599a1918be91873d1ef17ba14b1`

## Executive Summary

- Problem: bare `mpfb` import did not create the Blender addon identity needed
  by pinned MPFB2 `get_preference()`.
- Decision: the bounded addon-init claim is supported. The child now registers
  the existing source as a local Blender 4.2 extension and enables
  `bl_ext.src.mpfb`; real identity, preference, and registration markers all
  pass before service access.
- Required outcome: accept this bounded slice and preserve the stop boundary.
  The full character route remains stopped at the newly exposed downstream
  `GLB_skeleton: index invalid` error; no repair belongs in this review.

## Source-Level Clearance Notes

- `.p2p/system/p2p_capabilities/mpfb_blender_entrypoint.py`: clear for the
  reviewed addon-init invariant. Lines 326-363 validate the existing pinned
  package and use Blender's local extension repository; lines 364-393 call
  `addon_utils.enable(module_name, default_set=True, persistent=False)`, check
  the real addon key, call `get_preference()`, and only then import
  `HumanService`. There is no preferences-dictionary injection, fake addon
  object, MPFB upstream edit, or bare MPFB fallback.
- `.p2p/system/p2p_capabilities/mpfb_adapter.py` and
  `.p2p/system/p2p_capabilities/windows_network_isolation.py`: clear and
  preserved. The current candidate diff contains no changes to either file.
- Plan/evidence/benchmark/status and coder report: clear as bounded evidence
  artifacts. They distinguish addon-init PASS from the downstream structural
  blocker and record the stop law.

## Evidence Checked

Passed:

- Fresh `git fetch --prune origin` and `git ls-remote origin refs/heads/main`
  both returned `b65948b00ed2a8969fed70ab59f68b5d9b53858d`; current candidate
  is a descendant of that base. Current HEAD is
  `8aaa6637f92608584dd51da6e7522c67a009eae6`, tree
  `9f989ab3655468b6e9eddaefe07db9657066e496`, with a clean worktree.
- Candidate diff has one production source file plus the bounded ledgers and
  reports. No adapter/firewall production diff is present.
- Fresh focused test invocation passed `35/35`. Earlier compile and direct
  source checks remain recorded in the evidence ledger; no broad suite was
  treated as proof.
- Existing runtime manifest binds Blender `4.2.23 LTS`, MPFB2 `2.0.17`, exact
  pin `80919fa4682335c41847f761a4d79dcad4124732`, local extension module
  `bl_ext.src.mpfb`, and portable user resources beside Blender.
- Current real child log contains `MPFB_ADDON_IDENTITY_PRESENT=YES`,
  `MPFB_GET_PREFERENCE_PASS=YES`, `MPFB_REGISTER_PASS=YES`, MPFB
  initialization completion, HumanService skin-material creation, and native
  glTF export start/finish. The child PID was `10540`.
- Current artifact checks find exactly `Oak.glb` and its provenance sidecar.
  `Oak.glb` is `9093808` bytes with SHA-256
  `5f96f86fbfd4cdc01201e767b0383807ac5e2a7a6365252aee568a91a949c0c4`.
- Fresh provenance validation passed schema, recipe binding, CORE_CC0 asset
  binding, and GLB hash checks. The sidecar SHA-256 is
  `d5d50b0bea9dfb096762e566211df4db62be1ed1f7bb47473919a5f9f672f7b7`.
- Fresh firewall inspection returned exact post-cleanup rule count `0`.
  The child reached post-spawn structural validation, so firewall setup and
  verification preceded the child spawn in the recorded run.
- The recorded Game Truyen before/after fingerprint is unchanged and the
  protected checkout was not a runtime target. No Game Truyen mutation is
  present in the candidate diff.

Failed:

- The real runner result is `status=FAILED` at the first downstream validator
  error: `GLB_skeleton: index invalid`. A fresh direct call to
  `validate_glb_output()` reproduces the same error; independent GLB parsing
  shows one skin with `skeleton=null`.

Not run:

- A second Blender smoke, GLB repair, validator repair, another character,
  hardening, benchmarks, and broad regression were intentionally not run after
  the first downstream blocker, as required by the current workstream.

## Invariant Closure

- affected invariant: Blender-owned MPFB2 addon identity and registration must
  exist before MPFB preference/service access.
- sibling surfaces checked: child entrypoint, pinned MPFB manifest/source,
  Blender extension probe and portable resource boundary, parent adapter,
  firewall helper, output/provenance validators, and protected Game Truyen
  boundary.
- residual unverified same-invariant surfaces: none for addon initialization.
  The GLB rooted-skeleton requirement is a separate downstream invariant and
  is explicitly blocked, not silently accepted.

## Overall Evaluation

The evidence closes the requested addon-initialization defect with one
supported lifecycle binding and preserves the security, provenance, pin, and
immutability boundaries. The review accepts only that bounded claim. It does
not convert the real downstream structural failure into a success claim and
does not authorize a second fix.
