#!/command/with-contenv sh
set -eu

# This wrapper runs only after Hermes' normal stage2/bootstrap lifecycle on the
# PID-1 s6 path. At this point /opt/data ownership/config migration are complete.
# Enable the bundled P2P behavior plugin as the unprivileged Hermes account so
# no root-owned runtime state is introduced into the persistent volume.
s6-setuidgid hermes /opt/hermes/.venv/bin/hermes plugins enable p2p-personal-behavior >/dev/null

# Opik remains an explicit local-stack pilot. The essential stack bind-mounts
# the plugin under HERMES_HOME and installs the exact SDK at build time. Other
# deployments keep the gate off and therefore do not acquire an observability
# dependency or external data flow.
if [ "${P2P_ENABLE_OPIK:-NO}" = "YES" ]; then
    test -f /opt/data/plugins/p2p-opik-observer/plugin.yaml || {
        echo "OPIK_PLUGIN_MISSING: /opt/data/plugins/p2p-opik-observer/plugin.yaml" >&2
        exit 2
    }
    s6-setuidgid hermes /opt/hermes/.venv/bin/hermes plugins enable p2p-opik-observer >/dev/null
fi

exec /opt/hermes/docker/main-wrapper.sh "$@"
