# Arena Owner Continuation Gate — rollout receipt

Date: 2026-09-22

Canonical P2P main at rollout:
`49d8550d2aa0fae438c992490924673bc227e55c`

Canonical notebook source SHA-256:
`ac65fb5855081611a8884a036d55d79b081d2721fdbafe2760ac527dbb9de7ba`

Package:
`8.4.7-C-codex.74`

## Owner-selected flow

```text
REAL TASK
  -> FIRST SAFE SLICE = FAST_CANARY
  -> CANARY_EVIDENCE_PACKET_V1
  -> CONTROL TOWER / INDEPENDENT GRADE
  -> OWNER CONTINUATION GATE
  -> CONTINUE | LIMIT | REROLL
```

For Arena surfaces that expose the native continuation affordance, use the
product's Keep working/Continue action. The executor does not control or fake UI
rendering. Fallback Owner reply is:

`Tiếp tục công việc`

External grading remains authoritative; the tested Arena session does not grade
itself.

## 15-repository audit

Detection follows the existing `scripts/p2p_sync_managed_projects.py`
contract: a repository is P2P-managed when durable P2P markers exist
(managed AGENTS block / legacy P2P CODEX block / portable or installed P2P
surface). No new registry/database is introduced.

### Canonical authority

| Repository | Main | Status |
| --- | --- | --- |
| `P2P-upgrade-github-1` | `49d8550d2aa0fae438c992490924673bc227e55c` | CANONICAL_CURRENT |

### P2P-managed projects — current

All rows below were fresh-read after rollout. Each has:
- managed `<!-- BEGIN P2P PORTABLE LAW -->` entrypoint;
- `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md`;
- source hash `ac65fb5855081611a8884a036d55d79b081d2721fdbafe2760ac527dbb9de7ba`;
- `OWNER_CONTINUATION_GATE_V1`.

| Repository | Main after rollout | Notes |
| --- | --- | --- |
| `Du_An_Gia_Pha-github` | `160850e1dbcc6f35b73b4b621bf94f88dc9558e9` | portable refreshed |
| `game-truyen-github` | `a66c4a204c2e839906cddcedd50f25e6ad41e8b6` | migrated legacy P2P CODEX repo; existing CODEX block preserved |
| `thien-ha-ai-2d5` | `8fa6c52fdf840cdb63733388437cae8a4118cdd8` | portable refreshed |
| `p2p-video-lab` | `a4f4452a1ffd188bb442f3736d3d32402ea77791` | portable refreshed |
| `logistics-work-desk-arena` | `4a36a748329ac4d8406e8832b5509ae5e948a7c1` | portable refreshed |
| `ziping-bazi-research` | `c17774057b9861f7790cfa71ed8398ce463d9de1` | portable refreshed after BAZI bug fix |
| `VNLAW` | `dddd4cd95285706309efb9ba56ea63f4f8281d1f` | portable refreshed |
| `child-learning-lab` | `311823a751383fb0542e5d5b3b660f6c98cd07b6` | portable refreshed |
| `1ziping-bazi-pilot` | `92c8c5c24472df0360505a1d84d20dc6774c0f95` | portable refreshed |
| `huyen-hoc-lab` | `4ff033562a136834999716cb424b37a5d44dd3fe` | added portable fallback + exact managed AGENTS block |

### Repositories intentionally not mutated

These repositories do not carry current durable P2P-managed markers under the
existing detector, so this rollout does not install P2P into them implicitly.

| Repository | Main | Audit result |
| --- | --- | --- |
| `logistics-work-desk` | `2eb2c343c10c2f909685f1f83cb77683197572f8` | no current P2P managed marker; skipped |
| `cloudflare_temp_email` | `0bd06db91fdb390bdc66089ef57c2c273313f8d5` | no AGENTS / no portable marker; skipped |
| `logistics-demo` | `535c9d12a436ddbb97f46c72a022f9ffe69150e5` | no AGENTS / no portable marker; skipped |
| `logi-good` | `974b7cfff2a73ef78d53b7233e1ae932063a5dcf` | no AGENTS / no portable marker; skipped |

## Rollout PRs

- P2P canonical: PR #238
- Gia Phả: PR #15
- Thiên Hạ AI 2D5: PR #14
- P2P Video Lab: PR #22
- Logistics Arena: PR #94
- BAZI: PR #118
- VNLAW: PR #103
- Child Learning Lab: PR #29
- BAZI pilot: PR #16
- Huyền Học Lab: PR #6 + #7 (portable fallback, then exact managed block)
- Game Truyện: PR #4

## Acceptance

```text
REPOSITORIES_AUDITED=15
CANONICAL_P2P=1
P2P_MANAGED_PROJECTS=10
P2P_MANAGED_CURRENT=10
INTENTIONALLY_UNMANAGED_OR_REFERENCE=4
STALE_MANAGED_PROJECTS=0
BLOCKED_MANAGED_PROJECTS=0
```

Future P2P-managed repositories inherit the continuation behavior from the
canonical installer/projector path; no project-specific reimplementation is
required.

This report is evidence only. It is not a project registry and does not replace
the existing durable-marker discovery mechanism.
