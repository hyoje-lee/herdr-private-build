$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$activate = Join-Path $root ".venv\Scripts\Activate.ps1"
if (Test-Path $activate) {
    . $activate
}
python (Join-Path $root "scripts\secure_build.py") app @args
exit $LASTEXITCODE
