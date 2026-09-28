#!/usr/bin/env bash
set -euo pipefail

scope="${1:-project}"
project_path="${2:-$PWD}"
artifact_path="${3:-}"
artifact_sha256="${4:-}"
package_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -f "$package_root/VERSION" ]]; then
  echo "Package VERSION is missing: $package_root/VERSION" >&2
  exit 2
fi
package_version="$(tr -d '\r\n' < "$package_root/VERSION")"
if [[ -z "$package_version" ]]; then
  echo "Package VERSION is empty" >&2
  exit 2
fi
if [[ -z "$artifact_path" || ! -f "$artifact_path" || ! "$artifact_sha256" =~ ^[0-9a-fA-F]{64}$ ]]; then
  echo "Artifact path and a full 64-hex artifact SHA-256 are required for canonical project pinning." >&2
  exit 2
fi
artifact_path="$(cd "$(dirname "$artifact_path")" && pwd)/$(basename "$artifact_path")"
actual_artifact_sha256="$(sha256sum "$artifact_path" | awk '{print tolower($1)}')"
if [[ "$actual_artifact_sha256" != "${artifact_sha256,,}" ]]; then
  echo "Artifact SHA-256 mismatch; installation is blocked before project mutation." >&2
  exit 2
fi

if [[ "$scope" == "user" ]]; then
  root="${HOME}"
  instructions_path="$root/.codex/AGENTS.md"
elif [[ "$scope" == "project" ]]; then
  root="$(cd "$project_path" && pwd)"
  instructions_path="$root/AGENTS.md"
else
  echo "Usage: ./install.sh [project PATH | user]" >&2
  exit 2
fi

stamp="$(date +%Y%m%d-%H%M%S)"
backup_root="$root/.p2p/install-backups/$stamp"
skills_destination="$root/.agents/skills"
agents_destination="$root/.codex/agents"
config_path="$root/.codex/config.toml"
package_config_path="$package_root/.codex/config.toml"
system_destination="$root/.p2p/system"
project_policy_path="$root/.p2p/project-policy.json"
release_marker_path="$system_destination/release.json"
install_class="FRESH_INSTALL"
project_already_initialized=false
if [[ -f "$project_policy_path" || -d "$root/.p2p/state" ]]; then
  project_already_initialized=true
fi
if [[ -d "$system_destination" ]]; then
  if [[ -f "$release_marker_path" ]]; then
    previous_version="$(python3 - "$release_marker_path" <<'PY'
import json
import sys
from pathlib import Path
try:
    value = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(str(value.get("package_version", "")))
except Exception:
    print("")
PY
)"
    if [[ "$previous_version" == "$package_version" ]]; then
      install_class="SAME_VERSION_REINSTALL"
    elif [[ -n "$previous_version" ]]; then
      install_class="UPGRADE_FROM_$previous_version"
    else
      install_class="LEGACY_SYSTEM_UPGRADE"
    fi
  else
    install_class="LEGACY_SYSTEM_UPGRADE"
  fi
elif [[ "$project_already_initialized" == true ]]; then
  install_class="ALREADY_INITIALIZED_PROJECT"
fi

if [[ -e "$system_destination" && "$install_class" != "SAME_VERSION_REINSTALL" ]]; then
  mkdir -p "$backup_root"
  mv "$system_destination" "$backup_root/system"
fi
mkdir -p "$system_destination/governance" "$system_destination/scripts"
cp -a "$package_root/governance/." "$system_destination/governance/"
cp \
  "$package_root/scripts/p2p_governance.py" \
  "$package_root/scripts/p2p_eval.py" \
  "$package_root/scripts/p2p_approval.py" \
  "$package_root/scripts/p2p_gate.py" \
  "$package_root/scripts/p2p_bootstrap.py" \
  "$package_root/scripts/p2p_workflow.py" \
  "$package_root/scripts/p2p_control_tower.py" \
  "$package_root/scripts/p2p_orientation.py" \
  "$package_root/scripts/p2p_decision_trace.py" \
  "$package_root/scripts/p2p_task_state.py" \
  "$package_root/scripts/p2p_safe_installer.py" \
  "$package_root/scripts/p2p_skill_profile.py" \
  "$package_root/scripts/doctor.py" \
  "$system_destination/scripts/"

