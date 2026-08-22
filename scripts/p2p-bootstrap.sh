#!/usr/bin/env bash
# P2P PROJECT BOOTSTRAP HARNESS — deterministic, provider-neutral.
#
# Usage:
#   ./scripts/p2p-bootstrap.sh discover        # inspect tracked bootstrap only
#   ./scripts/p2p-bootstrap.sh verify-sha      # fetch + sha256 check of release asset
#   ./scripts/p2p-bootstrap.sh detect-runtime  # local runtime present? (0/1)
#   ./scripts/p2p-bootstrap.sh install         # canonical install via release artifact
#   ./scripts/p2p-bootstrap.sh doctor          # run project doctor
#   ./scripts/p2p-bootstrap.sh doctor-status   # HEALTHY / UNHEALTHY only
#
# No network activity occurs in `discover` or `detect-runtime`.
# `verify-sha` and `install` need the release asset reachable (asset URL via
# env FW01_ASSET_URL or the canonical GitHub releases API with token).
# Fail-closed: any verification failure exits non-zero and prints STOP.
set -uo pipefail

BOOTSTRAP="P2P-PROJECT-BOOTSTRAP.md"
PROJECT_ROOT="${P2P_PROJECT_ROOT:-$PWD}"
BOOTSTRAP_PATH="$PROJECT_ROOT/$BOOTSTRAP"
SYSTEM="$PROJECT_ROOT/.p2p/system"
RELEASE_MARKER="$SYSTEM/release.json"

field() { # extract VALUE of FIELD: from the tracked bootstrap (deterministic)
  grep -m1 "^$1:" "$BOOTSTRAP_PATH" | sed 's/^[^:]*: *//' | tr -d '\r'
}

cmd_discover() {
  if [[ ! -f "$BOOTSTRAP_PATH" ]]; then
    echo "BOOTSTRAP_ABSENT"
    exit 1
  fi
  schema="$(field BOOTSTRAP_SCHEMA)"
  if [[ "$schema" != "p2p-project-bootstrap/1" ]]; then
    echo "BOOTSTRAP_SCHEMA_UNSUPPORTED: $schema"
    exit 2
  fi
  echo "TRACKED_PROJECT_BOOTSTRAP=FOUND"
  echo "P2P_REQUIRED=$(field P2P_REQUIRED)"
  echo "RELEASE_IDENTIFIER=$(field RELEASE_IDENTIFIER)"
  echo "RELEASE_ARTIFACT=$(field RELEASE_ARTIFACT)"
  echo "RELEASE_SHA256=$(field RELEASE_SHA256)"
  echo "ENTRY_CONTRACT_VERSION=$(field ENTRY_CONTRACT_VERSION)"
  echo "PROJECT_BINDING_MODE=$(field PROJECT_BINDING_MODE)"
  echo "DOCTOR_REQUIREMENT=$(field DOCTOR_REQUIREMENT)"
  echo "FAIL_CLOSED_POLICY=$(field FAIL_CLOSED_POLICY)"
}

cmd_verify_sha() {
  cmd_discover >/dev/null
  asset_url="${FW01_ASSET_URL:-}"
  if [[ -z "$asset_url" ]]; then
    echo "FW01_ASSET_URL not provided; cannot fetch published asset"
    exit 3
  fi
  tmp="$(mktemp -d)"
  curl -sL -o "$tmp/asset.zip" "$asset_url"
  got="$(sha256sum "$tmp/asset.zip" | awk '{print $1}')"
  want="$(field RELEASE_SHA256)"
  if [[ "$got" == "$want" ]]; then
    echo "RELEASE_SHA_BINDING=VERIFIED ($got)"
  else
    echo "RELEASE_SHA_BINDING=MISMATCH expected=$want got=$got"
    echo "STOP"
    exit 4
  fi
  rm -rf "$tmp"
}

cmd_detect_runtime() {
  if [[ -f "$RELEASE_MARKER" ]]; then
    echo "LOCAL_RUNTIME=PRESENT ($(field package_version < "$RELEASE_MARKER" 2>/dev/null || python3 -c "import json,sys;print(json.load(open('$RELEASE_MARKER'))['package_version'])"))"
    exit 0
  fi
  echo "LOCAL_RUNTIME=MISSING"
  exit 0
}

