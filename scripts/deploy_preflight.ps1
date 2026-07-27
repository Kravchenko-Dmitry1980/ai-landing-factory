# Local deploy preflight — does NOT push or deploy to a server.
#
# Usage:
#   .\scripts\deploy_preflight.ps1
#   .\scripts\deploy_preflight.ps1 -SkipRuntime
#   .\scripts\deploy_preflight.ps1 -SkipBuild

param(
    [switch]$SkipRuntime,
    [switch]$SkipBuild,
    [switch]$SkipStaticBuild,
    [switch]$Help
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if ($Help) {
    Write-Host @"
deploy_preflight.ps1 — local readiness checks before server deploy.

Checks Python/Node/.venv, env examples, deploy templates, no tracked .env,
optional runtime health, optional frontend build, optional static release build.
Never pushes or SSHes to a server.
"@
    exit 0
}

$failed = 0
$warnings = 0

function Ok([string]$msg) { Write-Host "[PASS] $msg" -ForegroundColor Green }
function Warn([string]$msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow; $script:warnings++ }
function Fail([string]$msg) { Write-Host "[FAIL] $msg" -ForegroundColor Red; $script:failed++ }

Write-Host "== Deploy preflight ==" -ForegroundColor Cyan
Write-Host "Root: $Root"

# Tooling
try {
    $py = & python --version 2>&1
    Ok "python: $py"
} catch { Fail "python missing" }

$venvPy = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $venvPy) {
    $vp = & $venvPy --version 2>&1
    Ok ".venv python: $vp"
} else {
    Fail ".venv missing ($venvPy)"
}

try {
    $nv = & node --version 2>&1
    Ok "node: $nv"
} catch { Fail "node missing" }

try {
    $np = & npm --version 2>&1
    Ok "npm: $np"
} catch { Fail "npm missing" }

$nm = Join-Path $Root "frontend\node_modules"
if (Test-Path $nm) { Ok "frontend/node_modules present" } else { Warn "frontend/node_modules missing — run npm ci in frontend" }

# Env examples
$envExamples = @(
    "backend\.env.example",
    "backend\.env.production.example",
    "frontend\.env.local.example",
    "frontend\.env.production.example",
    "deploy\docker\.env.docker.example"
)
foreach ($e in $envExamples) {
    if (Test-Path (Join-Path $Root $e)) { Ok "env example: $e" } else { Fail "missing env example: $e" }
}

# Deploy templates
$templates = @(
    "deploy\nginx\ai-landing-full.conf",
    "deploy\nginx\ai-landing-static.conf",
    "deploy\systemd\alf-backend.service",
    "deploy\systemd\alf-frontend.service",
    "deploy\ubuntu\README_FULL_SYSTEMD_DEPLOY.md",
    "deploy\ubuntu\README_DOCKER_FIRST_DEPLOY.md",
    "deploy\ubuntu\install_prereqs.sh",
    "deploy\ubuntu\deploy_release.sh",
    "deploy\ubuntu\rollback.sh",
    "deploy\ubuntu\healthcheck.sh",
    "deploy\static\README_STATIC_DEPLOY.md",
    "deploy\docker\docker-compose.yml",
    "deploy\docker\backend.Dockerfile",
    "deploy\docker\frontend.Dockerfile",
    "scripts\build_static_demo_release.ps1",
    "scripts\build_full_release.ps1"
)
foreach ($t in $templates) {
    if (Test-Path (Join-Path $Root $t)) { Ok "template: $t" } else { Fail "missing template: $t" }
}

# No tracked .env
$trackedEnv = & git -C $Root ls-files | Select-String -Pattern '(^|/)\.env$'
if ($trackedEnv) {
    Fail "tracked .env files found in git"
    $trackedEnv | ForEach-Object { Write-Host "  $_" }
} else {
    Ok "no tracked .env files"
}

# Demo pack
$demo = Join-Path $Root "demo_release_20260531_2247"
if (Test-Path $demo) { Ok "demo pack present" } else { Warn "demo_release_20260531_2247 missing" }

# Frontend build
if (-not $SkipBuild) {
    Write-Host "== frontend build ==" -ForegroundColor Cyan
    Push-Location (Join-Path $Root "frontend")
    try {
        & npm run build
        if ($LASTEXITCODE -eq 0) { Ok "npm run build" } else { Fail "npm run build failed (exit $LASTEXITCODE)" }
    } finally {
        Pop-Location
    }
} else {
    Warn "frontend build skipped (-SkipBuild)"
}

# Runtime
if (-not $SkipRuntime) {
    Write-Host "== runtime ==" -ForegroundColor Cyan
    $stop = Join-Path $Root "scripts\stop_dev.ps1"
    $run = Join-Path $Root "run.ps1"
    if (Test-Path $stop) { & $stop | Out-Null }
    & $run -SkipInstall
    Start-Sleep -Seconds 8
    try {
        $h = Invoke-WebRequest -Uri "http://127.0.0.1:8001/health" -UseBasicParsing -TimeoutSec 10
        if ($h.StatusCode -eq 200) { Ok "backend /health 200" } else { Fail "backend /health $($h.StatusCode)" }
    } catch { Fail "backend /health unreachable: $($_.Exception.Message)" }
    try {
        $f = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 15
        if ($f.StatusCode -eq 200) { Ok "frontend / 200" } else { Fail "frontend / $($f.StatusCode)" }
    } catch { Fail "frontend unreachable: $($_.Exception.Message)" }
} else {
    Warn "runtime checks skipped (-SkipRuntime)"
}

# Static release build
if (-not $SkipStaticBuild) {
    Write-Host "== static demo release ==" -ForegroundColor Cyan
    & (Join-Path $Root "scripts\build_static_demo_release.ps1")
    if ($LASTEXITCODE -eq 0 -and (Test-Path (Join-Path $Root ".runtime\release\ai-landing-static-demo.zip"))) {
        Ok "static demo zip built"
    } else {
        Fail "static demo release failed"
    }
} else {
    Warn "static build skipped (-SkipStaticBuild)"
}

Write-Host ""
Write-Host "== Summary: failed=$failed warnings=$warnings ==" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })
if ($failed -gt 0) { exit 1 }
exit 0
