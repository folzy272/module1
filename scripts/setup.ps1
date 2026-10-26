$ErrorActionPreference='Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker Desktop is not installed or not running' }
docker run --rm -v "${PWD}:/workspace" -w /workspace alpine:3.21 sh scripts/bootstrap.sh
if ($LASTEXITCODE -ne 0) { throw 'Setup failed - inspect console logs.' }
Write-Host 'Next: docker compose up -d'