cmd_install() {
  cmd_discover >/dev/null
  asset_url="${FW01_ASSET_URL:-}"
  if [[ -z "$asset_url" ]]; then
    echo "FW01_ASSET_URL not provided"
    exit 3
  fi
  if [[ -f "$RELEASE_MARKER" ]]; then
    echo "ALREADY_INSTALLED — no duplicate install"
    exit 0
  fi
  tmp="$(mktemp -d)"
  curl -sL -o "$tmp/asset.zip" "$asset_url"
  got="$(sha256sum "$tmp/asset.zip" | awk '{print $1}')"
  want="$(field RELEASE_SHA256)"
  if [[ "$got" != "$want" ]]; then
    echo "STOP: release SHA mismatch during install"
    rm -rf "$tmp"
    exit 4
  fi
  mkdir -p "$tmp/extract"
  unzip -o -q "$tmp/asset.zip" -d "$tmp/extract"
  # Artifact layout: either flat (install.sh at extract root) or nested in one
  # top-level directory — locate the canonical installer accordingly.
  if [[ -f "$tmp/extract/install.sh" ]]; then
    pkg_root="$tmp/extract"
  else
    pkg_root="$(find "$tmp/extract" -maxdepth 1 -mindepth 1 -type d | head -1)"
  fi
  if [[ ! -f "$pkg_root/install.sh" ]]; then
    echo "STOP: canonical installer not found in artifact"
    rm -rf "$tmp"
    exit 5
  fi
  chmod +x "$pkg_root/install.sh"
  # Zip extraction does not preserve Unix executable bits, so every installed
  # runtime script must have its bits restored here. Without this the harness
  # correctly treats the runtime as corrupt (doctor requires -x); restoring
  # bits is the documented recovery, not a weakened check.
  post_restore_marker() {
    if [[ -d "$PROJECT_ROOT/.p2p/system/scripts" ]]; then
      find "$PROJECT_ROOT/.p2p/system/scripts" -type f -name '*.py' -exec chmod u+x {} + 2>/dev/null
      find "$PROJECT_ROOT/.p2p/system/scripts" -type f \( -name '*.sh' -o -name 'doctor' \) -exec chmod u+x {} + 2>/dev/null
    fi
  }
  # Preflight: does the artifact's own governance lock pass on this machine?
  # If the lock's technical preview report is unreachable here, doctor will
  # FAIL for every fresh workspace (upstream mint defect). Report clearly
  # BEFORE running the package installer, and skip install if so — fail
  # closed rather than half-installed.
  if [[ -f "$pkg_root/governance/live-specs.lock.json" ]]; then
    preflight_check="$(mktemp)"
    cat > "$preflight_check" <<'PY'
import json, sys
from pathlib import Path
lock = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
ref = lock.get("technical_report", "")
if not ref:
    sys.exit(1)
p = Path(ref)
if not p.is_absolute():
    p = Path(sys.argv[1]).parent / p
sys.exit(0 if p.is_file() else 1)
PY
    if ! python3 "$preflight_check" "$pkg_root/governance/live-specs.lock.json"; then
      echo "DOCTOR_BLOCKED_UPSTREAM_MINT_DEFECT (see bootstrap docs: Known certification gap)"
      echo "STOP"
      rm -rf "$tmp" "$preflight_check"
      exit 7
    fi
    rm -f "$preflight_check"
  fi
  bash "$pkg_root/install.sh" project "$PROJECT_ROOT" "$tmp/asset.zip" "$got"
  rc=$?
  rm -rf "$tmp"
  if [[ $rc -ne 0 ]]; then
    echo "STOP: canonical install failed"
    exit $rc
  fi
  post_restore_marker
  echo "CANONICAL_INSTALL=VERIFIED"
}

cmd_doctor() {
  if [[ ! -x "$SYSTEM/scripts/doctor.py" && -f "$SYSTEM/scripts/doctor.py" ]]; then
    # Zip-extracted runtime lost its executable bit; documented recovery.
    chmod u+x "$SYSTEM/scripts/doctor.py"
  fi
  if [[ ! -x "$SYSTEM/scripts/doctor.py" ]]; then
    echo "DOCTOR=UNHEALTHY (doctor.py missing — runtime absent or corrupt)"
    exit 6
  fi
  python3 "$SYSTEM/scripts/doctor.py" --root "$PROJECT_ROOT"
  rc=$?
  if [[ $rc -eq 0 ]]; then
    echo "DOCTOR=HEALTHY"
  else
    echo "DOCTOR=UNHEALTHY (repair path required; no execution)"
  fi
  exit $rc
}

cmd_doctor_status() {
  if [[ ! -x "$SYSTEM/scripts/doctor.py" && -f "$SYSTEM/scripts/doctor.py" ]]; then
    chmod u+x "$SYSTEM/scripts/doctor.py"
  fi
  if [[ ! -x "$SYSTEM/scripts/doctor.py" ]]; then
    echo "UNHEALTHY"
    exit 1
  fi
  out="$(python3 "$SYSTEM/scripts/doctor.py" --root "$PROJECT_ROOT" 2>&1)"
  rc=$?
  if [[ $rc -eq 0 ]]; then
    echo "HEALTHY"
    exit 0
  fi
  if echo "$out" | grep -q "technical preview report is missing"; then
    echo "BLOCKED (upstream mint defect: preview report path absent; no silent execution)"
    exit 7
  fi
  echo "UNHEALTHY"
  exit 1
}

case "${1:-}" in
  discover) cmd_discover ;;
  verify-sha) cmd_verify_sha ;;
  detect-runtime) cmd_detect_runtime ;;
  install) cmd_install ;;
  doctor) cmd_doctor ;;
  doctor-status) cmd_doctor_status ;;
  *) echo "Usage: $0 {discover|verify-sha|detect-runtime|install|doctor|doctor-status}" >&2; exit 1 ;;
esac