for metadata_name in \
  CANDIDATE-DISTRIBUTION-MANIFEST.json \
  SOURCE-BINDING.json \
  ARTIFACT-IDENTITY.json \
  INVENTORY.json \
  release-manifest.json \
  RELEASE-SHA256SUMS.txt; do
  if [[ ! -f "$package_root/$metadata_name" ]]; then
    echo "Canonical release metadata is missing: $metadata_name" >&2
    exit 2
  fi
  cp "$package_root/$metadata_name" "$system_destination/$metadata_name"
done

# Shield runtime: ship the packaged Shield surface into the managed P2P system
# so an installed target can run it with PYTHONPATH=<root>/.p2p/system.
# Fail closed if a canonical package that claims this feature is missing it.
# The "<source>/." form copies contents into the destination, so upgrade and
# reinstall refresh .p2p/system/shield in place without nested shield/shield.
shield_source="$package_root/shield"
if [[ ! -d "$shield_source" ]]; then
  echo "Packaged Shield runtime is missing: shield/" >&2
  exit 2
fi
mkdir -p "$system_destination/shield"
cp -a "$shield_source/." "$system_destination/shield/"

# P2P operations notebook: install the canonical full notebook into the
# managed P2P system so the installed project can discover and follow it.
# Fail closed if a canonical package that claims this feature is missing it.
operations_notebook_rel="docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md"
operations_notebook_src="$package_root/$operations_notebook_rel"
if [[ ! -f "$operations_notebook_src" ]]; then
  echo "Canonical P2P operations notebook is missing: $operations_notebook_src" >&2
  exit 2
fi
mkdir -p "$system_destination/docs"
cp "$operations_notebook_src" "$system_destination/docs/P2P-OPERATIONS-NOTEBOOK.md"

uiux_runtime="$package_root/runtime"
if [[ -d "$uiux_runtime" ]]; then
  for required_path in \
    VERSION \
    p2p.manifest.json \
    references/UPSTREAM-UI-UX-PRO-MAX-PROVENANCE.md \
    docs/evals/p2p-uiux-eval-suite.json \
    p2p_capabilities/capabilities.json \
    p2p_capabilities/__init__.py \
    p2p_capabilities/model.py \
    p2p_capabilities/routing.py \
    p2p_capabilities/context.py \
    p2p_capabilities/trust.py \
    p2p_capabilities/evidence.py \
    p2p_capabilities/providers.py \
    p2p_capabilities/specialist.py \
    p2p_capabilities/skill_standard.py \
    p2p_capabilities/beginner.py \
    p2p_capabilities/isolation.py \
    p2p_capabilities/domain.py \
    p2p_capabilities/decision_trace.py \
    p2p_capabilities/project_pin.py \
    p2p_capabilities/project_context.py \
    p2p_capabilities/project_map.py \
    scripts/p2p_capability_doctor.py \
    scripts/p2p_decision_trace.py \
    scripts/p2p_host_identity_hook.py \
    p2p_uiux \
    scripts/p2p_uiux.py \
    scripts/p2p_router.py \
    scripts/p2p_uiux_governance.py \
    scripts/p2p_uiux_eval.py \
    scripts/p2p_uiux_eval_impl.py \
    scripts/p2p_uiux_doctor.py \
    scripts/p2p_uiux_drift_check.py \
    scripts/p2p_uiux_secret_scan.py; do
    if [[ ! -e "$uiux_runtime/$required_path" ]]; then
      echo "Full-release UI/UX runtime payload is incomplete: $required_path" >&2
      exit 2
    fi
  done
  mkdir -p "$system_destination/p2p_uiux"
  cp -a "$uiux_runtime/p2p_uiux/." "$system_destination/p2p_uiux/"
  cp "$uiux_runtime/VERSION" "$uiux_runtime/p2p.manifest.json" "$system_destination/"
  mkdir -p "$system_destination/p2p_capabilities"
  cp -a "$uiux_runtime/p2p_capabilities/." "$system_destination/p2p_capabilities/"
  mkdir -p "$system_destination/references" "$system_destination/docs/evals"
  cp "$uiux_runtime/references/UPSTREAM-UI-UX-PRO-MAX-PROVENANCE.md" "$system_destination/references/"
  cp "$uiux_runtime/docs/evals/p2p-uiux-eval-suite.json" "$system_destination/docs/evals/"
  cp \
    "$uiux_runtime/scripts/p2p_capability_doctor.py" \
    "$uiux_runtime/scripts/p2p_decision_trace.py" \
    "$uiux_runtime/scripts/p2p_host_identity_hook.py" \
    "$uiux_runtime/scripts/p2p_uiux.py" \
    "$uiux_runtime/scripts/p2p_router.py" \
    "$uiux_runtime/scripts/p2p_uiux_governance.py" \
    "$uiux_runtime/scripts/p2p_uiux_eval.py" \
    "$uiux_runtime/scripts/p2p_uiux_eval_impl.py" \
    "$uiux_runtime/scripts/p2p_uiux_doctor.py" \
    "$uiux_runtime/scripts/p2p_uiux_drift_check.py" \
    "$uiux_runtime/scripts/p2p_uiux_secret_scan.py" \
    "$system_destination/scripts/"
