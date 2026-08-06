# Thin PowerShell shim around scripts/install.py for Windows users.
# Use install.py directly for full cross-platform behavior; this script
# exists for muscle-memory `.\install.ps1` usage on Windows.

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

$python = (Get-Command python -ErrorAction SilentlyContinue) `
    ?? (Get-Command python3 -ErrorAction SilentlyContinue) `
    ?? (Get-Command py -ErrorAction SilentlyContinue)

if (-not $python) {
    Write-Error "Python 3.10+ is required. Install from https://www.python.org/downloads/"
    exit 1
}

& $python.Path "$here\install.py" $args
exit $LASTEXITCODE

