#Requires -Version 5.1
<#
.SYNOPSIS
  Simple Release Gate before push/release (no OCR/VLM, no live ENDO).

.EXAMPLE
  .\scripts\release_check.ps1

.EXAMPLE
  .\scripts\release_check.ps1 -Fast

.EXAMPLE
  .\scripts\release_check.ps1 -Full

.EXAMPLE
  .\scripts\release_check.ps1 -SkipFrontendBuild

.EXAMPLE
  .\scripts\release_check.ps1 -Full -SkipShowcaseSmoke
#>
[CmdletBinding()]
param(
    [switch]$Fast,
    [switch]$Full,
    [switch]$SkipFrontendBuild,
    [switch]$SkipShowcaseSmoke
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$PythonExe = Join-Path $RootDir ".venv\Scripts\python.exe"
$BackendEnv = Join-Path $BackendDir ".env"
$npmCmd = Get-Command npm.cmd -ErrorAction SilentlyContinue
if ($npmCmd) { $NpmExe = $npmCmd.Source } else { $NpmExe = "npm.cmd" }

$results = New-Object System.Collections.Generic.List[object]
$failed = $false

function Write-Step([string]$Name) {
    Write-Host ""
    Write-Host "== $Name ==" -ForegroundColor Cyan
}

function Add-Result([string]$Name, [bool]$Ok, [string]$Detail) {
    $script:results.Add([pscustomobject]@{ Name = $Name; Ok = $Ok; Detail = $Detail }) | Out-Null
    if (-not $Ok) { $script:failed = $true }
}

function Invoke-Step {
    param(
        [string]$Name,
        [string]$WorkingDirectory,
        [string[]]$Command
    )
    Write-Step $Name
    Write-Host ("    cd {0}" -f $WorkingDirectory)
    Write-Host ("    {0}" -f ($Command -join ' '))
    Push-Location $WorkingDirectory
    try {
        $prevEap = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        & $Command[0] @($Command[1..($Command.Count - 1)]) 2>&1 | ForEach-Object {
            if ($_ -is [System.Management.Automation.ErrorRecord]) {
                Write-Host $_.ToString()
            }
            else {
                Write-Host $_
            }
        }
        $ErrorActionPreference = $prevEap
        $code = $LASTEXITCODE
        if ($null -eq $code) { $code = 0 }
        Add-Result -Name $Name -Ok ($code -eq 0) -Detail ("exit={0}" -f $code)
        return $code
    }
    finally {
        Pop-Location
    }
}

if ($Fast) {
    $SkipFrontendBuild = $true
}

Write-Host "AI Landing Factory - Release Check"
Write-Host ("Root: {0}" -f $RootDir)
if ($Full) {
    Write-Host "Gate: Full Dev"
}
else {
    Write-Host "Gate: Simple Release"
}

Write-Step "Preconditions"
if (-not (Test-Path $RootDir)) {
    Write-Error "Root not found"
    exit 1
}
Write-Host "OK: root exists"

if (-not (Test-Path $PythonExe)) {
    Add-Result -Name "venv" -Ok $false -Detail "missing .venv - run .\run.ps1"
    Write-Host "FAIL: .venv not found. Run .\run.ps1"
}
else {
    Add-Result -Name "venv" -Ok $true -Detail $PythonExe
    Write-Host "OK: .venv exists"
}

if (-not (Test-Path $BackendEnv)) {
    Add-Result -Name "backend/.env" -Ok $false -Detail "missing - copy backend/.env.example"
    Write-Host "FAIL: backend/.env missing"
}
else {
    Add-Result -Name "backend/.env" -Ok $true -Detail $BackendEnv
    Write-Host "OK: backend/.env exists"
    $envLines = Get-Content -Path $BackendEnv -Encoding UTF8
    $modeLine = $envLines | Where-Object { $_ -match '^\s*PRODUCT_MODE\s*=' } | Select-Object -First 1
    if ($modeLine -match '=\s*simple\s*$') {
        Add-Result -Name "PRODUCT_MODE" -Ok $true -Detail "simple"
        Write-Host "OK: PRODUCT_MODE=simple"
    }
    elseif (-not $modeLine) {
        Add-Result -Name "PRODUCT_MODE" -Ok $true -Detail "unset (default simple in config.py)"
        Write-Host "OK: PRODUCT_MODE unset (defaults to simple)"
    }
    else {
        $detail = $modeLine.Trim()
        Add-Result -Name "PRODUCT_MODE" -Ok $false -Detail $detail
        Write-Host ("FAIL: expected PRODUCT_MODE=simple, got: {0}" -f $detail)
    }
}

Invoke-Step -Name "Git hygiene" -WorkingDirectory $RootDir -Command @(
    "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
    "-File", (Join-Path $RootDir "scripts\check_git_hygiene.ps1")
)

Invoke-Step -Name "Simple dependency audit" -WorkingDirectory $BackendDir -Command @(
    $PythonExe, "scripts\audit_simple_dependencies.py"
)

if ($Full) {
    Invoke-Step -Name "check_all simple (Full gate base)" -WorkingDirectory $RootDir -Command @(
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", (Join-Path $RootDir "scripts\check_all.ps1"),
        "-Simple", "-SkipFrontendBuild"
    )
}
else {
    Invoke-Step -Name "check_all simple" -WorkingDirectory $RootDir -Command @(
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", (Join-Path $RootDir "scripts\check_all.ps1"),
        "-Simple", "-SkipFrontendBuild"
    )
}

$pytestFiles = @(
    "tests/test_product_mode_simple.py",
    "tests/test_style_config_persistence.py",
    "tests/test_export_theme_api.py",
    "tests/test_export_theme_tokens.py",
    "tests/test_export_interactive.py",
    "tests/test_university_export_offline.py"
)
Invoke-Step -Name "Backend targeted pytest" -WorkingDirectory $BackendDir -Command @(
    @($PythonExe, "-m", "pytest") + $pytestFiles + @("-q")
)

Invoke-Step -Name "Frontend npm test" -WorkingDirectory $FrontendDir -Command @($NpmExe, "test")

if (-not $SkipFrontendBuild) {
    Invoke-Step -Name "Frontend npm build" -WorkingDirectory $FrontendDir -Command @($NpmExe, "run", "build")
}
else {
    Write-Step "Frontend npm build"
    Write-Host "SKIP: -SkipFrontendBuild or -Fast"
    Add-Result -Name "Frontend npm build" -Ok $true -Detail "skipped"
}

if ($Full) {
    if ($SkipShowcaseSmoke) {
        Write-Step "Showcase ZIP export smoke"
        Write-Host "SKIP: Showcase smoke skipped by user." -ForegroundColor Yellow
        Add-Result -Name "Showcase ZIP export smoke" -Ok $true -Detail "skipped by -SkipShowcaseSmoke"
        Add-Result -Name "Showcase registry smoke" -Ok $true -Detail "skipped by -SkipShowcaseSmoke"
        Add-Result -Name "Showcase registry/exporter tests" -Ok $true -Detail "skipped by -SkipShowcaseSmoke"
    }
    else {
        Invoke-Step -Name "Showcase ZIP export smoke" -WorkingDirectory $BackendDir -Command @(
            $PythonExe, "scripts\smoke_showcase_zip_export.py"
        )
        Invoke-Step -Name "Showcase registry smoke" -WorkingDirectory $BackendDir -Command @(
            $PythonExe, "scripts\smoke_showcase_registry.py"
        )
        Invoke-Step -Name "Showcase registry/exporter tests" -WorkingDirectory $BackendDir -Command @(
            $PythonExe, "-m", "pytest",
            "tests/test_showcase_zip_exporter.py",
            "tests/test_showcase_exporter.py",
            "tests/test_showcase_registry.py",
            "tests/test_showcase_api.py",
            "-q"
        )
    }
}
else {
    Write-Step "Showcase ZIP export smoke"
    Write-Host "SKIP: Showcase ZIP export smoke is Full gate only."
    Add-Result -Name "Showcase ZIP export smoke" -Ok $true -Detail "Full gate only"
    Write-Step "Showcase registry smoke"
    Write-Host "SKIP: Showcase registry smoke is Full gate only."
    Add-Result -Name "Showcase registry smoke" -Ok $true -Detail "Full gate only"
    Add-Result -Name "Showcase registry/exporter tests" -Ok $true -Detail "Full gate only"
}

Write-Step "Git status (informational)"
git status --short
if ($LASTEXITCODE -ne 0) {
    Add-Result -Name "git status" -Ok $false -Detail "git status failed"
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor DarkGray
Write-Host "RELEASE CHECK SUMMARY" -ForegroundColor DarkGray
Write-Host "==================================================" -ForegroundColor DarkGray
foreach ($r in $results) {
    $status = if ($r.Ok) { "PASS" } else { "FAIL" }
    $color = if ($r.Ok) { "Green" } else { "Red" }
    Write-Host ("{0,-28} {1} ({2})" -f $r.Name, $status, $r.Detail) -ForegroundColor $color
}

Write-Host ""
if ($failed) {
    Write-Host "RELEASE CHECK: FAIL" -ForegroundColor Red
    exit 1
}
Write-Host "RELEASE CHECK: PASS" -ForegroundColor Green
exit 0
