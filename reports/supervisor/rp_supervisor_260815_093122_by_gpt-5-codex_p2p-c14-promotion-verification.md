# Supervisor Report — P2P-C14 Promotion Verification

- Verdict: **PASS**
- Scope: collision resolution and promotion verification for P2P-C14 only.
- Protected code, source candidate bytes, and unrelated projects were not changed.

## Collision resolution

- Source was re-hashed before mutation: `D:\AI\P2P_dev\P2P-8.4.7-C-Codex-Edition-v19.zip`.
- Source SHA-256: `f1209c441edaff20ccc3e40f0be0b8b9baa5625ca5ae3599bcc81c3e42d55b61`.
- Source embedded version: `8.4.7-C-codex.15`.
- Archive directory was absent and was created within the owner-authorized path.
- Archive destination was absent before move; no overwrite flag was used.
- Stale artifact was moved to `D:\AI\P2P_dev\archive\stale-artifacts\P2P-8.4.7-C-Codex-Edition-v19__STALE_EMBEDDED-15__f1209c441edaff20.zip`.
- Archived SHA-256 remained `f1209c441edaff20ccc3e40f0be0b8b9baa5625ca5ae3599bcc81c3e42d55b61`.
- The original path was empty after the move. No rollback was needed because promotion succeeded.

## Approval and promotion binding

- Candidate path: `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4\.tmp\p2p-c14-final\P2P-8.4.7-C-Codex-Edition-v19.zip`.
- Candidate SHA-256 before promotion: `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`.
- Candidate embedded version: `8.4.7-C-codex.19`.
- Approval request: `P2P-APR-20260815T013545Z-0068b3047f`.
- Approval state: `APPROVED`; canonical approval verification: `PASS`.
- Technical report SHA-256: `a85e83faffcb1f10efd5a772019c877ff8c8e85e3aae5a38e73a5e933671cf46`; report status: `PASS`; failures: `0`.
- Final gate status: `PASS`; release decision: `APPROVED`; subject and technical-report bindings matched exactly.
- After archive, the canonical `.19` destination was empty.
- Promotion used a byte-preserving, non-overwriting copy of the exact approved candidate. No rebuild and no version change occurred.

## Post-promotion verification

- Promoted path: `D:\AI\P2P_dev\P2P-8.4.7-C-Codex-Edition-v19.zip`.
- Promoted SHA-256: `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`.
- Promoted `VERSION`, runtime version, package manifest version, runtime manifest package version, and release-manifest package version all equal `8.4.7-C-codex.19`.
- Release manifest: package version `.19`, generated at `2026-08-15T01:12:35+00:00`, file count `406`.
- Package doctor: `PASS`.
- Capability doctor: `PASS`; registry valid; canonical denominator `8`; full quorum `8/8`; optional specialist excluded from denominator; no external provider required.
- UI/UX doctor: `PASS`; package version `.19`; no errors.
- Design Intelligence discovery from the promoted runtime: `status=READY`, `design_mode=NUI_BACKED_DESIGN`, single router `p2p_uiux.router.classify_request`, registry faculty count `174`.
- NUI registry: schema `p2p-nui-registry/1`; canonical faculty count `174`; skill map count `174`; bodies loaded at bootstrap `0`; runtime network fetch `false`; automatic update `false`.
- NUI provenance: upstream revision `46780cdd58e41bea8338b2d27269d339c95e28e7`, MIT license, graph SHA bound to the lock; registry lock SHA matched actual `nui_registry.json` SHA `b1790ff1c5b793996cf2d57905b556d54fee2eb975cc2a0b0504c8a08eddd0d3`.
- Canonical identities: `p2p_iris`, `p2p_tecton`, `p2p_axiom`, `p2p_vector`, `p2p_datos`, `p2p_anon`, `p2p_architecton`, `p2p_helios`; count `8`; quorum `8/8`.
- Approval-to-release linkage: `PASS`; promoted SHA equals the approved subject SHA and final-gate subject SHA; approval request ID and technical-report SHA match.

## Mutation and scope review

- Stale artifact was moved, not deleted, overwritten, rebuilt, or modified in bytes.
- Approved candidate remained byte-identical and was promoted only to its authorized canonical `.19` path.
- No other release, official artifact, protected project, connector, network, hook, or proxy was touched.

Conclusion: `PROMOTED_VERIFIED / OFFICIAL_8.4.7-C-codex.19`.
