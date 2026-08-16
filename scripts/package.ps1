param(
  [string]$Output
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$PythonCommand = Get-Command py -ErrorAction SilentlyContinue
if (-not $PythonCommand) {
  $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
}
if (-not $PythonCommand) {
  throw "Python was not found. It is required to build the integrity-checked P2P release."
}
$Arguments = @((Join-Path $Root "scripts\package_release.py"), "--root", $Root, "build")
if ($Output) {
  $Arguments = @((Join-Path $Root "scripts\package_release.py"), "--root", $Root, "--output", $Output, "build")
}
& $PythonCommand.Source @Arguments
if ($LASTEXITCODE -ne 0) {
  throw "P2P release package build failed."
}
