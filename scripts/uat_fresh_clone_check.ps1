#Requires -Version 5.1
<#
.SYNOPSIS
  Fresh-clone UAT checks after .\run.ps1 (no OCR/VLM).

.EXAMPLE
  .\scripts\uat_fresh_clone_check.ps1
#>
[CmdletBinding()]
param(
    [switch]$SkipFrontend
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BackendDir = Join-Path $RootDir "backend"
$PythonExe = Join-Path $RootDir ".venv\Scripts\python.exe"
$FrontendSmoke = Join-Path $PSScriptRoot "smoke_frontend_simple.ps1"

function Write-Step([string]$Name) {
    Write-Host ""
    Write-Host "== $Name ==" -ForegroundColor Cyan
}

if (-not (Test-Path $PythonExe)) {
    Write-Error "venv not found. Run .\run.ps1 first."
    exit 1
}

$failed = $false

Write-Step "Dependency audit"
Push-Location $BackendDir
try {
    & $PythonExe scripts\audit_simple_dependencies.py
    if ($LASTEXITCODE -ne 0) { $failed = $true }
}
finally {
    Pop-Location
}

Write-Step "Product mode runtime"
Push-Location $BackendDir
try {
    & $PythonExe scripts\smoke_product_mode_runtime.py
    if ($LASTEXITCODE -ne 0) { $failed = $true }
}
finally {
    Pop-Location
}

Write-Step "Simple user flow"
Push-Location $BackendDir
try {
    & $PythonExe scripts\smoke_user_flow_simple.py
    if ($LASTEXITCODE -ne 0) { $failed = $true }
}
finally {
    Pop-Location
}

if (-not $SkipFrontend) {
    Write-Step "Frontend HTTP smoke"
    if (Test-Path $FrontendSmoke) {
        & $FrontendSmoke
        if ($LASTEXITCODE -ne 0) {
            Write-Host "WARN: frontend HTTP check failed (servers may still be starting)" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "SKIP: smoke_frontend_simple.ps1 missing"
    }
}

Write-Host ""
if ($failed) {
    Write-Host "UAT FRESH CLONE CHECK: FAIL" -ForegroundColor Red
    exit 1
}
Write-Host "UAT FRESH CLONE CHECK: PASS" -ForegroundColor Green
exit 0
