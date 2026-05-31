#Requires -Version 5.1
<#
.SYNOPSIS
  Parse-check PowerShell entry scripts (no execution).
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$scripts = @(
    (Join-Path $RootDir "run.ps1"),
    (Join-Path $RootDir "scripts\smoke_simple_product.ps1"),
    (Join-Path $RootDir "scripts\check_all.ps1"),
    (Join-Path $RootDir "scripts\release_check.ps1"),
    (Join-Path $RootDir "scripts\check_git_hygiene.ps1"),
    (Join-Path $RootDir "scripts\start_dev.ps1")
)

$failed = 0
foreach ($path in $scripts) {
    if (-not (Test-Path $path)) {
        Write-Host "MISSING: $path"
        $failed++
        continue
    }
    $tokens = $null
    $errors = $null
    $null = [System.Management.Automation.Language.Parser]::ParseFile(
        $path,
        [ref]$tokens,
        [ref]$errors
    )
    if ($errors -and $errors.Count -gt 0) {
        Write-Host "FAIL: $path"
        foreach ($err in $errors) {
            Write-Host "  $($err.Message)"
        }
        $failed++
    }
    else {
        Write-Host "OK: $path"
    }
}

$checkAllPath = Join-Path $RootDir "scripts\check_all.ps1"
if (Test-Path $checkAllPath) {
    $checkAllText = Get-Content -Path $checkAllPath -Raw -Encoding UTF8
    $contractChecks = @(
        @{ Name = "check_all defines -Simple switch"; Pattern = '\[switch\]\$Simple' },
        @{ Name = "Simple skips OCR smoke by default"; Pattern = '\$RunOcrSmoke = \$false' },
        @{ Name = "Simple skips VLM contract smoke"; Pattern = '\$SkipVlmContractSmoke = \$true' },
        @{ Name = "University export uses offline smoke"; Pattern = 'scripts\\smoke_university_export\.py", "--offline"' }
    )
    foreach ($check in $contractChecks) {
        if ($checkAllText -match $check.Pattern) {
            Write-Host ("OK: {0}" -f $check.Name)
        }
        else {
            Write-Host ("FAIL: {0}" -f $check.Name)
            $failed++
        }
    }
}

$runPs1Path = Join-Path $RootDir "run.ps1"
if (Test-Path $runPs1Path) {
    $runPs1Text = Get-Content -Path $runPs1Path -Raw -Encoding UTF8
    $runChecks = @(
        @{ Name = "run.ps1 defines Clear-ProxyEnv"; Pattern = 'function Clear-ProxyEnv' },
        @{ Name = "run.ps1 defines Invoke-PipSafe"; Pattern = 'function Invoke-PipSafe' },
        @{ Name = "run.ps1 pip uses --no-cache-dir"; Pattern = '--no-cache-dir' },
        @{ Name = "run.ps1 pip uses pypi index"; Pattern = 'https://pypi\.org/simple' },
        @{ Name = "run.ps1 avoids --proxy empty string"; Pattern = '--proxy ""'; ShouldNotMatch = $true },
        @{ Name = "run.ps1 avoids --isolated"; Pattern = '--isolated'; ShouldNotMatch = $true }
    )
    foreach ($check in $runChecks) {
        $matched = $runPs1Text -match $check.Pattern
        $invert = $check.ContainsKey("ShouldNotMatch") -and $check.ShouldNotMatch
        $ok = if ($invert) { -not $matched } else { $matched }
        if ($ok) {
            Write-Host ("OK: {0}" -f $check.Name)
        }
        else {
            Write-Host ("FAIL: {0}" -f $check.Name)
            $failed++
        }
    }
}

$releaseCheckPath = Join-Path $RootDir "scripts\release_check.ps1"
if (Test-Path $releaseCheckPath) {
    $releaseCheckText = Get-Content -Path $releaseCheckPath -Raw -Encoding UTF8
    $releaseChecks = @(
        @{ Name = "release_check defines -Full switch"; Pattern = '\[switch\]\$Full' },
        @{ Name = "release_check defines -SkipShowcaseSmoke"; Pattern = '\[switch\]\$SkipShowcaseSmoke' },
        @{ Name = "release_check references showcase ZIP smoke script"; Pattern = 'smoke_showcase_zip_export\.py' },
        @{ Name = "release_check Full gate guards showcase ZIP smoke"; Pattern = '(?s)if \(\$Full\).*smoke_showcase_zip_export\.py' },
        @{ Name = "release_check simple skips showcase ZIP smoke"; Pattern = 'Full gate only' }
    )
    foreach ($check in $releaseChecks) {
        $matched = $releaseCheckText -match $check.Pattern
        if ($matched) {
            Write-Host ("OK: {0}" -f $check.Name)
        }
        else {
            Write-Host ("FAIL: {0}" -f $check.Name)
            $failed++
        }
    }
}

if ($failed -gt 0) {
    exit 1
}
Write-Host "PS1 syntax: PASS"
exit 0
