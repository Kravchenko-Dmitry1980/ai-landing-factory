# Build the Interactive WOW Bundle (Stage P.7.2).
#
# Produces frontend/dist-wow/assets/wow-app.js (+ wow-app.css) — the standalone
# React/R3F app embedded into the exported WOW ZIP by the backend exporter.
#
# Usage:
#   .\scripts\build_wow_bundle.ps1
#   .\scripts\build_wow_bundle.ps1 -Smoke   # also run the backend export smoke

param(
    [switch]$Smoke
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $Root "frontend"
$BackendDir = Join-Path $Root "backend"
$PythonExe = Join-Path $Root ".venv\Scripts\python.exe"

Push-Location $FrontendDir
try {
    Write-Host "Building interactive WOW bundle (esbuild)..." -ForegroundColor Cyan
    & npm run build:wow-bundle
    if ($LASTEXITCODE -ne 0) { Write-Error "build:wow-bundle failed" }
}
finally {
    Pop-Location
}

if ($Smoke) {
    if (-not (Test-Path $PythonExe)) {
        Write-Error "venv not found: $PythonExe"
    }
    Push-Location $BackendDir
    try {
        Write-Host "Running backend bundle export smoke..." -ForegroundColor Cyan
        & $PythonExe "scripts\smoke_wow_bundle_export.py"
        exit $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
}
