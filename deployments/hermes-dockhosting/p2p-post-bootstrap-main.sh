#!/command/with-contenv sh
set -eu

# This wrapper runs only after Hermes' normal stage2/bootstrap lifecycle on the
# PID-1 s6 path. At this point /opt/data ownership/config migration are complete.
# Enable the bundled P2P behavior plugin as the unprivileged Hermes account so
# no root-owned runtime state is introduced into the persistent volume.
s6-setuidgid hermes /opt/hermes/.venv/bin/hermes plugins enable p2p-personal-behavior >/dev/null

# NotebookLM is optional and secret-gated. When no auth state is configured,
# the plugin stays disabled/hidden and the existing Hermes Telegram runtime is
# unchanged.
if [ -n "${NOTEBOOKLM_AUTH_JSON:-}" ]; then
    s6-setuidgid hermes /opt/hermes/.venv/bin/hermes plugins enable notebooklm-knowledge >/dev/null
fi

# Opik remains explicit opt-in. The reusable P2P Hermes image bundles the
# observer plugin; the local essential stack may additionally bind-mount the
# same source under HERMES_HOME while iterating. No telemetry is enabled merely
# by bundling the plugin. A build that opts into runtime telemetry must also
# contain the exact Opik SDK, otherwise fail closed at startup instead of
# pretending observability is active.
if [ "${P2P_ENABLE_OPIK:-NO}" = "YES" ]; then
    if [ -f /opt/hermes/plugins/p2p-opik-observer/plugin.yaml ]; then
        :
    elif [ -f /opt/data/plugins/p2p-opik-observer/plugin.yaml ]; then
        :
    else
        echo "OPIK_PLUGIN_MISSING: expected bundled or HERMES_HOME plugin" >&2
        exit 2
    fi
    s6-setuidgid hermes /opt/hermes/.venv/bin/python -c 'import importlib.metadata, opik; assert importlib.metadata.version("opik") == "2.2.59"' >/dev/null || {
        echo "OPIK_SDK_MISSING_OR_WRONG_VERSION: build with P2P_INSTALL_OPIK=1" >&2
        exit 3
    }
    s6-setuidgid hermes /opt/hermes/.venv/bin/hermes plugins enable p2p-opik-observer >/dev/null
fi

exec /opt/hermes/docker/main-wrapper.sh "$@"
