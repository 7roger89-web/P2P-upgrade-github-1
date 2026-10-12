# Notes & Decisions Log — 2026-10-12

## Issue #333 — signed generic repo-read admission

- Candidate: PR #348.
- Coder report: [Issue #333 Signed Generic Repo-Read Admission](../../reports/coder/rp_coder_261012_171000_by_gpt-5-6-sol_issue-333-signed-generic-read-admission.md).
- Source/runtime verification head: `6020a3c7fbbda46ccc572678916ab828faa25dac`.
- Real external actor: `GITHUB_COPILOT_CLI_ACTIONS`; canary `38235241033` PASS.
- GitHub OIDC evidence verification PASS; evidence SHA-256 `7db1aeda5f42c3d6e386b53fd41befb04d08c2bb9137725747764a2e8d9dfd93`.
- Shield `38235247660` PASS; focused 366 PASS; diagnostic remains baseline `FAIL / 22 findings`.
- Decision: generic admission requires current C21 + verified GitHub-signed actor-read evidence. C21-only/self-report remains insufficient; native ARENA/CODEX and PROMPT_ONLY remain unchanged.
- Reality correction: `actions/attest` was unavailable for this user-owned private repo; final design uses GitHub Actions OIDC JWT verification.
- Status: closure artifacts queued for fresh exact-head CI, then independent Supervisor. No merge/release/deploy/promotion in Writer role.
