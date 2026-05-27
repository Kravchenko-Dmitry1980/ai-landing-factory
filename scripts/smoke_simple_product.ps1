#Requires -Version 5.1
<#
.SYNOPSIS
  Simple product mode smoke (backend only, no OCR/VLM).
#>
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BackendDir = Join-Path $RootDir "backend"
$PythonExe = Join-Path $RootDir ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Error "venv Python not found: $PythonExe. Run .\run.ps1 first."
    exit 1
}

Push-Location $BackendDir
try {
    & $PythonExe scripts\smoke_simple_product_mode.py
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
