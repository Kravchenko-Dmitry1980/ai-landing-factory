# Build static demo release from demo_release_* pack.
# Output: .runtime/release/static-demo/ + ai-landing-static-demo.zip
#
# Usage:
#   .\scripts\build_static_demo_release.ps1
#   .\scripts\build_static_demo_release.ps1 -DemoDir demo_release_20260531_2247

param(
    [string]$DemoDir = "",
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

function Show-Help {
    Write-Host @"
build_static_demo_release.ps1

Collects offline demo pack into .runtime/release/static-demo and zips it.
Does not deploy to a server.
"@
}

if ($Help) { Show-Help; exit 0 }

function Find-DemoDir {
    param([string]$Preferred)
    if ($Preferred) {
        $p = if ([IO.Path]::IsPathRooted($Preferred)) { $Preferred } else { Join-Path $Root $Preferred }
        if (-not (Test-Path $p)) { throw "DemoDir not found: $p" }
        return (Resolve-Path $p).Path
    }
    $exact = Join-Path $Root "demo_release_20260531_2247"
    if (Test-Path $exact) { return (Resolve-Path $exact).Path }
    $latest = Get-ChildItem -Path $Root -Directory -Filter "demo_release_*" |
        Sort-Object Name -Descending |
        Select-Object -First 1
    if (-not $latest) { throw "No demo_release_* directory found under $Root" }
    return $latest.FullName
}

function Test-NoExternalCdn {
    param([string]$Path)
    $patterns = @(
        "cdn\.jsdelivr\.net",
        "unpkg\.com",
        "cdnjs\.cloudflare\.com",
        "aframe\.io/releases",
        "fonts\.googleapis\.com"
    )
    $hits = @()
    Get-ChildItem -Path $Path -Recurse -Include *.html,*.js,*.css -File -ErrorAction SilentlyContinue |
        ForEach-Object {
            $text = Get-Content -LiteralPath $_.FullName -Raw -ErrorAction SilentlyContinue
            if (-not $text) { return }
            foreach ($pat in $patterns) {
                if ($text -match $pat) {
                    $hits += "$($_.FullName) ~ $pat"
                }
            }
        }
    return $hits
}

$demo = Find-DemoDir -Preferred $DemoDir
Write-Host "Demo source: $demo" -ForegroundColor Cyan

$outDir = Join-Path $Root ".runtime\release\static-demo"
$zipPath = Join-Path $Root ".runtime\release\ai-landing-static-demo.zip"
$checkDir = Join-Path $Root ".runtime\release\static-demo-check"

if (Test-Path $outDir) { Remove-Item -Recurse -Force $outDir }
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

# Copy README + checks
Copy-Item (Join-Path $demo "README_DEMO_RU.md") (Join-Path $outDir "README_DEMO_RU.md") -Force
if (Test-Path (Join-Path $demo "CHECKS")) {
    Copy-Item (Join-Path $demo "CHECKS") (Join-Path $outDir "CHECKS") -Recurse -Force
}
if (Test-Path (Join-Path $demo "demo_pack_meta.json")) {
    Copy-Item (Join-Path $demo "demo_pack_meta.json") (Join-Path $outDir "demo_pack_meta.json") -Force
}
Copy-Item (Join-Path $Root "deploy\static\README_STATIC_DEPLOY.md") `
    (Join-Path $outDir "README_STATIC_DEPLOY.md") -Force -ErrorAction SilentlyContinue

# Standard landing
$stdSrc = Join-Path $demo "04_standard_landing\standard_landing.html"
$stdDst = Join-Path $outDir "standard"
New-Item -ItemType Directory -Force -Path $stdDst | Out-Null
if (Test-Path $stdSrc) {
    Copy-Item $stdSrc (Join-Path $stdDst "index.html") -Force
} else {
    Write-Warning "standard_landing.html missing"
}

# Static WOW HTML
$wowHtmlSrc = Join-Path $demo "02_static_wow_landing\wow_landing.html"
$wowHtmlDst = Join-Path $outDir "static-wow"
New-Item -ItemType Directory -Force -Path $wowHtmlDst | Out-Null
if (Test-Path $wowHtmlSrc) {
    Copy-Item $wowHtmlSrc (Join-Path $wowHtmlDst "index.html") -Force
}

# Interactive WOW ZIP → wow/
$wowZip = Join-Path $demo "01_interactive_wow_landing\ai-wow-landing.zip"
$wowDst = Join-Path $outDir "wow"
New-Item -ItemType Directory -Force -Path $wowDst | Out-Null
if (Test-Path $wowZip) {
    Expand-Archive -LiteralPath $wowZip -DestinationPath $wowDst -Force
} else {
    Write-Warning "ai-wow-landing.zip missing"
}

# Showcase ZIP → showcase/
$showZip = Join-Path $demo "03_showcase_vr_ar\ai-showcase.zip"
$showDst = Join-Path $outDir "showcase"
New-Item -ItemType Directory -Force -Path $showDst | Out-Null
if (Test-Path $showZip) {
    Expand-Archive -LiteralPath $showZip -DestinationPath $showDst -Force
} else {
    Write-Warning "ai-showcase.zip missing"
}

# Root index.html navigator
$indexHtml = @"
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AI Landing Factory — Static Demo</title>
  <style>
    body { font-family: Georgia, "Times New Roman", serif; margin: 0; padding: 2.5rem;
           background: linear-gradient(160deg, #f7f4ef 0%, #e8eef5 100%); color: #1a1a1a; }
    main { max-width: 42rem; }
    h1 { font-size: 2rem; margin: 0 0 0.5rem; }
    p { line-height: 1.5; }
    ul { padding-left: 1.2rem; }
    a { color: #0b3d5c; }
  </style>
</head>
<body>
  <main>
    <h1>AI Landing Factory</h1>
    <p>Статический demo pack (без backend / AI).</p>
    <ul>
      <li><a href="./wow/">Interactive WOW landing</a></li>
      <li><a href="./static-wow/">Static WOW HTML</a></li>
      <li><a href="./showcase/">VR/AR Showcase</a></li>
      <li><a href="./standard/">Standard landing</a></li>
      <li><a href="./README_DEMO_RU.md">README (RU)</a></li>
    </ul>
  </main>
</body>
</html>
"@
Set-Content -Path (Join-Path $outDir "index.html") -Value $indexHtml -Encoding UTF8

# Required checks
$required = @(
    (Join-Path $outDir "index.html"),
    (Join-Path $outDir "wow\index.html"),
    (Join-Path $outDir "standard\index.html")
)
foreach ($req in $required) {
    if (-not (Test-Path $req)) { throw "Required file missing: $req" }
}

$cdnHits = Test-NoExternalCdn -Path $outDir
if ($cdnHits.Count -gt 0) {
    Write-Warning "Possible external CDN references found:"
    $cdnHits | ForEach-Object { Write-Warning "  $_" }
} else {
    Write-Host "CDN check: no common external CDN hits" -ForegroundColor Green
}

# Zip
if (Test-Path $zipPath) { Remove-Item -Force $zipPath }
Compress-Archive -Path (Join-Path $outDir "*") -DestinationPath $zipPath -Force

# Optional expand verify
if (Test-Path $checkDir) { Remove-Item -Recurse -Force $checkDir }
Expand-Archive -LiteralPath $zipPath -DestinationPath $checkDir -Force
if (-not (Test-Path (Join-Path $checkDir "index.html"))) {
    throw "Zip verify failed: index.html missing in archive"
}

Write-Host ""
Write-Host "Static demo release OK" -ForegroundColor Green
Write-Host "  Folder: $outDir"
Write-Host "  Archive: $zipPath"
Write-Host ("  Size: {0:N1} MB" -f ((Get-Item $zipPath).Length / 1MB))
