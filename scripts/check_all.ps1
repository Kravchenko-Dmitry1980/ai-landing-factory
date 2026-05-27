#Requires -Version 5.1
<#
.SYNOPSIS
  One-command QA pipeline for AI Landing Factory.

.EXAMPLE
  .\scripts\check_all.ps1

.EXAMPLE
  .\scripts\check_all.ps1 -ProjectId 55a98f90-73fc-4d26-a477-3c974a0cbeed -FailFast

.EXAMPLE
  .\scripts\check_all.ps1 -SkipFrontendBuild -VerboseOutput
#>
[CmdletBinding()]
param(
    [string]$ProjectId = "55a98f90-73fc-4d26-a477-3c974a0cbeed",
    [string]$BackendUrl,
    [string]$FrontendUrl,
    [switch]$SkipBackendTests,
    [switch]$SkipCorpusSmoke,
    [switch]$SkipFrontendBuild,
    [switch]$SkipVisualSmoke,
    [switch]$SkipVisualClassifierSmoke,
    [switch]$SkipVlmContractSmoke,
    [switch]$SkipPublicExportSmoke,
    [switch]$SkipLiveMultifileSmoke,
    [switch]$RunOcrSmoke,
    [switch]$Simple,
    [switch]$FailFast,
    [switch]$VerboseOutput
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
}
catch { }

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$EnvLocalPath = Join-Path $FrontendDir ".env.local"
. (Join-Path $PSScriptRoot "lib\ports.ps1")
$PythonExe = Join-Path $RootDir ".venv\Scripts\python.exe"
$npmCmd = Get-Command npm.cmd -ErrorAction SilentlyContinue
if ($npmCmd) { $NpmExe = $npmCmd.Source } else { $NpmExe = "npm.cmd" }
$NodeExe = "C:\Program Files\nodejs\node.exe"
if (-not (Test-Path $NodeExe)) {
    $nodeCmd = Get-Command node.exe -ErrorAction SilentlyContinue
    if ($nodeCmd) { $NodeExe = $nodeCmd.Source } else { $NodeExe = "node" }
}
$LogDir = Join-Path $RootDir "logs\qa"
$LogFile = Join-Path $LogDir ("check_all_{0:yyyyMMdd_HHmmss}.log" -f (Get-Date))
$PortsFile = Join-Path $RootDir ".runtime\ports.json"

$defaultBackendUrl = "http://127.0.0.1:8001"
$defaultFrontendUrl = "http://localhost:3000"
$usedRuntimePorts = $false

if (-not $PSBoundParameters.ContainsKey("BackendUrl") -and -not $PSBoundParameters.ContainsKey("FrontendUrl")) {
    if (Test-Path $PortsFile) {
        try {
            $runtimePorts = Get-Content -Path $PortsFile -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($runtimePorts.backend_url) { $BackendUrl = [string]$runtimePorts.backend_url }
            if ($runtimePorts.frontend_url) { $FrontendUrl = [string]$runtimePorts.frontend_url }
            $usedRuntimePorts = $true
        }
        catch {
            Write-Warning "Could not read $PortsFile - using default URLs."
        }
    }
}

if ([string]::IsNullOrWhiteSpace($BackendUrl)) {
    $BackendUrl = $defaultBackendUrl
}
if ([string]::IsNullOrWhiteSpace($FrontendUrl)) {
    $FrontendUrl = $defaultFrontendUrl
}

$BackendUrl = $BackendUrl.TrimEnd("/")
$FrontendUrl = $FrontendUrl.TrimEnd("/")

$script:Results = @()
$script:ShouldStop = $false

function Write-Log {
    param(
        [string]$Message,
        [switch]$ConsoleOnly
    )
    $line = "[{0:yyyy-MM-dd HH:mm:ss}] {1}" -f (Get-Date), $Message
    if (-not $ConsoleOnly) {
        Add-Content -Path $script:LogFile -Value $line -Encoding UTF8
    }
    Write-Host $Message
}

