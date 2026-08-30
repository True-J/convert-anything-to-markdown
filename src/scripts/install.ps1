# Thin PowerShell shim around scripts/install.py for Windows users.
# Use install.py directly for full cross-platform behavior; this script
# exists for muscle-memory `.\install.ps1` usage on Windows.

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

# Prefer `python`, then `python3`, then the Windows Store `py` launcher.
# Chosen via a loop (not the PowerShell 7 `??` null-coalescing operator)
# so this shim also runs under Windows PowerShell 5.1.
$python = $null
foreach ($name in "python", "python3", "py") {
    $cand = Get-Command $name -ErrorAction SilentlyContinue
    if ($cand) { $python = $cand; break }
}

if (-not $python) {
    Write-Error "Python 3.10+ is required. Install from https://www.python.org/downloads/"
    exit 1
}

& $python.Path "$here\install.py" $args
exit $LASTEXITCODE

