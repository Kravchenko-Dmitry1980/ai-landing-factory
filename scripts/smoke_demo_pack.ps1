# Smoke test for the final demo pack (Stage P.8.2).
#
# Usage:
#   .\scripts\smoke_demo_pack.ps1
#   .\scripts\smoke_demo_pack.ps1 -DemoDir demo_release_20260531_1200

param(
    [string]$DemoDir = "",
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $Root "backend"
$PythonExe = Join-Path $Root ".venv\Scripts\python.exe"

if ($Help) {
    Write-Host "smoke_demo_pack.ps1 - demo pack smoke (offline, no dev-server)"
    exit 0
}

if (-not (Test-Path $PythonExe)) {
    Write-Error "venv not found: $PythonExe"
}

$pyArgs = @("scripts\smoke_demo_pack.py")
if ($DemoDir) {
    $resolved = if ([System.IO.Path]::IsPathRooted($DemoDir)) { $DemoDir } else { Join-Path $Root $DemoDir }
    $pyArgs += @("--dir", $resolved)
}

Push-Location $BackendDir
try {
    & $PythonExe @pyArgs
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