function Write-LogBlock {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return }
    foreach ($row in ($Text -split "`r?`n")) {
        Write-Log $row -ConsoleOnly
        Add-Content -Path $script:LogFile -Value $row -Encoding UTF8
    }
}

function Test-HttpAvailable {
    param(
        [string]$Url,
        [int]$TimeoutSec = 8
    )
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec -Method Get
        return @{
            Ok     = $true
            Status = [int]$response.StatusCode
            Error  = ""
        }
    }
    catch {
        $status = 0
        if ($null -ne $_.Exception.Response) {
            try { $status = [int]$_.Exception.Response.StatusCode.value__ } catch { }
        }
        $message = $_.Exception.Message
        if ($message -match "Unable to connect|actively refused|connection attempt failed") {
            $message = "connection refused or host unreachable"
        }
        return @{
            Ok     = $false
            Status = $status
            Error  = $message
        }
    }
}

function Add-Result {
    param(
        [string]$Name,
        [string]$Status,
        [double]$DurationSec,
        [string]$Message = ""
    )
    $script:Results += [PSCustomObject]@{
        Name        = $Name
        Status      = $Status
        DurationSec = [math]::Round($DurationSec, 1)
        Message     = $Message
    }
}

function Invoke-QACommand {
    param(
        [string]$Name,
        [string]$WorkingDirectory,
        [string[]]$Command,
        [switch]$Skip,
        [string]$SkipReason = "",
        [switch]$RequireBackend,
        [switch]$RequireFrontend,
        [string]$BackendUnavailableMessage = "",
        [string]$FrontendUnavailableMessage = ""
    )

    if ($script:ShouldStop) {
        Add-Result -Name $Name -Status "SKIP" -DurationSec 0 -Message "FailFast: earlier step failed"
        return
    }

    if ($Skip) {
        Write-Log ("SKIP: {0} - {1}" -f $Name, $SkipReason)
        Add-Result -Name $Name -Status "SKIP" -DurationSec 0 -Message $SkipReason
        return
    }

    if ($RequireBackend -and -not $script:BackendAvailable) {
        Write-Log ("FAIL: {0} - backend unavailable" -f $Name)
        Write-Log $BackendUnavailableMessage
        Add-Result -Name $Name -Status "FAIL" -DurationSec 0 -Message $BackendUnavailableMessage
        if ($FailFast) { $script:ShouldStop = $true }
        return
    }

    if ($RequireFrontend -and -not $script:FrontendAvailable) {
        Write-Log ("FAIL: {0} - frontend unavailable" -f $Name)
        Write-Log $FrontendUnavailableMessage
        Add-Result -Name $Name -Status "FAIL" -DurationSec 0 -Message $FrontendUnavailableMessage
        if ($FailFast) { $script:ShouldStop = $true }
        return
    }

    $exe = $Command[0]
    $args = @()
    if ($Command.Count -gt 1) {
        $args = $Command[1..($Command.Count - 1)]
    }

    Write-Log ""
    Write-Log ("START: {0}" -f $Name)
    Write-Log ("    cd {0}" -f $WorkingDirectory)
    Write-Log ("    {0} {1}" -f $exe, ($args -join ' '))

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $output = ""
    $exitCode = 0

    Push-Location $WorkingDirectory
    try {
        $lines = [System.Collections.Generic.List[string]]::new()
        if ($VerboseOutput) {
            & $exe @args 2>&1 | ForEach-Object {
                $line = if ($_ -is [System.Management.Automation.ErrorRecord]) { $_.ToString() } else { $_.ToString() }
                $lines.Add($line)
                Write-LogBlock $line
            }
        }
        else {
            & $exe @args 2>&1 | ForEach-Object {
                $line = if ($_ -is [System.Management.Automation.ErrorRecord]) { $_.ToString() } else { $_.ToString() }
                $lines.Add($line)
            }
            $output = $lines -join "`n"
            Write-LogBlock $output
        }
        $output = $lines -join "`n"
        if ($null -ne $LASTEXITCODE -and $LASTEXITCODE -ne 0) {
            $exitCode = [int]$LASTEXITCODE
        }
        elseif (-not $?) {
            $exitCode = 1
        }
    }
    catch {
        $output = $_.Exception.Message
        Write-LogBlock $output
        $exitCode = 1
    }
    finally {
        Pop-Location
    }
    $sw.Stop()

    $status = if ($exitCode -eq 0) { "PASS" } else { "FAIL" }
    $tail = ""
    if ($status -eq "FAIL" -and -not [string]::IsNullOrWhiteSpace($output)) {
        $tail = ($output.Trim() -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -Last 6) -join '; '
    }

    $dur = [math]::Round($sw.Elapsed.TotalSeconds, 1)
    Write-Log ("DONE: {0} - {1} (exit={2}, {3}s)" -f $Name, $status, $exitCode, $dur)
    Add-Result -Name $Name -Status $status -DurationSec $sw.Elapsed.TotalSeconds -Message $tail

    if ($status -eq "FAIL" -and $FailFast) {
        $script:ShouldStop = $true
    }
}

