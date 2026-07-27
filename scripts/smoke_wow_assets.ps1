# Smoke: verify WOW bundle assets exist for Docker/release deploy.
# Usage (repo root):
#   .\scripts\smoke_wow_assets.ps1
#   .\scripts\smoke_wow_assets.ps1 -CheckDockerImage alf-backend

param(
    [string]$CheckDockerImage = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$assetsRel = "frontend/dist-wow/assets/wow-app.js"

function Assert-FileExists([string]$Path, [string]$Hint) {
    if (-not (Test-Path -LiteralPath $Path)) {
        Write-Error "Missing WOW asset: $Path. $Hint"
    }
}

Write-Host "== smoke_wow_assets ==" -ForegroundColor Cyan

# 1) Local dist-wow (optional — may be absent in CI before build)
$localJs = Join-Path $repoRoot $assetsRel
if (Test-Path -LiteralPath $localJs) {
    Write-Host "OK: local $assetsRel" -ForegroundColor Green
} else {
    Write-Host "SKIP: local $assetsRel not built (run: cd frontend && npm run build:wow-bundle)" -ForegroundColor Yellow
}

# 2) Backend Dockerfile must bake dist-wow
$dockerfile = Join-Path $repoRoot "deploy/docker/backend.Dockerfile"
$df = Get-Content -Raw -LiteralPath $dockerfile
if ($df -notmatch "build:wow-bundle") {
    Write-Error "backend.Dockerfile does not run build:wow-bundle"
}
if ($df -notmatch "/app/frontend/dist-wow") {
    Write-Error "backend.Dockerfile does not COPY dist-wow to /app/frontend/dist-wow"
}
Write-Host "OK: backend.Dockerfile embeds dist-wow" -ForegroundColor Green

# 3) Optional: inspect running backend image
if ($CheckDockerImage) {
    $containerPath = "/app/frontend/dist-wow/assets/wow-app.js"
    $out = docker exec $CheckDockerImage sh -lc "test -f $containerPath && echo OK || echo MISSING"
    if ($out -notmatch "OK") {
        Write-Error "Container $CheckDockerImage missing $containerPath"
    }
    Write-Host "OK: $CheckDockerImage has $containerPath" -ForegroundColor Green
}

Write-Host "PASS: smoke_wow_assets" -ForegroundColor Green
