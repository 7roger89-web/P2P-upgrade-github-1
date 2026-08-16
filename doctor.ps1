param(
  [string]$Root = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path -LiteralPath $Root).Path
$Skills = Join-Path $Root ".agents\skills"
$Agents = Join-Path $Root ".codex\agents"
$Config = Join-Path $Root ".codex\config.toml"
$ExpectedSkills = @(
  "bb4pda", "notebook-pack", "p2p", "p2p-uiux", "p2p-approval", "p2p-atlas", "p2p-capsule",
  "p2p-chain", "p2p-download", "p2p-explore", "p2p-feedback",
  "p2p-idea", "p2p-karpathy", "p2p-metrics", "p2p-pxpipe", "p2p-quorum",
  "p2p-scope", "p2p-teacher", "p2p-eval", "pxpipe", "rag-grounding", "rag-prep",
  "rag-router"
)
$ExpectedAgents = @(
  "p2p-anon.toml", "p2p-architecton.toml", "p2p-axiom.toml",
  "p2p-datos.toml", "p2p-helios.toml", "p2p-iris.toml",
  "p2p-tecton.toml", "p2p-vector.toml"
)
$OptionalAgent = "p2p-aesthetica.toml"
$Failed = $false

function Check {
  param([bool]$Condition, [string]$Message)
  if ($Condition) {
    Write-Host "[PASS] $Message" -ForegroundColor Green
  } else {
    Write-Host "[FAIL] $Message" -ForegroundColor Red
    $script:Failed = $true
  }
}

Check (Test-Path -LiteralPath $Skills -PathType Container) "Skills directory exists"
foreach ($Name in $ExpectedSkills) {
  Check (Test-Path -LiteralPath (Join-Path $Skills "$Name\SKILL.md") -PathType Leaf) "Skill $Name"
}
Check (Test-Path -LiteralPath $Agents -PathType Container) "Custom-agent directory exists"
foreach ($Name in $ExpectedAgents) {
  $Path = Join-Path $Agents $Name
  $Ok = (Test-Path -LiteralPath $Path -PathType Leaf)
  if ($Ok) {
    $Text = Get-Content -LiteralPath $Path -Raw
    $Ok = $Text -match "(?m)^name\s*=" -and $Text -match "(?m)^description\s*=" -and $Text -match "(?m)^developer_instructions\s*="
  }
  Check $Ok "Agent $Name has required fields"
}
$OptionalAgentPath = Join-Path $Agents $OptionalAgent
$OptionalOk = Test-Path -LiteralPath $OptionalAgentPath -PathType Leaf
if ($OptionalOk) {
  $OptionalText = Get-Content -LiteralPath $OptionalAgentPath -Raw
  $OptionalOk = $OptionalText -match '(?m)^name\s*=\s*"p2p_aesthetica"' -and
    $OptionalText -match '(?m)^description\s*=' -and
    $OptionalText -match '(?m)^developer_instructions\s*=' -and
    $OptionalText -match '(?m)^sandbox_mode\s*=\s*"read-only"\s*$'
}
$ManifestPath = Join-Path $Root ".p2p\system\p2p.manifest.json"
$OptionalManifestOk = Test-Path -LiteralPath $ManifestPath -PathType Leaf
if ($OptionalManifestOk) {
  try {
    $Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
    $OptionalEntries = @($Manifest.optional_specialists | Where-Object { $_.name -eq "p2p_aesthetica" })
    $OptionalManifestOk = $OptionalEntries.Count -eq 1 -and
      $OptionalEntries[0].classification -eq "SUPPORTING / OPTIONAL DOMAIN SPECIALIST" -and
      $OptionalEntries[0].optional_specialist -eq $true -and
      $OptionalEntries[0].canonical_quorum_member -eq $false
  } catch {
    $OptionalManifestOk = $false
  }
}
Check ($OptionalOk -and $OptionalManifestOk) "Optional specialist $OptionalAgent is real and non-canonical"
Check (Test-Path -LiteralPath $Config -PathType Leaf) "Codex config exists"
if (Test-Path -LiteralPath $Config -PathType Leaf) {
  $Text = Get-Content -LiteralPath $Config -Raw
  Check ($Text -match "(?m)^\s*\[agents\]\s*$") "Config contains [agents]"
  Check ($Text -match "(?m)^\s*enabled\s*=\s*true\s*$") "agents.enabled is true"
  Check ($Text -match "(?m)^\s*max_concurrent_threads_per_session\s*=\s*8\s*$") "Agent thread limit is 8"
}
Check (Test-Path -LiteralPath (Join-Path $Root ".p2p\system\governance\fact-ledger.json") -PathType Leaf) "FACT_LEDGER exists"
Check (Test-Path -LiteralPath (Join-Path $Root ".p2p\system\governance\live-specs.json") -PathType Leaf) "Generated Live Specs exists"
Check (Test-Path -LiteralPath (Join-Path $Root ".p2p\system\governance\live-specs.lock.json") -PathType Leaf) "Live Specs synchronization lock exists"
Check (Test-Path -LiteralPath (Join-Path $Root ".p2p\system\governance\live-specs-preview-report.json") -PathType Leaf) "Live Specs technical preview report exists"
Check (Test-Path -LiteralPath (Join-Path $Root ".p2p\system\governance\runtime-manifest.lock.json") -PathType Leaf) "Protected-runtime lock exists"
Check (Test-Path -LiteralPath (Join-Path $Root ".p2p\system\governance\approval-policy.json") -PathType Leaf) "Mandatory approval policy exists"
Check (Test-Path -LiteralPath (Join-Path $Root ".p2p\project-policy.json") -PathType Leaf) "Project protection policy exists"
Check (Test-Path -LiteralPath (Join-Path $Root ".p2p\system\scripts\p2p_governance.py") -PathType Leaf) "Drift gate helper exists"
Check (Test-Path -LiteralPath (Join-Path $Root ".p2p\system\scripts\p2p_eval.py") -PathType Leaf) "Project eval helper exists"
Check (Test-Path -LiteralPath (Join-Path $Root ".p2p\system\scripts\p2p_approval.py") -PathType Leaf) "User approval helper exists"
Check (Test-Path -LiteralPath (Join-Path $Root ".p2p\system\scripts\p2p_gate.py") -PathType Leaf) "Final release gate helper exists"