function Write-Summary {
    Write-Log ""
    Write-Log "=================================================="
    Write-Log "AI LANDING FACTORY QA SUMMARY"
    Write-Log "=================================================="
    Write-Log ""
    Write-Log ("{0,-30} {1,-10} {2}" -f "Check", "Status", "Duration")

    $hasFail = $false
    $hasSkipRequired = $false

    foreach ($r in $script:Results) {
        $dur = if ($r.DurationSec -gt 0) { "{0}s" -f $r.DurationSec } else { "-" }
        Write-Log ("{0,-30} {1,-10} {2}" -f $r.Name, $r.Status, $dur)
        if ($r.Status -eq "FAIL") { $hasFail = $true }
        if ($r.Message) {
            Write-Log ("  -> {0}" -f ($r.Message -replace "`r?`n", " "))
        }
    }

    foreach ($r in $script:Results) {
        if ($r.Status -eq "SKIP" -and $r.Message -notmatch "^FailFast") {
            $hasSkipRequired = $true
        }
    }

    Write-Log ""
    if ($hasFail) {
        Write-Log "Overall: FAIL"
        $script:FinalExitCode = 1
    }
    else {
        Write-Log "Overall: PASS"
        $script:FinalExitCode = 0
    }

    Write-Log ""
    Write-Log "Active URLs:"
    Write-Log "  Backend:  $BackendUrl"
    Write-Log "  Frontend: $FrontendUrl"
    if ($script:NextPublicApiUrlSummary) {
        Write-Log "  NEXT_PUBLIC_API_URL: $script:NextPublicApiUrlSummary"
    }
    if ($usedRuntimePorts) {
        Write-Log "  (from .runtime/ports.json)"
    }
    Write-Log ""
    Write-Log "Log file: $script:LogFile"
    Write-Log "Exit code: $script:FinalExitCode"
}

# --- Bootstrap ---
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

Write-Log "AI Landing Factory - check_all QA pipeline"
Write-Log "Root:       $RootDir"
Write-Log "ProjectId:  $ProjectId"
Write-Log "BackendUrl: $BackendUrl"
Write-Log "FrontendUrl:$FrontendUrl"
if ($usedRuntimePorts) {
    Write-Log "Ports file: $PortsFile (active dev URLs)"
}
Write-Log "Log:        $LogFile"
Write-Log "Options:    FailFast=$($FailFast.IsPresent) SkipBackendTests=$($SkipBackendTests.IsPresent) SkipCorpusSmoke=$($SkipCorpusSmoke.IsPresent) SkipFrontendBuild=$($SkipFrontendBuild.IsPresent) SkipVisualSmoke=$($SkipVisualSmoke.IsPresent) SkipPublicExportSmoke=$($SkipPublicExportSmoke.IsPresent)"