fi

mkdir -p "$root/.p2p/approvals/requests" "$root/.p2p/approvals/records" "$root/.p2p/gates" "$root/.p2p/state"
if [[ ! -f "$project_policy_path" ]]; then
  python3 - "$package_root/governance/project-policy.template.json" "$project_policy_path" "$root" <<'PY'
from pathlib import Path
import json
import sys

source, target, root = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
value = json.loads(source.read_text(encoding="utf-8"))
value["project"] = root.name
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
fi

mkdir -p "$skills_destination" "$agents_destination" "$(dirname "$config_path")"

profile_mode="AUTO"
if [[ "$scope" == "user" ]]; then
  profile_mode="ALL"
fi
profile_receipt_path="$system_destination/capability-profile.json"
python3 "$package_root/scripts/p2p_skill_profile.py" \
  --root "$root" \
  --skills-dir "$package_root/.agents/skills" \
  --profile "$profile_mode" \
  --format json > "$profile_receipt_path"
capability_profile="$(python3 - "$profile_receipt_path" <<'PY'
import json
import sys
from pathlib import Path
print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["profile"])
PY
)"

while IFS= read -r name; do
  [[ -z "$name" ]] && continue
  source="$package_root/.agents/skills/$name"
  destination="$skills_destination/$name"
  if [[ "$install_class" == "SAME_VERSION_REINSTALL" && -e "$destination" ]]; then
    continue
  fi
  if [[ -e "$destination" ]]; then
    mkdir -p "$backup_root/skills"
    mv "$destination" "$backup_root/skills/$name"
  fi
  cp -a "$source" "$destination"
done < <(
  python3 "$package_root/scripts/p2p_skill_profile.py" \
    --root "$root" \
    --skills-dir "$package_root/.agents/skills" \
    --profile "$profile_mode" \
    --format lines
)

for source in "$package_root"/.codex/agents/p2p-*.toml; do
  name="$(basename "$source")"
  destination="$agents_destination/$name"
  if [[ "$install_class" == "SAME_VERSION_REINSTALL" && -e "$destination" ]]; then
    continue
  fi
  if [[ -e "$destination" ]]; then
    mkdir -p "$backup_root/agents"
    mv "$destination" "$backup_root/agents/$name"
  fi
  cp "$source" "$destination"
done

if [[ -f "$config_path" && "$install_class" != "SAME_VERSION_REINSTALL" ]]; then
  mkdir -p "$backup_root/config"
  cp "$config_path" "$backup_root/config/config.toml"
fi

python3 - "$config_path" "$package_config_path" <<'PY'
from pathlib import Path
import re
import sys

path, package_config_path = map(Path, sys.argv[1:])
text = path.read_text(encoding="utf-8") if path.exists() else ""
package_text = package_config_path.read_text(encoding="utf-8") if package_config_path.exists() else ""
match = re.search(r"(?ms)^\s*\[agents\]\s*$.*?(?=^\s*\[|\Z)", text)
if match is None:
    text = text.rstrip() + "\n\n[agents]\nenabled = true\nmax_concurrent_threads_per_session = 8\n"