$PythonCommand = Get-Command py -ErrorAction SilentlyContinue
if (-not $PythonCommand) {
  $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
}
$DeepDoctor = Join-Path $Root ".p2p\system\scripts\p2p_uiux_doctor.py"
$FoundationDoctor = Join-Path $Root ".p2p\system\scripts\p2p_capability_doctor.py"
if (-not $PythonCommand) {
  Check $false "Python is available for the mandatory drift and manifest checks"
} elseif (-not (Test-Path -LiteralPath $DeepDoctor -PathType Leaf)) {
  Check $false "Deep doctor exists at $DeepDoctor"
} else {
  & $PythonCommand.Source $DeepDoctor --source (Join-Path $Root ".p2p\system")
  Check ($LASTEXITCODE -eq 0) "Deep FACT/eval/runtime-drift doctor passes"
}
if (-not $PythonCommand) {
  Check $false "Python is available for the capability foundation check"
} elseif (-not (Test-Path -LiteralPath $FoundationDoctor -PathType Leaf)) {
  Check $false "Capability Foundation doctor exists at $FoundationDoctor"
} else {
  & $PythonCommand.Source $FoundationDoctor --source (Join-Path $Root ".p2p\system") --profile-root $Agents
  Check ($LASTEXITCODE -eq 0) "Capability Foundation canonical, beginner, trust, readiness, and provider checks pass"
}

$DecisionTraceRuntime = Join-Path $Root ".p2p\system\p2p_capabilities\decision_trace.py"
$DecisionTraceCli = Join-Path $Root ".p2p\system\scripts\p2p_decision_trace.py"
$DecisionTraceManifest = Join-Path $Root ".p2p\system\p2p.manifest.json"
Check (Test-Path -LiteralPath $DecisionTraceRuntime -PathType Leaf) "Native Decision Trace runtime exists"
Check (Test-Path -LiteralPath $DecisionTraceCli -PathType Leaf) "Native Decision Trace CLI exists"
$DecisionTraceMetadataOk = $false
if (Test-Path -LiteralPath $DecisionTraceManifest -PathType Leaf) {
  try {
    $ManifestValue = Get-Content -LiteralPath $DecisionTraceManifest -Raw | ConvertFrom-Json
    $TraceMetadata = $ManifestValue.decision_trace
    $DecisionTraceMetadataOk = $TraceMetadata.schema -eq "p2p-decision-trace/1" -and
      $TraceMetadata.implementation -eq "P2P_NATIVE" -and
      $TraceMetadata.storage -eq ".p2p/state/execution-ledger.jsonl" -and
      $TraceMetadata.external_dependencies_required -eq $false
  } catch {
    $DecisionTraceMetadataOk = $false
  }
}
Check $DecisionTraceMetadataOk "Native Decision Trace manifest binds the existing ledger without external dependencies"
if (-not $PythonCommand) {
  Check $false "Python is available for the Native Decision Trace doctor"
} elseif (-not (Test-Path -LiteralPath $DecisionTraceCli -PathType Leaf)) {
  Check $false "Native Decision Trace doctor exists at $DecisionTraceCli"
} else {
  & $PythonCommand.Source $DecisionTraceCli --project $Root doctor --json
  Check ($LASTEXITCODE -eq 0) "Native Decision Trace doctor preserves canonical 8/8 and optional Aesthetica"
}

if ($Failed) {
  Write-Host "RESULT: FAIL" -ForegroundColor Red
  exit 1
}
Write-Host "RESULT: PASS" -ForegroundColor Green
