param(
  [ValidateSet("Project", "User")]
  [string]$Scope = "Project",
  [string]$ProjectPath = (Get-Location).Path,
  [string]$ArtifactPath,
  [string]$ArtifactSha256
)

$ErrorActionPreference = "Stop"
$PackageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$NL = [Environment]::NewLine
$PackageVersionPath = Join-Path $PackageRoot "VERSION"
if (-not (Test-Path -LiteralPath $PackageVersionPath -PathType Leaf)) {
  throw "Package VERSION is missing: $PackageVersionPath"
}
$PackageVersion = (Get-Content -LiteralPath $PackageVersionPath -Raw).Trim()
if (-not $PackageVersion) {
  throw "Package VERSION is empty."
}
if (-not $ArtifactPath -or -not $ArtifactSha256 -or $ArtifactSha256 -notmatch '^[0-9a-fA-F]{64}$') {
  throw "ArtifactPath and a full 64-hex ArtifactSha256 are required for canonical project pinning."
}
$ArtifactPath = (Resolve-Path -LiteralPath $ArtifactPath -ErrorAction Stop).Path
$ActualArtifactSha256 = (Get-FileHash -LiteralPath $ArtifactPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($ActualArtifactSha256 -ne $ArtifactSha256.ToLowerInvariant()) {
  throw "Artifact SHA-256 mismatch; installation is blocked before project mutation."
}

if ($Scope -eq "User") {
  $Root = [Environment]::GetFolderPath("UserProfile")
  $InstructionsPath = Join-Path $Root ".codex\AGENTS.md"
} else {
  $Root = (Resolve-Path -LiteralPath $ProjectPath).Path
  $InstructionsPath = Join-Path $Root "AGENTS.md"
}

$SkillsSource = Join-Path $PackageRoot ".agents\skills"
$AgentsSource = Join-Path $PackageRoot ".codex\agents"
$SkillsDestination = Join-Path $Root ".agents\skills"
$AgentsDestination = Join-Path $Root ".codex\agents"
$ConfigPath = Join-Path $Root ".codex\config.toml"
$PackageConfigPath = Join-Path $PackageRoot ".codex\config.toml"
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackupRoot = Join-Path $Root ".p2p\install-backups\$Stamp"
$SystemDestination = Join-Path $Root ".p2p\system"
$ProjectPolicyPath = Join-Path $Root ".p2p\project-policy.json"
$ReleaseMarkerPath = Join-Path $SystemDestination "release.json"
$ProjectAlreadyInitialized = (Test-Path -LiteralPath $ProjectPolicyPath -PathType Leaf) -or (Test-Path -LiteralPath (Join-Path $Root ".p2p\state") -PathType Container)
$InstallClass = "FRESH_INSTALL"
if (Test-Path -LiteralPath $SystemDestination -PathType Container) {
  if (Test-Path -LiteralPath $ReleaseMarkerPath -PathType Leaf) {
    try {
      $PreviousMarker = Get-Content -LiteralPath $ReleaseMarkerPath -Raw | ConvertFrom-Json
      $PreviousVersion = [string]$PreviousMarker.package_version
      if ($PreviousVersion -eq $PackageVersion) {
        $InstallClass = "SAME_VERSION_REINSTALL"
      } elseif ($PreviousVersion) {
        $InstallClass = "UPGRADE_FROM_$PreviousVersion"
      } else {
        $InstallClass = "LEGACY_SYSTEM_UPGRADE"
      }
    } catch {
      $InstallClass = "LEGACY_SYSTEM_UPGRADE"
    }
  } else {
    $InstallClass = "LEGACY_SYSTEM_UPGRADE"
  }
} elseif ($ProjectAlreadyInitialized) {
  $InstallClass = "ALREADY_INITIALIZED_PROJECT"
}

function Backup-Path {
  param([string]$Path, [string]$RelativeName)
  if (Test-Path -LiteralPath $Path) {
    $Backup = Join-Path $BackupRoot $RelativeName
    $Parent = Split-Path -Parent $Backup
    New-Item -ItemType Directory -Force -Path $Parent | Out-Null
    Move-Item -LiteralPath $Path -Destination $Backup
  }
}

New-Item -ItemType Directory -Force -Path $SkillsDestination | Out-Null
New-Item -ItemType Directory -Force -Path $AgentsDestination | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ConfigPath) | Out-Null

