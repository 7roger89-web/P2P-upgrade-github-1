#!/bin/sh
# CloudDesk pilot workspace preparation.
#
# Resets ONE disposable synthetic workspace to a pristine state and plants the
# *hostile* symlink fixtures the workspace-boundary probe needs. The symlinks
# cannot be created through MCP tools (apply_patch refuses symlink writes), so
# they are pre-planted out-of-band to model a repository that already contains a
# malicious symlink before any agent connects.
#
# Everything the validation harness itself uses is created through MCP tools only.
#
# WARNING: this wipes the workspace directory. Only ever point it at a
# disposable synthetic pilot workspace -- never at a real repository.
#
# Usage (as root, or via sudo):  prepare_workspace.sh [WORKSPACE_ROOT]
set -e

WORKSPACE="${1:-/srv/clouddesk-pilot/workspace}"
PILOT_USER="${PILOT_USER:-ctmpilot}"
RUNTIME_DIR="${RUNTIME_DIR:-/srv/clouddesk-pilot/runtime}"

if [ "$(id -u)" -eq 0 ]; then
    RUNAS="setpriv --reuid=$PILOT_USER --regid=$PILOT_USER --init-groups"
else
    RUNAS=""
fi

case "$WORKSPACE" in
    /|/etc|/usr|/bin|/sbin|/var|/home|/root|/srv)
        echo "REFUSING to wipe protected path: $WORKSPACE" >&2
        exit 2
        ;;
esac

# The workspace's parent directory is root-owned, so removing/creating the
# workspace entry itself needs root; the contents are then created as the pilot
# user so every file is owned by the identity the MCP server runs as.
if [ "$(id -u)" -eq 0 ]; then
    rm -rf "$WORKSPACE"
    mkdir -p "$WORKSPACE"
    chown "$PILOT_USER:$PILOT_USER" "$WORKSPACE"
    chmod 700 "$WORKSPACE"
else
    $RUNAS rm -rf "$WORKSPACE"
    $RUNAS mkdir -p "$WORKSPACE"
fi

export HOME="$RUNTIME_DIR"
$RUNAS env HOME="$RUNTIME_DIR" git -C "$WORKSPACE" init -q -b main
$RUNAS env HOME="$RUNTIME_DIR" git -C "$WORKSPACE" config user.email "pilot@clouddesk.invalid"
$RUNAS env HOME="$RUNTIME_DIR" git -C "$WORKSPACE" config user.name "CloudDesk Pilot"

$RUNAS mkdir -p "$WORKSPACE/hostile"
$RUNAS ln -sfn /etc/passwd "$WORKSPACE/hostile/escape-passwd"
$RUNAS ln -sfn /etc "$WORKSPACE/hostile/escape-dir"
$RUNAS ln -sfn /nonexistent-target "$WORKSPACE/hostile/dangling"

echo "workspace reset: $WORKSPACE"
$RUNAS env HOME="$RUNTIME_DIR" git -C "$WORKSPACE" status --short --branch
echo "hostile symlink fixtures planted in $WORKSPACE/hostile:"
ls -l "$WORKSPACE/hostile"
