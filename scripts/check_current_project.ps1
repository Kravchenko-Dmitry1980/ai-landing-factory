#Requires -Version 5.1
<#
.SYNOPSIS
  Run live project verdict gate on the current/last opened project.

.EXAMPLE
  .\scripts\check_current_project.ps1
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PortsFile = Join-Path $RootDir ".runtime\ports.json"
$PythonExe = Join-Path $RootDir ".venv\Scripts\python.exe"
$ScriptPath = Join-Path $RootDir "backend\scripts\check_live_project_verdict.py"

if (-not (Test-Path $PythonExe)) {
    Write-Error "Python venv not found: $PythonExe"
}

$backendUrl = "http://127.0.0.1:8001"
if (Test-Path $PortsFile) {
    try {
        $ports = Get-Content -Path $PortsFile -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($ports.backend_url) {
            $backendUrl = [string]$ports.backend_url
        }
    }
    catch {
        Write-Warning "Could not read $PortsFile — using default backend URL."
    }
}

Write-Host "Live project verdict (current) — backend: $backendUrl"

& $PythonExe $ScriptPath --current --backend-url $backendUrl --runtime-root $RootDir
exit $LASTEXITCODE
