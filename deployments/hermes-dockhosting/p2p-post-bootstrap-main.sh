#!/command/with-contenv sh
set -eu

# This wrapper runs only after Hermes' normal stage2/bootstrap lifecycle on the
# PID-1 s6 path. At this point /opt/data ownership/config migration are complete.
# Enable the bundled P2P behavior plugin as the unprivileged Hermes account so
# no root-owned runtime state is introduced into the persistent volume.
s6-setuidgid hermes /opt/hermes/.venv/bin/hermes plugins enable p2p-personal-behavior >/dev/null

exec /opt/hermes/docker/main-wrapper.sh "$@"