if ($InstallClass -ne "SAME_VERSION_REINSTALL") {
  Backup-Path -Path $SystemDestination -RelativeName "system"
}
New-Item -ItemType Directory -Force -Path (Join-Path $SystemDestination "governance") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $SystemDestination "scripts") | Out-Null
Get-ChildItem -LiteralPath (Join-Path $PackageRoot "governance") -Force | ForEach-Object {
  Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $SystemDestination "governance") -Recurse -Force
}
foreach ($ScriptName in @("p2p_governance.py", "p2p_eval.py", "p2p_approval.py", "p2p_gate.py", "p2p_bootstrap.py", "p2p_workflow.py", "p2p_orientation.py", "p2p_decision_trace.py", "p2p_task_state.py", "p2p_safe_installer.py", "doctor.py")) {
  Copy-Item -LiteralPath (Join-Path $PackageRoot ("scripts\" + $ScriptName)) -Destination (Join-Path $SystemDestination ("scripts\" + $ScriptName)) -Force
}

$UiUxRuntime = Join-Path $PackageRoot "runtime"
if (Test-Path -LiteralPath $UiUxRuntime -PathType Container) {
  foreach ($RequiredPath in @(
    "VERSION",
    "p2p.manifest.json",
    "references\UPSTREAM-UI-UX-PRO-MAX-PROVENANCE.md",
    "docs\evals\p2p-uiux-eval-suite.json",
    "p2p_capabilities\capabilities.json",
    "p2p_capabilities\__init__.py",
    "p2p_capabilities\model.py",
    "p2p_capabilities\routing.py",
    "p2p_capabilities\context.py",
    "p2p_capabilities\trust.py",
    "p2p_capabilities\evidence.py",
    "p2p_capabilities\providers.py",
    "p2p_capabilities\specialist.py",
    "p2p_capabilities\skill_standard.py",
    "p2p_capabilities\beginner.py",
    "p2p_capabilities\isolation.py",
    "p2p_capabilities\domain.py",
    "p2p_capabilities\decision_trace.py",
    "scripts\p2p_capability_doctor.py",
    "scripts\p2p_decision_trace.py",
    "scripts\p2p_host_identity_hook.py",
    "p2p_uiux",
    "scripts\p2p_uiux.py",
    "scripts\p2p_router.py",
    "scripts\p2p_uiux_governance.py",
    "scripts\p2p_uiux_eval.py",
    "scripts\p2p_uiux_eval_impl.py",
    "scripts\p2p_uiux_doctor.py",
    "scripts\p2p_uiux_drift_check.py",
    "scripts\p2p_uiux_secret_scan.py"
  )) {
    if (-not (Test-Path -LiteralPath (Join-Path $UiUxRuntime $RequiredPath))) {
      throw "Full-release UI/UX runtime payload is incomplete: $RequiredPath"
    }
  }
  $UiUxDestination = Join-Path $SystemDestination "p2p_uiux"
  New-Item -ItemType Directory -Force -Path $UiUxDestination | Out-Null
  Copy-Item -Path (Join-Path $UiUxRuntime "p2p_uiux\*") -Destination $UiUxDestination -Recurse -Force
  Copy-Item -LiteralPath (Join-Path $UiUxRuntime "VERSION") -Destination $SystemDestination
  Copy-Item -LiteralPath (Join-Path $UiUxRuntime "p2p.manifest.json") -Destination $SystemDestination
  $FoundationDestination = Join-Path $SystemDestination "p2p_capabilities"
  New-Item -ItemType Directory -Force -Path $FoundationDestination | Out-Null
  Copy-Item -Path (Join-Path $UiUxRuntime "p2p_capabilities\*") -Destination $FoundationDestination -Recurse -Force
  New-Item -ItemType Directory -Force -Path (Join-Path $SystemDestination "references") | Out-Null
  Copy-Item -LiteralPath (Join-Path $UiUxRuntime "references\UPSTREAM-UI-UX-PRO-MAX-PROVENANCE.md") -Destination (Join-Path $SystemDestination "references")
  New-Item -ItemType Directory -Force -Path (Join-Path $SystemDestination "docs\evals") | Out-Null
  Copy-Item -LiteralPath (Join-Path $UiUxRuntime "docs\evals\p2p-uiux-eval-suite.json") -Destination (Join-Path $SystemDestination "docs\evals")
  foreach ($ScriptName in @("p2p_capability_doctor.py", "p2p_decision_trace.py", "p2p_host_identity_hook.py", "p2p_uiux.py", "p2p_router.py", "p2p_uiux_governance.py", "p2p_uiux_eval.py", "p2p_uiux_eval_impl.py", "p2p_uiux_doctor.py", "p2p_uiux_drift_check.py", "p2p_uiux_secret_scan.py")) {
    Copy-Item -LiteralPath (Join-Path $UiUxRuntime ("scripts\" + $ScriptName)) -Destination (Join-Path $SystemDestination ("scripts\" + $ScriptName)) -Force
  }
}

foreach ($MetadataName in @("CANDIDATE-DISTRIBUTION-MANIFEST.json", "SOURCE-BINDING.json", "ARTIFACT-IDENTITY.json", "INVENTORY.json", "release-manifest.json", "RELEASE-SHA256SUMS.txt")) {
  $MetadataPath = Join-Path $PackageRoot $MetadataName
  if (-not (Test-Path -LiteralPath $MetadataPath -PathType Leaf)) {
    throw "Canonical release metadata is missing: $MetadataName"
  }
  Copy-Item -LiteralPath $MetadataPath -Destination (Join-Path $SystemDestination $MetadataName) -Force
}

# Shield runtime: ship the packaged Shield surface into the managed P2P system
# so an installed target can run it with PYTHONPATH=<Root>\.p2p\system.
# Fail closed if a canonical package that claims this feature is missing it.
# Files are copied to computed relative destinations so upgrade and reinstall
# refresh .p2p\system\shield in place instead of nesting shield\shield.
$ShieldSource = Join-Path $PackageRoot "shield"
if (-not (Test-Path -LiteralPath $ShieldSource -PathType Container)) {
  throw "Packaged Shield runtime is missing: shield\"
}
$ShieldDestination = Join-Path $SystemDestination "shield"
New-Item -ItemType Directory -Force -Path $ShieldDestination | Out-Null
Get-ChildItem -LiteralPath $ShieldSource -Recurse -Force -File | ForEach-Object {
  $ShieldRelative = $_.FullName.Substring($ShieldSource.Length).TrimStart('\')
  $ShieldTarget = Join-Path $ShieldDestination $ShieldRelative
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ShieldTarget) | Out-Null
  Copy-Item -LiteralPath $_.FullName -Destination $ShieldTarget -Force
}

# P2P operations notebook: install the canonical full notebook into the
# managed P2P system so the installed project can discover and follow it.
# Fail closed if a canonical package that claims this feature is missing it.
$OperationsNotebookRel = "docs\p2p-development\P2P-OPERATIONS-NOTEBOOK.md"
$OperationsNotebookSource = Join-Path $PackageRoot $OperationsNotebookRel
if (-not (Test-Path -LiteralPath $OperationsNotebookSource -PathType Leaf)) {
  throw "Canonical P2P operations notebook is missing: $OperationsNotebookSource"
}
New-Item -ItemType Directory -Force -Path (Join-Path $SystemDestination "docs") | Out-Null
Copy-Item -LiteralPath $OperationsNotebookSource -Destination (Join-Path $SystemDestination "docs\P2P-OPERATIONS-NOTEBOOK.md") -Force

New-Item -ItemType Directory -Force -Path (Join-Path $Root ".p2p\approvals\requests") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Root ".p2p\approvals\records") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Root ".p2p\gates") | Out-Null
if (-not (Test-Path -LiteralPath $ProjectPolicyPath -PathType Leaf)) {
  $Policy = Get-Content -LiteralPath (Join-Path $PackageRoot "governance\project-policy.template.json") -Raw | ConvertFrom-Json
  $Policy.project = Split-Path -Leaf $Root
  $PolicyJson = ($Policy | ConvertTo-Json -Depth 20) + $NL
  [System.IO.File]::WriteAllText($ProjectPolicyPath, $PolicyJson, [System.Text.UTF8Encoding]::new($false))
}

foreach ($Skill in Get-ChildItem -LiteralPath $SkillsSource -Directory) {
  $Destination = Join-Path $SkillsDestination $Skill.Name
  if ($InstallClass -eq "SAME_VERSION_REINSTALL" -and (Test-Path -LiteralPath $Destination)) {
    continue
  }
  Backup-Path -Path $Destination -RelativeName ("skills\" + $Skill.Name)
  Copy-Item -LiteralPath $Skill.FullName -Destination $Destination -Recurse
}

foreach ($Agent in Get-ChildItem -LiteralPath $AgentsSource -File -Filter "p2p-*.toml") {
  $Destination = Join-Path $AgentsDestination $Agent.Name
  if ($InstallClass -eq "SAME_VERSION_REINSTALL" -and (Test-Path -LiteralPath $Destination)) {
    continue
  }
  Backup-Path -Path $Destination -RelativeName ("agents\" + $Agent.Name)
  Copy-Item -LiteralPath $Agent.FullName -Destination $Destination
}

if (Test-Path -LiteralPath $ConfigPath) {
  if ($InstallClass -ne "SAME_VERSION_REINSTALL") {
    New-Item -ItemType Directory -Force -Path (Join-Path $BackupRoot "config") | Out-Null
    Copy-Item -LiteralPath $ConfigPath -Destination (Join-Path $BackupRoot "config\config.toml")
  }
  $Config = Get-Content -LiteralPath $ConfigPath -Raw
} else {
  $Config = ""
}
$PackageConfig = ""
if (Test-Path -LiteralPath $PackageConfigPath -PathType Leaf) {
  $PackageConfig = Get-Content -LiteralPath $PackageConfigPath -Raw
}

if ($Config -notmatch "(?m)^\s*\[agents\]\s*$") {
  $Config = $Config.TrimEnd() + $NL + $NL + "[agents]" + $NL + "enabled = true" + $NL + "max_concurrent_threads_per_session = 8" + $NL
} else {
  $Pattern = "(?ms)(^\s*\[agents\]\s*\r?\n)(.*?)(?=^\s*\[|\z)"
  $Config = [regex]::Replace($Config, $Pattern, {
    param($Match)
    $Header = $Match.Groups[1].Value
    $Body = $Match.Groups[2].Value
    if ($Body -match "(?m)^\s*enabled\s*=") {
      $Body = [regex]::Replace($Body, "(?m)^\s*enabled\s*=.*$", "enabled = true")
    } else {
      $Body = "enabled = true" + $NL + $Body
    }
    if ($Body -match "(?m)^\s*max_concurrent_threads_per_session\s*=") {
      $Body = [regex]::Replace($Body, "(?m)^\s*max_concurrent_threads_per_session\s*=.*$", "max_concurrent_threads_per_session = 8")
    } elseif ($Body -match "(?m)^\s*max_threads\s*=") {
      $Body = [regex]::Replace($Body, "(?m)^\s*max_threads\s*=.*$", "max_concurrent_threads_per_session = 8")
    } else {
      $Body = "max_concurrent_threads_per_session = 8" + $NL + $Body
    }
    return $Header + $Body
  })
}
if (-not $Config.Contains("p2p_host_identity_hook.py") -and $PackageConfig.Contains("p2p_host_identity_hook.py")) {
  $HookHeader = "[[hooks.SubagentStart]]"
  $HookIndex = $PackageConfig.IndexOf($HookHeader)
  if ($HookIndex -ge 0) {
    $HookBlock = $PackageConfig.Substring($HookIndex).Trim()
    $Config = $Config.TrimEnd() + $NL + $NL + $HookBlock + $NL
  }
}
[System.IO.File]::WriteAllText($ConfigPath, $Config, [System.Text.UTF8Encoding]::new($false))

$Begin = "<!-- BEGIN P2P CODEX -->"
$End = "<!-- END P2P CODEX -->"
$P2PInstructions = Get-Content -LiteralPath (Join-Path $PackageRoot "docs\p2p-development\P2P-AGENTS-INSTALL.md") -Raw
$Block = $Begin + $NL + $P2PInstructions.Trim() + $NL + $End
if (Test-Path -LiteralPath $InstructionsPath) {
  if ($InstallClass -ne "SAME_VERSION_REINSTALL") {
    New-Item -ItemType Directory -Force -Path (Join-Path $BackupRoot "instructions") | Out-Null
    Copy-Item -LiteralPath $InstructionsPath -Destination (Join-Path $BackupRoot "instructions\AGENTS.md")
  }
  $Existing = Get-Content -LiteralPath $InstructionsPath -Raw
  if ($Existing.Contains($Begin) -and $Existing.Contains($End)) {
    $Regex = [regex]::Escape($Begin) + "(?s).*?" + [regex]::Escape($End)
    $Merged = [regex]::Replace($Existing, $Regex, $Block)
  } else {
    $Merged = $Existing.TrimEnd() + $NL + $NL + $Block + $NL
  }
} else {
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $InstructionsPath) | Out-Null
  $Merged = $Block + $NL
}
[System.IO.File]::WriteAllText($InstructionsPath, $Merged, [System.Text.UTF8Encoding]::new($false))

$PythonCommand = Get-Command py -ErrorAction SilentlyContinue
if (-not $PythonCommand) {
  $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
}
if (-not $PythonCommand) {
  throw "Python was not found. It is required to build the mandatory P2P runtime drift lock."
}
& $PythonCommand.Source (Join-Path $SystemDestination "scripts\p2p_governance.py") lock-runtime `
  --root $Root `
  --governance (Join-Path $SystemDestination "governance") `
  --reason "Explicit package installation by user"
if ($LASTEXITCODE -ne 0) {
  throw "Could not build the mandatory P2P runtime drift lock."
}
New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null
& $PythonCommand.Source (Join-Path $PackageRoot "scripts\p2p_safe_installer.py") pin `
  $Root `
  --package-root $PackageRoot `
  --artifact $ArtifactPath `
  --sha $ArtifactSha256 `
  --version $PackageVersion `
  --mode ("PACKAGED_" + $Scope.ToUpperInvariant()) `
  --rollback-source (".p2p\install-backups\" + $Stamp)
if ($LASTEXITCODE -ne 0) {
  throw "Canonical project pin creation failed; installation is not verified."
}
Write-Host ""
Write-Host "P2P Codex installed successfully." -ForegroundColor Green
Write-Host "Scope: $Scope"
Write-Host "Root:  $Root"
Write-Host "Install class: $InstallClass"
if (Test-Path -LiteralPath $BackupRoot) {
  Write-Host "Backup: $BackupRoot"
}
Write-Host ""
& (Join-Path $PackageRoot "doctor.ps1") -Root $Root
if ($LASTEXITCODE -ne 0) {
  throw "P2P doctor failed; release marker was not written."
}
$Marker = [ordered]@{
  schema_version = "p2p-install-release/1"
  package_version = $PackageVersion
  candidate_version = $PackageVersion
  artifact_sha256 = $ArtifactSha256.ToLowerInvariant()
  install_class = $InstallClass
  scope = $Scope
  managed_file_count = @(Get-ChildItem -LiteralPath $SystemDestination -File -Recurse).Count
  preserved_existing_canonical_profiles = $true
  preserved_existing_core_skill = $true
  protected_state_hashes = [ordered]@{ project_policy = (Get-FileHash -LiteralPath $ProjectPolicyPath -Algorithm SHA256).Hash.ToLowerInvariant() }
  installed_at = (Get-Date).ToUniversalTime().ToString("o")
}
[System.IO.File]::WriteAllText($ReleaseMarkerPath, (($Marker | ConvertTo-Json -Depth 10) + $NL), [System.Text.UTF8Encoding]::new($false))
Write-Host "Release marker: $ReleaseMarkerPath"