if (-not (Test-Path $BackendDir)) {
    Write-Log "FATAL: backend directory not found: $BackendDir"
    exit 1
}
if (-not (Test-Path $FrontendDir)) {
    Write-Log "FATAL: frontend directory not found: $FrontendDir"
    exit 1
}
if (-not (Test-Path $PythonExe)) {
    Write-Log "FATAL: venv Python not found: $PythonExe"
    Write-Log "Create venv at project root: python -m venv .venv"
    exit 1
}

$script:FinalExitCode = 1

if ($Simple) {
    $SkipVisualClassifierSmoke = $true
    $SkipVlmContractSmoke = $true
    $SkipVisualSmoke = $true
    $SkipLiveMultifileSmoke = $true
    $SkipFrontendBuild = $true
    $SkipBackendTests = $true
    $RunOcrSmoke = $false
    Write-Log "Mode: Simple (skip OCR/VLM/visual/live multifile/full pytest)"
}

$backendPrivacyUrl = "$BackendUrl/api/v1/projects/privacy"
Write-Log ""
Write-Log "=== Server availability ==="

$nextPublicApiUrl = ""
if (Test-Path $EnvLocalPath) {
    $envLine = Get-Content -Path $EnvLocalPath -Encoding UTF8 | Where-Object { $_ -match "^NEXT_PUBLIC_API_URL=" } | Select-Object -First 1
    if ($envLine) {
        $nextPublicApiUrl = ($envLine -replace "^NEXT_PUBLIC_API_URL=", "").Trim()
    }
}
if ($nextPublicApiUrl) {
    Write-Log "NEXT_PUBLIC_API_URL: $nextPublicApiUrl"
    $script:NextPublicApiUrlSummary = $nextPublicApiUrl
}
else {
    Write-Log "NEXT_PUBLIC_API_URL: (frontend/.env.local not found)"
}

$activeCorsOrigins = ""
if ($usedRuntimePorts -and (Test-Path $PortsFile)) {
    try {
        $runtimePortsDetail = Get-Content -Path $PortsFile -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($runtimePortsDetail.cors_origins) {
            $activeCorsOrigins = [string]$runtimePortsDetail.cors_origins
        }
    }
    catch { }
}
if ($activeCorsOrigins) {
    Write-Log "CORS origins (start_dev): $activeCorsOrigins"
}
else {
    Write-Log "CORS origins: dev default localhost/127.0.0.1 :3000-3050 (see backend/app/config.py)"
}

$backendProbe = Test-HttpAvailable -Url $backendPrivacyUrl
$frontendProbe = Test-HttpAvailable -Url $FrontendUrl

$script:BackendAvailable = $backendProbe.Ok
$script:FrontendAvailable = $frontendProbe.Ok

if ($script:BackendAvailable) {
    Write-Log ("Backend:  OK [{0}] HTTP {1}" -f $backendPrivacyUrl, $backendProbe.Status)
}
else {
    Write-Log ("Backend:  FAIL [{0}]" -f $backendPrivacyUrl)
    Write-Log "Backend недоступен."
    Write-Log "Запустите:"
    Write-Log ".\scripts\start_dev.ps1"
    Write-Log "или вручную:"
    Write-Log "cd C:\Dima\Projects\CURSOR\Lend\backend"
    Write-Log "..\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8001"
    if ($backendProbe.Error) { Write-Log "  ($($backendProbe.Error))" }
}

