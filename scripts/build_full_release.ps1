# Build full-product release archive for systemd/nginx deploy.
# Output: .runtime/release/full-product/ + ai-landing-full-product.zip
#
# Excludes: .git, .venv, node_modules, .runtime, logs, backend/data, .env, caches
#
# Usage:
#   .\scripts\build_full_release.ps1

param(
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

if ($Help) {
    Write-Host "build_full_release.ps1 - pack sources + deploy templates into a zip (no secrets)."
    exit 0
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$stage = Join-Path $Root ".runtime\release\full-product"
$zipPath = Join-Path $Root ".runtime\release\ai-landing-full-product.zip"

if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
New-Item -ItemType Directory -Force -Path $stage | Out-Null

$excludeDirNames = @(
    ".git", ".venv", "node_modules", ".runtime", "logs", ".next", ".pytest_cache",
    "__pycache__", "dist-wow", ".claude", ".cursor", "hallmark"
)
$excludeFileGlobs = @(
    "*.pyc", "*.pyo", "*.log", ".DS_Store", "Thumbs.db",
    ".env", ".env.local", ".env.production", ".env.docker"
)

function Should-SkipPath {
    param([string]$FullPath, [string]$RootPath)
    $rel = $FullPath.Substring($RootPath.Length).TrimStart("\", "/")
    $parts = $rel -split "[\\/]"
    foreach ($p in $parts) {
        if ($excludeDirNames -contains $p) { return $true }
    }
    # backend/data and uploads
    if ($rel -match '(?i)^backend[\\/]data([\\/]|$)') { return $true }
    if ($rel -match '(?i)^backend[\\/]\.env$') { return $true }
    if ($rel -match '(?i)^frontend[\\/]\.env') {
        # allow tracked examples only
        if ($rel -notmatch '(?i)\.example$') { return $true }
    }
    $name = Split-Path $FullPath -Leaf
    if ($name -eq ".env" -or $name -eq ".env.local" -or $name -eq ".env.production") { return $true }
    if ($name -match '\.log$') { return $true }
    if ($name -eq "-files logs") { return $true }
    return $false
}

$includeRoots = @(
    "backend",
    "frontend",
    "scripts",
    "deploy",
    "docs",
    "demo_release_20260531_2247",
    "requirements.txt",
    "run.ps1",
    "README.md",
    "README_RUN.md",
    ".gitignore",
    "FINAL_GO_NO_GO.md",
    "SERVER_DEPLOY_PREP.md",
    "UAT_ALGOFUSION_DOCX_REPAIR_REPORT.md",
    "UAT_FREEMODEL_REPORT.md",
    "UAT_FRESH_CLONE_REPORT.md",
    "UAT_RELEASE_REPORT.md",
    "DEPLOY_PREP_REPORT.md",
    "DEPLOY_SECURITY_AUDIT.md",
    "DEPLOY_RELEASE_CHECKLIST.md"
)

Write-Host "Staging full release into $stage" -ForegroundColor Cyan

foreach ($item in $includeRoots) {
    $src = Join-Path $Root $item
    if (-not (Test-Path $src)) {
        Write-Host "  skip missing: $item"
        continue
    }
    $itemObj = Get-Item $src
    if ($itemObj.PSIsContainer) {
        Get-ChildItem -Path $src -Recurse -Force -File | ForEach-Object {
            if (Should-SkipPath -FullPath $_.FullName -RootPath $Root) { return }
            $rel = $_.FullName.Substring($Root.Length).TrimStart("\", "/")
            $dest = Join-Path $stage $rel
            $destParent = Split-Path $dest -Parent
            if (-not (Test-Path $destParent)) {
                New-Item -ItemType Directory -Force -Path $destParent | Out-Null
            }
            Copy-Item -LiteralPath $_.FullName -Destination $dest -Force
        }
    } else {
        Copy-Item -LiteralPath $src -Destination (Join-Path $stage $item) -Force
    }
}

# Ensure empty backend/data placeholder (no user uploads)
$dataPlaceholder = Join-Path $stage "backend\data"
New-Item -ItemType Directory -Force -Path $dataPlaceholder | Out-Null
Set-Content -Path (Join-Path $dataPlaceholder ".gitkeep") -Value "" -Encoding UTF8

# Sanity: secrets / junk must not be present
$forbidden = @(
    (Join-Path $stage "backend\.env"),
    (Join-Path $stage "frontend\.env.local"),
    (Join-Path $stage ".venv"),
    (Join-Path $stage "frontend\node_modules"),
    (Join-Path $stage ".git"),
    (Join-Path $stage ".runtime")
)
foreach ($bad in $forbidden) {
    if (Test-Path $bad) { throw "Forbidden path present in stage: $bad" }
}

# Spot-check required deploy templates
$need = @(
    "deploy\systemd\alf-backend.service",
    "deploy\systemd\alf-frontend.service",
    "deploy\nginx\ai-landing-full.conf",
    "deploy\nginx\ai-landing-static.conf",
    "backend\.env.production.example",
    "frontend\.env.production.example",
    "backend\app\main.py",
    "frontend\package.json",
    "frontend\package-lock.json",
    "backend\requirements.txt"
)
foreach ($n in $need) {
    $p = Join-Path $stage $n
    if (-not (Test-Path $p)) { throw "Missing required release file: $n" }
}

if (Test-Path $zipPath) { Remove-Item -Force $zipPath }
Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $zipPath -Force

# Verify zip has no .env
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [IO.Compression.ZipFile]::OpenRead($zipPath)
try {
    $envEntries = $zip.Entries | Where-Object {
        $_.FullName -match '(^|[\\/])\.env$' -or
        $_.FullName -match '(^|[\\/])\.env\.local$' -or
        $_.FullName -match 'node_modules' -or
        $_.FullName -match '(^|[\\/])\.venv([\\/]|$)' -or
        $_.FullName -match '(^|[\\/])\.git([\\/]|$)'
    }
    if ($envEntries) {
        $names = ($envEntries | Select-Object -First 10 | ForEach-Object { $_.FullName }) -join ", "
        throw "Zip contains forbidden entries: $names"
    }
}
finally {
    $zip.Dispose()
}

Write-Host ""
Write-Host "Full product release OK" -ForegroundColor Green
Write-Host "  Folder: $stage"
Write-Host "  Archive: $zipPath"
Write-Host ("  Size: {0:N1} MB" -f ((Get-Item $zipPath).Length / 1MB))
Write-Host "  Stamp: $stamp"
