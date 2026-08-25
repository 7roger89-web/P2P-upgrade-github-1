# Coder Report — P2P Vendor Skills Reconstructed Candidate

- Date: `2026-08-25`
- Candidate: `D:\AI\P2P_dev\P2P-upgrade-github\.tmp\p2p-vendor-skills-reconstructed-03`
- Branch: `codex/p2p-vendor-skills-reconstructed-03`
- Status: `TECHNICAL_GATES_PASS_PENDING_SUPERVISOR`
- Owner gate: not requested or executed; no promotion, merge, push, release, or deployment.

## Authority and reconstruction boundary

The broken root was used only as read-only candidate material. Its `.git`
authority remains unusable and was not repaired. The candidate was created from
the valid Git reference:

- `RECONSTRUCTION_BASE_SHA=557b502758581812a8845355ed6b426ba75372ec`
- `RECONSTRUCTION_BASE_TREE=2bd89d97f8877d372f0444218ec9c7339da14d7f`
- `RECONSTRUCTION_BASE_REASON=USER_VERIFIED_CLEAN_REFERENCE; NO_NEWER_DESCENDANT_CANONICAL_OR_OWNER_PROMOTED_REF_PROVEN`
- remote: `https://github.com/7roger89-web/P2P-upgrade-github-1.git`

Fresh remote-head and local ancestry checks did not prove a newer descendant
canonical or owner-promoted reference. The base is therefore explicit and is
not described as promoted.

## Invariant-family map

1. Canonical quorum: the exact eight canonical identities, denominator `8`, and
   full quorum `8/8` remain unchanged. The two vendors are ordinary `SKILL`
   records, not optional specialists and not quorum members.
2. Single router/provider neutrality: the existing router remains the only
   router. The change adds a vendor projection and readiness branch without
   adding a provider, model fallback, nested router, or certification system.
3. Provenance and integrity: each vendor path and entrypoint is hash-bound to
   the registry; snapshots are copied byte-for-byte and optional operations are
   dependency-probed/fail-closed.
4. Permission boundary: vendor content is treated as local data. Discovery is
   metadata-only and cannot grant tools, permissions, network, credentials, or
   commercial approval.
5. Baseline preservation: role contracts, role verification, model semantics,
   profiles/configuration, canonical hashes, and the provider-neutral C35 test
   remain baseline surfaces and were not copied from the broken snapshot.

## Sibling surfaces and legacy fallback

The reconstructed surface is deliberately limited to:

- `.p2p/system/p2p_capabilities/capabilities.json`: append exactly two vendor
  manifests to the preserved base registry.
- `.p2p/system/p2p_capabilities/vendor_skill.py`: manifest-driven vendor seam,
  path/hash/readiness/optional-dependency boundary.
- `.p2p/system/p2p_uiux/router.py`: additive vendor readiness and projection
  through the existing router.
- `.p2p/vendor/skill/srt-whiteboard-animation-main/**` and
  `.p2p/vendor/skill/xiaoma-durex-copywriter-main/**`: exact snapshots.
- `tests/test_p2p_vendor_skill_integration.py` and the two vendor-specific
  expectation changes in `tests/test_p2p_capability_foundation.py`.

No legacy fallback or whole-snapshot fallback was introduced. The selected
fallback is the verified base itself when vendor readiness or optional render
dependencies are unavailable; no installation or external execution is
attempted.

## Hash evidence

| Surface | SHA-256 / tree hash | Result |
|---|---|---|
| vendor adapter | `d469a15d4edd41f05b8355d32686185b8ffb9a81c1dd89327cbfef3d246f4490` | exact supplied |
| vendor integration test | `2b5f09865afce0b245006335f8d146dcde1c4017d554a1de73db2324873d88b7` | exact supplied |
| whiteboard vendor tree | `55dbed4743cad90f80d1603ed639508c8e3a6e650a1abccfe7d4e8b2e148742c` | exact supplied |
| copywriter vendor tree | `5a02c082b531b6731dbdd6e55ccc8798ba2514bbb27df8e9c2ef74c88752830d` | exact supplied |
| reconstructed capabilities registry | `36d74ff8c7a8ef91958153efecda5b3232e804cb362e7c29c395c20d1b5cb97e` | base plus two manifests |
| reconstructed router | `9074d8b4a6fd655a55e717c661d82ddf39561247aabcb51f2b232b4f68f7f641` | base plus additive vendor projection |

The reconstructed registry/router/foundation-test hashes are not required to
equal the broken-root hashes because they were reapplied onto the valid base.

## Validation

- Clean-base C35: `python -m unittest tests.test_p2p_c35_provider_neutral_runtime`
  => exit `0`, `57/57 OK`.
- Candidate C35: same command => exit `0`, `57/57 OK`.
- Vendor integration: `17/17 OK`.
- Capability foundation: `28/28 OK`.
- Combined focused suites: `45/45 OK`.
- Build: `python -m compileall -q .p2p/system scripts tests` => exit `0`.
  One pre-existing `SyntaxWarning` remains at
  `tests/test_p2p_live_certification.py:179`; that file is outside scope.

## Doctor differential

| Doctor | Clean base | Candidate | Classification |
|---|---|---|---|
| package | exit `1`, portable requested on development checkout | exit `1`, same role mismatch | inherited / expected |
| development | exit `1`, governance drift | exit `1`, same drift; runtime/profile/config/foundation checks pass | inherited |
| capability | exit `0`, PASS, registry `13`, canonical `8/8` | exit `0`, PASS, registry `15`, canonical `8/8`; vendor records HEALTHY | attributable change is healthy |
| optional Aesthetica | RESOLVED; execution/identity not proven | same | optional-expected; not fabricated |

No candidate-only attributable doctor blocker was found. The two nonzero
doctors are not relabeled as PASS; their exact inherited causes remain visible.

## Git and Anvien scope

Before source edits the candidate worktree was clean at the exact base. After
the reconstruction, direct Git showed only the intended three tracked source
edits plus the new adapter, focused test, exact vendor trees, plan/evidence
artifacts, decision log, and this report. `git diff --stat` for tracked source
edits is `262 insertions, 4 deletions`.

Anvien was refreshed on the candidate (`927` files, `166` parsed code,
`38,325` nodes, `44,277` relationships, exit `0`) and registered under the
unique alias `p2p-vendor-reconstructed-03`. On the final bounded staged scope:

```text
anvien detect-changes --repo p2p-vendor-reconstructed-03 --scope all --json
exit=0
changed_files=44
affected_files=6
changed_count=177
risk_level=low
resolution_gap_changes=108 analyzer_gap entries
```

The graph includes text vendor files but does not fully model binary assets and
some hidden `.p2p` paths in its semantic projection. That is a documented
Anvien coverage limitation, not source absence; direct Git diff, source
inspection, hashes, and focused tests are the authority for the complete scope.

## Residual unverified surfaces

- Optional renderer dependencies were not installed and no external renderer,
  image API, network, or credential path was executed.
- Real eight-thread runtime QUORUM and named-agent identity were not claimed.
- Aesthetica execution/identity remains unproven.
- Owner approval, promotion, merge, push, release, and deployment remain
  separate unperformed gates.
- The checkpoint commit is intentionally pending the fresh supervisor verdict.

## Handoff

Technical evidence supports one unpromoted checkpoint candidate, conditional on
the independent supervisor review. The old broken-root supervisor report is not
acceptance authority for this candidate.