else:
    section = match.group(0)
    if re.search(r"(?m)^\s*enabled\s*=", section):
        section = re.sub(r"(?m)^\s*enabled\s*=.*$", "enabled = true", section)
    else:
        section = section.replace("[agents]", "[agents]\nenabled = true", 1)
    if re.search(r"(?m)^\s*max_concurrent_threads_per_session\s*=", section):
        section = re.sub(r"(?m)^\s*max_concurrent_threads_per_session\s*=.*$", "max_concurrent_threads_per_session = 8", section)
    elif re.search(r"(?m)^\s*max_threads\s*=", section):
        section = re.sub(r"(?m)^\s*max_threads\s*=.*$", "max_concurrent_threads_per_session = 8", section)
    else:
        section = section.replace("[agents]", "[agents]\nmax_concurrent_threads_per_session = 8", 1)
    text = text[:match.start()] + section + text[match.end():]
if "p2p_host_identity_hook.py" not in text and "p2p_host_identity_hook.py" in package_text:
    marker = "[[hooks.SubagentStart]]"
    start = package_text.find(marker)
    if start >= 0:
        text = text.rstrip() + "\n\n" + package_text[start:].strip() + "\n"
path.write_text(text, encoding="utf-8")
PY

if [[ -f "$instructions_path" && "$install_class" != "SAME_VERSION_REINSTALL" ]]; then
  mkdir -p "$backup_root/instructions"
  cp "$instructions_path" "$backup_root/instructions/AGENTS.md"
fi

python3 - "$instructions_path" "$package_root/docs/p2p-development/P2P-AGENTS-INSTALL.md" <<'PY'
from pathlib import Path
import re
import sys

target, source = map(Path, sys.argv[1:])
begin = "<!-- BEGIN P2P CODEX -->"
end = "<!-- END P2P CODEX -->"
block = begin + "\n" + source.read_text(encoding="utf-8").strip() + "\n" + end
text = target.read_text(encoding="utf-8") if target.exists() else ""
pattern = re.escape(begin) + r".*?" + re.escape(end)
if re.search(pattern, text, flags=re.S):
    text = re.sub(pattern, block, text, flags=re.S)
else:
    text = text.rstrip() + ("\n\n" if text.strip() else "") + block + "\n"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(text, encoding="utf-8")
PY

python3 "$system_destination/scripts/p2p_governance.py" lock-runtime \
  --root "$root" \
  --governance "$system_destination/governance" \
  --reason "Explicit package installation by user"

mkdir -p "$backup_root"
python3 "$package_root/scripts/p2p_safe_installer.py" pin \
  "$root" \
  --package-root "$package_root" \
  --artifact "$artifact_path" \
  --sha "$artifact_sha256" \
  --version "$package_version" \
  --mode "PACKAGED_${scope^^}" \
  --rollback-source ".p2p/install-backups/$stamp"

echo "P2P Codex installed successfully."
echo "Scope: $scope"
echo "Root:  $root"
echo "Install class: $install_class"
echo "Capability profile: $capability_profile"
[[ -d "$backup_root" ]] && echo "Backup: $backup_root"
if ! python3 "$package_root/scripts/doctor.py" --root "$root"; then
  echo "P2P doctor failed; release marker was not written." >&2
  exit 1
fi
managed_file_count="$(find "$system_destination" -type f | wc -l | tr -d ' ')"
project_policy_sha256="$(sha256sum "$project_policy_path" | awk '{print $1}')"
python3 - "$release_marker_path" "$package_version" "$install_class" "$scope" "$managed_file_count" "$project_policy_sha256" "$artifact_sha256" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

target = Path(sys.argv[1])
version = sys.argv[2]
install_class = sys.argv[3]
scope = sys.argv[4]
managed_file_count = int(sys.argv[5])
project_policy_sha256 = sys.argv[6]
artifact_sha256 = sys.argv[7]
value = {
    "schema_version": "p2p-install-release/1",
    "package_version": version,
    "candidate_version": version,
    "artifact_sha256": artifact_sha256.lower(),
    "install_class": install_class,
    "scope": scope,
    "managed_file_count": managed_file_count,
    "preserved_existing_canonical_profiles": True,
    "preserved_existing_core_skill": True,
    "protected_state_hashes": {"project_policy": project_policy_sha256},
    "installed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
}
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
echo "Release marker: $release_marker_path"
