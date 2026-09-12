# P2P Shield Slice 2 — minimum BASE profile

Status: `CANDIDATE_UNPROMOTED`. Goal: `P2P_SHIELD_V0_2_BASE_PROFILE_MINIMUM`.
No promotion, deployment, production change, or Slice 3 work.

## Authority and fresh state

- Read canonical `main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md`, section
  `P2P_SUPREME_OPERATING_LAW_V1`, at main SHA
  `6306fde0eb992e11bab4199e32561bb6f87b05e1`. No law edits.
- Read `docs/p2p-shield-plan:docs/p2p-development/P2P-SHIELD-PLAN.md`.
  Fresh candidate base: `cd1ef83e7938188bef9577408c39d632b93bb0de`;
  PR #101 confirmed merged. No material checkpoint drift.
- Session branch: `arena/01a09301-p2p-upgrade-github-1`. Its clean initial
  main-based checkout was aligned to the candidate before implementation.
- PR: https://github.com/7roger89-web/P2P-upgrade-github-1/pull/102
  Base `docs/p2p-shield-plan`; leave unmerged.

## Implemented boundary

Exactly `SHIELD-SECRET-01@0.1.0` + `SHIELD-DEPENDENCY-01@0.1.0` in
`SHIELD-BASE@0.1.0`. Secret control requires BOTH history and worktree records;
its implementation, mapping, acquisition and acceptance files are unchanged.

Dependency qualification is deliberately narrow: explicitly supplied
`requirements.txt` files with exact PyPI `name==version` entries. Every declared
inventory entry must appear in the provider report; missing, unsupported,
empty, malformed, mismatched or unreliable inventory blocks. No package is
installed. Other dependency formats are not qualified by this slice.

OSV-specific acquisition was simpler than generalizing the Gitleaks tarball
acquirer: OSV ships a direct executable and uses `--version`. No shared-code
mutation, registry, factory, plugin loader or dynamic discovery was needed.
Exact repository/tag/asset gates remain explicit. Official upstream release:
https://github.com/google/osv-scanner/releases/tag/v2.4.0

`osv-scanner_linux_amd64` was checked against the exact release's official
`osv-scanner_SHA256SUMS` before execution. Observed version: `2.4.0`.
Observed binary SHA-256:
`15314940c10d26af9c6649f150b8a47c1262e8fc7e17b1d1029b0e479e8ed8a0`.
No mirror, Docker, package-manager fallback, source build or provider upgrade.

## Verified evidence

Acceptance code head: `764e308`.
Hosted run: https://github.com/7roger89-web/P2P-upgrade-github-1/actions/runs/34661860444
Result: **SUCCESS**. Job `base`, ID `103465839556`.

| Case | Real result |
| --- | --- |
| `idna==3.15`, temporary Git repo | Secret history PASS, secret worktree PASS, dependency PASS, 0 findings; profile PASS |
| `Django==1.11.29`, metadata only | Dependency FAIL, 16 advisory records; expected `GHSA-8x94-hmjh-97hq` observed; profile FAIL |
| Missing executable | Dependency BLOCKED; profile BLOCKED |
| Missing dependency evidence | Profile BLOCKED |
| Every profile result | `SYSTEM_SECURITY_VERDICT=NOT_EVALUATED` |

38 focused unittest cases passed locally and hosted (8 Slice-2 tests, 30
unchanged Slice-1 tests). Hosted unchanged Slice-1 real acceptance also passed
its six clean/leak/unavailable/non-Git cases using Gitleaks `8.18.4`.

Logs and step summary contain full scoped records. The ten BASE annotations
preserve acquisition, dependency records, composition results and the terminal
acceptance result, without an artifact service. Secret records also remain in
job logs/summary. Arena cannot download the Actions log storage URLs; the
Actions annotations and step states were independently inspected through GitHub.

Earlier runs `34661774758` and `34661811065` did not pass: initial PASS fixture
`idna==3.10` correctly matched `GHSA-65pc-fj4g-8rjx` / `PYSEC-2026-215`.
The official GitHub advisory identified `3.15` as first patched. Only fixture
metadata was corrected; no finding was suppressed and no provider changed.
The second run added annotations to recover accessible evidence, not a new
infrastructure path.

## Use and interpretation

The hosted workflow is `.github/workflows/p2p-shield-base-slice.yml`: Ubuntu,
read-only contents, exact-SHA checkout, no persisted Git credentials, no deploy.
`python3 -m shield.base_acceptance` is the real-provider runtime harness.
`shield.osv_acquire.acquire(directory)` returns an executable and a checksum
receipt. Dependency CLI requires explicit target, executable, manifest and
reference; profile CLI requires explicit expected target/ref and evidence files.

The receipt binds the local executable bytes to acquisition in a trusted
assessment session. It is not a signed remote attestation: a malicious actor
able to rewrite both executable and receipt is outside this trust boundary.
Checksum verification relies on official HTTPS release integrity, not an
independently verified publisher signature. Network/API failure blocks; no
offline database, cache or mirror was introduced.

Profile evaluator checks all required scopes, control versions, target and
Git HEAD, evidence fields, statuses/counts and coverage presence. Missing or
invalid evidence has precedence over FAIL; among valid complete evidence,
FAIL has precedence over BLOCKED. It composes trusted runner evidence, not
arbitrary adversarial attestations. Caller supplies expected target/ref and
must obtain fresh records for a changed working tree; HEAD alone is not a
working-tree content digest or universal evidence TTL. No system-wide verdict
is inferred. Findings count is advisory records, not deduplicated root causes
or exploitability/severity claims. Published OSV data changes over time.

## OE gate — Không bị over engineering chứ?

1. Simpler equivalent path? Keep Slice 1 unchanged and use one small OSV helper.
2. New capability/evidence? Dependency assessment and two-control composition.
3. Omitting a component? Would remove a requested contract or acceptance proof.
4. Main capability, not ancillary infrastructure? Yes; only runtime fixtures,
   one workflow and logs/annotations/summary.
5. Smaller while proving BASE? Restrict qualification to pinned PyPI metadata,
   require both existing secret scopes, and defer all other controls.

No generic plugin framework; no new security platform. Explicitly deferred:
SAST, CI workflow scanner, DAST, authn/authz, backup/recovery, AI/RAG, egress,
zizmor, CodeQL, Trivy, CyberStrikeAI, ZAP, promptfoo and OPA. No PRIVATE/VAULT,
second dependency provider, database, daemon, dashboard, SIEM/SOC, Kubernetes,
service mesh or custom cryptography.

`SLICE_VERDICT=PASS` for this bounded acceptance only.
`SYSTEM_SECURITY_VERDICT=NOT_EVALUATED`.
`NEXT_ACTION=RETURN_TO_P2P_CONTROL_TOWER_FOR_REVIEW`.
