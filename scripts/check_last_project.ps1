#Requires -Version 5.1
<#
.SYNOPSIS
  Live project verdict gate for the newest project (no manual UUID).

.EXAMPLE
  .\scripts\check_last_project.ps1

.EXAMPLE
  .\scripts\check_last_project.ps1 -Help
#>
param(
    [switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

if ($Help) {
    Write-Host @"
Usage:
  .\scripts\check_last_project.ps1
  .\scripts\check_last_project.ps1 -Help

Description:
  Runs LIVE PROJECT VERDICT on the newest project from GET /api/v1/projects.
  Backend URL is read from .runtime\ports.json automatically.
  No manual PROJECT_ID required.

Examples:
  cd C:\Dima\Projects\CURSOR\Lend
  .\scripts\check_last_project.ps1
"@
    exit 0
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
$PortsFile = Join-Path $RootDir ".runtime\ports.json"
$PythonExe = Join-Path $RootDir ".venv\Scripts\python.exe"
$VerdictScript = Join-Path $RootDir "backend\scripts\check_live_project_verdict.py"

if (-not (Test-Path $PortsFile)) {
    Write-Host "ports.json not found. Run .\scripts\start_dev.ps1 first."
    exit 1
}

if (-not (Test-Path $PythonExe)) {
    Write-Host "Python venv not found. Run .\.venv\Scripts\pip.exe install -r backend\requirements.txt"
    exit 1
}

$Ports = Get-Content $PortsFile -Raw -Encoding UTF8 | ConvertFrom-Json
$BackendUrl = [string]$Ports.backend_url

if ([string]::IsNullOrWhiteSpace($BackendUrl)) {
    Write-Host "backend_url is empty in .runtime\ports.json. Run .\scripts\start_dev.ps1 first."
    exit 1
}

$BackendUrl = $BackendUrl.TrimEnd("/")

& $PythonExe $VerdictScript --latest --backend-url $BackendUrl
exit $LASTEXITCODE
