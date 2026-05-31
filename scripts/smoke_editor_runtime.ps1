param(
    [string]$ProjectId = "",
    [switch]$RequireFrontend
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$message) {
    Write-Host "[SMOKE] $message"
}

function Invoke-Check {
    param(
        [string]$Name,
        [scriptblock]$Action
    )
    try {
        & $Action
        Write-Host "[PASS] $Name"
    } catch {
        Write-Host "[FAIL] $Name"
        throw
    }
}

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$portsPath = Join-Path $root ".runtime\ports.json"

if (-not (Test-Path $portsPath)) {
    throw "ports.json not found: $portsPath"
}

$ports = Get-Content $portsPath | ConvertFrom-Json
$backend = "http://127.0.0.1:$($ports.backend_port)"
$frontend = "http://localhost:$($ports.frontend_port)"

Write-Step "Backend: $backend"
Write-Step "Frontend: $frontend"

Invoke-Check -Name "backend /health" -Action {
    $res = Invoke-WebRequest "$backend/health" -UseBasicParsing
    if ($res.StatusCode -ne 200) {
        throw "Unexpected health status: $($res.StatusCode)"
    }
}

$resolvedProjectId = $ProjectId
if (-not $resolvedProjectId) {
    Write-Step "Resolving project id from API..."
    $projects = Invoke-RestMethod "$backend/api/v1/projects?limit=1&sort=updated_desc" -Method Get
    if (-not $projects -or $projects.Count -lt 1) {
        throw "No projects found in backend storage"
    }
    $resolvedProjectId = $projects[0].id
}

Write-Step "Using project_id: $resolvedProjectId"

Invoke-Check -Name "project API" -Action {
    $res = Invoke-WebRequest "$backend/api/v1/projects/$resolvedProjectId" -UseBasicParsing
    if ($res.StatusCode -ne 200) {
        throw "Unexpected project status: $($res.StatusCode)"
    }
}

Invoke-Check -Name "contract API" -Action {
    $res = Invoke-WebRequest "$backend/api/v1/projects/$resolvedProjectId/contract" -UseBasicParsing
    if ($res.StatusCode -ne 200) {
        throw "Unexpected contract status: $($res.StatusCode)"
    }
}

Invoke-Check -Name "export html standard" -Action {
    $res = Invoke-WebRequest "$backend/api/v1/projects/$resolvedProjectId/export/html" -UseBasicParsing
    if ($res.StatusCode -ne 200) {
        throw "Unexpected standard export status: $($res.StatusCode)"
    }
}

Invoke-Check -Name "export html wow" -Action {
    $res = Invoke-WebRequest "$backend/api/v1/projects/$resolvedProjectId/export/html?mode=wow" -UseBasicParsing
    if ($res.StatusCode -ne 200) {
        throw "Unexpected wow export status: $($res.StatusCode)"
    }
}

Invoke-Check -Name "export wow bundle endpoint" -Action {
    try {
        $res = Invoke-WebRequest "$backend/api/v1/projects/$resolvedProjectId/export/wow-bundle" -UseBasicParsing
        if ($res.StatusCode -ne 200) {
            throw "Unexpected wow bundle status: $($res.StatusCode)"
        }
    } catch {
        $response = $_.Exception.Response
        if (-not $response) {
            throw
        }
        $status = [int]$response.StatusCode
        if ($status -ne 503) {
            throw "Unexpected wow bundle failure status: $status"
        }
        Write-Step "WOW bundle returned 503 (dist-wow missing) - acceptable in smoke"
    }
}

$frontendWarnings = @()

foreach ($path in @(
        "/editor/$resolvedProjectId",
        "/preview/$resolvedProjectId",
        "/preview/${resolvedProjectId}?mode=wow",
        "/preview/${resolvedProjectId}?mode=wow3d"
    )) {
    $name = "frontend $path"
    try {
        $res = Invoke-WebRequest "$frontend$path" -UseBasicParsing
        if ($res.StatusCode -ne 200) {
            throw "Unexpected status $($res.StatusCode)"
        }
        Write-Host "[PASS] $name"
    } catch {
        if ($RequireFrontend) {
            Write-Host "[FAIL] $name"
            throw
        }
        $frontendWarnings += ("{0} unavailable: {1}" -f $name, $_.Exception.Message)
        Write-Host "[WARN] $name"
    }
}

if ($frontendWarnings.Count -gt 0) {
    Write-Host ""
    Write-Host "Frontend warnings:"
    $frontendWarnings | ForEach-Object { Write-Host " - $_" }
}

Write-Host ""
Write-Host "SMOKE EDITOR RUNTIME: PASS"
Write-Host "project_id=$resolvedProjectId"
