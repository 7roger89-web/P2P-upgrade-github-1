# P2P PROJECT BOOTSTRAP

> **Purpose (durable project identity):** this project requires the P2P
> autonomous operating loop for managed development. This file is the
> tracked, provider-neutral, model-neutral, backend-neutral binding between
> the project source and the P2P runtime. It is NOT project truth: task
> lists, business data, decisions, and product state remain in the project's
> own documents and source. It is NOT the runtime: the full `.p2p` system
> stays local and installable per the release below.

```
BOOTSTRAP_SCHEMA: p2p-project-bootstrap/1
P2P_REQUIRED: true
RELEASE_IDENTIFIER: p2p-8.4.7-C-codex.24-fw01-v1
RELEASE_ARTIFACT: P2P-8.4.7-C-codex.24-fw01-autonomous-operating-loop-candidate-v1.zip
RELEASE_SHA256: eb396dc17bd5cfb7c67a80ceff43ccd9050a6bd6fde25afe5919425d100d3d7d
RELEASE_SOURCE: https://github.com/7roger89-web/P2P-upgrade-github-1/releases/tag/p2p-8.4.7-C-codex.24-fw01-v1
ENTRY_CONTRACT_VERSION: codex-project-agents/1 (legacy compatibility ALIAS — names the Codex-class host presentation surface; NOT a P2P schema, NOT a provider authority; bootstrap authority is provider-neutral)
PROJECT_BINDING_MODE: repository-root-manifest
RUNTIME_LOCATION: local (./.p2p after install; intentionally untracked)
DOCTOR_REQUIREMENT: mandatory before first managed task
FAIL_CLOSED_POLICY: deny — without a verified runtime, no P2P-managed task
  may execute; the project must never claim P2P management silently.
ROLLBACK_SEMANTICS: removing the local runtime does NOT remove this tracked
  file; removing P2P integration requires an explicit project-source change
  (delete this file + related ignore rules) by a human.
LAST_SYNCED: 2026-08-19 (FW01 durable-bootstrap certification)
```

## What a fresh workspace can determine from this file

| Question | Answer |
| --- | --- |
| Is P2P required for this project? | Yes (`P2P_REQUIRED: true`) |
| Which release? | `p2p-8.4.7-C-codex.24-fw01-v1` |
| Which artifact, bound to what hash? | `RELEASE_ARTIFACT` + `RELEASE_SHA256` |
| Entry contract expected? | Codex project agents surface (`AGENTS.md` `<-- BEGIN P2P CODEX -->` block) |
| Where does project truth live? | In the project source itself; this manifest binds only |
| Is the local runtime present? | Check `./.p2p/system/release.json` — absent means install needed |
| How to install/verify? | `scripts/p2p-bootstrap.sh` (in the P2P package) or manual: download artifact, verify SHA-256, run `install.sh project <PROJECT_ROOT> <ARTIFACT_PATH> <ARTIFACT_SHA256>` |
| How to run doctor? | `python3 .p2p/system/scripts/doctor.py --root . --role installed --strict` |
| Rollback? | Runtime removal leaves this file; full removal requires deleting it explicitly |

## Install / verify (manual, provider-neutral)

1. Download `RELEASE_ARTIFACT` from `RELEASE_SOURCE` (or the published asset
   URL under the same tag).
2. `sha256sum <artifact>` must equal `RELEASE_SHA256`. **Mismatch → STOP.**
3. Unzip to a fresh directory; run `./install.sh project <PROJECT_ROOT> <ARTIFACT_PATH> <ARTIFACT_SHA256>` from the artifact root. The installer creates the canonical project pin from the packaged metadata.
4. Create and execute the project-owned eval suite; do not hand-write a pin or suite fixture as release evidence.
5. Run strict Doctor: `python3 .p2p/system/scripts/doctor.py --root . --role installed --strict` → HEALTHY,
   with the release marker and verified project pin present.
5. Enter project: open the repository root in a Codex-compatible host; the
   tracked entry contract (`AGENTS.md` P2P block) loads automatically; or
   invoke `$p2p` from any host that reads `.agents/skills`.

## Arena Agent Mode binding

GitHub-connected Arena work uses the canonical
[`docs/ARENA_AGENT_MODE_PROTOCOL.md`](../ARENA_AGENT_MODE_PROTOCOL.md). A fresh
Arena session reconstructs from GitHub project state, not from an earlier
Arena chat. When the project has the standard paths, read them in this order:

1. `AGENTS.md`;
2. the project master specification;
3. `docs/CURRENT_STATE.md`;
4. `production/SESSION_INDEX.md`;
5. the latest accepted session report;
6. task-specific projected P2P capabilities; and
7. the Arena Agent Mode protocol.

If a project uses different canonical names, bind the order to those actual
files. Do not create duplicate state documents just to satisfy this list. The
projection remains selective and plan-declared through the existing P2P host
projection and project-pin contracts; this bootstrap file does not add a new
materializer or runtime path.

## Why this design

| Concern | Resolution |
| --- | --- |
| Do not commit `.p2p` runtime | Runtime stays local/untracked; only the manifest is tracked |
| Provider/model/backend neutral | Manifest names a release, not a vendor, model, or backend |
| Fail closed | Doctor is mandatory; missing/failed runtime → no P2P-managed work; manifest absence → project never silently "is P2P" |
| No secrets | Manifest contains only release identity + policy; no credentials |
| No duplicated project truth | No task lists, business data, or decisions copied here |
| Single authority | Exactly one tracked manifest per project; installer never creates a second |
| Rollback semantics | Tracked bootstrap != local runtime; each removable separately |

## Known certification gap (FW01 fresh-clone evidence)

During fresh-clone certification the published FW01 artifact's governance
lock (`live-specs.lock.json`) references the Live Specs technical preview
report at an absolute developer-machine path (`/home/ubuntu/p2p-repo/...`
with SHA `e96a1d5b...`). The rev-3 preview file is versioned in the P2P
repository tree (hash matches the lock) but is not shipped inside the
package, the canonical installer copies `governance/` verbatim without
rebinding absolute references, and path resolution accepts the absolute
path with no fallback. Consequently `doctor` FAILs on a genuinely
fresh workspace (`Live Specs technical preview report is missing`), the
release marker is not written, and `install` exits 1. Failure class:
`DOCTOR_PATH_RESOLUTION_BUG` (contributing: package-layout mismatch) — not a
payload/integrity defect; the package is intact. Silently rewriting the
lock would violate fail-closed governance evidence rules, and re-minting
is owner-authorized separately. The minimal correction is install-time
rebinding of the lock's `technical_report`/`approval_record` to
package-relative copies (or packaging the rev-3 preview with a relative
reference). Until that correction ships, fresh-workspace bootstrap MUST
report `DOCTOR=BLOCKED` rather than proceeding silently — the fail-closed
policy above handles exactly this case.

## Integrity

This file is tracked in git. Its presence in the repository root (or path
declared in a project's `.gitignore` complement) is the durable signal that
**this project uses P2P**. Any host that can read git files can discover it.
Auto-discovery by every AI host is NOT claimed — see FW01 terminal report
host-discovery honesty table.
