# P2P FCC Local Bus — strict loopback lane

Status: `SOURCE_CANDIDATE_UNPROMOTED`

Date: 2026-09-15

Upstream inspected:

- `Alishahryar1/free-claude-code`
- commit `22d9d19f5e7a1b31f7d8fccff6fef77cbb19357f`
- FCC `6.2.28`

## Goal

Turn the existing P2P FCC adapter into a usable **strict local discovery +
certification path** for read/search/analyze work without creating another
router and without pretending a local model is present when it is not.

This slice does not install a model, mutate FCC config, certify code mutation,
promote/release anything, or claim the Owner Windows host has passed live
certification before the command actually succeeds there.

## Reused architecture

```text
P2P task decision
  -> existing BackendAdapterRegistry / BackendExecutionBridge
  -> fcc-claude adapter (permission-mode=plan)
  -> running FCC server
  -> strict local provider/model
```

No second P2P router is added.

The older `scripts/free_model_probe.py` remains the cloud/free provider probe.
It is not duplicated. `fcc_local_bus.py` covers the different problem of
loopback local model discovery and FCC egress safety.

## Local discovery

The source gate recognizes only these local FCC provider namespaces:

| FCC provider | Default loopback URL | Discovery |
|---|---|---|
| `ollama` | `http://127.0.0.1:11434` | `/api/tags` |
| `lmstudio` | `http://127.0.0.1:1234/v1` | `/models` |
| `llamacpp` | `http://127.0.0.1:8080/v1` | `/models` |

Configured FCC base URLs are read from the running FCC Admin config. Any local
provider URL that is not loopback (`127.0.0.1`, `localhost`, `::1`) is rejected
for this lane. Probes explicitly disable HTTP proxy inheritance so a failed
localhost service cannot accidentally escape through `HTTP_PROXY`.

## Why a runtime fallback gate is mandatory

FCC 6.2.28 resolves even a direct provider/model reference to a primary target
plus ordered `MODEL_FALLBACKS`. Therefore:

```text
--model ollama/qwen
```

does **not** by itself prove a request cannot fall back to a cloud provider.

Before a P2P strict-local task runs, the certification command launches an
**isolated temporary FCC server** and queries that running instance at its
loopback-only Admin API:

```text
GET /admin/api/config
```

and requires:

1. the selected model ref is `ollama/*`, `lmstudio/*`, or `llamacpp/*`;
2. `MODEL_FALLBACKS` is present in effective runtime config;
3. every configured fallback is also one of those local namespaces;
4. every involved provider base URL resolves to loopback.

Anything unknown or cloud-capable fails closed.

This proves **loopback transport policy**, not a universal physical-compute
claim. A local daemon that independently proxies work elsewhere is outside this
slice; obvious model labels containing `cloud`/`remote` are merely deprioritized,
not treated as cryptographic proof.

## Live certification command

From the P2P repository on the intended execution host:

```powershell
python scripts/p2p_fcc_local_certify.py
```

Optional exact model:

```powershell
python scripts/p2p_fcc_local_certify.py --model ollama/qwen2.5-coder:7b
```

The command:

1. verifies `fcc-server` and `fcc-claude` are installed;
2. discovers local models directly on loopback;
3. picks a coding-oriented candidate deterministically unless one is pinned;
4. creates a temporary FCC config containing only the selected local route,
   blank `MODEL_FALLBACKS`, loopback provider URLs, and a temporary auth token;
5. launches a temporary `fcc-server` on a random `127.0.0.1` port with a
   whitelisted child environment that carries no cloud credentials/proxy vars;
6. asks that running server's Admin API for its **effective** config and applies
   the strict local fallback/URL gate;
7. runs the existing `fcc-claude` adapter with `--permission-mode plan`;
8. requires the marker `P2P_FCC_LOCAL_OK`;
9. terminates the temporary FCC server and removes the temporary config;
10. leaves normal adapter evidence under `.p2p/evidence/fcc-local/`.

The normal/global FCC config is not modified and an already-running FCC server
is not reused.

Terminal success:

```text
PASS_LOCAL_ONLY_READ_ANALYZE
```

Safe blocks include:

```text
BLOCKED_FCC_BINARIES_MISSING
BLOCKED_NO_LOCAL_MODEL
BLOCKED_FCC_FALLBACK_EGRESS_UNSAFE
BLOCKED_FCC_LOCAL_PROVIDER_URL_NOT_LOOPBACK
BLOCKED_FCC_CLAUDE_NOT_READY
BLOCKED_LIVE_TASK_NOT_VERIFIED
```

## Acceptance boundary

Deterministic source acceptance requires:

- local payload parsing for Ollama, LM Studio and llama.cpp;
- coding-model ranking;
- cloud fallback fail-closed;
- non-loopback provider URL fail-closed;
- all-local fallback acceptance;
- missing runtime fallback field fail-closed;
- FCC port resolution from current env / managed env;
- existing FCC adapter CI remains green.

Live certification remains host-specific. A merge of this source is **not**
proof that the Owner Windows host has FCC or a local model. The certifier itself
owns the temporary FCC server lifecycle, so the Owner does **not** need to start
or reconfigure a normal FCC server first.
