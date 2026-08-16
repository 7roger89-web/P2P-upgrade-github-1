#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to build the integrity-checked P2P release" >&2
  exit 2
fi
args=("$root/scripts/package_release.py" --root "$root" build)
if [[ $# -gt 0 ]]; then
  args=("$root/scripts/package_release.py" --root "$root" --output "$1" build)
fi
exec python3 "${args[@]}"
