---
name: pxpipe
description: >-
  Preserve and audit the experimental P2P PXPIPE optical-compression scripts without
  enabling them. Use only for explicit security review, dependency inspection, offline
  measurement review, or a deliberate future port; never invoke implicitly.
---

# PXPIPE — preserved but disabled

The original scripts are retained for audit and parity. They assume Anthropic
image-token accounting, Claude-specific reader gates, proxy variables, and
unverified model behavior. Those assumptions do not establish Codex support.

## Gate

1. Keep proxying and compression disabled.
2. Review `package.json`, all scripts, transitive dependencies, data paths, and
   output handling before any install.
3. Verify current OpenAI image/token behavior through official documentation.
4. Test only with non-sensitive synthetic data in an isolated project.
5. Require explicit user approval before installing dependencies or writing
   compressed artifacts.

Do not treat an offline pixel estimate as a billing guarantee, do not replace
byte-exact text with an image, and do not use `--force` to bypass a failed gate.
The untouched upstream component also remains under `experimental/pxpipe-source`.
