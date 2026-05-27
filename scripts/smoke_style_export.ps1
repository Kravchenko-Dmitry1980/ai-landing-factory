# Smoke: export style profiles (offline + optional HTTP)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$PythonExe = Join-Path $Root ".venv\Scripts\python.exe"
$BackendDir = Join-Path $Root "backend"

if (-not (Test-Path $PythonExe)) {
    Write-Error "venv not found: $PythonExe"
}

$args = @("scripts\smoke_style_export.py")
$BackendUrl = $env:ALF_API_URL
if (-not $BackendUrl) { $BackendUrl = "http://127.0.0.1:8001" }

$lastProject = Join-Path $Root ".runtime\last_project.json"
if (Test-Path $lastProject) {
    try {
        $pid = (Get-Content $lastProject -Raw | ConvertFrom-Json).project_id
        if ($pid) {
            $args += @("--backend-url", $BackendUrl, "--project-id", $pid)
        }
    }
    catch { }
}

Push-Location $BackendDir
try {
    & $PythonExe @args
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
