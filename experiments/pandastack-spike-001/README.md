# P2P PandaStack Spike 001

Status: **PILOT / NONCANONICAL / UNPROMOTED**

Purpose: verify PandaStack as a possible P2P execution substrate without changing P2P routing, authority, release, or production behavior.

## Acceptance

The spike passes only when one live PandaStack run proves:

1. a hosted sandbox can be created;
2. commands execute inside the sandbox;
3. files can be written and read;
4. a public Git repository can be cloned;
5. a tiny HTTP service can be exposed through a preview URL;
6. a forked child inherits prepared disk state and can diverge independently;
7. all sandboxes are explicitly cleaned up.

Private-repo push / PR creation is a **separate credential-gated follow-up**. This spike does not store or hardcode GitHub or PandaStack credentials.

## Run

Python 3.9+:

```bash
cd experiments/pandastack-spike-001
python -m pip install -r requirements.txt
export PANDASTACK_API_KEY=pds_...
python spike.py
```

Optional:

```bash
export P2P_SPIKE_CLONE_URL=https://github.com/octocat/Hello-World.git
```

Expected terminal result:

```text
PANDASTACK_SPIKE_RESULT=PASS
```

If the key is missing:

```text
PANDASTACK_SPIKE_RESULT=BLOCKED
OWNER_GATE=PANDASTACK_API_KEY_REQUIRED
```

## Boundary

- No merge or promotion.
- No production deploy.
- No P2P router/orchestrator changes.
- No persistent sandbox.
- TTL is bounded.
- Preview URL is treated as temporary capability evidence only.
- Secrets are read from environment variables only.
