# Smoke: default university export + custom style_config safety
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$ApiBase = if ($env:ALF_API_URL) { $env:ALF_API_URL } else { "http://127.0.0.1:8001/api/v1" }

$lastProject = Join-Path $Root ".runtime\last_project.json"
if (-not (Test-Path $lastProject)) {
    Write-Error "No .runtime/last_project.json — run .\run.ps1 and open a project first."
}
$projectId = (Get-Content $lastProject -Raw | ConvertFrom-Json).project_id
if (-not $projectId) { Write-Error "project_id missing in last_project.json" }

$errors = @()

function Test-Export($Query, $Label) {
    $uri = "$ApiBase/projects/$projectId/export/html$Query"
    try {
        $resp = Invoke-RestMethod -Uri $uri -Method Get
    } catch {
        $script:errors += "$Label : HTTP failed — $_"
        return
    }
    $html = $resp.html
    if (-not $html -or $html.Length -lt 200) {
        $script:errors += "$Label : HTML empty"
        return
    }
    return $html
}

Write-Host "Smoke style export — project $projectId"

$htmlDefault = Test-Export "" "default"
if ($htmlDefault -notmatch "theme-university_platform") {
    $errors += "default: missing theme-university_platform body class"
}

$styleConfig = @{
    profile = "custom"
    custom_style_prompt = "тёмный технологичный синий 3d"
    theme_tokens = @{
        color_scheme = "dark"
        accent = "blue"
        hero_mode = "future_3d"
    }
} | ConvertTo-Json -Compress
$encoded = [uri]::EscapeDataString($styleConfig)
$htmlCustom = Test-Export "?style_config=$encoded" "custom"
if ($htmlCustom -match "<script>") {
    $errors += "custom: raw script tag leaked"
}
if ($htmlCustom -notmatch "hero--future-3d") {
    $errors += "custom: missing hero--future-3d hook"
}
if ($htmlCustom -notmatch "--accent: #2563eb") {
    $errors += "custom: accent CSS override missing"
}

if ($errors.Count -gt 0) {
    Write-Host "FAILED"
    $errors | ForEach-Object { Write-Host " - $_" }
    exit 1
}

Write-Host "OK — university default + custom tokens"
exit 0