if ($script:FrontendAvailable) {
    Write-Log ("Frontend: OK [{0}] HTTP {1}" -f $FrontendUrl, $frontendProbe.Status)
    $corsOrigin = $FrontendUrl
    $corsProbe = Test-CorsPreflight -BackendUrl $BackendUrl -Origin $corsOrigin
    if ($corsProbe.Ok -and $corsProbe.AllowOrigin -eq $corsOrigin) {
        Write-Log ("CORS:     OK [Origin {0}] allow-origin={1}" -f $corsOrigin, $corsProbe.AllowOrigin)
    }
    else {
        Write-Log ("CORS:     FAIL [Origin {0}] HTTP {1}" -f $corsOrigin, $corsProbe.Status)
        if ($corsProbe.Error) { Write-Log "  ($($corsProbe.Error))" }
        Write-Log "Browser UI may show 'Backend nedostupen' - restart via .\scripts\start_dev.ps1"
    }
    $previewProbeUrl = "${FrontendUrl}/preview/${ProjectId}?style=university_platform"
    $previewProbe = Test-HttpAvailable -Url $previewProbeUrl -TimeoutSec 15
    if ($previewProbe.Ok) {
        Write-Log ("Preview:  OK [{0}] HTTP {1}" -f $previewProbeUrl, $previewProbe.Status)
    }
    else {
        Write-Log ("Preview:  FAIL [{0}] HTTP {1}" -f $previewProbeUrl, $previewProbe.Status)
        Write-Log "Preview route unhealthy (often stale node on :3000)."
        Write-Log "Restart frontend: cd frontend && npm run dev"
        if (-not $SkipVisualSmoke) {
            $script:FrontendAvailable = $false
        }
    }
}
else {
    Write-Log ("Frontend: FAIL [{0}]" -f $FrontendUrl)
    Write-Log "Frontend недоступен."
    Write-Log "Запустите:"
    Write-Log ".\scripts\start_dev.ps1"
    Write-Log "или вручную:"
    Write-Log "cd C:\Dima\Projects\CURSOR\Lend\frontend"
    Write-Log "npm run dev"
    if ($frontendProbe.Error) { Write-Log "  ($($frontendProbe.Error))" }
}

$backendDownMsg = "Backend unavailable - start uvicorn on $BackendUrl"
$frontendDownMsg = "Frontend unavailable - run npm run dev on $FrontendUrl"

# --- Pipeline ---
Write-Log ""
Write-Log "=== QA pipeline ==="

Invoke-QACommand -Name "PS1 syntax" `
    -WorkingDirectory $RootDir `
    -Command @(
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", (Join-Path $RootDir "scripts\test_ps1_syntax.ps1")
    )

Invoke-QACommand -Name "Simple product smoke" `
    -WorkingDirectory $BackendDir `
    -Command @($PythonExe, "scripts\smoke_simple_product_mode.py") `
    -Skip:(-not $Simple) `
    -SkipReason "Use -Simple to run product smoke"

Invoke-QACommand -Name "Product mode tests" `
    -WorkingDirectory $BackendDir `
    -Command @($PythonExe, "-m", "pytest", "tests\test_product_mode_simple.py", "-q") `
    -Skip:(-not $Simple) `
    -SkipReason "Use -Simple to run product mode tests"

Invoke-QACommand -Name "PII env" `
    -WorkingDirectory $BackendDir `
    -Command @($PythonExe, "scripts\check_pii_env.py") `
    -Skip:$Simple `
    -SkipReason "Simple mode"

