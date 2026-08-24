# Notes and Decisions Log — 2026-08-24

## P2P AERG Development-Plane Reconciliation

- Decision: reconcile the historical provider-neutral AERG subject as a
  bounded in-memory evidence/assurance layer on the post-C43 development
  plane; preserve current evidence, QI, FW01, role-verifier, and owner
  authority boundaries.
- Implementation checkpoint: `fc1b9dc` — `AERG: reconcile provider-neutral
  evidence assurance`.
- Invariant closure: structured exact subject binding, deterministic claim
  identity, freshness/provenance/assurance/authority dimensions, structured
  contradiction precedence, and fail-closed unsupported evidence.
- Integration: AERG is lazy and post-execution at the existing FW01 seam;
  current QI receives only the optional bounded result; RF01 README-first
  orientation does not auto-load it.
- Validation: AERG 26/26 matrix and 12 tests PASS; QI 44/44 plus one skip;
  full hidden capability suite 347/347 plus six skips; checkpoint 6/6;
  composition 7/7; C43 9/9; RF01 orientation 7/7 and packaging 2/2;
  compileall exit 0.
- Governance: one current `AI_EXECUTION_RELIABILITY_GUARD` record is
  `FOUNDATION_READY` under `VERIFICATION_AND_EVALUATION`; this is not a
  release/promotion/certification authority.
- Preserved boundary: `.19` remains `PROMOTED_VERIFIED`; `.74` remains
  `SEALED_UNPROMOTED / NONCANONICAL`; CPT01-R2 remains
  `EXTERNAL_HOST_CAPABILITY_LIMITATION`; `promotion.allowed=false` remains
  unchanged; no host/release/promotion/deployment mutation occurred.
- Inherited failures: framework validator 52/59 with seven inherited
  residuals, the rail validator external-path failure, and the absent FW01
  closure fixture remain visible and are not reclassified as AERG failures.
- Coder report:
  `reports/coder/rp_coder_260824_140503_by_gpt-5-codex_p2p-aerg-reconciliation.md`.
- Next safe action: supervisor review only, then stop for owner direction.
