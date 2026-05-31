# Build the final demo pack (Stage P.8.2).
#
# Runs release gates (optional), WOW bundle build, assembles demo artifacts.
#
# Usage:
#   .\scripts\build_demo_pack.ps1
#   .\scripts\build_demo_pack.ps1 -ProjectId 8d1393c9-0803-4096-8ec9-8b4ca3ee7364
#   .\scripts\build_demo_pack.ps1 -SkipGates -SkipBuild
#   .\scripts\build_demo_pack.ps1 -Help

param(
    [string]$ProjectId = "",
    [string]$OutputDir = "",
    [switch]$SkipBuild,
    [switch]$SkipGates,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"
$PythonExe = Join-Path $Root ".venv\Scripts\python.exe"

function Show-Help {
    Write-Host @"
build_demo_pack.ps1 - final demo pack (Stage P.8.2)

Параметры:
  -ProjectId <uuid>   UUID проекта (иначе last_project / registry / fixture)
  -OutputDir <path>   Папка вывода (иначе demo_release_YYYYMMDD_HHMM)
  -SkipBuild           Не пересобирать frontend/dist-wow
  -SkipGates           Не запускать release_check перед сборкой
  -Help                Эта справка

Пример:
  .\scripts\build_demo_pack.ps1
"@
}

if ($Help) {
    Show-Help
    exit 0
}

if (-not (Test-Path $PythonExe)) {
    Write-Error "venv not found: $PythonExe"
}

$gateSimple = "skipped"
$gateFull = "skipped"
$smokeWow = "skipped"

if (-not $SkipGates) {
    Write-Host "== Release gate: Simple ==" -ForegroundColor Cyan
    & (Join-Path $Root "scripts\release_check.ps1") -SkipFrontendBuild
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Simple release gate FAILED - demo pack not built"
    }
    $gateSimple = "PASS"

    Write-Host "== Release gate: Full ==" -ForegroundColor Cyan
    & (Join-Path $Root "scripts\release_check.ps1") -Full -SkipFrontendBuild
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Full release gate FAILED - demo pack not built"
    }
    $gateFull = "PASS"
}
else {
    $gateSimple = "PASS (pre-run via release_check.ps1)"
    $gateFull = "PASS (pre-run via release_check.ps1 -Full)"
}

if (-not $SkipBuild) {
    Push-Location $FrontendDir
    try {
        Remove-Item -Recurse -Force .\dist-wow -ErrorAction SilentlyContinue
        Write-Host "Building WOW bundle (npm run build:wow-bundle)..." -ForegroundColor Cyan
        & npm run build:wow-bundle
        if ($LASTEXITCODE -ne 0) { Write-Error "build:wow-bundle failed" }
    }
    finally {
        Pop-Location
    }

    Push-Location $BackendDir
    try {
        Write-Host "WOW bundle export smoke..." -ForegroundColor Cyan
        & $PythonExe "scripts\smoke_wow_bundle_export.py"
        if ($LASTEXITCODE -ne 0) { Write-Error "smoke_wow_bundle_export failed" }
        $smokeWow = "PASS"
    }
    finally {
        Pop-Location
    }
}

if (-not $OutputDir) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmm"
    $OutputDir = Join-Path $Root "demo_release_$stamp"
}

$pyArgs = @("scripts\build_demo_pack.py", "--output-dir", $OutputDir)
if ($ProjectId) { $pyArgs += @("--project-id", $ProjectId) }
$pyArgs += @("--gate-simple", $gateSimple, "--gate-full", $gateFull, "--smoke-wow-bundle", $smokeWow)

Push-Location $BackendDir
try {
    Write-Host "Assembling demo pack -> $OutputDir" -ForegroundColor Cyan
    & $PythonExe @pyArgs
    if ($LASTEXITCODE -ne 0) { Write-Error "build_demo_pack.py failed" }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Demo pack ready: $OutputDir" -ForegroundColor Green
Write-Host "Next: .\scripts\smoke_demo_pack.ps1 -DemoDir `"$OutputDir`""
