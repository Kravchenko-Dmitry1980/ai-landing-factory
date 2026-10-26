# Packs a release archive for the server from a git commit (default HEAD).
#
# git archive takes exactly what is committed: no local data, accounts, .env files,
# node_modules or caches can slip in, and with autocrlf off every file keeps the LF
# line endings it has in the repository (shell scripts with CRLF fail on Ubuntu).
#
#   pwsh scripts/build_full_release.ps1            # HEAD
#   pwsh scripts/build_full_release.ps1 -Ref v1.2  # a tag or another commit

param(
    [string]$Ref = "HEAD",
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

if ($Help) {
    Write-Host "build_full_release.ps1 [-Ref <commit>] - release zip from a git commit (no local data, LF endings)."
    exit 0
}

$commit = & git -C $Root rev-parse --verify --short "$Ref^{commit}" 2>$null
if ($LASTEXITCODE -ne 0 -or -not $commit) { throw "Unknown git ref: $Ref" }
$commit = $commit.Trim()
$dirty = & git -C $Root status --porcelain
if ($Ref -eq "HEAD" -and $dirty) {
    Write-Warning "Changes not committed (and new files not added) are NOT in the release, it is built from commit ${commit}:"
    $dirty | Select-Object -First 15 | ForEach-Object { Write-Warning "  $_" }
}

# Scripts must be executable in git itself: with core.filemode=false on Windows the bit is not
# taken from the disk (set it with: git add --chmod=+x <file>).
$notExecutable = & git -C $Root ls-tree -r $Ref -- deploy |
    Where-Object { $_ -match '^(\d+) blob \S+\t(.+\.sh)$' -and $Matches[1] -ne '100755' } |
    ForEach-Object { ($_ -split "`t", 2)[1] }
if ($LASTEXITCODE -ne 0) { throw "git ls-tree failed for $Ref" }
if ($notExecutable) { throw "Not executable in git (git add --chmod=+x): $($notExecutable -join ', ')" }

$stamp = Get-Date -Format "yyyyMMdd_HHmm"
$outDir = Join-Path $Root ".runtime\release"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$zipPath = Join-Path $outDir "lend-release-$stamp-$commit.zip"
if (Test-Path $zipPath) { Remove-Item -Force $zipPath }

& git -C $Root -c core.autocrlf=false archive --format=zip -o $zipPath $Ref
if ($LASTEXITCODE -ne 0) { throw "git archive failed" }

# --- checks of the archive itself ---------------------------------------------------
$required = @(
    ".dockerignore",
    "deploy/docker/docker-compose.yml",
    "deploy/docker/backend.Dockerfile",
    "deploy/docker/frontend.Dockerfile",
    "deploy/docker/.env.docker.example",
    "deploy/docker/gateway/http.conf",
    "deploy/docker/gateway/https.conf",
    "deploy/docker/gateway/routes.inc",
    "deploy/docker/gateway/proxy.conf",
    "deploy/docker/docker-compose.traefik.yml",
    "deploy/docker/lib.sh",
    "deploy/docker/backup.sh",
    "deploy/docker/restore.sh",
    "deploy/docker/healthcheck.sh",
    "deploy/ubuntu/README_DOCKER_FIRST_DEPLOY.md",
    "backend/requirements.txt",
    "backend/app/main.py",
    "frontend/package.json",
    "frontend/package-lock.json"
)
# Files the server runs as they are: one carriage return breaks them.
$mustBeLf = '\.(sh|conf|inc|service)$|Dockerfile$|docker-compose(\.\w+)?\.yml$|\.env\.docker\.example$'
$forbidden = '(^|/)\.env$|(^|/)\.env\.local$|(^|/)node_modules/|(^|/)\.venv/|(^|/)\.git/|^backend/data/|\.sqlite3$|dev-accounts|\.pem$'

Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [IO.Compression.ZipFile]::OpenRead($zipPath)
try {
    $names = $zip.Entries | ForEach-Object { $_.FullName }
    $bad = $names | Where-Object { $_ -match $forbidden }
    if ($bad) { throw "Archive contains forbidden entries: $(($bad | Select-Object -First 10) -join ', ')" }

    $missing = $required | Where-Object { $names -notcontains $_ }
    if ($missing) { throw "Archive misses required files: $($missing -join ', ')" }

    $crlf = @()
    foreach ($entry in $zip.Entries | Where-Object { $_.FullName -match $mustBeLf }) {
        $stream = $entry.Open()
        try {
            $buffer = New-Object System.IO.MemoryStream
            $stream.CopyTo($buffer)
            if ([Array]::IndexOf($buffer.ToArray(), [byte]13) -ge 0) { $crlf += $entry.FullName }
        }
        finally { $stream.Dispose() }
    }
    if ($crlf) { throw "CRLF line endings in files the server runs: $($crlf -join ', ')" }
}
finally {
    $zip.Dispose()
}

Write-Host ""
Write-Host "Release OK" -ForegroundColor Green
Write-Host "  Commit:  $commit ($Ref)"
Write-Host "  Archive: $zipPath"
Write-Host ("  Size:    {0:N1} MB" -f ((Get-Item $zipPath).Length / 1MB))
Write-Host "  Server:  deploy/ubuntu/README_DOCKER_FIRST_DEPLOY.md"