Invoke-QACommand -Name "Backend tests" `
    -WorkingDirectory $BackendDir `
    -Command @($PythonExe, "-m", "pytest", "tests\", "-q") `
    -Skip:$SkipBackendTests `
    -SkipReason "SkipBackendTests"

# Offline: lightweight text snapshots in test_corpus/golden (no binary uploads in git)
Invoke-QACommand -Name "Test corpus smoke" `
    -WorkingDirectory $BackendDir `
    -Command @($PythonExe, "scripts\smoke_corpus.py") `
    -Skip:$SkipCorpusSmoke `
    -SkipReason "SkipCorpusSmoke"

Invoke-QACommand -Name "Team group blocks smoke" `
    -WorkingDirectory $BackendDir `
    -Command @($PythonExe, "scripts\smoke_team_group_blocks.py") `
    -Skip:$SkipCorpusSmoke `
    -SkipReason "SkipCorpusSmoke"

Invoke-QACommand -Name "Visual classifier smoke" `
    -WorkingDirectory $BackendDir `
    -Command @($PythonExe, "scripts\smoke_visual_classifier.py") `
    -Skip:$SkipVisualClassifierSmoke `
    -SkipReason "SkipVisualClassifierSmoke"

Invoke-QACommand -Name "VLM adapter contract smoke" `
    -WorkingDirectory $BackendDir `
    -Command @($PythonExe, "scripts\smoke_vlm_adapter_contract.py") `
    -Skip:$SkipVlmContractSmoke `
    -SkipReason "SkipVlmContractSmoke"

if ($RunOcrSmoke) {
    Invoke-QACommand -Name "OCR env check" `
        -WorkingDirectory $BackendDir `
        -Command @($PythonExe, "scripts\check_ocr_env.py", "--require-ocr")

    Invoke-QACommand -Name "PPTX OCR team smoke" `
        -WorkingDirectory $BackendDir `
        -Command @($PythonExe, "scripts\smoke_pptx_ocr_team.py", "--require-ocr")
}
else {
    Write-Log "SKIP: OCR smoke (pass -RunOcrSmoke to enable)"
}

Invoke-QACommand -Name "Endocrinology acceptance" `
    -WorkingDirectory $BackendDir `
    -Command @($PythonExe, "scripts\smoke_endocrinology_acceptance.py", "--project-id", $ProjectId) `
    -Skip:$Simple `
    -SkipReason "Simple mode" `
    -RequireBackend `
    -BackendUnavailableMessage $backendDownMsg

Invoke-QACommand -Name "University export smoke" `
    -WorkingDirectory $BackendDir `
    -Command @($PythonExe, "scripts\smoke_university_export.py", "--project-id", $ProjectId, "--backend-url", $BackendUrl) `
    -RequireBackend `
    -BackendUnavailableMessage $backendDownMsg

Invoke-QACommand -Name "Export polish smoke" `
    -WorkingDirectory $BackendDir `
    -Command @($PythonExe, "scripts\smoke_public_export.py", "--project-id", $ProjectId, "--backend-url", $BackendUrl) `
    -Skip:($SkipPublicExportSmoke -or $Simple) `
    -SkipReason "SkipPublicExportSmoke or Simple" `
    -RequireBackend `
    -BackendUnavailableMessage $backendDownMsg

Invoke-QACommand -Name "Live multifile smoke" `
    -WorkingDirectory $BackendDir `
    -Command @($PythonExe, "scripts\smoke_live_multifile_project.py", "--backend-url", $BackendUrl, "--corpus-project", "indlab_telegram_news") `
    -Skip:$SkipLiveMultifileSmoke `
    -SkipReason "SkipLiveMultifileSmoke" `
    -RequireBackend `
    -BackendUnavailableMessage $backendDownMsg

Invoke-QACommand -Name "Frontend tests" `
    -WorkingDirectory $FrontendDir `
    -Command @($NpmExe, "test") `
    -Skip:$Simple `
    -SkipReason "Simple mode"

Invoke-QACommand -Name "Frontend build" `
    -WorkingDirectory $FrontendDir `
    -Command @($NpmExe, "run", "build") `
    -Skip:$SkipFrontendBuild `
    -SkipReason "SkipFrontendBuild"

Invoke-QACommand -Name "Visual acceptance smoke" `
    -WorkingDirectory $FrontendDir `
    -Command @(
        $NodeExe, "scripts\smoke-visual-acceptance.mjs",
        "--project-id", $ProjectId,
        "--frontend-url", $FrontendUrl,
        "--backend-url", $BackendUrl
    ) `
    -Skip:$SkipVisualSmoke `
    -SkipReason "SkipVisualSmoke" `
    -RequireBackend `
    -RequireFrontend `
    -BackendUnavailableMessage $backendDownMsg `
    -FrontendUnavailableMessage $frontendDownMsg

Write-Summary
exit $script:FinalExitCode
