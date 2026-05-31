#Requires -Version 5.1
<#
.SYNOPSIS
  Optional Showcase Builder smoke (HTTP /showcase + registry API flow).

.DESCRIPTION
  Runs backend/scripts/smoke_showcase_browser.py when dev servers are up.
  By default exits 0 with WARN if servers are unavailable (opt-in smoke).

.EXAMPLE
  .\scripts\smoke_showcase_browser.ps1

.EXAMPLE
  .\scripts\smoke_showcase_browser.ps1 -RequireBrowser

.EXAMPLE
  .\scripts\release_check.ps1 -Full -RunBrowserSmoke -RequireBrowserSmoke
#>
[CmdletBinding()]
param(
    [switch]$RequireBrowser,
    [switch]$RequireServer
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PythonExe = Join-Path $RootDir ".venv\Scripts\python.exe"
$SmokeScript = Join-Path $RootDir "backend\scripts\smoke_showcase_browser.py"

if (-not (Test-Path $PythonExe)) {
    Write-Host "FAIL: .venv not found. Run .\run.ps1" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $SmokeScript)) {
    Write-Host "FAIL: missing $SmokeScript" -ForegroundColor Red
    exit 1
}

$args = @($SmokeScript)
if ($RequireBrowser -or $RequireServer) {
    $args += "--require-server"
}

Write-Host "== Showcase browser/API smoke ==" -ForegroundColor Cyan
& $PythonExe @args
$code = $LASTEXITCODE
if ($null -eq $code) { $code = 0 }

if ($code -ne 0) {
    Write-Host "SHOWCASE BROWSER SMOKE: FAIL" -ForegroundColor Red
    exit $code
}

Write-Host "SHOWCASE BROWSER SMOKE: PASS" -ForegroundColor Green
exit 0
